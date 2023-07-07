# -*- coding: utf-8 -*-

from odoo import fields, models, _, api
import logging
_logger = logging.getLogger(__name__)

class ShopOffers(models.Model):
    _name = "cdiscount.offers"
    _description = "Shop Offers"
    _rec_name = "offer_id"


    # Base Fields
    offer_id = fields.Char("Offer Id")
    offer_state = fields.Char(string='Offer State')
    comments = fields.Char(string='Comments')
    ean = fields.Char(string='EAN')
    parent_product_id = fields.Char("Parent Product ID")
    product_state = fields.Char("Product State")
    product_condition_id = fields.Char("Product Comdition ID")
    product_condition_name = fields.Char("Product Comdition Name")
    price = fields.Float("Shop Price")
    display_name = fields.Char("Display Name")
    eco_tax = fields.Float("Eco Tax")
    vat_rate = fields.Float("Vat Rate")
    dea_tax = fields.Float("Dea Tax")
    price_must_be_aligned = fields.Char("price must be aligned")
    minimum_price_for_price_alignment = fields.Float("minimum price for price alignment")
    best_shipping_charges = fields.Float("best shipping charges")
    product_packaging_unit = fields.Char("product packaging unit")
    product_packaging_unit_price = fields.Float("product packaging unit price")
    product_packaging_value = fields.Float("product packaging value")
    striked_price = fields.Float("striked price")
    cdiscount_product_id = fields.Char("Cdiscount Product ID")
    cdiscount_shop_id = fields.Many2one("cdiscount.seller","CDiscount Shop")

    
    product_sku = fields.Char("Shop Product")
    product_id = fields.Many2one("product.product", "Product")

    present_in_odoo = fields.Boolean("Product Present in Odoo")
    creation_date = fields.Date(string='creation date')
    last_update_date = fields.Date(string='last update date')

    stock_id = fields.Char("Stock ID")
    quantity = fields.Integer("Shop Quantity")
    sold_qty = fields.Integer("Sold Qty")


    #Pass on invenotry notification button
    def pass_call(self):
        pass
    