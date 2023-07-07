# import imp
from asyncio.log import logger
from odoo import fields, models,api
from odoo.tools import float_compare
import logging
_logger = logging.getLogger(__name__)
import datetime


class WayfairOrder(models.Model):
    _name = 'wayfair.orders'
    _description = 'Wayfair Orders Managment'


    name = fields.Char("Item Name")
    wayfair_order_id = fields.Char("PO Number")
    order_date = fields.Char("PO Date")
    first_name = fields.Char("First Name")
    last_name = fields.Char("Last Name")
    order_id = fields.Many2one('sale.order',"Sale Order")
    order_status = fields.Char('Order Status')
    shipping_method = fields.Char("Delivery Method")
    shipping_address = fields.Char("Deliver to Address")
    warehouse = fields.Char("Warehouse Name")
    store = fields.Char("Store Name")
    shipping_zip = fields.Char("Deliver to Postal Code")
    delivery_city = fields.Char("Deliver to City")
    delivery_country = fields.Char("Destination Country")
    product_id = fields.Many2one("product.product","Product")
    full_name = fields.Char("Deliver to Name")
    product_status = fields.Char("Product Status")
    product_ref = fields.Char("Item Number")
    delivery_speed = fields.Char("Delivery Speed")
    quantity = fields.Char("Quantity")
    total_price = fields.Char("Wholesale Price")
    delivery_cost = fields.Char("Amount Delivery costs (€ incl. VAT)")
    phone = fields.Char('Deliver to Phone')
    line_id = fields.Char('Line ID')
    tracking_number = fields.Char("Tracking Number")
    sku = fields.Char("SKU")
    billing_zip = fields.Char("Billing postcode")
    billing_city = fields.Char("Billing city")
    billing_country = fields.Char("Billing country")
    dispatch_date = fields.Char("Must Dispatch by")
    back_order_date = fields.Char("Backorder Date")
    carrier_name = fields.Char("Carrier Name")
    delivery_account = fields.Char("Delivery Account Number")
    street2 = fields.Char("Deliver to Address 2")
    province = fields.Char("Deliver to Province")
    qty_at_po = fields.Char("Inventory at PO Time")
    po_date_time = fields.Char("PO Date & Time")
    time_stamp = fields.Char("Registered Timestamp")
    custom_text = fields.Char("Customisation Text")
    event_name = fields.Char("Event Name")
    event_id = fields.Char("Event ID")
    event_start_date = fields.Char("Event Start Date")
    event_end_date = fields.Char("Event End Date")
    event_type = fields.Char("Event Type")
    back_order_reason = fields.Char("Backorder reason")
    org_product_id = fields.Char("Original Product ID")
    org_product_name = fields.Char("Original Product Name")
    ev_inventory_source = fields.Char("Event Inventory Source")
    ship_url = fields.Char("Packing Slip URL")
    prickup_date = fields.Char("Ready for Pickup Date")
    dept_id = fields.Char("Depot ID")
    dept_name = fields.Char("Depot Name")
    wholesale_event = fields.Char("Wholesale Event Source")
    wholesale_event_store = fields.Char("Wholesale Event Store Source")
    b2b_order = fields.Char("B2BOrder")
    composit_wood_product = fields.Char("Composite Wood Product")
    sale_channel = fields.Char("Sales Channel")
    inventory_send_date = fields.Char("Inventory Send Date")
    warehouse_id = fields.Many2one('stock.warehouse','Warehouse ID')
    shop_id = fields.Many2one('wayfair.seller','Shop')

    @api.model_create_multi
    def create(self,vals):
        result = super(WayfairOrder,self).create(vals)
        for res in result:
            if res:
                res.line_id = res.id
                res.warehouse_id = self.env.context.get('warehouse_id')
                res.shop_id = self.env.context.get('shop_id')
            if res.product_ref and res.product_ref.startswith('='):
                res.product_ref = res.product_ref[2:]
                res.product_ref = res.product_ref[:-1]
        return result

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
            self.env.cr.commit()

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
        sale_order = self.env['sale.order'].search([('wayfair_order_id', '=', order.wayfair_order_id)], limit=1) or False
        if not sale_order:
            if order.shop_id.warehouse_id.code in ['IFUL','ETL']:
                customer_id = self._create_customer(order)
                billing_id = self._create_billing_customer(order, customer_id)
                shipping_id = self._create_shipping_customer(order, customer_id)
                status = 'sale'
                
                mirakl_state = None
                if order.order_status:
                    if order.order_status == 'Shipped':
                        mirakl_state = 'shipped'
                    elif order.order_status == 'Ready For Pickup':
                        mirakl_state = 'shipping'
                        status = 'sale'
                    elif order.order_status == 'Cancelled':
                        mirakl_state = 'canceled'
                        status = 'cancel'
                    elif order.order_status == 'Pending Ship Confirmation':
                        mirakl_state = 'shipping'
                    elif order.order_status == 'Returned':
                        mirakl_state = 'received'
                    else:
                        mirakl_state = 'closed'
                        status = 'sale'
                warehouse_id = None
                #Warehouse ID assignment
                if order.delivery_country not in ['GB']:
                    warehouse_id = self.env['stock.warehouse'].search([('code','=','ETL')]).id
                elif order.delivery_country in ['GB']:
                    if order.warehouse in ["Surya B.V. 48488","Surya B.V.  48488"]:
                        warehouse_id = self.env['stock.warehouse'].search([('code','=','ETL')]).id
                    elif order.warehouse == "Surya B.V.":
                        if order.carrier_name in ["DPD", "GLS"]:
                            warehouse_id = self.env['stock.warehouse'].search([('code','=','ETL')]).id
                        else:
                            warehouse_id = self.env['stock.warehouse'].search([('code','=','IFUL')]).id
                    else:
                        warehouse_id = self.env['stock.warehouse'].search([('code','=','IFUL')]).id
                else:
                    # print("Data does not map")
                    logger.info("Data does not match according to the warehouse and imported file")
                    # return F
                if customer_id and warehouse_id:
                    date = False
                    aa = order.po_date_time.split(" ")
                    try:
                        date = datetime.datetime.strptime(aa[0], '%d/%m/%Y').strftime('%Y-%m-%d')
                    except Exception as err:
                        logger.info(err)
                    try:
                        date = datetime.datetime.strptime(aa[0], '%Y-%m-%d').strftime('%Y-%m-%d')
                    except Exception as err:
                        logger.info(err)
                    sale_order = self.env['sale.order'].create({
                            'partner_id': customer_id,
                            'partner_invoice_id': billing_id,
                            'partner_shipping_id': shipping_id ,
                            'wayfair_order_id': order.wayfair_order_id,
                            'state': status,
                            'sku': order.sku,
                            'full_name': order.full_name,
                            'order_status': order.order_status,
                            'mirakl_order_state': mirakl_state,
                            'warehouse_id': warehouse_id,
                            'market_place_shop': order.shop_id.name,
                            'warehouse': order.warehouse,
                            'date_order': date or datetime.datetime.now().date(),
                            'delivery_country': order.delivery_country,
                        })
                    order_line = self.get_sale_order_lines(sale_order,order)
                    if sale_order and order_line:
                        if date :
                            sale_order.write({
                                'date_order': date if date else False,
                            })
                        logger.info(" >>> Order added with ID " + sale_order.name + " and Line added with ID "+ str(order_line.id))
                    return (sale_order)
            
        elif sale_order and order.line_id not in  sale_order.order_line.ids:
            product = self.env['product.product'].search([('name','=',order.product_ref)])
            ex_product_ids = [line.product_id.id for line in sale_order.order_line]
            if product and product.id not in ex_product_ids:
                line = self.env['sale.order.line'].create({
                    'product_id': product.id,
                                    'description': order.name,
                                    #  'name': order.name,
                                    'name': product.name,
                                    'order_id': sale_order.id,
                                    'product_uom_qty': order.quantity,
                                    'product_uom' : product.uom_id.id,

                                    'price_subtotal': order.total_price,
                                    'price_unit': order.total_price,
                    })
                # line.product_id_change()
                new_added_line += 1
                logger.info("***LIne Added to Existing Sale Order "+ sale_order.name + "with ID****" + str(line.id))
                date = False
                aa = order.po_date_time.split(" ")
                try:
                    date = datetime.datetime.strptime(aa[0], '%d/%m/%Y').strftime('%Y-%m-%d')
                except Exception as err:
                    logger.info(err)
                try:
                    date = datetime.datetime.strptime(aa[0], '%Y-%m-%d').strftime('%Y-%m-%d')
                except Exception as err:
                    logger.info(err)
                sale_order.write({'date_order': date or datetime.datetime.now().date()})
                return sale_order, new_added_line
            else:
                for line in sale_order.order_line:
                    if line.product_id == product:
                        line.update({'product_uom_qty': order.quantity,'price_unit': order.total_price})
                        logger.info("Existing Line Updated")
                customer_id = self._create_customer(order)
                billing_id = self._create_billing_customer(order, customer_id)
                shipping_id = self._create_shipping_customer(order, customer_id)
                sale_order.write({'partner_id': customer_id, 'partner_shipping_id': shipping_id, 'partner_invoice_id': billing_id})
                mirakl_state = None
                odoo_state = None
                if order.order_status:
                    if order.order_status == 'Shipped':
                        mirakl_state = 'shipped'
                        odoo_state = 'sale'
                    elif order.order_status == 'Pending Ship Confirmation':
                        mirakl_state = 'shipping'
                        odoo_state = 'sale'
                    elif order.order_status == 'Ready For Pickup':
                        odoo_state = 'sale'
                        mirakl_state = 'shipping'
                    elif order.order_status == 'Withdrawn':
                        mirakl_state = 'canceled'
                        odoo_state = 'cancel'
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
                date = False
                aa = order.po_date_time.split(" ")
                try:
                    date = datetime.datetime.strptime(aa[0], '%d/%m/%Y').strftime('%Y-%m-%d')
                except Exception as err:
                    logger.info(err)
                try:
                    date = datetime.datetime.strptime(aa[0], '%Y-%m-%d').strftime('%Y-%m-%d')
                except Exception as err:
                    logger.info(err)
                sale_order.write({'date_order': date or datetime.datetime.now().date()})
                sale_order.write({'mirakl_order_state': mirakl_state, 'state': odoo_state,'order_status': order.order_status})
                return sale_order
        else:
            mirakl_state = None
            odoo_state = None
            if order.order_status:
                if order.order_status == 'Shipped':
                    mirakl_state = 'shipped'
                    odoo_state = 'sale'
                elif order.order_status == 'Pending Ship Confirmation':
                        mirakl_state = 'shipping'
                        odoo_state = 'sale'
                elif order.order_status == 'Ready For Pickup':
                        odoo_state = 'sale'
                        mirakl_state = 'shipping'
                elif order.order_status == 'Withdrawn':
                    mirakl_state = 'canceled'
                    odoo_state = 'cancel'
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
                sale_order.write({'mirakl_order_state': mirakl_state, 'state': odoo_state,'order_status': order.order_status})
            logger.info("****** Sale Order Already Exist WIth ID " + str(sale_order.id))
            customer_id = self._create_customer(order)
            billing_id = self._create_billing_customer(order, customer_id)
            shipping_id = self._create_shipping_customer(order, customer_id)
            sale_order.write({'partner_id': customer_id, 'partner_shipping_id': shipping_id, 'partner_invoice_id': billing_id})
            
            return (sale_order)

    def update_shop_name(self):
        for order in self:
            if order.order_id:
                order.order_id.wayfair_shop_id = order.shop_id
                order.order_id.market_place_shop = order.shop_id.name
                logger.info(order.order_id.market_place_shop)

    def get_sale_order_lines(self,order,order1):
        product = self.env['product.product'].search([('name','=',order1.product_ref)],limit=1)
        if product:
            line = self.env['sale.order.line'].create({
                                'product_id': product.id,
                                'name': order1.name,
                                'order_id': order.id,
                                'product_uom' : product.uom_id.id,
                                'price_unit': float(order1.total_price),
            })
            return line

    def _create_customer(self, order):
        customer_env = self.env['res.partner']
        customer = customer_env.search(['|','&',('phone', '=', order.phone),('name','=',order.full_name),('parent_id','=',False), '&', ('name','=',order.full_name),('parent_id','=',False)],limit=1)
        if not customer:
            customer = customer_env.create({
                    'company_type': 'person',
                    'name': order.full_name,
                    'phone': order.phone,
                    'street': order.shipping_address,
                    'street': order.street2,
                    'zip': order.shipping_zip,
                    'city': order.delivery_city,
                    'country_id': self.env['res.country'].search([('code','=', order.delivery_country)],limit=1).id or False,
            })
        else:
            # _logger.info("HEllo *********",order.shipping_zip,order.delivery_city,order.phone)
            customer.country_id = self.env['res.country'].search([('code','=',order.delivery_country)]).id
            customer.zip = order.shipping_zip
            customer.city = order.delivery_city
            customer.street2 = order.street2
            customer.phone = order.phone and order.phone
            customer.street = order.shipping_address
        
        return customer.id



    def _create_billing_customer(self,order, customer_id):
        billing_customer = self.env['res.partner'].search([('type', '=', 'invoice'), ('parent_id', '=', customer_id)]) or False
        if not billing_customer:
            state = full_name = False
            country = self.env['res.country'].search([('code', '=', order.delivery_country)])
            billing_customer = self.env['res.partner'].create({
                'company_type': 'person',
                'type': 'invoice',
                'name': order.full_name,
                'parent_id': customer_id,
                'street': order.shipping_address,
                'street2': order.street2,
                'phone': order.phone,
                'city': order.delivery_city,
                'country_id': country.id if country else False,
                'country_code': country.code if country else False,
                'zip': order.billing_zip,
            })
        else:
            if order.delivery_city:
                billing_customer.city  = order.delivery_city
            if order.phone:
                billing_customer.phone = order.phone
            if order.shipping_address:
                billing_customer.street = order.shipping_address
            if order.delivery_country:
                billing_customer.country_id = self.env['res.country'].search([('code', '=', order.delivery_country)]).id or False
            if order.shipping_zip:
                billing_customer.zip = order.shipping_zip
            if order.street2:
                billing_customer.street2 = order.street2
        return billing_customer.id



    def _create_shipping_customer(self, order, customer_id):
        shipping_customer = self.env['res.partner'].search([('type', '=', 'delivery'), ('parent_id', '=', customer_id)]) or False
        if not shipping_customer:
            country = self.env['res.country'].search([('code', '=', order.delivery_country)])
            shipping_customer = self.env['res.partner'].create({
                'company_type': 'person',
                'type': 'delivery',
                'name': order.full_name,
                'parent_id': customer_id,
                'street': order.shipping_address,
                'street2': order.street2,
                'phone': order.phone,
                'city': order.delivery_city,
                'country_id': country.id if country else country,
                'country_code': country.code if country else False,
                'zip': order.shipping_zip,
            })
        else:
            if order.delivery_city:
                shipping_customer.city  = order.delivery_city
            if order.phone:
                shipping_customer.phone = order.phone
            if order.delivery_country:
                shipping_customer.country_id = self.env['res.country'].search([('code', '=', order.delivery_country)]).id or False
            if order.shipping_address:
                shipping_customer.street = order.shipping_address
            if order.shipping_zip:
                shipping_customer.zip = order.shipping_zip
            if order.street2:
                shipping_customer.street2 = order.street2

        return shipping_customer.id




