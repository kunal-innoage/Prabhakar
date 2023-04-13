from odoo import fields, models,api


class Check24Product(models.Model):
    _name = "check.product"
    _description = "Check24 Product"
    _rec_name="sku"

    sku=fields.Char("SKU")
    sku_name=fields.Char("SKU Name")
    link=fields.Char("Link")
    price=fields.Float("Price")
    status=fields.Char("Status")
    check_shop_id=fields.Many2one("check.shops","Shop ID")
    
    # wayfair_shop_id = fields.Many2one("wayfair.shops","Wayfair Shop")

    @api.model_create_multi
    def create(self, vals):
        res = super(Check24Product, self).create(vals)
        if res._context.get('import_file'):
            # _logger.info("............  %r ,...........",res._context)
            for product in res:
                product_id= self.env['product.product'].search([('default_code','=',product.sku)])
                if product_id:
                    product.product_id = product_id
                    product.is_odoo_product = True
                check_shop_id =self.env['check.shops'].search([('id', '=', res._context.get('active_id'))])
                product.check_shop_id = check_shop_id.id
        return res