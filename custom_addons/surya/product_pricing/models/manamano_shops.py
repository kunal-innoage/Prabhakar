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
    manomano_shop_id = fields.Many2one("manomano.seller","Shop" , required = True)

    

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

    def manomano_product_listing(self):
        for rec in self:
            if rec.manomano_shop_id:
                offers = self.env['manomano.offers'].search([('shop_id','=',rec.manomano_shop_id.id)])
                for offer in offers:
                    product_id = self.env['manomano.productlisting'].search([('product_sku','=',offer.product_id.default_code), ('manomano_shop_id', '=', rec.id)], limit=1)
                    if not product_id:
                        product_id=rec.env['manomano.productlisting'].create({
                            'product_sku':offer.product_id.default_code,
                            'price':offer.price,
                            'on_shop_quantity':offer.quantity,
                            'manomano_shop_id':rec.id,
                        })
                    else:
                        product_id.on_shop_quantity = offer.quantity
                        product_id.price = offer.price
                count = self.env['manomano.productlisting'].search([('manomano_shop_id','=',rec.id)])
            else: 
                pass
                   

    def mano_product_action(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _("%s's Products", self.shop_name),
            'view_mode': 'list,form',
            'res_model': 'manomano.productlisting',
            'domain' : [('manomano_shop_id','=',self.id)],
        }
    
    #############
    # TOTAL SKU #
    #############

    def _compute_mano_product_count(self):
        for rec in self:
            if rec.manomano_shop_id:
                total_no_of_products = self.env['manomano.productlisting'].search([('manomano_shop_id', '=', rec.id)])
                rec.total_no_of_products=len(total_no_of_products)
            else:
                pass

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
                        if shop.shop_name == "Manomano FR":
                            productShop_object.manomano_fr = rec.price
                        
                        if shop.shop_name == "Manomano ES":
                            productShop_object.manomano_es = rec.price
                        
                        if shop.shop_name == "Manomano IT":
                            productShop_object.manomano_it = rec.price
                        
                        if shop.shop_name == "Manomano DE":
                            productShop_object.manomano_de = rec.price
                        
                        if shop.shop_name == "Manomano GB":
                            productShop_object.manomano_gb = rec.price
                        found = True
                
                if not found :
                    product_id =  productShop_object.create({
                        'sku': rec.product_sku
                        })
                    if product_id:
                        if shop.shop_name == "Manomano FR":
                            product_id.manomano_fr = rec.price
                            
                        if shop.shop_name == "Manomano ES":
                            product_id.manomano_es = rec.price
                        
                        if shop.shop_name == "Manomano IT":
                            product_id.manomano_it = rec.price
                        
                        if shop.shop_name == "Manomano DE":
                            product_id.manomano_de = rec.price
                        
                        if shop.shop_name == "Manomano GB":
                            product_id.manomano_gb = rec.price
                    

    
    ########################
    # STOCK PRODUCT METHOD #
    ########################

    def mapping_manomano_products_stock(self):
        # pass
        for shop in self:
            shop.ensure_one()
            shop.manomano_product_listing()
            offers = self.env['manomano.productlisting'].search([ ('manomano_shop_id','=',shop.id)])
            
            for offer in offers :
                product_id = self.env['product.pricing'].search([('product_name','=',offer.product_sku),('create_date', '>=', Datetime.to_string(Datetime.now().replace(hour=0, minute=0, second=0, microsecond=0))),('shop','=',shop.shop_name)], limit =1)
                if product_id :
                    for product in product_id:
                        product_id.price = offer.price
                        product.on_shop_quantity = offer.on_shop_quantity
                else:
                    product_id = self.env['product.pricing'].create({
                        'product_name' : offer.product_sku,
                        'price' : offer.price,
                        'on_shop_quantity': offer.on_shop_quantity,
                        'shop' : shop.shop_name,
                        'manomano_id': shop.id,
                    })



    def returning_method_for_stock(self):
        self.ensure_one()
        return{
            'type':'ir.actions.act_window','type': 'ir.actions.act_window',
            'name': _("%s's Products", self.shop_name),
            'view_mode': 'list,form',
            'res_model': 'product.pricing',
            'domain': [('manomano_id', '=', self.id)],
        }
   
        
    
