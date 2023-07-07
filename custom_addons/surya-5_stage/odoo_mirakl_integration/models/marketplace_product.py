# -*- coding: utf-8 -*-

from odoo import fields, models, _, api

import logging
_logger = logging.getLogger(__name__)


class MarketplaceProduct(models.Model):
    _name = "marketplace.product"
    _description = "Marketplace Products"
    _rec_name = "sku"

    sku = fields.Char("SKU")
    design = fields.Char("DESIGN")
    material_design = fields.Char("MASTER DESIGN(VARIANT CODE)")
    vendor_ref_number = fields.Char("VENDOR REFRENCE NUMBER")
    collection_name = fields.Char("Collection Name")
    pattern = fields.Char("Pattern/Style")
    rug_shape = fields.Char("Rug Shape")
    product_link = fields.Char("Product Link")
    hs_code = fields.Char("HS CODE")
    colors = fields.Char("COLORS")
    upc = fields.Char("UPC/EAN")
    size = fields.Char("Size")
    length_cm = fields.Char("Length cm")
    width_cm = fields.Char("Width cm")
    total_area = fields.Float("Total Area")
    product_weight_kg = fields.Char("Product weight kg")
    ship_weight_kg = fields.Char("Ship Weight_ kg")
    ship_length_cm = fields.Char("Ship Length_ cm")
    ship_width_cm = fields.Char("Ship Width_ cm")
    ship_height_cm = fields.Char("Ship Height_ cm")
    volume_per_pcs = fields.Char("Volume per pcs (cbm-m3)")
    material_composition = fields.Char("Content/Material Composition")
    construction = fields.Char("Construction")
    in_out_door = fields.Char("In Door_Out Door")
    machine_washable = fields.Char("Machine Washable")
    vendor = fields.Char("Vendor")
    country = fields.Char("Country")
    fob_psm = fields.Char("FOB PSM")
    fob_cost_per_pc = fields.Char("FOB Cost per pc")
    landed_cost_psm = fields.Char("Landed Cost PSM")
    landed_cost_per_pc_usd = fields.Char("Landed Cost per Piece USD")
    landed_cost_per_pc_eur = fields.Char("Landed Cost per Piece EUR")
    points = fields.Char("POINTS")
    reed = fields.Char("REED")
    shots = fields.Char("SHOTS")
    dtex = fields.Char("DTEX")
    colors_in_creel = fields.Char("# OF COLORS IN CREEL")
    pile_weight = fields.Char("Pile weight")
    backing_weight_gr = fields.Char("Backing weight-gr")
    weight_sqm_gr = fields.Char("Weight/sqm(gr)")
    backing_material = fields.Char("Backing material")
    fringe = fields.Char("Fringe")
    carved = fields.Char("Carved")
    length_of_finge_cm = fields.Char("Length of Finge cm")
    lance = fields.Char("Lance")
    pile_height_mm = fields.Char("pile height-mm")
    overall_thickness_backing = fields.Char("Overall Thikness Including Backing-MM")
    pile_type = fields.Char("Pile Type")
    loom_size_cm = fields.Char("LOOM SIZE CM")
    container_capacity_in_pile = fields.Char("Container Capacity/m2 pile in")
    container_capacity_out_pile = fields.Char("Container Capacity/m2 pile out")
    quality_degree = fields.Char("Quality Degree")
    etl_wh = fields.Char("ETL WH")
    waryfair_wh = fields.Char("Wayfair CG WH")
    iful_wh = fields.Char("I-Fulfilment UK WH")
    cdisc_wh = fields.Char("Cdiscount-3PL")

    product_id = fields.Many2one('product.product', string="Product")


    def map_product_info(self):
        for product in self:
            product_id = self.env['product.product'].search([('default_code','=',product.sku)])
            if product_id:
                product.product_id = product_id
                if product_id.vendor_reference != product.vendor_ref_number:
                    product_id.vendor_reference = product.vendor_ref_number
                if product_id.marketplace_product_id != product.id:
                    product_id.marketplace_product_id = product

    def map_fob_cost(self):
        for product in self:
            if product.product_id:
                for seller in product.product_id.seller_ids:
                    if product.vendor in  seller.name.name:
                        seller.price = product.fob_cost_per_pc
                        
                        
    # def map_marketplace_product_with_asi_extension(self):
    #     for rec in self:
    #         product_id  = self.env['product.product'].search([("default_code","=",rec.sku)])
    #         if product_id:
    #             product_id.ship_weight_kg = rec.ship_weight_kg
                
    

                

