from odoo import models,api,fields

class ResPartner(models.Model):
    _inherit = 'res.partner'

    wayfair_customer_id = fields.Char("Wayfair Customer Id")