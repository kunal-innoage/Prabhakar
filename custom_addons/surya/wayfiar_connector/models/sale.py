# -*- coding: utf-8 -*-

from odoo import fields,api,models

import logging
_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    wayfair_order_id = fields.Char("Wayfair Order ID")
    warehouse = fields.Char("Warehouse name")
    wayfair_order_date = fields.Char("Wayfair Order Date")
    wayfair_shop_id = fields.Many2one("wayfair.seller", "Wayfair Shop")
    wayfair_platform_order_id = fields.Char(string='Wayfair Platform Order ID')
    label = fields.Binary(string='Label')
    label_id = fields.Many2one('wayfair.labels', "Import Label ID")
    wayfair_estimated_ship_date = fields.Char("Wayfair estimated ship date")
    registered_for_shipping = fields.Boolean("Order Register for shipping")
    is_label_attached = fields.Boolean("Is Label attached?")
    wayfair_carrier_code = fields.Char("Wayfair Carrier Code")
    

    def export_warehouse_orders(self):

        shipping_sale_orders = []
        for order in self:
            if order.mirakl_order_state and order.mirakl_order_state == "shipping" and order.wayfair_order_id:
                shipping_sale_orders.append(order)
        if len(shipping_sale_orders) > 0:
            _logger.info("_________%r Order Processed to Warehouse From Wayfair - ~~~~~~~~",len(shipping_sale_orders))
            self.env['shop.integrator'].separate_warehouse_orders(shipping_sale_orders)
        return super(SaleOrder, self).export_warehouse_orders()

    def generate_wayfair_label(self):
        wayfair_obj = self.env['wayfair.seller'].search([],limit=1)
        for rec in self:
            if rec.wayfair_order_id and not rec.is_label_attached and not rec.registered_for_shipping:
                register = wayfair_obj.register_order_for_shipping(rec.wayfair_order_id)
                wayfair_obj.get_wayfair_label(rec.wayfair_order_id)
            _logger.info("Either %s is already register for shipping or label is generated", rec )

    def marketplace_action_update(self):
        multi_shop_orders = {}
        for order in self:
            if order.wayfair_order_id:
                self.env['wayfair.seller'].get_orders(order.wayfair_order_id)

        return super(SaleOrder,self).marketplace_action_update()

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    line_id = fields.Char("Line Id")
