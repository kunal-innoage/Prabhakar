from odoo import fields, models

class Competitor(models.Model):
    _name ="competitor.shop"
    _description="Competitor shops"

    name=fields.Char("Name")
    url=fields.Char("URL")
