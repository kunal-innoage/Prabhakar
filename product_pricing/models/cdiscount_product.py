from odoo import fields, models,api
import logging
_logger = logging.getLogger(__name__)

class CDiscountProduct(models.Model):
    _name = "cdiscount.product"
    _description = "CDiscount Products"
    _rec_name="product_sku"

    product_sku=fields.Char("Product SKU")
    price=fields.Float("Price")
    # cdiscount_shop_id = fields.Many2one("manomano.productlisting","CDiscount Shop ID")
    link=fields.Char("Product URL")
    status=fields.Char("Status")
    shop_quantity=fields.Char("Shop Quantity")
    sold_quantity=fields.Char("Sold Quantity")

    cdiscount_shop_id = fields.Many2one("cdiscount.shops","Cdiscount Shop ID")


    @api.model_create_multi
    def create(self, vals):
        res = super(CDiscountProduct, self).create(vals)
        if res._context.get('import_file'):
            for product in res:
                cdiscount_shop_id =self.env['cdiscount.shops'].search([('id', '=', res._context.get('active_id'))])
                product.cdiscount_shop_id = cdiscount_shop_id.id
        # if self.env("shop.integrator").search([('shop_code', '=' , 'shop_code')]):
        return res   


         

