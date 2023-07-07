# -*- coding: utf-8 -*-

from odoo import api, models, fields, _


class Partner(models.Model):
    _inherit = "res.partner"

    is_amazon_b2b_customer = fields.Boolean("Is a Amazon B2B Customer")
    warehouse_code = fields.Char("Warehouse Code")
    warehouse_name = fields.Char("Warehouse")
