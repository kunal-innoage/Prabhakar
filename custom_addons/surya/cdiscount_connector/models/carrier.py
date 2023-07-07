from odoo import fields,models,api


class CdiscountCarrier(models.Model):
    _name = 'cdiscount.carrier'
    _description = 'Cdiscount Carrier'

    shop_id = fields.Many2one(comodel_name='cdiscount.seller', string='Shop')
    label = fields.Char(string='Label')
    code = fields.Char("Code")
    tracking_url = fields.Char(string='Tracking URL')
    
    
    