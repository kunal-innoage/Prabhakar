from odoo import models, fields,api
from asyncio.log import logger

class ProductImage(models.Model):
    _name = 'product.image'
    _description = 'Product Images And Video'
    _rec_name = "sku"

    sku = fields.Char(string='SKU')
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
    product_id = fields.Many2one(comodel_name='product.template', string='Product')
    


    def map_product_information(self):
        for rec in self:
            if rec.sku:
                product = self.env['product.template'].search([('default_code','=',rec.sku)],limit=1)
                if product:
                    # product.
                    # pass
                    product.shape = rec.shape
                    product.flat_image = rec.flat_image
                    product.corner = rec.corner
                    product.fold_image = rec.fold_image
                    product.front = rec.front
                    product.pile = rec.pile
                    product.roomscene1 = rec.roomscene1
                    product.swatch = rec.swatch
                    product.roomscene2 = rec.roomscene2
                    product.styleshot = rec.styleshot
                    product.video = rec.video
                    product.roomscene3 = rec.roomscene3
                    product.design_id = rec.design_id
                    product.texture = rec.texture
                    rec.product_id = product.id
                    logger.info("Information mapped with the product")
    
    
