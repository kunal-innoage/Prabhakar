# -*- coding: utf-8 -*-

from odoo import fields, models, _, api
from odoo.exceptions import ValidationError, UserError, MissingError

import logging
_logger = logging.getLogger(__name__)


class MiraklStock(models.Model):
    _name="mirakl.stock"
    _description="Mirakl Stock Manangement"
    _rec_name = 'odoo_product_id'

    @api.depends('mirakl_product_ref')
    def get_onhand_qty(self):
        for rec in self:
            rec.warehouse_quantity = rec.odoo_product_id.qty_available

    odoo_product_id = fields.Many2one('product.product', 'Product', required=True, readonly=True)
    
    inventory_alert_limit = fields.Integer("Product Qty Alert Count", default=10, readonly=True)

    quantity = fields.Float('On Shop Quantity', readonly=True, digits='Product Unit of Measure',
        help='Quantity of products in this quant, in the default unit of measure of the product', default= 10)

    warehouse_quantity = fields.Float('On Hand Quantity', readonly=True, compute="get_onhand_qty")

    shop_id = fields.Many2one("shop.integrator", string="Shop", required=True, readonly=True)

    last_updated_date = fields.Datetime("Last Stock Updated Date", readonly=True)
    
    mirakl_product_ref = fields.Char("Marketplace Reference", required=True, readonly=True)


    def update_stock_quantity(self):
        return {'name': 'Add Product', 'res_model': 'shop.offer', 'type': 'ir.actions.act_window', 'view_mode': 'form', 'domain': '[]', 'target': 'new', 'nodestroy': True}

    def change_stock_quantity(self):
        return {'name': 'Update Product', 'res_model': 'shop.offer', 'type': 'ir.actions.act_window', 'view_mode': 'form', 'view_id': self.env.ref("odoo_mirakl_integration.shop_product_qty_updated_form").id, 'target': 'new', 'nodestroy': True}
        