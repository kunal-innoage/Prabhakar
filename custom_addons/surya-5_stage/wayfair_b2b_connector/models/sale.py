from odoo import fields,api,models

import logging
_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    wayfair_b2b_order_id = fields.Many2one("wayfair.b2b.sale.order","Wayfair B2b Order")
    wayfair_b2b_order_number = fields.Char("Wayfair B2B Order Number")
    wayfair_b2b_shop_id = fields.Many2one("wayfair.b2b.shop","Wayfair B2b Shop ID")

    def update_date(self):
        res = super(SaleOrder, self).update_date()
        for order in self:
            if order.wayfair_b2b_order_id:
                try:
                    # Convert Date 
                    date, month, year =  order.wayfair_b2b_order_id.po_date_and_time.split("/")
                    year, time = year.split(" ")
                    date = year + "-" + month + "-" + date + " " + time
                    order.date_order = date
                except:
                    try:
                        month,date, year =  order.wayfair_b2b_order_id.po_date_and_time.split("/")
                        year, time = year.split(" ")
                        date = year + "-" + month + "-" + date + " " + time
                        order.date_order = date
                    except:
                        _logger.info("~~~~~~~~~~Date Format Issue ~~~~~~~~~")
        return res


    def marketplace_action_update(self):
        multi_shop_orders = {}
        for order in self:
            if order.wayfair_b2b_order_number or order.wayfair_b2b_order_id:
                self.env['wayfair.b2b.shop'].get_orders(order)

        return super(SaleOrder,self).marketplace_action_update()
