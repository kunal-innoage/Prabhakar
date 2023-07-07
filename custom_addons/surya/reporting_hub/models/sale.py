from odoo import models,fields


class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    market_place_shop = fields.Char(string='Shop')
