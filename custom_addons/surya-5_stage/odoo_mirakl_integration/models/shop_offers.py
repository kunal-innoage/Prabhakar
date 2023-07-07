# -*- coding: utf-8 -*-

from odoo import fields, models, _, api
from odoo.exceptions import ValidationError, UserError
import requests
from odoo.http import request
import json, datetime
from datetime import timedelta

import logging
_logger = logging.getLogger(__name__)

class ShopOffers(models.Model):
    _name = "mirakl.offers"
    _description = "Shop Offers"
    _rec_name = "offer_id"


    # Base Fields
    offer_id = fields.Char("Offer Id")
    active = fields.Boolean("Active")
    shop_id = fields.Many2one("shop.integrator", "Shop")
    shop_stock_ids = fields.Many2one("mirakl.stock", "Shop Stock")
    product_id = fields.Many2one("product.product", "Product")
    product_sku = fields.Char("Shop Product")
    description = fields.Char("Shop Description")
    quantity = fields.Integer("Shop Quantity")
    offer_update_date = fields.Datetime("Last Update Date")
    inventory_id = fields.Many2one("warehouse.inventory","inventory id")
    # Price Fields
    price = fields.Float("Shop Price")
    total_price = fields.Float("Shop Total Price")
    origin_price = fields.Float("Shop Origin Price")
    discount_price = fields.Float("Shop Discount Price")
    discount_start_date = fields.Datetime("Shop Discount Start Date")
    discount_end_date = fields.Datetime("Shop Discount End Date")
    available_start_date = fields.Datetime("Shop Available Start Date")
    available_end_date = fields.Datetime("Shop Available End Date")
    currency_iso_code = fields.Char("Shop Currency ISO Code")
    discount_ranges = fields.Char("Shop Discount Range")
    min_shipping_price = fields.Char("Shop Min Shipping Price")
    min_shipping_price_additional = fields.Char("Shop Min Shipping Price Additional")
    price_ranges = fields.Char("Shop Price Ranges")
    
    # Extra Fields
    state_code = fields.Integer("State Code")
    mirakl_shop_id = fields.Integer("Shop Id")
    shop_name = fields.Char("Shop Name")
    professional = fields.Boolean("Professional")
    premium = fields.Boolean("Premium")
    logistic_class = fields.Char("Logistic Class")
    favorite_rank = fields.Char("Favorite Rank")
    channels = fields.Char("Channels")
    deleted = fields.Boolean("Deleted")
    leadtime_to_ship = fields.Char("Leadtime To Ship")
    allow_quote_requests = fields.Boolean("Allow Quote Requests")
    fulfillment_center_code = fields.Char("Fullfillment Center Code")
    origin = fields.Char("Origin")
    min_shipping_zone = fields.Char("Min Shipping Zone")
    min_shipping_type = fields.Char("Min Shipping Type")
    last_updated_import_id = fields.Char("Last Updated Import ID")
    stock_in_sync = fields.Boolean("Stock in sync", compute="_compute_stock_sync")


    @api.depends('quantity')
    def _compute_stock_sync(self):
        for rec in self:
            inventory_record = self.env['warehouse.inventory'].search([('odoo_product_id','=',rec.product_id.id)], order= 'create_date desc' ,limit=1)

            if rec.quantity == inventory_record.available_stock_count:
                rec.stock_in_sync = True
            else:
                rec.stock_in_sync = False

    #Pass on invenotry notification button
    def pass_call(self):
        pass


    


