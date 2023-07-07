from odoo import fields, models


class ShopProduct(models.Model):
    _name = "shops.product"
    _description = "Marketplace Products"

       
    product_name=fields.Many2one("product.product","Product")