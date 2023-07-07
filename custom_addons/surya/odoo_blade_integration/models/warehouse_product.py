from odoo import api, fields, models


class WarehouseProduct(models.Model):
    _name = 'blade.product'
    _description = 'Blade Product'

    name = fields.Char(string='Name')
    sku = fields.Char("SKU")
    variation_id = fields.Char("Variation ID")
    is_primary = fields.Char(string='IS Primary')
    status = fields.Char(string='status')
    create_date_at_blade = fields.Char(string='Create Date at blade')
    date_tz = fields.Char(string='Time Zone')
    blade_product_id = fields.Char(string='Blade Product')
    product_channel_id = fields.Char(string='Product Channel ID')
    prod_org_id = fields.Char(string='Organization ID')
    
    
