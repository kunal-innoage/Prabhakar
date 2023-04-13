from odoo import fields, models,api
import logging
_logger = logging.getLogger(__name__)

class MiraklProduct(models.Model):
    _name = "mirakl.product"
    _description = "Mirakl Products"
    _rec_name="product_sku"

    product_sku=fields.Char("Product SKU")
    price=fields.Float("Price")
    link=fields.Char("Link")
    status=fields.Char("Status")
    on_shop_quantity=fields.Integer("ON Shop Quantity")
    
    mirakl_shop_id = fields.Many2one("mirakl.shops","Mirakl Shop ID")


    @api.model_create_multi
    def create(self, vals):
        res = super(MiraklProduct, self).create(vals)
        if res._context.get('import_file'):
            for product in res:
                mirakl_shop_id =self.env['mirakl.shops'].search([('id', '=', res._context.get('active_id'))])
                product.mirakl_shop_id = mirakl_shop_id.id
        # if self.env("shop.integrator").search([('shop_code', '=' , 'shop_code')]):
        return res            