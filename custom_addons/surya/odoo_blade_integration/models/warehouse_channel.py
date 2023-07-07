from odoo import api, fields, models


class WarehouseChannels(models.Model):
    _name = 'blade.channel'
    _description = 'Channels'
    _rec_name = 'org_name'

    channel_id = fields.Char(string='Channel ID')
    org_id = fields.Char(string='Organization ID')
    tax_id = fields.Char("Tax ID")
    tax_name = fields.Char(string='Tax')
    tax_code = fields.Char(string='Tax Code')
    tax_rate = fields.Char(string='Rate')
    org_name = fields.Char("organization name")
    
    
    