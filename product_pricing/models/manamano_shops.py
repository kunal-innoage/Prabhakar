from odoo import fields, models, _
import logging
from odoo.fields import Datetime
_logger = logging.getLogger(__name__)


class ManoManoShop(models.Model):
    _name = "manomano.shops"
    _description = "ManoMano Shops"
    _rec_name="shop_name"

    shop_name=fields.Char("Shop Name")
    url=fields.Char("URL")
    total_no_of_products=fields.Integer("Total Number of Products" , compute ="_compute_mano_product_count")

    

    # def manomano_productlisting_action(self):
    #    action = self.env.ref('product_pricing.manomano_productlisting_action').read()[0]
    #    return action  

    # def product_pricing_action(self):
    #     self.ensure_one()
    #     return{
    #         'type':'ir.actions.act_window','type': 'ir.actions.act_window',
    #         'name': _("%s's Products", self.shop_name),
    #         'view_mode': 'list,form',
    #         'res_model': 'product.pricing',
    #         'domain': [('shop', '=', self.shop_name)],

    #     }

    ##########################
    # PRODUCT lISTING METHOD #
    ##########################    

    def mano_product_action(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _("%s's Products", self.shop_name),
            'view_mode': 'list,form',
            'res_model': 'manomano.productlisting',
        }
    
    #############
    # TOTAL SKU #
    #############

    def _compute_mano_product_count(self):
        for rec in self:
            total_no_of_products = self.env['manomano.productlisting'].search([('manomano_shop_id', '=', rec.id)])
            rec.total_no_of_products=len(total_no_of_products)

    ##########################
    # PRODUCT PRICING METHOD #
    ##########################

    def product_shopp_action(self):
        self.ensure_one()
        self.product_shop_pricing()
        return{
            'type':'ir.actions.act_window','type': 'ir.actions.act_window',
            'name': _("%s's Products", self.shop_name),
            'view_mode': 'list,form',
            'res_model': 'product.shop',
        }

    

    def product_shop_pricing(self):
        for shop in self:
            shop.ensure_one()

            recs=self.env['manomano.productlisting'].search([("manomano_shop_id","=", shop.id) ])
            for rec in recs:
                productShop_object=self.env['product.shop'].search([('sku','=',rec.product_sku),('create_date', '>=', Datetime.to_string(Datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)))])
                found = False
                if productShop_object:
                    for product in productShop_object:
                        if shop.shop_name == "Manomano":
                            productShop_object.manomano_shop = rec.price
                        found = True
                
                if not found :
                    product_id =  productShop_object.create({
                        'sku': rec.product_sku
                        })
                    if shop.shop_name == "Manomano":
                            product_id.manomano_shop = rec.price

                    

    
    ########################
    # STOCK PRODUCT METHOD #
    ########################

    def mapping_manomano_products_stock(self):
        for shop in self:
            shop.ensure_one()
            offers = self.env['manomano.productlisting'].search([ ('manomano_shop_id','=',shop.id)])
            
            for offer in offers :
                product_id = self.env['product.pricing'].search([('product_name','=',offer.product_sku),('create_date', '>=', Datetime.to_string(Datetime.now().replace(hour=0, minute=0, second=0, microsecond=0))),('manomano_id','=',shop.id)], limit =1)
                if product_id :
                    for product in product_id:
                        product_id.price = offer.price
                else:
                    product_id = self.env['product.pricing'].create({
                        'product_name' : offer.product_sku,
                        'price' : offer.price,
                        'shop' : shop.shop_name,
                        # 'Manomano' : offer.shop,
                    })



    def returning_method_for_stock(self):
        self.ensure_one()
        return{
            'type':'ir.actions.act_window','type': 'ir.actions.act_window',
            'name': _("%s's Products", self.shop_name),
            'view_mode': 'list,form',
            'res_model': 'product.pricing',
            'domain': [('shop', '=', self.shop_name)],
        }
   
        
    
