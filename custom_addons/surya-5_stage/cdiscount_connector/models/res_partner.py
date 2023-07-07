from odoo import models,api,fields

class ResPartner(models.Model):
    _inherit = 'res.partner'

    cdiscount_customer_id = fields.Char("Cdiscount Customer Id")