from odoo import fields,api, models,_
import requests
from odoo.http import request
import json, datetime

import logging
_logger = logging.getLogger(__name__)

class EverstoxProductUnit(models.Model):
    _name = 'everstox.product.unit'
    _description = 'Everstox Product Unit'

    unit_id = fields.Char("Unit ID")
    name = fields.Char("Name")
    default_unit = fields.Char("Default Unit")
    gtin = fields.Char("GTIN")
    base_item = fields.Char("Base Item")
    base_unit_id = fields.Char("Base Unit ID")
    base_unit_name = fields.Char("Base Unit Name")
    quantity_of_base_unit = fields.Char("Quantity Of Base Unit")
    weight_net_in_kg = fields.Char("Net Weight in KG")
    weight_gross_in_kg = fields.Char("Gross Wieght In KG")
    height_in_cm = fields.Char("Height In CM")
    width_in_cm = fields.Char("Width In CM")
    length_in_cm = fields.Char("Length In CM")
    
    everstox_shop_id = fields.Many2one("everstox.shop", string= "Shop")
    everstox_product_id = fields.Many2one("everstox.shop.product", string= "Product")
