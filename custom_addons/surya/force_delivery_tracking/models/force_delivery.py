import requests, json
from odoo import models , fields
import logging
_logger = logging.getLogger(__name__)

class StockPicking(models.Model):
    _inherit = 'stock.picking'
    
    def map_force_delivery(self):
        # for rec in self:
        shop_orders = {}
        for delivery in self:
            if delivery.sale_id and delivery.mirakl_shop_id :
                if delivery.mirakl_shop_id in shop_orders.keys():
                    shop_orders[delivery.mirakl_shop_id] += [delivery.sale_id]
                else:
                    shop_orders[delivery.mirakl_shop_id] = [delivery.sale_id]
                    _logger.info("~~~~~~~~~SHOP ORDERS~~%r",shop_orders)
                    
        shipment_ids = []
        for shop in shop_orders.keys():
            for order in shop_orders[shop]: 
                response = shop.get_shipment_tracking_info(order.mirakl_order_id)
                _logger.info("~~~~~~~RESPONSE~~~~~%r",response)
                if response:
                    for shipment in response:
                        for picking in order.picking_ids:
                            for line in picking.moveline:
                                if line.product_id.default_code == shipment.get("shipment_lines")[0].get("offer_sku"):
                                    _logger.info("~~~~~carrier_name~~~~%r~",'carrier_name')
                                    _logger.info("~~~~~line.mirakl_carrier_name~~~~~",line.mirakl_carrier_name)
                                    picking.write({
                                        "carrier_name": line.mirakl_carrier_name,
                                        "carrier_code": line.mirakl_carrier_code,
                                        "tracking_number": line.shipping_tracking,
                                        "tracking_url": line.shipping_tracking_url,
                                        
                                    })
                        if shipment.get("status") == "SHIPPING":
                            shipment_ids += [shipment.get("id")]
                else:
                    _logger.info("~~~~~~~Error while getting forcing shipment as shipped.````````")
            _logger.info("~~~~~~~~~~~%r~~~~~~~~~~", shipment_ids)
            shipment_data = self.get_shipment_validation_data(shipment_ids)
            res = shop.force_validate_shops(shipment_data)
            
            # call = "{{URL}}/api/shipments/tracking"
            # requests.post(call,headers={'Authorization': shop_id.api_key,'Content-Type': 'application/json'},payload={'shipments': shipment_ids}).json()
               
    def get_shipment_validation_data(self, shipment_ids):
        if shipment_ids:
            shipment_data = []
            for shipment in shipment_ids:
                shipment_data.append({'id': shipment})
            data = {"shipments": shipment_data}
            _logger.info("~~~~~DATA~~~~%r",data)
        return data if shipment_ids else False