from odoo import api, fields, models


class WayfairApiConfig(models.Model):
    _name = 'wayfair.api.config'
    _description = 'Wayfair Api Config'

    name = fields.Char(string='Name', required=True)
    desc = fields.Char(string='Description')
    is_prod = fields.Boolean("Production")
    sb_client_id = fields.Char("SandBox Client ID")
    sb_client_secret = fields.Char("SandBox Client Seceret")
    sb_audience = fields.Char("Sandbox Audience")
    prod_client_id = fields.Char("Production Client ID")
    prod_client_secret = fields.Char("Production Client Seceret")
    prod_audience = fields.Char("Production Audience")
    dropship_orders_ids = fields.One2many('wayfair.b2c.orders', 'wayfair_api_id', 'Dropship Orders')
    castlegate_orders_ids = fields.One2many('wayfair.b2b.orders', 'wayfair_api_id', 'B2B Orders')



class WayfairDropShipOrders(models.Model):
    _name = 'wayfair.b2c.orders'
    _description = 'Wayfair Dropship Orders'

    shop_id = fields.Many2one('wayfair.seller',"Shop")
    warehouse_id = fields.Many2one("stock.warehouse","Warehouse")
    wayfair_api_id = fields.Many2one(comodel_name='wayfair.api.config', string='Api Config ID')


class WayfairB2bOrders(models.Model):
    _name = 'wayfair.b2b.orders'
    _description = 'Wayfair CastleGate Orders'

    shop_id = fields.Many2one('wayfair.b2b.shop',"Shop")
    warehouse_id = fields.Many2one("stock.warehouse","Warehouse")
    wayfair_api_id = fields.Many2one(comodel_name='wayfair.api.config', string='Api Config ID')
    

    
