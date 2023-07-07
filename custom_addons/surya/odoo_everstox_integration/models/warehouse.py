from odoo import fields,api, models,_
import requests
from odoo.http import request
import json, datetime

import logging
_logger = logging.getLogger(__name__)

class EverstoxShopWarehouse(models.Model):
    _name = 'everstox.shop.warehouse'
    _description = 'Everstox Shop Warehouse'
    _rec_name = "warehouse_name"

    warehouse_id = fields.Char("Id")
    warehouse_name = fields.Char("Name")
    internal_reference = fields.Char("Internal Reference")
    creation_date = fields.Char("Creation Date")
    updated_date = fields.Char("Updated Date")
    cut_off_time = fields.Char("Cut Of Time")
    cut_off_window = fields.Char("Cut Of Window")
    onboarding = fields.Boolean("On Boarding")

    everstox_shop_id = fields.Many2one("everstox.shop", string= "Shop")
    