# -*- coding: utf-8 -*-

from odoo import fields, models, _, api

import logging
_logger = logging.getLogger(__name__)

class ShopCarrier(models.Model):
    _name = "mirakl.carrier"
    _description = "Shop Carrier"
    _rec_name = "label"


    # Base Fields
    activate = fields.Boolean("Activate")
    shop_id = fields.Many2one("shop.integrator", "Shop")
    label = fields.Char("Label")
    code = fields.Char("Code")
    tracking_url = fields.Char("Tracking Url")


    def sync_shop_carriers(self, shop_id, carrier_info):

        for carrier in carrier_info['carriers']:
            if len(self.search([('shop_id', 'in', [shop_id.id]), ('label', 'in', [carrier.get('label')]), ('code', 'in', [carrier.get('code')])])) == 0:
                try:
                    self.create({
                        "shop_id": shop_id.id,
                        "label": carrier.get('label'),
                        "code": carrier.get('code'),
                        "tracking_url": carrier.get('tracking_url'),
                    })
                except:
                    _logger.info("Carrier Sync Failed for %r shop with info - %r", shop_id.name, carrier)
        return True
