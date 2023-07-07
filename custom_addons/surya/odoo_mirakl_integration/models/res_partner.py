# -*- coding: utf-8 -*-

from odoo import api, models, fields, _


class Partner(models.Model):
    _inherit = "res.partner"

    mirakl_customer_id = fields.Char("Mirakl Customer Id")
    mirakl_locale = fields.Char("Mirakl Locale")
    