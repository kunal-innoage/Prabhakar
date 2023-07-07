from odoo import fields, models


class Transfers(models.Model):
    _name = "transfer"

    reference = fields.Char("Reference")
    contact=fields.Integer("Contact") 
    date=fields.Datetime("Date-Time")
    sourceDocument=fields.Char("Source Document")
    company=fields.Char("Company Name")
    product=fields.Char("Product")
    demand=fields.Char("Demand")
    shipping_policy=fields.Char("Shipping Policy")
    responsible=fields.Char("Responsible")
    procurement_group=fields.Char("Procurement Group")
    company=fields.Char("Company")


