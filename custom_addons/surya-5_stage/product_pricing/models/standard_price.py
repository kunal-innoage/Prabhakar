from odoo import fields , models

class StandardPricing(models.Model):
    _name = "standard.pricing"
    _description = "Standard Pricing"

    sku = fields.Char("SKU")
    recommended_retail_price = fields.Float("Recommended Retail Price")

    def map_recommended_price(self):
        for shop in self:
            shop.ensure_one()
            recs = self.env['wayfair.product'].search([('supplier_part_number','=',shop.sku)])
            for rec in recs:
                product_id = self.env['wayfair.product'].create({
                    'recommended_retail_price':rec.recommended_retail_price
                })

