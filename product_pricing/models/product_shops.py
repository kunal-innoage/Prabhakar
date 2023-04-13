from odoo import fields , models 
import logging
_logger = logging.getLogger(__name__)


class ProductShops(models.Model):
    _name="product.shop"
    _description="Product Shop analysis"
    _rec_name="sku"




    sku=fields.Char("Products/SKU")
    
    # product_id=fields.Many2one("product.pricing", "Product ID")

    #################
    # WAYFAIR SHOPS #
    #################

    wayfair_uk=fields.Char("Wayfair UK")
    wayfair_de=fields.Char("Wayfair DE")

    ##################
    # MANOMANO SHOPS #
    ##################

    manomano_shop=fields.Char("Manomano Shop")

    #################
    # CHECK24 SHOPS #
    #################

    check=fields.Char("Check24")

    ################
    # AMAZON SHOPS #
    ################

    amazon_de=fields.Char("Amazon DE")
    amazon_uk=fields.Char("Amazon UK")
    amazon_fr=fields.Char("Amazon FR")

    ################
    # MIRAKL SHOPS #
    ################

    maison=fields.Char("Maison")
    conforama=fields.Char("Conforama")
    bricoprive=fields.Char("Bricoprive")
    home24_de=fields.Char("Home24 DE")
    pccomponentes=fields.Char("Pccomponentes")
    rueduco=fields.Char("Rueduco")
    carrefoures=fields.Char("Carrefoures")
    adeo=fields.Char("Adeo")
    leclerc=fields.Char("Leclerc")
    carrefourfr=fields.Char("Carrefourfr")
    but=fields.Char("But")
    empik_place=fields.Char("Empik Place")
    inno=fields.Char("INNO")
    vente_unique=fields.Char("VenteUnique")
    worten=fields.Char("Worten")
    home24_at=fields.Char("Home24 AT")
    home24_fr=fields.Char("Home24 FR")
    darty=fields.Char("Darty")
    vente_unique_es=fields.Char("VenteUnique ES")
    vente_unique_it=fields.Char("VenteUnique IT")
    clube_fashion=fields.Char("ClubeFashion")

    ###################
    # CDISCOUNT SHOPS #
    ###################

    cdiscount=fields.Char("cdiscount")

    ########################
    # MAPPING PRICE METHOD #
    ########################   

    def product_pricing_analysis_cron(self):
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

    

        
    