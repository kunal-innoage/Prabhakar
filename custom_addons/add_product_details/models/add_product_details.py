from odoo import fields, models
# import logging
# _logger = logging.getLogger(__name__)

class ProductDescription(models.Model):
    _name = "add.product.details"
    _rec_name = "product_name"
    _description = "Product Details"

       
    product_name=fields.Char("Product Name")
    supplier_part_number=fields.Char("Supplier Part Number")
    option_name=fields.Char("Option Names")
    construction=fields.Char("Construction")
    technique=fields.Char("Technique / Weave")
    rug_type=fields.Char("Rug Type")
    material_composition=fields.Char("Material Composition")
    backing_material_composition=fields.Char("Backing Material Composition")
    rug_shape=fields.Char("Rug Shape" )
    primary_colour=fields.Char("Primary Colour")
    pattern=fields.Char("Pattern")
    purposeful_distressing_type=fields.Char("Purposeful Distressing Type")
    loaction=fields.Char("Location")
    life_stage=fields.Char("Life Stage", help='Please choose from the following:    Baby; Child; Teen; Adult')
    product_care=fields.Char("Product Care", help='Any manufacturer-specific instructions regarding how to care for this product. E.g., "Spot Clean with dry cloth," "Vacuum with no beater bar/rotating brush.')
    rug_size=fields.Char("Rug Size")
    pile_height=fields.Char("Pile Height")
    overall_product_weight=fields.Char("Overall Product Weight")
    overall_width=fields.Char("Overall Width - Side to Side")
    overall_length=fields.Char("Overall Length - End to End")
    warranty_length=fields.Char("Warranty Length")
    product_id=fields.Many2one("product.template", string="Product")


    def map_description(self):
        for product in self:
            desc=product.supplier_part_number

            prod_id=self.env["product.template"].search([("default_code","=",desc)], limit=1)

            # _logger.info("~~~~~~~~~~~%r~~~~~~~~~~", prod_id)
            
            product.product_id = prod_id
            if prod_id:
                prod_id.description_sale = product.option_name +"\n"+ product.technique 
        
            
            
           
