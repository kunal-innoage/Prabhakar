from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit="product.template"
 
    def publish_website_products(self):
        for product in self:
            product.is_published = True
            product.website_published = True
    
