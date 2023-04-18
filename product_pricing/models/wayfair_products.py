from odoo import fields, models,api
import logging
_logger = logging.getLogger(__name__)


class WayfairProduct(models.Model):
    _name = "wayfair.product"
    _description = "Wayfair Product"
    _rec_name="supplier_part_number"

    supplier_part_number=fields.Char("SKU")
    brand_catalog=fields.Char("Brand Catalog")
    retail_price=fields.Float("Retail Price")
    status=fields.Char("Status")
    link=fields.Char("Link")
    wayfair_uk=fields.Char("Waifair UK" , invisible='0')
    wayfair_de=fields.Char("Wayfair DE" , invisible='0')
    wayfair_shop_id = fields.Many2one("wayfair.shops","Wayfair Shop")
    product_id = fields.Many2one("product.product","Wayfair Shop")
    recommended_retail_price = fields.Float("Recommended Retail Price" , invisible = True)
   

    # currency_id = fields.Many2one("wayfair.shops","Currency")
    is_odoo_product = fields.Boolean("Is Odoo Product")
    # currency_difference = fields.Float("Currency")


    @api.model_create_multi
    def create(self, vals):
        res = super(WayfairProduct, self).create(vals)

        if res._context.get('import_file'):
            # difference = self.env['wayfair.shops'].browse(['])
            for product in res:
            #     if product.brand_catalog == "Wayfair UK":
                    
            #         product.retail_price = round((float(product.retail_price)*difference) , 2)
                wayfair_shop_id= self.env['wayfair.shops'].search([('id','=',res._context.get('active_id'))])
                product.wayfair_shop_id = wayfair_shop_id.id
                if product.wayfair_shop_id.difference:
                    product.retail_price = (product.wayfair_shop_id.difference)*(product.retail_price)


                product_id= self.env['product.product'].search([('default_code','=',product.supplier_part_number)])
                if product_id:
                    product.product_id = product_id
                    product.is_odoo_product = True 
                    # _logger.info(">>>>>>>>>PRE............  %r ,...........",len(product_id))
 
                if not product_id :
                    product.unlink()

                    
                wayfair_shop_id =self.env['wayfair.shops'].search([('id','=',res._context.get('active_id'))])
                product.wayfair_shop_id = wayfair_shop_id.id

                
                    # _logger.info(">>>>>>>>>PRE>>>>>>>............  %r ,...........",(product.retail_price))

                # else:
                #     pass
        return res
    


