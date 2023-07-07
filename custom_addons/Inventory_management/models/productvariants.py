from odoo import fields, models

class ProductVariants(models.Model):
    _name = "product.variant"
    _inherit=["mail.thread","mail.activity.mixin"]
    # _rec_name = "product variant"


    reference = fields.Char("Internal Reference")
    name=fields.Char("Name") 
    website=fields.Char("Website")
    salesPrice=fields.Integer("Sales Price")
    cost=fields.Integer("Cost")
    quantity=fields.Integer("Quantity On Hand")
    producttype=fields.Selection([('service','Service'),('consumeable','Consumeable')],string="Product Type")
    dimensions=fields.Integer("Dimensions")
    color=fields.Selection([('red','Red'),('blue','Blue')],string="Color")
    cost=fields.Integer("Cost")