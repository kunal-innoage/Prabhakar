# -*- coding: utf-8 -*-

from odoo import fields, models, _, api
import datetime
import pytz


import logging
_logger = logging.getLogger(__name__)


class MarketplaceVendor(models.Model):
    _name = "marketplace.vendor"
    _description = "Marketplace Vendors"
    _rec_name = "name"

    name = fields.Char("Name")
    short_name = fields.Char("Short Name")
    is_a_company = fields.Char("Is a company")
    reated_company = fields.Char("Related company")
    address_type = fields.Char("Address type")
    street = fields.Char("Street")
    zip = fields.Char("ZIP")
    city = fields.Char("City")
    state = fields.Char("State")
    country = fields.Char("Country")

    partner_id = fields.Many2one('res.partner', string='Vendor', help="If vendor is connected, details are mapped.")


    def map_vendor_info(self):
        for vendor in self:
            if not vendor.partner_id:
                seller_id = self.env['res.partner'].search([('name','=', vendor.name), ('supplier_rank','>=', 1)],limit=1)
            else:
                seller_id = vendor.partner_id
            if seller_id:
                vendor.partner_id = seller_id
                if seller_id.name != vendor.name:
                    seller_id.name = vendor.name
                if seller_id.street != vendor.street:
                    seller_id.street = vendor.street
                    seller_id.street2 = False
                if seller_id.city != vendor.city:
                    seller_id.city = vendor.city
                if seller_id.zip != vendor.zip:
                    seller_id.zip = vendor.zip
                if seller_id.country_id.name != vendor.country:
                    country_id = self.env['res.country'].search([('name','=', vendor.country)], limit=1)
                    seller_id.country_id = country_id
                    if seller_id.state_id.name != vendor.state:
                        state_id = self.env['res.country.state'].search([('name', '=', vendor.state), ('country_id', 'in', [country_id.id])])
                        seller_id.state_id = state_id
                
