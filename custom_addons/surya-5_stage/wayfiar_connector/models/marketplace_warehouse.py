from odoo import fields,models

class MarketplaceWarehouse(models.Model):
    _inherit = 'marketplace.warehouse'

    wayfair_supplier_id = fields.Char("Wayfair Supplier ID")
