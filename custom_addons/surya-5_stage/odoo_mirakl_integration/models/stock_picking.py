# -*- coding: utf-8 -*-

from odoo import models, fields, _
from odoo.exceptions import ValidationError, UserError

import logging
_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    delivery_logs = fields.Selection(related='sale_id.mirakl_order_state', string="Order Status", store=True, readonly=False)
    is_tracking_updated = fields.Boolean('Tracking Info Updated') 
    
    # Mirakl Fields
    is_mirakl_stock_transfer = fields.Boolean('Is Mirakl Stock Transfer')
    shipping_tracking = fields.Char(string= 'Shipping Tracking', store=True, readonly=False)
    shipping_tracking_url = fields.Char(string= 'Shipping Tracking URL', store=True, readonly=False)
    mirakl_shop_id = fields.Many2one("shop.integrator",related = "sale_id.mirakl_shop_id", string ="Shop")
    mirakl_carrier_name = fields.Char(string='Carrier Name',store=True, readonly=False) #Used for all marketplaces
    mirakl_carrier_code = fields.Char(string='Carrier Code',store=True, readonly=False) # Used for all marketplaces

    # Cdiscount Fields
    



    # Method to validate delivery
    def button_validate(self):
        res = super(StockPicking, self).button_validate()

        for picking in self:
            if picking.sale_id.mirakl_order_id:
                if picking.is_tracking_updated:
                    picking.sale_id.mirakl_order_state = "shipped"
                    picking.sale_id.invoice_status = 'to invoice'
            else:
                picking.sale_id.invoice_status = 'to invoice'
        
        return res

    def _update_sale_order_pickings(self, picking):
        # all_validated = False
        count = 0
        for picking in picking.sale_id.picking_ids:
            if picking.state == 'done':
                count  += 1
        if count == len(picking.sale_id.picking_ids):
            picking.sale_id.mirakl_order_state = "shipped"
            picking.sale_id.invoice_status = 'to invoice'
            picking.sale_id.all_delivered = True





class StockImmediateTransfer(models.TransientModel):
    _inherit = 'stock.immediate.transfer'


    def devide_per_shop(self, pickings):
        shop_wise_pickings = {}
        for picking in pickings:
            if picking.sale_id.mirakl_order_id:
                if picking.sale_id.mirakl_shop_id not in shop_wise_pickings.keys():
                    shop_wise_pickings[picking.sale_id.mirakl_shop_id] = [picking]
                else:
                    shop_wise_pickings[picking.sale_id.mirakl_shop_id].append(picking)
        return shop_wise_pickings

    def shop_shipment_info_prepration(self, shipments):
        
        # Limitation of 1000 shipments
        picking_data = {"shipments": []}
        for picking in shipments:
            if picking.sale_id.mirakl_order_id and picking.sale_id.mirakl_shop_id:
                if picking.shipping_tracking and picking.shipping_tracking_url and picking.mirakl_carrier_code and not picking.is_tracking_updated:
                    mirakl_offer_sku_id = ""
                    for order_line in picking.sale_id.order_line:
                        if len(picking.move_line_ids_without_package) == 1:
                            if order_line.product_id == picking.move_line_ids_without_package.product_id:
                                mirakl_offer_sku_id = order_line.offer_sku
                                break
                    
                    if mirakl_offer_sku_id:
                        shipment_data = {
                            "order_id": picking.sale_id.mirakl_order_id,
                            "shipment_lines": [
                                {
                                "offer_sku": mirakl_offer_sku_id,
                                "quantity": 1,
                            }
                            ],
                            "shipped": True,
                            "tracking": {
                                "carrier_code": picking.mirakl_carrier_code,
                                "carrier_name": picking.mirakl_carrier_name,
                                "carrier_url": picking.shipping_tracking_url,
                                "tracking_number": picking.shipping_tracking,     
                            }    
                        }
                        picking_data['shipments'].append(shipment_data)
                        picking.is_tracking_updated = True
                    else:
                        _logger.info(" ~~~~~~~ Mirakl Offer Id is missing in the offer id ______;;;;;;")
                else:
                    if not picking.is_tracking_updated:
                        raise ValidationError(_("Please add tracking info inside the delivery -    %r  ;;;;;",picking.name))
                    else:
                        _logger.info(" ~~~~~~~ Mirakl order shipment already updated on mirakl ______;;;;;;")
        return picking_data
                
    def process(self):

        shop_wise_deliveries = self.devide_per_shop(self.pick_ids)
        
        # Data Preparation & Mirakl Update
        for shop in shop_wise_deliveries.keys():
            
            if len(shop_wise_deliveries[shop]) > 0:

                rejected_pickings = []
                picking_data = self.shop_shipment_info_prepration(shop_wise_deliveries[shop])
                rejected_pickings = self.env['shop.integrator'].update_bulk_shipment_tracking(picking_data, shop)
                
                # Remove Extra Pickings
                if rejected_pickings:
                    picking_obj = self.env['stock.picking']
                    for picking in self.pick_ids:
                        if picking.sale_id.mirakl_order_id not in rejected_pickings:
                            picking_obj += picking
                    self.pick_ids = picking_obj

        return super(StockImmediateTransfer, self).process()
