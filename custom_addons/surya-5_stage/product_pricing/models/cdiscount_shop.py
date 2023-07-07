from odoo import fields , models , _
import logging
from odoo.fields import Datetime
_logger = logging.getLogger(__name__)


class CDiscount(models.Model):
    _name="cdiscount.shops"
    _description="CDiscount Shops"
    _rec_name="shop_name"

    shop_name=fields.Char("Shop Name")
    total_no_of_products=fields.Integer("Total Number of Products", compute ="_compute_cdiscount_product_count")
    cdiscount_shop_id=fields.Many2one("cdiscount.seller", "Shop")

    ##########################
    # PRODUCT LISTING METHOD #
    ##########################

    def cdiscount_product_action(self):
        # for rec in self:
        self.ensure_one()
        
        # self.cdiscount_shop_id.cdsicount_inventory_offers()
        # _logger.info(">>POST>.....count.......  %r ,...........", self.cdiscount_shop_id.cdsicount_inventory_offers())


        offers = self.env['cdiscount.offers'].search([])
        _logger.info("............  %r ,...........",offers)

        for offer in offers:
            product_ids=self.env['cdiscount.product'].search([('product_sku','=',offer.product_sku)])
            if not product_ids:
                self.env['cdiscount.product'].create({
                    'product_sku': offer.product_sku,
                    'price': offer.price,
                    'status': offer.offer_state,
                    'shop_quantity': offer.quantity,
                    'sold_quantity': offer.sold_qty,
                    'cdiscount_shop_id': self.id,
                })
            else:
                product_ids.shop_quantity = offer.quantity
                product_ids.price = offer.price 

    def cdiscount_product_listing_action(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _("%s's Products", self.shop_name),
            'view_mode': 'list,form',
            'res_model': 'cdiscount.product',
            'domain': [('cdiscount_shop_id', '=', self.id)],
        }
    
    #############
    # TOTAL SKU #
    #############
    
    def _compute_cdiscount_product_count(self):
        for rec in self:
            # if rec.cdiscount_shop_id:
            total_no_of_products = self.env['cdiscount.product'].search([('cdiscount_shop_id', '=',rec.id)])
            rec.total_no_of_products=len(total_no_of_products)
    

    
    
    # def product_shopp_action(self):
    #     self.ensure_one()
    #     # self.product_shop_pricing()
    #     return{
    #         'type':'ir.actions.act_window','type': 'ir.actions.act_window',
    #         'name': _("%s's Products", self.shop_name),
    #         'view_mode': 'list,form',
    #         'res_model': 'product.shop',}

###########################
# PRODUCT PRICING METHODS #
###########################

    def map_product_listing(self):
            self.ensure_one()
            self.product_shop_pricing()
            return{
                'type':'ir.actions.act_window',
                'name': _("%s's Products", self.shop_name),
                'view_mode': 'list,form',
                'res_model': 'product.shop',
            }
    
    def product_shop_pricing(self):
            for shop in self :
                shop.ensure_one()
                shop.cdiscount_product_action()

            
            recs=self.env['cdiscount.product'].search([("cdiscount_shop_id","=", shop.id)])
            for rec in recs:
                productShop_object=self.env['product.shop'].search([('sku','=',rec.product_sku),('create_date', '>=', Datetime.to_string(Datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)))])
                found = False 
                if productShop_object:
                    for product in productShop_object:
                        if shop.shop_name == "CDiscount":
                            productShop_object.cdiscount = rec.price
                        found = True
                        break

                if not found :
                    product_id=  productShop_object.create({'sku': rec.product_sku})
                    if product_id:
                        if shop.shop_name == "CDiscount":
                            product_id.cdiscount = rec.price



    
    ########################
    # STOCK PRODUCT METHOD #
    ########################
    

    def cdiscount_product_mapping_action(self):
        for shop in self:
            shop.ensure_one()                       
            offers = self.env['cdiscount.product'].search([('cdiscount_shop_id','=',shop.id)])

            for offer in offers:
                
                product_id=self.env['product.pricing'].search([('product_name','=',offer.product_sku),('create_date', '>=', Datetime.to_string(Datetime.now().replace(hour=0, minute=0, second=0, microsecond=0))), ('cdiscount_id', '=', shop.id)], limit=1)
                if product_id:
                    for product in product_id:
                        product.price = offer.price,
                        product.on_shop_quantity = offer.shop_quantity
                else:
                    product_id = self.env['product.pricing'].create({
                        'product_name': offer.product_sku,
                        'price': offer.price,
                        'on_shop_quantity': offer.shop_quantity,
                        'shop' : shop.shop_name,
                        'cdiscount_id': shop.id,
                    })
                

    def product_pricing_action(self):
        self.ensure_one()
        return{
            'type':'ir.actions.act_window',
            'name': _("%s's Products", self.shop_name),
            'view_mode': 'list,form',
            'res_model': 'product.pricing',
            'domain': [('cdiscount_id', '=', self.id)],

        }