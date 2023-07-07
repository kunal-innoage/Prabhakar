from odoo import models,api,fields

class ResPartner(models.Model):
    _inherit = 'res.partner'

    amazon_customer_id = fields.Char("Amazon Customer Id")