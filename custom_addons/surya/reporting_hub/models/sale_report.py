from odoo import models,api,fields



class SaleReport(models.Model):
    _inherit = 'sale.report'

    market_place_shop = fields.Char(string='Shop')
    warehouse_id = fields.Many2one("stock.warehouse","Warehouse")
    mirakl_shop_id = fields.Many2one("shop.integrator","Mirakl Shop")
    wayfair_shop_id = fields.Many2one("wayfair.seller","Wayfair Shop")


    def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
        fields['market_place_shop'] = ",s.market_place_shop"
        fields['warehouse_id'] = ",s.warehouse_id"
        fields['mirakl_shop_id'] = ",s.mirakl_shop_id"
        fields['wayfair_shop_id'] = ",s.wayfair_shop_id"
        return super(SaleReport, self)._query(with_clause, fields, groupby, from_clause)

    



class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    
    market_place_shop = fields.Char(string='Shop')

