from odoo import fields, models


class ModuleName(models.TransientModel):
    _inherit = 'bulk.inventory.update'

    wayafair_shops = fields.Many2many(comodel_name='wayfair.seller', string='Wayfair Shops')
    