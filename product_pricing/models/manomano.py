from odoo import models, fields, api
# import logging
# _logger = logging.getLogger(__name__)



class Manomano(models.Model):
    _name="manomano.productlisting"
    _description="Manomano Product List"
    _rec_name="product_sku"

    product_sku=fields.Char("SKU")
    price=fields.Float("Price Inclusive VAT")
    link=fields.Char("Product URL")
    status=fields.Char("Status")
    manomano_shop_id = fields.Many2one("manomano.shops","Manomano Shop")
    


    @api.model_create_multi
    def create(self, vals):
        res = super(Manomano, self).create(vals)
        if res._context.get('import_file'):
            # _logger.info("............  %r ,...........",res._context)
            for product in res:
                manomano_shop_id =self.env['manomano.shops'].search([('id', '=', res._context.get('active_id'))])
                product.manomano_shop_id = manomano_shop_id.id
        return res