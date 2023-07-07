from odoo import fields,api, models,_
import json, datetime

import logging
_logger = logging.getLogger(__name__)

class ShipmentOptions(models.Model):
    _name = 'shipment.options'
    _description = 'Everstox Shiment Options'

    name = fields.Char(string="Name")
    carrier_id = fields.Char(string="Carrier ID")
    creation_date = fields.Char(string="Creation Date")
    ignored = fields.Char("Ignored")
    external_identifiers = fields.Char("External Identifier")
    status = fields.Char(string="Status")
    updated_date = fields.Char(string="Updated Date")
    everstox_shop_id = fields.Many2one("everstox.shop", string= "Shop")
    shipment_option_aliases_ids = fields.One2many("shipment.options.aliases", "shipment_option_id", string= "Aliases")


class ShipmentOptionsAliases(models.Model):
    _name = 'shipment.options.aliases'
    _description = "Shipment Options Aliases"

    name = fields.Char("Name")
    aliase_id = fields.Char("Aliase ID")
    shipment_option_id = fields.Many2one("shipment.options", string= "Shipment Option")
