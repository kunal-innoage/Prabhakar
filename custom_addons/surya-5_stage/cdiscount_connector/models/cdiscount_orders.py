from asyncio.log import logger
from odoo import fields, models,api,_
from datetime import datetime
from odoo.tools import float_compare


class CDiscountOrder(models.Model):
    _name = 'cdiscount.orders'
    _description = 'CDiscount Orders Managment'


    name = fields.Char("Name")
    cdiscount_order_id = fields.Char("Order Reference")
    first_name = fields.Char("First Name")
    last_name = fields.Char("Last Name")
    order_status = fields.Char('Status')
    shipping_method = fields.Char("Shipping Method")
    # date_order = fields.Char("Order Date")
    date_order_sent = fields.Datetime("Converted Date time")
    shipping_address = fields.Char("Address")
    shipping_zip = fields.Char("Delivery zip code")
    delivery_city = fields.Char("Delivery City")
    delivery_country = fields.Char("Delivery Country")
    product_id = fields.Many2one("product.product","Product")
    product_status = fields.Char("Product Status")
    product_ref = fields.Char("Vendor Reference")
    quantity = fields.Char("Quantity")
    total_price = fields.Char("Total price (€ incl. VAT) excluding processing fees")
    delivery_cost = fields.Char("Amount Delivery costs (€ incl. VAT)")
    phone = fields.Char('Phone')
    line_id = fields.Char('Line ID')
    billing_zip = fields.Char("Billing postcode")
    billing_city = fields.Char("Billing city")
    billing_country = fields.Char("Billing country")
    sku = fields.Char("SKU")
    order_id = fields.Many2one("sale.order","Sale Order")
    #new fields
    ean = fields.Char("EAN")
    product_state = fields.Char("Product State")
    civillity = fields.Char("Civillity")
    date_modify = fields.Char("Date of Last Modification")
    fee = fields.Char("Fee (€ incl. VAT)")
    seller_remu = fields.Char("Seller remuneration (€ incl. VAT)")
    phone_free2 = fields.Char("Phone free 2")
    name_and_billing_address = fields.Char("Name and Billing Address")
    house_number = fields.Char("House Number")
    warehouse_id = fields.Many2one("stock.warehouse", "Warehouse")
    shop_id = fields.Many2one('cdiscount.seller','Shop')


    @api.model_create_multi
    def create(self,vals):
        result = super(CDiscountOrder,self).create(vals)
        for res in result:
            res.line_id = res.id
            res.warehouse_id = self.env.context.get('warehouse_id')
            res.shop_id = self.env.context.get('shop_id')
            if res.shipping_address:
                # split_address = res.shipping_address.split(' ')
                # if len(split_address) > 2:
                #     res.house_number = split_address[0]
                #     res.shipping_address = split_address[1:]
                if res.total_price and len(res.total_price) > 1:
                    res.total_price = res.total_price.split(' ')[0]
                if res.delivery_cost and len(res.delivery_cost) > 1:
                    res.delivery_cost = res.delivery_cost.split(' ')[0]
                if res.quantity and len(res.quantity) > 1:
                    res.quantity = res.quantity.split(' ')[0]
                if res.fee and len(res.fee) > 1:
                    res.fee = res.fee.split(' ')[0]
                if res.seller_remu and len(res.seller_remu) > 1:
                    res.seller_remu = res.seller_remu.split(' ')[0]
                # else:

        return result
    
    

    def action_view_sale_order(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _("Sale Order"),
            'view_mode': 'form',
            'res_model': 'sale.order',
            'domain': [('cdiscount_order_id', '=', self.cdiscount_order_id)],
        }

    def map_sale_orders(self):
        total_count = 0
        new_added_so = new_added_line = 0
        sale_orders = self.env['sale.order'].search([]).ids
        for order in self:
            res = self.create_sale_order(order)
            if res:
                total_count +=1
                if res[0].id not in sale_orders:
                    new_added_so += 1
                order.order_id = res[0].id
                if len(res) > 2:
                    new_added_line += 1
                self.check_for_delivery_validation(res[0])
        return self.env['amazon.wizard'].sudo().show_wizard_message(new_added_so, new_added_line, total_count - (new_added_line + new_added_so))

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
        sale_order = self.env['sale.order'].search([('cdiscount_order_id', '=', order.cdiscount_order_id)], limit=1)
        product = self.env['product.product'].search(['|',('name','=',order.product_ref),('default_code','=',order.sku)],limit=1)
        if not sale_order and product.id:
            customer_id = self._create_customer(order)
            billing_id = self._create_billing_customer(order, customer_id)
            shipping_id = self._create_shipping_customer(order, customer_id)

            #Order State Filter for sale order logs
            mirakl_state = None
            odoo_state = None
            if order.order_status:
                if order.order_status in ['Shipped','Expédiée']:
                    mirakl_state = 'shipped'
                    odoo_state = 'sale'
                elif order.order_status == 'awaiting_collection':
                    mirakl_state = 'to_collect'
                elif order.order_status == 'Withdrawn':
                    mirakl_state = 'canceled'
                    odoo_state = 'cancel'
                elif order.order_status == 'Canceled':
                    mirakl_state = 'canceled'
                    odoo_state = 'cancel'
                elif order.order_status in ['Validated - to be shipped', 'Validée - à expédier']:
                    mirakl_state = 'shipping'
                    odoo_state = 'sale'
                elif order.order_status == 'Refused':
                    odoo_state = 'cancel'
                    mirakl_state = 'refused'
                else:
                    odoo_state = 'sale'
                    mirakl_state = 'closed'
            if customer_id:
                sale_order = self.env['sale.order'].sudo().create({
                        'partner_id': customer_id,
                        'partner_invoice_id': billing_id,
                        'partner_shipping_id': shipping_id ,
                        'state': odoo_state,
                        # 'confirmation_date': fields.Datetime.now(),
                        'cdiscount_order_id': order.cdiscount_order_id,
                        # 'date_order': str(fields.Datetime.now()),
                        'type_id': self.env['sale.order.type'].search([('id','=', 1)]).id or False,
                        'civillity': order.civillity,
                        'market_place_shop': order.shop_id.name,
                        'fee': order.fee,
                        'warehouse_id': order.warehouse_id.id,
                        # 'date_modify': order.date_modify,
                        'seller_remu': order.seller_remu,
                        'phone_free2': order.phone_free2,
                        'mirakl_order_state': mirakl_state,
                        'name_and_billing_address': order.name_and_billing_address,
                        # 'date_order_sent': order.date_order_sent,
                        'shipping_address': order.shipping_address,
                        'shipping_zip': order.shipping_zip,
                        'delivery_city': order.delivery_city,
                        'delivery_country': order.delivery_country,
                        'phone': order.phone,
                        'billing_zip': order.billing_zip,
                        'billing_city': order.billing_city,
                        'billing_country': order.billing_country,
                        'sku': order.sku,
                        'ean': order.ean,
                        'order_status': order.order_status,
                        'shipping_method': order.shipping_method,
                        # 'date_order': order.date_order,
                    })
                order_line = self.get_sale_order_lines(sale_order,order)
                logger.info("***Order Created : "+ sale_order.name + " and Line added with ID : "+ str(order_line.id))
                return (sale_order)

        
        elif sale_order and order.line_id not in  sale_order.order_line.ids:
            product = self.env['product.product'].search(['|',('name','=',order.product_ref),('default_code','=',order.sku)],limit=1)
            ex_product_ids = [line.product_id.id for line in sale_order.order_line]
            if product and product.id not in ex_product_ids:
                line = self.env['sale.order.line'].create({
                    'product_id': product.id,
                                'description': order.name,
                                'name': product.name,
                                'order_id': sale_order.id,
                                'product_uom_qty': order.quantity,
                                'product_uom' : product.uom_id.id,
                                'price_subtotal': order.total_price,
                                'price_unit': order.total_price,
                })
                logger.info("***LIne Added to Existing Sale Order "+ sale_order.name + "with ID****" + str(line.id))
                return sale_order, new_added_line
            else:
                #Order State Filter for sale order logs
                mirakl_state = None
                odoo_state = None
                if order.order_status:
                    if order.order_status in ['Shipped','Expédiée']:
                        mirakl_state = 'shipped'
                        odoo_state = 'sale'
                    elif order.order_status == 'awaiting_collection':
                        mirakl_state = 'to_collect'
                    elif order.order_status == 'Withdrawn':
                        mirakl_state = 'canceled'
                        odoo_state = 'cancel'
                    elif order.order_status == 'Canceled':
                        mirakl_state = 'canceled'
                        odoo_state = 'cancel'
                    elif order.order_status in ['Validated - to be shipped', 'Validée - à expédier']:
                        mirakl_state = 'shipping'
                        odoo_state = 'sale'
                    elif order.order_status == 'Refused':
                        odoo_state = 'cancel'
                        mirakl_state = 'refused'
                    else:
                        odoo_state = 'sale'
                        mirakl_state = 'closed'
                sale_order.write({'mirakl_order_state': mirakl_state, 'state': odoo_state,'order_status': order.order_status})
                logger.info("**order Already exited with ID " + str(sale_order.id) + " Checking for Updates**")

                for line in sale_order.order_line:
                    if line.product_id == product:
                        line.update({'product_uom_qty': order.quantity,'price_unit': order.total_price})
                customer_id = self._create_customer(order)
                billing_id = self._create_billing_customer(order, customer_id)
                shipping_id = self._create_shipping_customer(order, customer_id)
                sale_order.write({'partner_id': customer_id, 'partner_shipping_id': shipping_id, 'partner_invoice_id': billing_id})
                return sale_order

  

    def get_sale_order_lines(self,order,order1):
        product = self.env['product.product'].search([('name','=',order1.product_ref)])
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
        customer = customer_env.search([('name', 'ilike', (order.first_name + ' ' + order.last_name)),('phone','in',[order.phone, order.phone_free2])],limit=1) or False
        if not customer:
            customer = customer_env.create({
                    'company_type': 'person',
                    'name': order.first_name + ' ' + order.last_name,
                    'phone': order.phone,
                    'street': order.shipping_address,
                    'zip': order.billing_zip,
                    'city': order.billing_city,
                    'country_id': self.env['res.country'].search([('code','=', order.delivery_country)],limit=1).id,
            })
        else:
            customer.country_id = self.env['res.country'].search([('code','=',order.delivery_country)]).id
            customer.zip = order.billing_zip
            customer.city = order.billing_city
            customer.phone = order.phone or order.phone_free2
            customer.street = order.shipping_address
            # customer.street_number = order.house_number
        return customer.id



    def _create_billing_customer(self,order, customer_id):
        billing_customer = self.env['res.partner'].search([('type', '=', 'invoice'), ('parent_id', '=', customer_id)]) or False
        if not billing_customer:
            country = state = full_name = False
            if order.first_name:
                full_name = order.first_name
                if order.last_name:
                    full_name += " "+ order.last_name
            else:
                if order.last_name:
                    full_name = order.first_name
            billing_customer = self.env['res.partner'].create({
                'company_type': 'person',
                'type': 'invoice',
                'name': full_name,
                'parent_id': customer_id,
                'city': order.billing_city,
                'phone': order.phone or order.phone_free2,
                'country_id': self.env['res.country'].search([('code', '=', order.billing_country)]).id,
                'country_code': country.code if country else False,
                'zip': order.billing_zip,
            })
        else:
            billing_customer.country_id = self.env['res.country'].search([('code','=',order.delivery_country)]).id
            billing_customer.zip = order.billing_zip
            billing_customer.city = order.billing_city
            billing_customer.phone = order.phone or order.phone_free2
            billing_customer.street = order.shipping_address
        return billing_customer.id



    def _create_shipping_customer(self, order, customer_id):
        billing_customer = self.env['res.partner'].search([('type', '=', 'invoice'), ('parent_id', '=', customer_id)]) or False
        if not billing_customer:
            country = state = full_name = False
            if order.first_name:
                full_name = order.first_name
                if order.last_name:
                    full_name += " "+ order.last_name
            else:
                if order.last_name:
                    full_name = order.first_name
            billing_customer = self.env['res.partner'].create({
                'company_type': 'person',
                'type': 'delivery',
                'name': full_name,
                'parent_id': customer_id,
                'street': order.shipping_address,
                'city': order.delivery_city,
                'country_id': self.env['res.country'].search([('code', '=', order.delivery_country)]).id,
                'country_code': country.code if country else False,
                'zip': order.shipping_zip,
            })
        else:
            billing_customer.country_id = self.env['res.country'].search([('code','=',order.delivery_country)]).id
            billing_customer.zip = order.billing_zip
            billing_customer.city = order.billing_city
            billing_customer.phone = order.phone or order.phone_free2
            billing_customer.street = order.shipping_address
        return billing_customer.id




