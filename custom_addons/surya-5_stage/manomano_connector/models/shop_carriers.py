# -*- coding: utf-8 -*-

from odoo import fields, models, _, api

import logging
_logger = logging.getLogger(__name__)

class ManomanoCarrier(models.Model):
    _name = "manomano.carrier"
    _description = "Manomano Carrier"
    _rec_name = "label"


    # Base Fields
    activate = fields.Boolean("Activate")
    shop_id = fields.Many2one("manomano.seller", "Shop")
    label = fields.Char("Label")
    code = fields.Char("Code")
    tracking_url = fields.Char("Tracking Url")

    @api.model_create_multi
    def create(self, vals):
        res = super(ManomanoCarrier, self).create(vals)
        if res._context.get('import_file'):
            shop = self.env['manomano.seller'].search([('id', '=', res._context.get('active_id'))])
            for carrier in res:
                carrier.shop_id = shop.id

        return res
