from odoo import fields, models , _
from odoo.fields import Datetime

class AmazonShop(models.Model):
    _name = "amazon.shops"
    _description = "Amazon shops"
    _rec_name="shop_name"

    shop_name=fields.Char("Shop Name")
    url=fields.Char("URL")
    total_no_of_products=fields.Integer("Total Number of Products", compute ="_compute_amazon_product_count" )

    ########################
    # STOCK PRODUCT METHOD #
    ######################## 

    def mapping_amazon_products_stock(self):
        for shop in self:
            shop.ensure_one()
            offers = self.env['amazon.sku'].search([('amazon_shop_id','=',shop.id)])
        
            for offer in offers :
                product_id = self.env['product.pricing'].search([('product_name','=',offer.vendor_sku),('create_date', '>=', Datetime.to_string(Datetime.now().replace(hour=0, minute=0, second=0, microsecond=0))),('shop','=',shop.shop_name)] , limit =1)
                if product_id:
                    for product in product_id:
                        product.price = offer.list_price_with_tax
                        break
                else:
                    product_id = self.env['product.pricing'].create({
                        'product_name': offer.vendor_sku,
                        'price': offer.list_price_with_tax,
                        'shop' : shop.shop_name
                    })
    

    def product_pricing_action(self):
        self.ensure_one()
        return{
            'type':'ir.actions.act_window',
            'name': _("%s's Products", self.shop_name),
            'view_mode': 'list,form',
            'res_model': 'product.pricing',
            'domain': [('shop', '=', self.shop_name)],
        }

    ##########################
    # PRODUCT lISTING METHOD #
    ##########################   

    def amazon_sku_action(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _("%s's Products", self.shop_name),
            'view_mode': 'list,form',
            'res_model': 'amazon.sku',
            'domain': [('amazon_shop_id', '=', self.id)],
        }
    
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

            recs=self.env['amazon.sku'].search([("amazon_shop_id","=", shop.id)])
            for rec in recs:
                productShop_object=self.env['product.shop'].search([('sku','=',rec.vendor_sku),('create_date', '>=', Datetime.to_string(Datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)))])
                found = False

                if productShop_object:
                    for product in productShop_object:
                        if shop.shop_name == "Amazon DE":
                            productShop_object.amazon_de = rec.list_price_with_tax
                    
                        if shop.shop_name == "Amazon FR":
                            productShop_object.amazon_fr = rec.list_price_with_tax
                        
                        if shop.shop_name == "Amazon UK":
                            productShop_object.amazon_uk = rec.list_price_with_tax
                        found = True
                        break

                if not found :
                    product_id = productShop_object.create({
                        'sku':rec.vendor_sku
                    })
                    if shop.shop_name == "Amazon DE":
                        product_id.amazon_de = rec.list_price_with_tax
                    
                    if shop.shop_name == "Amazon FR":
                        product_id.amazon_fr = rec.list_price_with_tax
                    
                    if shop.shop_name == "Amazon UK":
                        product_id.amazon_uk = rec.list_price_with_tax
    #############
    # TOTAL SKU #
    #############
     
    def _compute_amazon_product_count(self):
        for rec in self:
            total_no_of_products = self.env['amazon.sku'].search([('amazon_shop_id', '=',rec.id)])
            rec.total_no_of_products=len(total_no_of_products)