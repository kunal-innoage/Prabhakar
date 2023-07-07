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
    creel = fields.Char("Creel")
    continuity = fields.Char("Continuity")

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
                        
                
                        
                        
    def map_marketplace_product_with_asi_extension(self):
        for rec in self:
            product_id  = self.env['product.product'].search([("default_code","=",rec.sku)])
            if product_id:
                product_id.material_design = rec.material_design
                product_id.vendor_ref_number = rec.vendor_ref_number
                product_id.collection_name = rec.collection_name
                product_id.pattern = rec.pattern
                product_id.rug_shape = rec.rug_shape
                product_id.product_link = rec.product_link
                product_id.hs_code = rec.hs_code
                product_id.colors = rec.colors
                product_id.upc = rec.upc
                product_id.size = rec.size
                product_id.length_cm = rec.length_cm
                product_id.width_cm = rec.width_cm
                product_id.total_area = rec.total_area
                product_id.product_weight_kg = rec.product_weight_kg
                product_id.ship_length_cm = rec.ship_length_cm
                product_id.ship_width_cm = rec.ship_width_cm
                product_id.ship_height_cm = rec.ship_height_cm
                product_id.volume_per_pcs = rec.volume_per_pcs
                product_id.material_composition = rec.material_composition
                product_id.construction = rec.construction
                product_id.in_out_door = rec.in_out_door
                product_id.machine_washable = rec.machine_washable
                product_id.vendor = rec.vendor
                product_id.country = rec.country
                product_id.fob_psm = rec.fob_psm
                product_id.fob_cost_per_pc = rec.fob_cost_per_pc
                product_id.landed_cost_psm = rec.landed_cost_psm
                product_id.landed_cost_per_pc_usd = rec.landed_cost_per_pc_usd
                product_id.landed_cost_per_pc_eur = rec.landed_cost_per_pc_eur
                product_id.points = rec.points
                product_id.reed = rec.reed
                product_id.shots = rec.shots
                product_id.dtex = rec.dtex
                product_id.colors_in_creel = rec.colors_in_creel
                product_id.pile_weight = rec.pile_weight
                product_id.backing_weight_gr = rec.backing_weight_gr
                product_id.weight_sqm_gr = rec.weight_sqm_gr
                product_id.backing_material = rec.backing_material
                product_id.fringe = rec.fringe
                product_id.carved = rec.carved
                product_id.length_of_finge_cm = rec.length_of_finge_cm
                product_id.lance = rec.lance
                product_id.pile_height_mm = rec.pile_height_mm
                product_id.overall_thickness_backing = rec.overall_thickness_backing
                product_id.pile_type = rec.pile_type
                product_id.loom_size_cm = rec.loom_size_cm
                product_id.container_capacity_in_pile = rec.container_capacity_in_pile
                product_id.container_capacity_out_pile = rec.container_capacity_out_pile
                product_id.quality_degree = rec.quality_degree
                product_id.etl_wh = rec.etl_wh
                product_id.waryfair_wh = rec.waryfair_wh
                product_id.iful_wh = rec.iful_wh
                product_id.cdisc_wh = rec.cdisc_wh
                product_id.creel = rec.creel
                product_id.continuity = rec.continuity


    # def create_products(self):
    #     for rec in self:
    #         products = self.env["sale.order.line"].search([("name","=",rec.sku)])
            
            # _logger.info("!!!!!!!!!!!%r!!!!!!!!!",products)
            # if not products:
            #     product = self.env["sku.expense.analysis"].create({
            #         'product' : rec.sku 
            #     })