from asyncio.log import logger
from email.policy import default
from multiprocessing import context
from odoo.tools import float_compare
import datetime
from select import select
# import imp
from odoo import fields, models,api


class AmazonOrder(models.Model):
    _name = 'amazon.orders'
    _inherit = 'mail.thread'
    _description = 'Amazon Orders Managment'

    name = fields.Char("Item Title")
    amazon_order_id = fields.Char("Amazon Order ID")
    # partner_id = fields.Many2one("res.partner", "Customer")
    first_name = fields.Char("First Name")
    last_name = fields.Char("Last Name")
    order_status = fields.Char('Order Status')
    shipping_method = fields.Char("Ship Method")
    # date_order = fields.Datetime("Order Date")
    shipping_address = fields.Char("Ship To Address Line 1")
    shipping_zip = fields.Char("Ship To ZIP Code")
    delivery_city = fields.Char("Ship To City")
    delivery_country = fields.Char("Ship To Country or Region")
    product_id = fields.Many2one("product.product","Product")
    full_name = fields.Char("Ship To Name")
    product_status = fields.Char("Product Status")
    warehouse_id  = fields.Many2one('stock.warehouse')
    product_ref = fields.Char("Vendor Reference")
    quantity = fields.Char("Item Quantity")
    total_price = fields.Char("Item Cost")
    delivery_cost = fields.Char("Amount Delivery costs (€ incl. VAT)")
    phone = fields.Char('Phone Number')
    line_id = fields.Char('Line ID')
    billing_zip = fields.Char("Billing postcode")
    billing_city = fields.Char("Billing city")
    billing_country = fields.Char("Billing country")
    order_id = fields.Many2one('sale.order',"Sale Order")
    sku = fields.Char('SKU')
    warehouse = fields.Char('Warehouse Code')
    shop_id = fields.Many2one('amazon.seller','Shop')

    #new fields
    order_date = fields.Char("Order Place Date")
    req_ship_date = fields.Char("Required Ship Date")
    ship_method_code = fields.Char("Ship Method Code")
    shipping_address2 = fields.Char("Ship To Address Line 2")
    shipping_address3 = fields.Char("Ship To Address Line 3")
    shipping_state = fields.Char("Ship To State")
    is_gift = fields.Char("Is it Gift?")
    asin = fields.Char("ASIN")
    gift_meesage = fields.Char("Gift Message")
    tracking_id = fields.Char("Tracking ID")
    ship_date = fields.Char("Shipped Date")
    new_added_so = fields.Integer("New Added count",default=0)
    new_added_line = fields.Integer("New Added Line",default=0)
    existing_updated_line = fields.Integer("Existing Updated Line",default=0)

    @api.model_create_multi
    def create(self,vals):
        result = super(AmazonOrder,self).create(vals)
        for res in result:
            res.warehouse_id = self.env.context.get('warehouse_id')
            res.line_id = res.id
            res.shop_id = self.env.context.get('shop_id')
            # if res.shipping_address:
            #     if len(res.shipping_address) > 2:

            res.name = res.amazon_order_id

            #Code to handle price abnormality
            if res.total_price:
                if ',' in res.total_price:
                    res.total_price = res.total_price[::-1].replace(',','.',1)
                    res.total_price = res.total_price[::-1]
                if res.total_price.startswith('EUR'):
                    res.total_price = res.total_price.split(' ')[1]
                if res.total_price.endswith('EUR'):
                    res.total_price = res.total_price.split(' ')[0]
            
            
        return result
    
    #Creating Dummy Data for Amazon
    def create_dummy_data(self,order,partner_type):
        if not order.delivery_country:
            if order.warehouse in ['EGRG','EGRH','EGTD']:
                order.delivery_country = 'DE'
            else:
                order.delivery_country = 'GB'
        customer = self.env['res.partner'].create({
                        'company_type': 'person',
                        'type': partner_type,
                        'name': 'Amazon Customer',
                        'phone': '123456789',
                        'street': 'street one',
                        # 'amazon_customer_id': customer
                        'zip': '12345',
                        'city': 'Amazon Customer City',
                        'street_number': '1',
                        'country_id': self.env['res.country'].search([('code','=', order.delivery_country)],limit=1).id,
                })
        return customer

    def map_sale_orders(self):
        total_count = 0
        new_added_so = new_added_line = 0
        sale_orders = self.env['sale.order'].search([]).ids
        for order in self:
            res = self.create_sale_order(order)
            if res:
                total_count +=1
                if res[0].id not in sale_orders:
                    # res[0].action_confirm()
                    new_added_so += 1
                order.order_id = res[0].id
                if len(res) > 2:
                    new_added_line += 1
                self.check_for_delivery_validation(res[0])

        return self.env['amazon.wizard'].sudo().show_wizard_message(new_added_so, new_added_line, total_count - (new_added_line + new_added_so))

    def validate_pickings(self):
        print("Hello")
    
    def check_for_delivery_validation(self, sale_order):
        if sale_order.mirakl_order_state in ["shipped" ,"closed", "received"]:
            if len(sale_order.picking_ids) > 0:

                for delivery in sale_order.picking_ids:
                    if delivery.products_availability == "Available":
                        delivery.action_assign()
                        for move in delivery.move_lines.filtered(lambda m: m.state not in ["done", "cancel"]):
                            rounding = move.product_id.uom_id.rounding
                            if (
                                float_compare(
                                    move.quantity_done,
                                    move.product_qty,
                                    precision_rounding=rounding,
                                )
                                == -1
                            ):
                                for move_line in move.move_line_ids:
                                    move_line.qty_done = move_line.product_uom_qty
                        delivery.with_context(skip_immediate=True, skip_sms=True).button_validate()
        
    

    def create_sale_order(self,order):
        new_added_so = new_added_line = existing_line_update = 0
        sale_order = self.env['sale.order'].search([('amazon_order_id', '=', order.amazon_order_id)], limit=1) or False
        product = self.env['product.product'].search([('name','=',order.sku)])
        if not sale_order and product:
            customer_id = self._create_customer(order)
            billing_id = self._create_billing_customer(order, customer_id)
            shipping_id = self._create_shipping_customer(order, customer_id)

            #Order state filter for Sale Order Logs
            mirakl_state = None
            odoo_state = None
            if order.order_status:
                if order.order_status == 'SHIPPED':
                    odoo_state = 'sale'
                    mirakl_state = 'shipped'
                elif order.order_status == 'awaiting_collection':
                    mirakl_state = 'to_collect'
                elif order.order_status == 'Canceled':
                    mirakl_state = 'canceled'
                elif order.order_status == 'NEW':
                    mirakl_state = 'shipping'
                    odoo_state = 'sale'
                elif order.order_status == 'Refused':
                    mirakl_state = 'refused'
                    odoo_state = 'cancel'
                else:
                    odoo_state = 'sale'
                    mirakl_state = 'closed'

            if customer_id:
                a = False
                s1 = order.order_date.split(" ")
                try:
                    a = datetime.datetime.strptime(s1[0], '%d-%m-%Y').strftime('%Y-%m-%d')
                except Exception as err:
                    logger.info(err)
                try:
                    a = datetime.datetime.strptime(s1[0], '%d-%b-%Y').strftime('%Y-%m-%d')
                except Exception as err:
                    logger.info(err)
                sale_order = self.env['sale.order'].sudo().create({
                        'partner_id': customer_id,
                        'partner_invoice_id': billing_id,
                        'partner_shipping_id': shipping_id ,
                        'amazon_order_id': order.amazon_order_id,
                        'amazon_order': order.id,
                        'state': odoo_state,
                        'market_place_shop': order.shop_id.name,
                        'mirakl_order_state': mirakl_state,
                        'sku': order.sku,
                        'type_id': self.env['sale.order.type'].search([('id','=', 1)]).id,
                        'warehouse': order.warehouse,
                        'asin': order.asin,
                        'order_status': order.order_status,
                        'shipping_method': order.shipping_method,
                        'warehouse_id': order.warehouse_id.id,
                        'shipping_zip': order.shipping_zip,
                        'delivery_city': order.delivery_city,
                        'delivery_country': order.delivery_country,
                        'full_name': order.full_name,
                        'total_price': order.total_price,
                        'delivery_cost': order.delivery_cost,
                        'phone': order.phone,
                        'first_name': order.first_name,
                        'date_order': a,
                        'ship_method_code': order.ship_method_code,
                        'shipping_address2': order.shipping_address2,
                        'shipping_address3': order.shipping_address3,
                        'shipping_state': order.shipping_state,
                        'is_gift': order.is_gift,
                        'gift_meesage': order.gift_meesage,
                        'tracking_id': order.tracking_id,
                        'ship_date': order.ship_date,
                        'billing_zip': order.billing_zip,
                        'billing_city': order.billing_city,
                    })
                new_added_so += 1
                order_line = self.get_sale_order_lines(sale_order,order)
                logger.info("order Created with ID " + str(sale_order.id) + "and line added with ID" + str(order_line.id))
                return (sale_order)
        
        elif sale_order and order.line_id not in  sale_order.order_line.ids:
            product = self.env['product.product'].search([('name','=',order.sku)])
            ex_product_ids = [line.product_id.id for line in sale_order.order_line]
            if product and product.id not in ex_product_ids:
                line = self.env['sale.order.line'].create({
                    'product_id': self.env['product.product'].search([('name','=',order.sku)]).id,
                                'description': order.name,
                                'name': order.name,
                                'order_id': sale_order.id,
                                'product_uom_qty': order.quantity,
                                'price_subtotal': order.total_price,

                })
                logger.info("order Already exited with ID " + str(sale_order.id) + "and line added with ID" + str(line.id))
                new_added_line += 1
                return sale_order, new_added_line
            else:

                mirakl_state = None
                odoo_state = None
                if order.order_status:
                    if order.order_status == 'Shipped':
                        mirakl_state = 'shipped'
                        odoo_state = 'sale'
                    elif order.order_status == 'awaiting_collection':
                        mirakl_state = 'to_collect'
                    elif order.order_status == 'Withdrawn':
                        mirakl_state = 'canceled'
                        odoo_state = 'cancel'
                    elif order.order_status == 'NEW':
                        mirakl_state = 'shipping'
                        odoo_state = 'sale'
                    elif order.order_status == 'Canceled':
                        mirakl_state = 'canceled'
                        odoo_state = 'cancel'
                    elif order.order_status == 'Validated - to be shipped':
                        mirakl_state = 'shipping'
                        odoo_state = 'sale'
                    elif order.order_status == 'Refused':
                        odoo_state = 'cancel'
                        mirakl_state = 'refused'
                    else:
                        odoo_state = 'sale'
                        mirakl_state = 'closed'
                s1 = order.order_date.split(" ")
                a = False
                try:
                    a = datetime.datetime.strptime(s1[0], '%d-%m-%Y').strftime('%Y-%m-%d')
                except Exception as err:
                    logger.info(err)
                try:
                    a = datetime.datetime.strptime(s1[0], '%d-%b-%Y').strftime('%Y-%m-%d')
                except Exception as err:
                    logger.info(err)
                logger.info("**order Already exited with ID " + str(sale_order.id) + " Checking for Updates**")
                logger.info("Before date change >>>> %s", str(sale_order.date_order))
                sale_order.write({'date_order': a})
                logger.info("After date change >>>> %s", str(sale_order.date_order))

                for line in sale_order.order_line:
                    if line.product_id == product:
                        line.update({'product_uom_qty': order.quantity,'price_unit': order.total_price})
                existing_line_update += 1
                customer_id = self._create_customer(order)
                billing_id = self._create_billing_customer(order, customer_id)
                shipping_id = self._create_shipping_customer(order, customer_id)
                sale_order.write({'mirakl_order_state': mirakl_state, 'state': odoo_state,'order_status': order.order_status,'partner_id': customer_id, 'partner_invoice_id': billing_id, 'partner_shipping_id': shipping_id})
                return (sale_order)
        # else:

    def get_sale_order_lines(self,order,order1):
        product = self.env['product.product'].search([('name','=',order1.sku)])
        if product:
            line = self.env['sale.order.line'].create({
                                'product_id': product.id,
                                'name': product.name,
                                'order_id': order.id,
                                'product_uom' : product.uom_id.id,
                                'product_uom_qty': order1.quantity,
                                'price_unit': order1.total_price,
                                'price_subtotal': order1.total_price,
            })
            return line

    def _create_customer(self, order):
        customer_env = self.env['res.partner']
        customer = customer_env.search([('phone', '=', order.phone),('name','=',order.full_name)],limit=1)
        if not customer:
            customer = customer_env.create({
                        'company_type': 'person',
                        'name': order.full_name,
                        'phone': order.phone,
                        'street': order.shipping_address,
                        # 'amazon_customer_id': customer
                        'zip': order.billing_zip or order.shipping_zip,
                        'city': order.delivery_city,
                        'street2': order.shipping_address2,
                        'country_id': self.env['res.country'].search([('code','=', order.delivery_country)],limit=1).id,
            })
            
        elif customer and order.full_name:
            customer.country_id = self.env['res.country'].search([('code','=',order.delivery_country)]).id
            customer.zip = order.shipping_zip or order.billing_zip
            customer.city = order.delivery_city or order.billing_city
            customer.phone = order.phone
            customer.street_number =  order.shipping_address2
        else:
                customer = self.create_dummy_data(order,None)

        return customer.id



    def _create_billing_customer(self,order, customer_id):
        billing_customer = self.env['res.partner'].search([('type', '=', 'invoice'), ('parent_id', '=', customer_id)]) or False
        if not billing_customer:
            if order.full_name:
                billing_customer = self.env['res.partner'].create({
                    'company_type': 'person',
                    'type': 'invoice',
                    'parent_id': customer_id,
                    'name': order.full_name,
                    'phone': order.phone,
                    'street': order.shipping_address,
                    'street2': order.shipping_address2,
                    'zip': order.billing_zip or order.shipping_zip,
                    'city': order.delivery_city,
                    'street_number': order.shipping_address2,
                    'country_id': self.env['res.country'].search([('code','=', order.delivery_country)],limit=1).id,
                })
            else:
                billing_customer = self.create_dummy_data(order,'invoice')

        else:
            billing_customer.country_id = self.env['res.country'].search([('code','=',order.delivery_country)]).id
            billing_customer.zip = order.shipping_zip or order.billing_zip
            billing_customer.city = order.delivery_city or order.billing_city
            billing_customer.phone = order.phone
            billing_customer.street2 =  order.shipping_address2
            billing_customer.parent_id =  customer_id

        return billing_customer.id



    def _create_shipping_customer(self, order, customer_id):
        shipping_customer = self.env['res.partner'].search([('type', '=', 'invoice'), ('parent_id', '=', customer_id)]) or False
        if not shipping_customer:
            country = state = full_name = False
            if order.full_name:
                shipping_customer = self.env['res.partner'].create({
                    'company_type': 'person',
                    'type': 'delivery',
                    'name': order.full_name,
                    'parent_id': customer_id,
                    'phone': order.phone,
                    'street': order.shipping_address,
                    'zip': order.billing_zip or order.shipping_zip,
                    'city': order.delivery_city,
                    'street2': order.shipping_address2,
                    'street_number': order.shipping_address2,
                    'country_id': self.env['res.country'].search([('code','=', order.delivery_country)],limit=1).id,
                })
            else:
                shipping_customer = self.create_dummy_data(order,'delivery')
        else:
            shipping_customer.country_id = self.env['res.country'].search([('code','=',order.delivery_country)]).id
            shipping_customer.zip = order.shipping_zip or order.billing_zip
            shipping_customer.city = order.delivery_city or order.billing_city
            shipping_customer.phone = order.phone
            shipping_customer.street = order.shipping_address
            shipping_customer.parent_id =  customer_id

            shipping_customer.street2 =  order.shipping_address2
        return shipping_customer.id




