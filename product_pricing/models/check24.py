from odoo import fields, models, _
from odoo.fields import Datetime


class Check(models.Model):
    _name = "check.shops"
    _description = "check24 Shop"
    _rec_name="shop_name"

    shop_name=fields.Char("Shop Name")
    url=fields.Char("URL")
    total_no_of_products=fields.Integer("Total Number of Products", compute ="_compute_check_product_count")


    ########################
    # STOCK PRODUCT METHOD #
    ########################

    def mapping_check_products_stock(self):
        for shop in self:

            shop.ensure_one()
            offers = self.env['check.product'].search([('check_shop_id','=',shop.id)])

            for offer in offers:
                product_id = self.env['product.pricing'].search([('product_name','=',offer.sku),('create_date', '>=', Datetime.to_string(Datetime.now().replace(hour=0, minute=0, second=0, microsecond=0))),('shop','=',shop.shop_name)],limit =1)
                if product_id :
                    for product in product_id:
                        product.price = offer.price
                else:        
                    product_id = self.env['product.pricing'].create({
                        'product_name':offer.sku,
                        'price' : offer.price,
                        'shop' : self.shop_name,
                    })
               

    def product_pricing_action(self):
        self.ensure_one()
        return{
            'type':'ir.actions.act_window','type': 'ir.actions.act_window',
            'name': _("%s's Products", self.shop_name),
            'view_mode': 'list,form',
            'res_model': 'product.pricing',
            'domain': [('shop', '=', self.shop_name)],
        }

    ##########################
    # PRODUCT lISTING METHOD #
    ########################## 


    def check_product_action(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _("%s's Products", self.shop_name),
            'view_mode': 'list,form',
            'res_model': 'check.product',
        } 
        
    #############
    # TOTAL SKU #
    #############


    def _compute_check_product_count(self):
        for rec in self:
            total_no_of_products = self.env['check.product'].search([('check_shop_id', '=', rec.id)])
            rec.total_no_of_products=len(total_no_of_products)

    ###########################
    # PRODUCT PRICING METHODS #
    ###########################

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
        for shop in self :
            shop.ensure_one()
            

            recs=self.env['check.product'].search([("check_shop_id","=", shop.id) ])
            for rec in recs:
                productShop_object=self.env['product.shop'].search([('sku','=',rec.sku),('create_date', '>=', Datetime.to_string(Datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)))])
                found = False
                if productShop_object :
                    for product in productShop_object:
                        if shop.shop_name == "Check24":
                            productShop_object.check = rec.price
                        found = True
                if not found :
                        product_id =  productShop_object.create({
                            'sku': rec.sku
                            })
                        if shop.shop_name == "Check24":
                            product_id.check = rec.price
                else:
                    Found = None       