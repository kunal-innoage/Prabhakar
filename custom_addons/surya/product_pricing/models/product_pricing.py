from odoo import fields, models , api
import logging
from datetime import datetime
_logger = logging.getLogger(__name__)

class ProductPricing(models.Model):
    _name = "product.pricing"
    _description = "Product Pricing Analysis"
    _rec_name="product_name"
    # _inherit="amazon.sku"

       
    product_name=fields.Char("Product")
    shop=fields.Char("Shop")
    status=fields.Char("Status")
    comments=fields.Char("Comments")
    on_shop_quantity=fields.Char("On Shop Quantity")
    etl=fields.Char("ETL")
    cdiscount=fields.Char("Cdiscount")
    ifulfillment=fields.Char("Ifulfillment")
    cguk=fields.Char("CGUK")
    wayde=fields.Char("WAYDE")
    price=fields.Char("Price")
    # record = fields.Reference(string='Record', selection='_get_model_selection')


    amazon_id=fields.Many2one("amazon.shops" , "Amazon Shop")
    wayfair_id=fields.Many2one("wayfair.shops" , "Wayfair Shop")
    cdiscount_id=fields.Many2one("cdiscount.shops" , "Cdiscount Shop")
    check_id=fields.Many2one("check.shops" , "Check24 Shop")
    mirakl_id=fields.Many2one("mirakl.shops" , "Mirakl Shop")
    manomano_id=fields.Many2one("manomano.shops" , "Manomano Shop")

    # def _get_model_selection(self):
    #     models = self.env['ir.model'].search([])
    #     return [(model.model, model.name) for model in models]
    
    @api.model_create_multi
    def create(self, vals):
        res = super(ProductPricing, self).create(vals)
        if res._context.get('import_file'):
            shop_id =self.env[res._context.get("active_model")].search([('id','=', res._context.get("active_id"))])
            for product in res:
                product.shop = shop_id.shop_name
                if res._context.get("active_model") == "amazon.shops":
                    product.amazon_id = shop_id
                # elif res._context.get("active_model") == "manomano.shops":
                #     product.manomano_id = shop_id
                elif res._context.get("active_model") == "wayfair.shops":
                    product.wayfair_id = shop_id                
                # elif res._context.get("active_model") == "cdiscount.shops":
                #     product.cdiscount_id = shop_id                
                elif res._context.get("active_model") == "check.shops":
                    product.check_id = shop_id

                # Stock Assignment 
                # today_date
                # product in warehouse.inventory using date filter
                # if warehouse is ETL then assign product_pricing.ETL fields




                # elif res._context.get("active_model") == "wayfair_shops":
                #     product.wayfair_id = shop_id                
        return res
    

    # @api.model
    def getting_on_hand_warehouse_quantity(self):
        warehouses = self.env['marketplace.warehouse'].search([])
        # _logger.info("............  %r ,...........",warehouses)
        for product in self:
            for warehouse in warehouses :
                warehouse_stock=self.env['warehouse.inventory'].search([('warehouse_id','=',warehouse.id),('product_id','=',product.product_name)],order='create_date desc',limit=1)
                # _logger.info("............  %r ,.....%r......",warehouse_stock ,datetime.now().date())
                if warehouse_stock:

                    for inventory in warehouse_stock:


                        if inventory.warehouse_id.warehouse_code =="ETL" :
                            product.etl = inventory.available_stock_count

                        if inventory.warehouse_id.warehouse_code =="CDISC" :
                            product.cdiscount = inventory.available_stock_count

                        if inventory.warehouse_id.warehouse_code =="IFUL" :
                            product.ifulfillment = inventory.available_stock_count

                        if inventory.warehouse_id.warehouse_code =="CGUK" :
                            product.cguk = inventory.available_stock_count

                        if inventory.warehouse_id.warehouse_code =="WAYDE" :
                            product.wayde = inventory.available_stock_count


    ########################
    # MAPPING STOCK METHOD #
    ########################

    def product_stock_analysis_cron(self):
        shops=self.env['mirakl.shops'].search([])
        for shop in shops:
            shop.mirakl_product_mapping_action()

        shops=self.env['cdiscount.shops'].search([])
        for shop in shops:
            shop.cdiscount_product_mapping_action()
        
        shops=self.env['manomano.shops'].search([])
        for shop in shops:
            shop.mapping_manomano_products_stock()
        
        shops=self.env['wayfair.shops'].search([])
        for shop in shops:
            shop.mapping_wayfair_product_stock()
        
        shops=self.env['check.shops'].search([])
        for shop in shops:
            shop.mapping_check_products_stock()
        
        shops=self.env['amazon.shops'].search([])
        for shop in shops:
            shop.mapping_amazon_products_stock()
        
            
        
        