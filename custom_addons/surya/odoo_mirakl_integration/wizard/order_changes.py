# -*- coding: utf-8 -*-

# from math import prod
from odoo import fields, models, _, api
from odoo.exceptions import Warning, ValidationError

import datetime

import logging
_logger = logging.getLogger(__name__)

class ShopOffers(models.TransientModel):
    _name = "order.changes"
    _description = "Order Changes"

    sale_order_id = fields.Many2one("sale.order", "Sale Order")
    current_warehouse_id = fields.Many2one("stock.warehouse", "Current Warehouse", readonly=True)
    new_warehouse_id = fields.Many2one("stock.warehouse", "New Warehouse")


    def change_warehouse(self):
        for order in self:
            if self.current_warehouse_id != self.new_warehouse_id:
                for picking in self.sale_order_id.picking_ids:
                    picking.location_id = self.new_warehouse_id.lot_stock_id
                self.sale_order_id.warehouse_id = self.new_warehouse_id

    def switch_warehouse(self):
        for change in self:
            orders = self.env["sale.order"].search([("id","in", self._context.get("sale_order_ids"))])
            for order in orders:
                if order.warehouse_id != self.new_warehouse_id:
                    for picking in order.picking_ids:
                        picking.location_id = self.new_warehouse_id.lot_stock_id
                order.warehouse_id = self.new_warehouse_id
            

