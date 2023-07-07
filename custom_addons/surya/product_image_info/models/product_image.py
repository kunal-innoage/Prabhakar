from odoo import models, fields,api, _
from asyncio.log import logger
import requests
import logging 
_logger = logging.getLogger(__name__)
from odoo.exceptions import UserError, ValidationError



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
    product_id = fields.Many2one('product.template', string='Product')
    


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
    

    def check_image_links(self):
        
        expired = []
        for product in self:
            if product.flat_image:
                response = exit = False
                try:
                    response = requests.head(product.flat_image)
                except Exception as e:
                    _logger.info("Error while hitting head on image url ~~~~~~~~~~%r~~~~~~`",e)
                    expired.append(product.flat_image)
                    exit= True
                if response and not exit:
                    if response.status_code == 200:
                        _logger.info("Working URL ~~~~~~~~~~~~~~~~")
                    else:
                        expired.append(product.flat_image)
                
            if product.corner:
                response = exit = False
                try:
                    response = requests.head(product.corner)
                except Exception as e:
                    _logger.info("Error while hitting head on image url ~~~~~~~~~~%r~~~~~~`",e)
                    expired.append(product.corner)
                if response and not exit:
                    if response.status_code == 200:
                        _logger.info("Working URL ~~~~~~~~~~~~~~~~")
                    else:
                        expired.append(product.corner)
                
            if product.fold_image:
                response = exit = False
                try:
                    response = requests.head(product.fold_image)
                except Exception as e:
                    _logger.info("Error while hitting head on image url ~~~~~~~~~~%r~~~~~~`",e)
                    expired.append(product.fold_image)
                if response and not exit:
                    if response.status_code == 200:
                        _logger.info("Working URL ~~~~~~~~~~~~~~~~")
                    else:
                        expired.append(product.fold_image)
                
            if product.front:
                response = exit = False
                try:
                    response = requests.head(product.front)
                except Exception as e:
                    _logger.info("Error while hitting head on image url ~~~~~~~~~~%r~~~~~~`",e)
                    expired.append(product.front)
                if response and not exit:
                    if response.status_code == 200:
                        _logger.info("Working URL ~~~~~~~~~~~~~~~~")
                    else:
                        expired.append(product.front)
                
            if product.roomscene1:
                response = exit = False
                try:
                    response = requests.head(product.roomscene1)
                except Exception as e:
                    _logger.info("Error while hitting head on image url ~~~~~~~~~~%r~~~~~~`",e)
                    expired.append(product.roomscene1)
                if response and not exit:
                    if response.status_code == 200:
                        _logger.info("Working URL ~~~~~~~~~~~~~~~~")
                    else:
                        expired.append(product.roomscene1)
                
            if product.roomscene2:
                response = exit = False
                try:
                    response = requests.head(product.roomscene2)
                except Exception as e:
                    _logger.info("Error while hitting head on image url ~~~~~~~~~~%r~~~~~~`",e)
                    expired.append(product.roomscene2)
                if response and not exit:
                    if response.status_code == 200:
                        _logger.info("Working URL ~~~~~~~~~~~~~~~~")
                    else:
                        expired.append(product.roomscene2)
                
            if product.roomscene3:
                response = exit = False
                try:
                    response = requests.head(product.roomscene3)
                except Exception as e:
                    _logger.info("Error while hitting head on image url ~~~~~~~~~~%r~~~~~~`",e)
                    expired.append(product.roomscene3)
                if response and not exit:
                    if response.status_code == 200:
                        _logger.info("Working URL ~~~~~~~~~~~~~~~~")
                    else:
                        expired.append(product.roomscene3)
                
            if product.texture:
                response = exit = False
                try:
                    response = requests.head(product.texture)
                except Exception as e:
                    _logger.info("Error while hitting head on image url ~~~~~~~~~~%r~~~~~~`",e)
                    expired.append(product.texture)
                if response and not exit:
                    if response.status_code == 200:
                        _logger.info("Working URL ~~~~~~~~~~~~~~~~")
                    else:
                        expired.append(product.texture)
                
        if expired:
            _logger.info("~~~~~~~~~~~~  %r   ~~~~~~~~~~~~~", expired)
            raise ValidationError(_('Error URLS - %s',expired))
