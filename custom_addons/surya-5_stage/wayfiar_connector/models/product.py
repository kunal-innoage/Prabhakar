from odoo import fields,api,models
from asyncio.log import logger

class Product(models.Model):
    _inherit = 'product.template'

    wayfair_product_desc = fields.Text("Wayfair Product Description")



class WayfairProductDescription(models.Model):
    _name = 'wayfair.product.description'
    _description = "Wayfair Product Descrition"
    _rec_name = 'sku'

    sku = fields.Char("SKU")
    desc = fields.Char("Description/Name")
    odoo_product_id = fields.Many2one("product.template", "Odoo Product")

    def map_products(self):
        for res in self:
            product = self.env['product.product'].search([('default_code','=',res.sku)],limit=1)
            if product:
                product.wayfair_product_desc = res.desc
                logger.info("SKU %s mapped with odoo Product", res.sku)
            else:
                logger.info("SKU %s not found in odoo", res.sku)
