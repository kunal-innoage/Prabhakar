from odoo import fields, models,_
import requests

import logging
_logger = logging.getLogger(__name__)


class EverstoxWarehouseStockUpdates(models.Model):
    _name = 'everstox.warehouse.stock.updates'
    _description = 'Everstox Warehouse Stock Updates'
    _rec_name = "stock_update_id"

    action_type = fields.Char("Action Type")
    stock_update_id = fields.Char("Stock Update ID")
    new_quantity = fields.Integer("New Quantity")
    quantity_correction = fields.Integer("Quantity Correction")
    update_datetime = fields.Char("Updated Date Time")
    update_reason = fields.Char("Update Reason")
    update_reason_code = fields.Char("Update Reason Code")

    stock_id = fields.Many2one("everstox.warehouse.stock", "Stock")
    everstox_shop_id = fields.Many2one("everstox.shop", string= "Shop")

    def update_stock_updates(self):
        for stock_update in self:
            respone = False
            call = stock_update.everstox_shop_id.shop_url + "api/v1/shops/" + stock_update.everstox_shop_id.shop_id + "/stock-updates/"+ stock_update.stock_update_id

            try:
                _logger.info("........ Getting Stock Updates By Id  call -   %r   .........", call)
                response = requests.get(call,headers={'everstox-shop-api-token': stock_update.everstox_shop_id.shop_api_key,'Content-Type': 'application/json'})
            except Exception as e:
                _logger.info("Error in Update Stock Update API call !!!!!!!!!")

            if response:
                if response.status_code == 200:
                    try:
                        _logger.info("......... Update Stock Update Response -  %r  ..........", response.json())
                        self.process_stock_update(stock_update, response.json())
                    except Exception as e:
                        _logger.info("Error While Processing Stock Updates %r   response - %r   !!!!!!!", e, response.text)

    def process_stock_update(self, stock_update, data):
        stock_update.action_type = data.get("action_type")
        stock_update.new_quantity = data.get("new_quantity")
        stock_update.quantity_correction = data.get("quantity_correction")
        stock_update.update_datetime = data.get("update_datetime")
        stock_update.update_reason = data.get("update_reason")
        stock_update.update_reason_code = data.get("update_reason_code")
        if not stock_update.stock_id:
            stock_update.stock_id = self.env["everstox.warehouse.stock"].search([('stock_id', "=", data.get("stock").get("id"))])
            if stock_update.stock_id:
                stock_update.stock_id.total_stock = stock_update.new_quantity
                for item in stock_update.stock_id.stock_item_ids:
                            item.quantity = stock_update.stock_id.total_stock
        else:
            stock_update.stock_id.total_stock = stock_update.new_quantity
            for item in stock_update.stock_id.stock_item_ids:
                            item.quantity = stock_update.stock_id.total_stock
