 # -*- coding: utf-8 -*-

# from math import prod
from odoo import fields, models, _, api
from odoo.exceptions import Warning, ValidationError

import datetime

import logging
_logger = logging.getLogger(__name__)

class ShopOffers(models.TransientModel):
    _name = "shop.offer"
    _description = "Shop Offers"

    product_id = fields.Many2one("product.product", "Product")
    shop_ids = fields.Many2many("shop.integrator", "shop_quantity_ref", "offer_id", "shop_ids", "Marketplaces")
    updated_product_qty = fields.Integer(string="Add Products Qty")

    # Single Shop

    def push_product_qty(self):
        ctx = self._context
        shop_stock = self.env['mirakl.stock'].search([('id', '=', ctx['active_id'])])
        updated = shop_stock.shop_id.add_stock_qty(shop_stock.mirakl_product_ref, self.updated_product_qty)
        if updated:
            shop_stock.quantity += self.updated_product_qty
            shop_stock.last_updated_date = datetime.datetime.now()
            _logger.info("~~~~updated_product_qty~~~~~~~~~~%r~~~~~~", shop_stock.quantity)
        else:
            print("API call per minute has reached the limit. Please wait for a while and it will start working again.")

    def push_updated_product_qty(self):
        ctx = self._context
        shop_stock = self.env['mirakl.stock'].search([('id', '=', ctx['active_id'])])
        updated = shop_stock.shop_id.add_stock_qty(shop_stock.mirakl_product_ref, self.updated_product_qty)
        if updated:
            shop_stock.quantity = self.updated_product_qty
            shop_stock.last_updated_date = datetime.datetime.now()
            _logger.info("Updated product qty~~~~~~~~~~%r ;;;;;", shop_stock.quantity)
        else:
            print("API call per minute has reached the limit. Please wait for a while and it will start working again.")


    # Multiple Shops

    def push_updated_multiple_shops_qty(self):
        for shop in self.shop_ids:
            shop_stock = self.env['mirakl.stock'].search([('shop_id', '=', shop.id), ('odoo_product_id', '=', self.product_id.id)], limit=1)
            updated = shop.add_stock_qty(shop_stock.mirakl_product_ref, shop_stock.quantity + self.updated_product_qty)
            if updated:
                shop_stock.quantity += self.updated_product_qty
                shop_stock.last_updated_date = datetime.datetime.now()
                _logger.info("Updated_product_qty~~~~~~~~~~%r ;;;;;", shop_stock.quantity)
            else:
                print(" API call per minute has reached the limit. Please wait for a while and it will start working again.")



        
