from odoo import fields, models
import json
import logging
_logger = logging.getLogger(__name__) 


class Offers(models.Model):
    _name = "manomano.offers"
    _description = "Shop Offers"
    _rec_name = "offer_id"


    # Base Fields
    offer_id = fields.Char(string="Offer Id")
    shop_id = fields.Many2one("manomano.seller", string="Shop")
    product_id = fields.Many2one("product.product", "Product")
    product_sku = fields.Char("Shop Product")
    quantity = fields.Integer("Shop Quantity")
    price = fields.Char("Price")
    carrier = fields.Char("Carrier")


    # update manomano offer
    def update_manomano_offer(self):
        items = []
        for offer in self:
            to_add = {
                "sku": offer.product_sku,
                "price": {
                    "price_vat_included": offer.price
                },
                "stock": {
                    "quantity": offer.quantity
                }
            }
            items.append(to_add)
        data = {"content": [{"seller_contract_id": self[0].shop_id.seller_contract_id, "items": items }]}
        self.update_offer_api(data, self[0].shop_id)
        pass


    def update_offer_api(self, data, shop_id):
        call = "https://partnersapi.manomano.com/api/v2/offer-information/offers"
        data = json.dumps(data)

        _logger.info("!!!!!~~~~~Update Offer~~~~~~%r~~~~%r~~~~~~",call, data)
        
        try:
            # response = requests.patch(call,headers={'x-api-key': shop_id.api_key,'Content-Type': 'application/json'}, data = data)
            pass
        except Exception as err:
            _logger.info("~~~Update Offer API failed~~~~~~~~%r~~~~~~~~~", err)
            response = False



     # unfreeze manomano offer
    def unfreeze_manomano_offer(self):
        items = []
        for offer in self:
            items.append(offer.product_sku)
        to_add = {
            "seller_contract_id": self[0].shop_id.seller_contract_id,
            "skus": items,
            "fields": ["PRICE","STOCK"],
        }
        self.unfreeze_offer_api(to_add, self[0].shop_id)
        pass



    def unfreeze_offer_api(self, data, shop_id):
        call = "https://partnersapi.manomano.com/api/v1/offer-information/offers-unfreeze"
        data = json.dumps(data)

        _logger.info("!!!!!~~~~~Unfreeze Offer~~~~~~%r~~~~%r~~~~~~",call, data)

        try:
            # response = requests.patch(call,headers={'x-api-key': shop_id.api_key,'Content-Type': 'application/json'}, data = data)
            pass
        except Exception as err:
            _logger.info("~~~Unfreeze Offer API failed~~~~~~~~%r~~~~~~~~~", err)
            response = False







    
