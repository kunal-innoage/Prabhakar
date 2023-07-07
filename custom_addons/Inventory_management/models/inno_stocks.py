from odoo import fields, models


class InnoageStocks(models.Model):
    _name = "innoage.stocks"
    _inherit=["mail.thread","mail.activity.mixin"]
    _description = "Innoage Stocks"
    _rec_name = "product_ids"

    product_ids = fields.One2many("inno.inventory.management","stocks_ids","Products")
    quantity=fields.Integer("Quantity") 
    location=fields.Char("Location")
    received_on=fields.Datetime("Received On")
    per_unir_price=fields.Integer("Unit Price")
    