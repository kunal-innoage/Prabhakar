from odoo import models,fields



class SaleOrder(models.Model):
    _inherit = 'sale.order'

    blade_order_mapped = fields.Boolean("blade Order Mapped")
