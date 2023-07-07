# -*- coding: utf-8 -*-

from odoo import api, models, fields, _

import logging
_logger = logging.getLogger(__name__)

class Product(models.Model):
    _inherit = "product.product"


    
    everstox_mapped_state = fields.Selection([('mapped', 'Mapped'), ('unmapped', 'Unmapped')])
    everstox_shop_ids = fields.Many2one("everstox.shop", string = "Everstox Shop", readonly=True)
    everstox_product_id = fields.Many2one("everstox.shop.product", string="Everstox Product")


    # Map New Products
    def mapped_products_data(self):
        new_products = [product for product in self if product.everstox_mapped_state != "mapped"]
        for product in new_products:
            
            # Create EverStox Product 
            everstox_product_id = self.env['everstox.shop.product']
            already_exist = everstox_product_id.search([('sku', '=', product.default_code)])
            if not already_exist:
                product_details = self.env['marketplace.product'].search([('sku', '=',product.default_code)], limit=1)
                product_data = {
                    "batch_product": True,
                    "everstox_shop_id": product.everstox_shop_ids.id,
                    "ignore_during_import": False,
                    "name": product.default_code,
                    "size": product_details.size,
                    "sku": product.default_code,
                    "status": "active",
                    "color": product_details.colors,
                    "total_stock": 0,
                    "product_id": product.id,
                    "customs_code": product_details.hs_code,
                    "customs_description": "HS CODE",
                    "country_of_origin": product_details.country,
                    "ignore_during_import": False,
                    "everstox_warehouse_id": product.everstox_shop_ids.everstox_warehouse_id.id,
                    "api_mapping_status": "unmapped",
                    "everstox_batch_unit": [(0,0,
                        {
                        "default_unit": True,
                        "gtin": product.barcode,
                        "length_in_cm": product_details.ship_length_cm,
                        "width_in_cm": product_details.ship_width_cm,
                        "height_in_cm": product_details.ship_height_cm,
                        "name": "Piece",
                        "quantity_of_base_unit": 1,
                        "weight_gross_in_kg": product_details.product_weight_kg,
                        "weight_net_in_kg": product_details.ship_weight_kg,
                        }
                    )]
                }
                
                new_product = everstox_product_id.create(product_data)
                product.everstox_product_id = new_product
                product.everstox_mapped_state = "mapped"


    def unmap(self):
        for product in self:
            product.everstox_mapped_state = "unmapped"
            product.everstox_product_id = None
            