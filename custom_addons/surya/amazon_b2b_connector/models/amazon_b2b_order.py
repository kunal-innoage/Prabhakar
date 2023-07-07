# -*- coding: utf-8 -*-

from odoo import models, fields, _, api
from odoo.tools import float_compare


import logging
_logger = logging.getLogger(__name__)


class AmazonB2bSaleOrder(models.Model):
    _name = 'amazon.b2b.sale.order'
    _description = 'Amazon B2B Sale Orders'
    _rec_name = "purchase_order"
    
    purchase_order = fields.Char("PO")
    vendor = fields.Char("Vendor")
    warehouse = fields.Char("Warehouse") 
    asin = fields.Char("ASIN") 
    external_id = fields.Char("External ID")
    external_id_type = fields.Char("External Id Type") 
    model_number = fields.Char("Model Number") 
    title = fields.Char("Title") 
    availablity = fields.Char("Availability")
    window_type = fields.Char("Window Type")
    window_start = fields.Char("Window Start")
    window_end = fields.Char("Window End")
    expected_date = fields.Char("Expected Date")
    quantity_requested = fields.Char("Quantity Requested")
    expected_quantity = fields.Char("Expected Quantity")
    in_transit_quantity = fields.Char("in transit")
    current_stock = fields.Char("stock")
    accepted_quantity = fields.Char("Accepted Quantity")
    received_quantity = fields.Char("Received Quantity")
    outstanding_quantity = fields.Char("Outstanding Quantity")
    unit_cost = fields.Char("Unit Cost")
    total_cost = fields.Char("Total Cost")
    currency = fields.Char("Currency")
    invoice_date = fields.Datetime("Invoice Date")

    amazon_b2b_shop_id = fields.Many2one("amazon.b2b.shop", "Shop", readonly=True)
    sale_order_id = fields.Many2one("sale.order", "Sale Order", readonly=True)

    @api.model_create_multi
    def create(self, vals):
        res = super(AmazonB2bSaleOrder, self).create(vals)
        
        if res._context.get("import_file"):
            shop_id = self.env['amazon.b2b.shop'].search([('id', '=', res._context.get('active_id'))])
            for order in res:
                if shop_id:
                    order.amazon_b2b_shop_id = shop_id
        return res

    def map_with_bulk_order(self):

        sale_order = self.env["sale.order"]
        product_id = self.env["product.product"] 
        
        for po in self:
            order_id = sale_order.search([('amazon_b2b_order_id', '=', po.purchase_order)])
            if not order_id:
            
                # Get Customer 
                customer_id, billing_id, shipping_id = self._get_customer_details(po)

                # Get Order Lines
                same_po_ids = self.search([('purchase_order', '=', po.purchase_order), ('amazon_b2b_shop_id', '=', po.amazon_b2b_shop_id.id)])
                order_lines = []
                for order in same_po_ids:
                    product_id = product_id.search([('default_code','=',order.model_number)])
                    if int(order.accepted_quantity) != 0:
                        order_lines += [(0, 0, {
                                        'product_id': product_id.id,
                                        'price_unit': order.unit_cost,
                                        'product_uom_qty': order.accepted_quantity,
                                    })]

                # Create Order
                if len(order_lines) > 0 and customer_id and billing_id and shipping_id:

                        try:    
                            sale_order_id = sale_order.create({
                                'partner_id': customer_id.id,
                                'partner_invoice_id': billing_id.id,
                                'partner_shipping_id': shipping_id.id ,
                                'amazon_b2b_order_id': po.id,
                                'mirakl_order_state': "shipping",
                                'warehouse_id': po.amazon_b2b_shop_id.warehouse_id.id,
                                'order_line': order_lines,
                                'market_place_shop': po.amazon_b2b_shop_id.name,
                            })
                            if sale_order_id:
                                for same_po in same_po_ids:
                                    same_po.sale_order_id = sale_order_id
                                if po.invoice_date:
                                    sale_order_id.date_order = po.invoice_date
                        except Exception as e:
                            _logger.info("Error while order creation - %r   !!!!!", e)
                else:
                    _logger.info("Erorr while getting following data\n order lines - %r \n customer - %r, billing - %r, shipping - %r", order_lines, customer_id, billing_id, shipping_id)
                
                if po.sale_order_id:
                    po.process_to_done(po.sale_order_id)
            else:
                if po.invoice_date:
                    order_id.date_order = po.invoice_date
                po.sale_order_id = order_id

    def _get_customer_details(self, order):

        customer_env = self.env['res.partner']
        billing_customer = False
        shipping_customer = False
        customer_id = billing_customer = shipping_customer = self.env["res.partner"]
        #Country Code
        if order.vendor:
            customer_id = customer_env.search([('is_amazon_b2b_customer','=',True), ('warehouse_name','=',order.warehouse)], limit=1)
            _logger.info("~~~~~~~~~Customer        %r        ", customer_id)
            if customer_id:
                billing_customer = customer_env.search([('parent_id','=',customer_id.id)], limit=1)
                shipping_customer = customer_env.search([('parent_id','=',customer_id.id)], limit=1)
                if not billing_customer:
                    billing_customer = customer_env.create({
                        'company_type': 'person',
                        'type': 'invoice',
                        'parent_id': customer_id.id,
                        'name': customer_id.name,
                        'street': customer_id.street,
                        'state_id': customer_id.state_id.id if customer_id.state_id else None,
                        'country_id': customer_id.country_id.id,
                    })
                if not shipping_customer:
                    shipping_customer = customer_env.create({
                        'company_type': 'person',
                        'type': 'delivery',
                        'parent_id': customer_id.id,
                        'name': customer_id.name,
                        'street': customer_id.street,
                        'state_id': customer_id.state_id.id if customer_id.state_id else None,
                        'country_id': customer_id.country_id.id,
                    })

        return [customer_id, billing_customer, shipping_customer]


    def process_to_done(self, sale_order):

        # Confirm Order And Validate Delivery 
        sale_order.action_confirm()



        # if len(sale_order.picking_ids) > 0:
        #     for delivery in sale_order.picking_ids:
        #         if delivery.products_availability == "Available":
        #             delivery.action_assign()
        #             for move in delivery.move_lines.filtered(lambda m: m.state not in ["done", "cancel"]):
        #                 rounding = move.product_id.uom_id.rounding
        #                 if (
        #                     float_compare(
        #                         move.quantity_done,
        #                         move.product_qty,
        #                         precision_rounding=rounding,
        #                     )
        #                     == -1
        #                 ):
        #                     for move_line in move.move_line_ids:
        #                         move_line.qty_done = move_line.product_uom_qty
        #             delivery.with_context(skip_immediate=True, skip_sms=True).button_validate()
        #             sale_order.invoice_status = 'to invoice'
