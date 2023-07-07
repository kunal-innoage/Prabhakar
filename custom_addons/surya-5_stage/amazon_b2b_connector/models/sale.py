from odoo import fields,api,models

import logging
_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    amazon_b2b_order_id = fields.Many2one("amazon.b2b.sale.order","Amazon B2b Order")


    def update_date(self):
        res = super(SaleOrder, self).update_date()
        for order in self:
            if order.amazon_b2b_order_id:

                day, month, year = order.amazon_b2b_order_id.window_start.split("/")
                order.date_order = year+ "-" + month + "-" + day
        return res

    def export_warehouse_orders(self):

        shipping_sale_orders = []
        for order in self:
            if order.mirakl_order_state and order.mirakl_order_state == "shipping" and order.amazon_b2b_order_id:
                shipping_sale_orders.append(order)
        if len(shipping_sale_orders) > 0:
            self.env['shop.integrator'].separate_warehouse_orders(shipping_sale_orders)
        return super(SaleOrder, self).export_warehouse_orders()
