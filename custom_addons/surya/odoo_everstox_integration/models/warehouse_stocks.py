from odoo import fields, models,_

import logging
_logger = logging.getLogger(__name__)


class EverstoxWarehouseStock(models.Model):
    _name = 'everstox.warehouse.stock'
    _description = 'Everstox Warehouse Stock'
    _rec_name = "stock_id"

    batch_product = fields.Boolean("Is Batch Product")
    bundle_product = fields.Boolean("Is Bundle Product")
    ignore_during_import = fields.Boolean("Is Ignore During Import")
    ignore_during_shipment = fields.Boolean("Is Ignore During Shipment")
    last_stock_update = fields.Char("Last Stock Update")
    stock_id = fields.Char("Stock ID")
    name = fields.Char("Name")
    sku = fields.Char("SKU")
    status = fields.Char("Status")
    total_stock = fields.Char("Total Stock")

    stock_item_ids = fields.One2many("everstox.warehouse.stock.item", "stock_id", "Stock Items")
    everstox_shop_id = fields.Many2one("everstox.shop", string= "Shop")


class EverstoxWarehouseStockItem(models.Model):
    _name = "everstox.warehouse.stock.item"
    _description = "Everstox Warehouse Stock Item"

    stock_item_id = fields.Char("Stock Item ID")
    batch = fields.Boolean("Is Batch")
    quantity = fields.Integer("Quantity")
    stock_runway = fields.Integer("Stock Runway")
    stock_warehouse_id = fields.Char("Warehouse ID")
    stock_warehouse_name = fields.Char("Warehouse Name")
    updated_date = fields.Char("Updated Date")
    stock_quantities_ids = fields.One2many("everstox.stock.quantities", "stock_item_id", "Stock Quantities")

    stock_id = fields.Many2one("everstox.warehouse.stock", "Stock ID")


class EverstoxStockQuantites(models.Model):
    _name = "everstox.stock.quantities"
    _description = "EverstoxStockQuantities"

    stock_type = fields.Char("Stock Type")
    stock_quantity = fields.Integer("Stock Quantity")

    stock_item_id = fields.Many2one("everstox.warehouse.stock.item","Stock Item")


