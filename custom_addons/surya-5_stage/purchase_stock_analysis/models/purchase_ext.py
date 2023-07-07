from odoo import fields , models

class PurchaseExtension(models.Model):
    _name = "purchase.extension"
    _description = "Purchase Extension"

    sku = fields.Char("SKU")
    date_of_first_receipt = fields.Date("Date of first recipt")
    increased_stock = fields.Float("INCREASED Stock")
    
    warehouse = fields.Char("Warehouse")
    

    def map_increased_stock(self):
        for rec in self:
            rec.ensure_one()
            recs = self.env['purchase.analysis'].search([('sku','=',rec.sku)])
            for rec in recs:
                product_id = self.env['purchase.analysis'].create({
                    'date_of_first_receipt':rec.date_of_first_receipt ,
                    'increased_stock':rec.increased_stock
                })