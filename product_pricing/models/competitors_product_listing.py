from odoo import fields, models

class CompetitorProduct(models.Model):
    _name ="competitor.product.listing"
    _description="Competitor Product Listng"

    product_name=fields.Char("Product Name")
    product_url=fields.Char("URL")
