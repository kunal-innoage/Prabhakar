from odoo import fields , models 
import logging
from odoo.fields import Datetime
_logger = logging.getLogger(__name__)


class ProductShops(models.Model):
    _name="product.shop"
    _description="Product Shop analysis"
    _rec_name="sku"




    sku=fields.Char("Products/SKU")
    recommended_retail_price = fields.Float("Recommended Price" , invisible = True)
    
    # product_id=fields.Many2one("product.pricing", "Product ID")

    #################
    # WAYFAIR SHOPS #
    #################

    wayfair_uk=fields.Float("Wayfair UK")
    wayfair_de=fields.Float("Wayfair DE")

    ##################
    # MANOMANO SHOPS #
    ##################

    manomano_fr=fields.Float("Manomano FR")
    manomano_es=fields.Float("Manomano ES")
    manomano_it=fields.Float("Manomano IT")
    manomano_de=fields.Float("Manomano DE")
    manomano_gb=fields.Float("Manomano GB")

    #################
    # CHECK24 SHOPS #
    #################

    check=fields.Float("Check24")

    ################
    # AMAZON SHOPS #
    ################

    amazon_de=fields.Float("Amazon DE")
    amazon_uk=fields.Float("Amazon UK")
    amazon_fr=fields.Float("Amazon FR")

    ################
    # MIRAKL SHOPS #
    ################

    maison=fields.Float("Maison")
    conforama=fields.Float("Conforama")
    bricoprive=fields.Float("Bricoprive")
    home24_de=fields.Float("Home24 DE")
    pccomponentes=fields.Float("Pccomponentes")
    rueduco=fields.Float("Rueduco")
    carrefoures=fields.Float("Carrefoures")
    adeo=fields.Float("Adeo")
    leclerc=fields.Float("Leclerc")
    carrefourfr=fields.Float("Carrefourfr")
    but=fields.Float("But")
    empik_place=fields.Float("Empik Place")
    inno=fields.Float("INNO")
    vente_unique=fields.Float("VenteUnique")
    worten=fields.Float("Worten")
    home24_at=fields.Float("Home24 AT")
    home24_fr=fields.Float("Home24 FR")
    darty=fields.Float("Darty")
    vente_unique_es=fields.Float("VenteUnique ES")
    vente_unique_it=fields.Float("VenteUnique IT")
    clube_fashion=fields.Float("ClubeFashion")

    ###################
    # CDISCOUNT SHOPS #
    ###################

    cdiscount=fields.Float("cdiscount")

    #############################
    # MAPPING PRICE METHOD CRON #
    #############################   

    def product_pricing_analysis_cron(self):
        pp_obj = self.env['product.shop'].search([('create_date', '>=', Datetime.to_string(Datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)))])
        pp_obj.map_recommended_retail_price_with_product_shop()

        shops=self.env['mirakl.shops'].search([])
        for shop in shops:
            shop.product_shop_pricing()

        shops=self.env['cdiscount.shops'].search([])
        for shop in shops:
            shop.product_shop_pricing()
       
        shops=self.env['manomano.shops'].search([])
        for shop in shops:
            shop.product_shop_pricing() 
        
        shops=self.env['check.shops'].search([])
        for shop in shops:
            shop.product_shop_pricing() 
        
        shops=self.env['amazon.shops'].search([])
        for shop in shops:
            shop.product_shop_pricing() 
        
        shops=self.env['wayfair.shops'].search([])
        for shop in shops:
            shop.product_shop_pricing() 
        
        # shops=self.env['standard.pricing'].search([])
        # for shop in shops:
        #     shop.product_shop_pricing() 

    #####################################
    # RECOMMENDED RETAIL PRICE   METHOD #
    #####################################
    
    def map_recommended_retail_price_with_product_shop(self):

        for prod in self:
            prod.ensure_one()
            rec_id = self.env["standard.pricing"].search([('sku', '=', prod.sku)])
            if rec_id:
                prod.recommended_retail_price =  0.20*(rec_id.recommended_retail_price)+rec_id.recommended_retail_price
            else:
                prod.recommended_retail_price = None
    

        
    