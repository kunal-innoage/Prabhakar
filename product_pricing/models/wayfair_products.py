from odoo import fields, models,api
import logging
_logger = logging.getLogger(__name__)
import logging
_logger = logging.getLogger(__name__)


class WayfairProduct(models.Model):
    _name = "wayfair.product"
    _description = "Wayfair Product"
    _rec_name="supplier_part_number"

    supplier_part_number=fields.Char("SKU")
    brand_catalog=fields.Char("Brand Catalog")
    retail_price=fields.Char("Retail Price")
    status=fields.Char("Status")
    link=fields.Char("Link")
    wayfair_uk=fields.Char("Waifair UK" , invisible='0')
    wayfair_de=fields.Char("Wayfair DE" , invisible='0')
    wayfair_shop_id = fields.Many2one("wayfair.shops","Wayfair Shop")
    product_id = fields.Many2one("product.product","Wayfair Shop")
    is_odoo_product = fields.Boolean("Is Odoo Product")

    @api.model_create_multi
    def create(self, vals):
        res = super(WayfairProduct, self).create(vals)

        if res._context.get('import_file'):
            for product in res:
                product_id= self.env['product.product'].search([('default_code','=',product.supplier_part_number)])
                if product_id:
                    product.product_id = product_id
                    product.is_odoo_product = True 
                    # _logger.info(">>>>>>>>>PRE............  %r ,...........",len(product_id))
 
                if not product_id :
                    product.unlink()
                    # _logger.info(">>>>>>>>>POST............  %r ,...........",len(product_id))

                wayfair_shop_id =self.env['wayfair.shops'].search([('id','=',res._context.get('active_id'))])
                product.wayfair_shop_id = wayfair_shop_id.id
                # if product.brand_catalog == "Wayfair UK":
                #     product.wayfair_de=False
                # else:
                #     product.wayfair_uk=False
        return res
            
            