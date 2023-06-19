# -*- coding: utf-8 -*-

from odoo import api, models, fields, _

import logging
_logger = logging.getLogger(__name__)

class Product(models.Model):
    _inherit = "product.product"

    @api.depends('shop_stock_ids')
    def _get_mapped_shop_ids(self):
        if len(self.shop_stock_ids) > 0:
            for stock_id in self.shop_stock_ids:
                if stock_id.shop_id not in self.mapped_shop_ids:
                    self.mapped_shop_ids += stock_id.shop_id
        else:
            self.mapped_shop_ids = False
                


    mirakl_category_code = fields.Char("Category Code")
    mirakl_category_label = fields.Char("Category Label")
    average_landed_cost = fields.Float("Average Landing Cost")
    mirakl_product_sku = fields.Char("Mirakl Product SKU")
    product_title = fields.Char("Mirakl Product Title")
    vendor_reference = fields.Char("Vendor Reference Number")
    shop_stock_ids = fields.One2many("mirakl.stock", "odoo_product_id", "Shop Stocks")
    mapped_shop_ids = fields.Many2many("shop.integrator",  "product_shop_rel", "mapped_shop_ids", "product_id", string = "Marketplaces", readonly=True, compute = '_get_mapped_shop_ids')
    marketplace_product_id = fields.Many2one("marketplace.product", string="Marketplace Product")


    def action_update_quantity_on_shop(self):

        res = self.env['shop.offer'].create({
            "product_id": self.id,
            "shop_ids": self.mapped_shop_ids,
        })
        return {'name': 'Update Selected Shops Product Qty', 'res_id': res.id, 'res_model': 'shop.offer', 'type': 'ir.actions.act_window', 'view_mode': 'form', 'view_id': self.env.ref('odoo_mirakl_integration.multi_shop_product_qty_update_form').id, 'target': 'new', 'nodestroy': True}    
    
