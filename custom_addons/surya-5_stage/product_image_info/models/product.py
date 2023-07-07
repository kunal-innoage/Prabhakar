
from odoo import fields,models

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    shape = fields.Char(string='Shape')
    flat_image = fields.Char(string='Flat Image')
    corner = fields.Char(string='Corner')
    fold_image = fields.Char(string='Fold Image')
    front = fields.Char(string='Front')
    pile = fields.Char(string='Pile')
    roomscene1 = fields.Char("Room Scene 1")
    swatch = fields.Char("Swatch")
    roomscene2 = fields.Char("Room Scene 2")
    styleshot = fields.Char("Style Shot")
    video = fields.Char(string='Video')
    roomscene3 = fields.Char("Room Scene 3")
    design_id = fields.Char("Design ID")
    texture = fields.Char("Texture")