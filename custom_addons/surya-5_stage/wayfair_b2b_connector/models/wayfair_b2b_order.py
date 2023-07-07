# -*- coding: utf-8 -*-

from odoo import models, fields, _, api
from odoo.tools import float_compare


import logging
_logger = logging.getLogger(__name__)


class WayfairB2bSaleOrder(models.Model):
    _name = 'wayfair.b2b.sale.order'
    _description = 'Wayfair B2B Sale Orders'
    _rec_name = 'purchase_order'
    
    warehouse_name = fields.Char("Warehouse Name")
    store_name = fields.Char("Store Name")
    purchase_order = fields.Char("PO Number")
    purchase_date = fields.Char("PO Date")
    must_ship_date = fields.Char("Must Ship By")
    backorder_date = fields.Char("Backorder Date")
    order_status = fields.Char("Order Status")
    item_number = fields.Char("Item Number")
    item_name = fields.Char("Item Name")
    quantity = fields.Char("Quantity")
    wholesale_price = fields.Char("Wholesale Price")
    ship_method = fields.Char("Ship Method")
    carrier_name = fields.Char("Carrier Name")
    shipping_account_number = fields.Char("Shipping Account Number")
    ship_to_name = fields.Char("Ship To Name")
    ship_to_address = fields.Char("Ship To Address")
    ship_to_address2 = fields.Char("Ship To Address 2")
    ship_to_city = fields.Char("Ship To City")
    ship_to_state = fields.Char("Ship To State")
    ship_to_zip = fields.Char("Ship To Zip")
    ship_to_phone = fields.Char("Ship To Phone")
    inventory_at_po_time = fields.Char("Inventory at PO Time")
    inventory_send_date = fields.Char("Inventory Send Date")
    ship_speed = fields.Char("Ship Speed")
    po_date_and_time = fields.Char("PO Date & Time")
    registered_timestamp = fields.Char("Registered Timestamp")
    customization_text = fields.Char("Customization Text")
    event_name = fields.Char("Event Name")
    event_id = fields.Char("Event ID")
    event_start_date = fields.Char("Event Start Date")
    event_end_date = fields.Char("Event End Date")
    event_type = fields.Char("Event Type")
    backorder_reason = fields.Char("Backorder Reason")
    original_product_id = fields.Char("Original Product ID")
    original_prodcut_name = fields.Char("Original Product Name")
    event_inventory_source = fields.Char("Event Inventory Source")
    packing_ship_url = fields.Char("Packing Ship URL")
    tracking_number = fields.Char("Tracking Number")
    ready_for_pickup_date = fields.Char("Ready for Pickup Date")
    sku = fields.Char("SKU")
    destination_country = fields.Char("Destination Country")
    depot_id = fields.Char("Depot ID")
    depot_name = fields.Char("Depot Name")
    wholesale_event_source = fields.Char("Wholesale Event Source")
    wholesale_event_store_source = fields.Char("Wholesale Event Store Source")
    b2b_order = fields.Char("B2BOrder")
    composite_wood_product = fields.Char("Compostie Wood Product")
    sale_channel = fields.Char("Sales Channel")

    wayfair_b2b_shop_id = fields.Many2one("wayfair.b2b.shop", "Shop", readonly=True)
    sale_order_id = fields.Many2one("sale.order", "Sale Order", readonly=True)
    product_id = fields.Many2one("product.product", "Product", readonly=True)


    @api.model_create_multi
    def create(self, vals):
        res = super(WayfairB2bSaleOrder, self).create(vals)
        if res._context['import_file']:
            shop_id = self.env['wayfair.b2b.shop'].search([('id', '=', res._context.get('active_id'))])
            for order in res:
                if shop_id:
                    order.wayfair_b2b_shop_id = shop_id
                if order.item_number:
                    order.product_id = self.env['product.product'].search([('default_code', 'in', [order.item_number])])
        return res


    def map_with_bulk_order(self):
        sale_order_obj = self.env["sale.order"]
        for sale_order in self:
            if int(sale_order.quantity) != 0 and not sale_order.sale_order_id and sale_order.product_id:
                order_id = sale_order_obj.search([('wayfair_b2b_order_id.purchase_order', '=', sale_order.purchase_order)])
                
                if not order_id:
                    customer_id, billing_id, shipping_id = self._get_customer_details(sale_order)
                    
                    # Create SOL 
                    so_line = [(0, 0, {
                            'product_id': sale_order.product_id.id,
                            'price_unit': sale_order.wholesale_price,
                            'product_uom_qty': sale_order.quantity,
                        })]
                    # Create SO 
                    sale_order_id = sale_order_obj.create({
                        'partner_id': customer_id.id,
                        'partner_invoice_id': billing_id.id,
                        'partner_shipping_id': shipping_id.id ,
                        'wayfair_b2b_order_id': sale_order.id,
                        'mirakl_order_state': "closed",
                        'warehouse_id': sale_order.wayfair_b2b_shop_id.warehouse_id.id,
                        'order_line': so_line,
                        'market_place_shop': sale_order.wayfair_b2b_shop_id.name,
                    })
                    sale_order.sale_order_id = sale_order_id
                    

                else:
                    if sale_order.product_id:
                        self.env["sale.order.line"].create({
                            'product_id': sale_order.product_id.id,
                            'price_unit': sale_order.wholesale_price,
                            'product_uom_qty': sale_order.quantity,
                            'order_id': order_id.id,
                        })
                    sale_order.sale_order_id = order_id
                
                if sale_order.sale_order_id:
                    sale_order.process_to_done(sale_order.sale_order_id)


    def _get_customer_details(self, order):
        customer_env = self.env['res.partner']
        customer = customer_env.search([('name','=',order.wayfair_b2b_shop_id.name)],limit=1)
        if not customer:
            customer = customer_env.create({
                'company_type': 'person',
                'name': order.ship_to_name,
                'country_id': self.env['res.country'].search([('code','=', order.destination_country)],limit=1).id,
            })
            billing_customer = customer_env.create({
                'company_type': 'person',
                'type': 'invoice',
                'parent_id': customer.id,
                'name': order.ship_to_name,
                'country_id': self.env['res.country'].search([('code','=', order.destination_country )],limit=1).id,
            })
            shipping_customer = customer_env.create({
                'company_type': 'person',
                'type': 'delivery',
                'parent_id': customer.id,
                'name': order.ship_to_name,
                'country_id': self.env['res.country'].search([('code','=', order.destination_country )],limit=1).id,
            })
        else:
            billing_customer = customer_env.search([('type','=','invoice'),('parent_id', '=', customer.id)])
            shipping_customer = customer_env.search([('type','=','delivery'),('parent_id', '=', customer.id)])

        return [customer, billing_customer, shipping_customer]


    def process_to_done(self, sale_order):

        # Confirm Order
        sale_order.action_confirm()

        # Order Date Change
        month, date, year =  sale_order.wayfair_b2b_order_id.po_date_and_time.split("/")
        year, time = year.split(" ")
        date = year + "-" + month + "-" + date + " " + time
        sale_order.date_order = date

        # Validate Delivery 
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
                    sale_order.invoice_status = 'to invoice'
