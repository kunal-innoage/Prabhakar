from odoo import fields, models


class InventoryManagement(models.Model):
    _name = "inno.inventory.management"
    _inherit=["mail.thread","mail.activity.mixin"]
    _description = "Inventory Management"
    _rec_name = "product"

    product = fields.Char("Product Name")
    product_id=fields.Char("Product ID")
    quantity=fields.Integer("Quantity") 
    location=fields.Char("Location")
    date=fields.Datetime("Date-Time")
    color=fields.Selection([('red','Male'),('blue','Female'),('green','Green')],string="Color")
    purchase_id=fields.Many2one("purchasee","Purchase Order")
    vendor_id=fields.Many2one("vendor","Vendor Product")
    stocks_ids=fields.Many2one("innoage.stocks","Stocks")
    roq_id=fields.Many2one("request","Vendor Product")
