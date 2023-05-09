from odoo import fields, models, _ , api 
from datetime import datetime
import logging
from odoo.fields import Datetime
_logger = logging.getLogger(__name__)


class WayfairShop(models.Model):
    _name = "wayfair.shops"
    _description = "Wayfair"
    _rec_name="shop_name"

    shop_name=fields.Char("Shop Name")
    url=fields.Char("URL")
    difference = fields.Float("Currency Change from £ to €  ", invisible = True)
    total_no_of_products=fields.Integer("Total Number of Products" , compute='_compute_wayfair_product_count')
    
        
    ########################
    #PRODUCT PRICING METHOD
    ########################


    def product_shop_pricing(self):
        # pass
        for shop in self :
            shop.ensure_one()

            recs=self.env['wayfair.product'].search([("wayfair_shop_id","=", shop.id),('is_odoo_product','=', True) ])
            for rec in recs:
                productShop_object=self.env['product.shop'].search([('sku','=',rec.supplier_part_number),('create_date', '>=', Datetime.to_string(Datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)))])
                found = False
                if productShop_object:
                    for product in productShop_object :
                        if shop.shop_name == "Wayfair UK":
                            productShop_object.wayfair_uk = round((rec.retail_price),2)

                        if shop.shop_name == "Wayfair DE":
                            productShop_object.wayfair_de = rec.retail_price
                        found = True
                        break
        
                if not found :
                    product_id=  productShop_object.create({
                        'sku': rec.supplier_part_number
                        })
                    if product_id:
                        if shop.shop_name == "Wayfair UK":
                            product_id.wayfair_uk = round((rec.retail_price),2)

                        if shop.shop_name == "Wayfair DE":
                            product_id.wayfair_de = rec.retail_price

                
    def product_shopp_action(self):
        self.ensure_one()
        self.product_shop_pricing()
        return{
            'type':'ir.actions.act_window','type': 'ir.actions.act_window',
            'name': _("%s's Products", self.shop_name),
            'view_mode': 'list,form',
            'res_model': 'product.shop',
        }
        # return rec
        
    ##########################
    # PRODUCT lISTING METHOD #
    ##########################
    
    
    def wayfair_product_listing_action(self):
        for shop in self:
            shop.ensure_one()
            # recs=self.env['wayfair.product'].search([("wayfair_shop_id","=", shop.id),('is_odoo_product','=', True) ])
            # for rec in recs:
            #     standard_id= self.env['standard.pricing'].search([('sku','=',rec.supplier_part_number),('recommended_retail_price','>=',rec.retail_price)])
            #     if not standard_id:
            #         shop.color = 'red'
            #     else:
            #         shop.color = 'green'
                     
        return {
            'type': 'ir.actions.act_window',
            'name': _("%s's Products", self.shop_name),
            'view_mode': 'list,form',
            'res_model': 'wayfair.product',
            'domain': [('wayfair_shop_id', '=', self.id),('is_odoo_product','=', True)],
            'context':{'search_default_group_by_product_status': 1,}
        } 

    #############
    # TOTAL SKU #
    #############    

    def _compute_wayfair_product_count(self):
        for rec in self:

            total_no_of_products = self.env['wayfair.product'].search([('wayfair_shop_id', '=', rec.id),('is_odoo_product','=', True)])
            # _logger.info("........%r.......",len(total_no_of_products))
            rec.total_no_of_products=len(total_no_of_products)
           


    ########################
    # STOCK PRODUCT METHOD #
    ########################

    def mapping_wayfair_product_stock(self):
        # pass
        for shop in self:
            shop.ensure_one()
            offers = self.env['wayfair.product'].search([("wayfair_shop_id","=", shop.id),('is_odoo_product','=', True)])

            for offer in offers :
                # product_id = self.env['product.pricing'].search([('wayfair_id','=',shop.id)], limit = 1)
                # product_id = self.env['product.pricing'].search([('product_name','=',offer.supplier_part_number),('create_date', '>=', Datetime.to_string(Datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)))], limit = 1)
                product_id=self.env['product.pricing'].search([('product_name','=',offer.supplier_part_number),('create_date', '>=', Datetime.to_string(Datetime.now().replace(hour=0, minute=0, second=0, microsecond=0))),('shop', '=', shop.shop_name)])
                print('supplier_part_number')
                print('wayfair_id')
                print(shop.id)

                _logger.info("~~~~~~~~~~~%r~~~~~~~~~~",product_id)
                # _logger.info("~~~~~~~~~~~%r~~~~~~~~~~",wayfair_id)
                _logger.info("~~~~~~~~~~~%r~~~~~~~~~~",shop.id)
                if product_id :
                    for product in product_id :
                            product.price = round(offer.retail_price,2)
                            
                else :
                    product_id = self.env['product.pricing'].create({
                                'product_name' : offer.supplier_part_number,
                                'price' : round(offer.retail_price , 2),
                                'shop': shop.shop_name
                            })

    def product_pricing_action(self):
        self.ensure_one()
        return{
            'type':'ir.actions.act_window',
            'name': _("%s's Products", self.shop_name),
            'view_mode': 'list,form',
            'res_model': 'product.pricing',
            'domain': [('shop', '=', self.shop_name)],
            'context' : {'search_default_group_by_date': 1,'search_default_group_by_product': 1,}
        }

    #####################################
    # RECOMMENDED RETAIL PRICE   METHOD #
    #####################################

    def map_recommended_retail_price(self):
        for shop in self:
            shop.ensure_one()
            recs = self.env["standard.pricing"].search([])

            for rec in recs:
                product_id = self.env['wayfair.product'].search([('supplier_part_number','=',rec.sku)])
                _logger.info("............  %r ,...........",(product_id))
                if product_id:
                    for product in product_id:
                        
                        product.recommended_retail_price = rec.recommended_retail_price
 