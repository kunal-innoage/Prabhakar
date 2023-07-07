# -*- coding: utf-8 -*-

from odoo import models, fields, _
from odoo.exceptions import ValidationError, UserError

import logging
_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = 'stock.picking'


    # Method to validate delivery
    def button_validate(self):
        res = super(StockPicking, self).button_validate()

        for picking in self:
            if picking.sale_id.manomano_order_id:
                if picking.is_tracking_updated:
                    picking.sale_id.status = "SHIPPED"
                    picking.sale_id.mirakl_order_state = "shipped"
                    picking.sale_id.invoice_status = 'to invoice'
            else:
                picking.sale_id.invoice_status = 'to invoice'
        return res



class StockImmediateTransfer(models.TransientModel):
    _inherit = 'stock.immediate.transfer'


    def devide_per_shop_manomano(self, pickings):
        shop_wise_pickings = {}
        for picking in pickings:
            if picking.sale_id.manomano_order_id:
                if picking.sale_id.manomano_shop_id not in shop_wise_pickings.keys():
                    shop_wise_pickings[picking.sale_id.manomano_shop_id] = [picking]
                else:
                    shop_wise_pickings[picking.sale_id.manomano_shop_id].append(picking)
        return shop_wise_pickings


    def shop_shipment_info_prepration_manomano(self, shipments):
        
        # Limitation of 1000 shipments
        picking_data = []
        for picking in shipments:
            if picking.sale_id.manomano_order_id and picking.sale_id.manomano_shop_id:
                if picking.shipping_tracking and picking.shipping_tracking_url and picking.mirakl_carrier_code and not picking.is_tracking_updated:
                    for order_line in picking.sale_id.order_line:
                        if len(picking.move_line_ids_without_package) == 1:
                            if order_line.product_id == picking.move_line_ids_without_package.product_id:
                                manomano_offer_sku_id = order_line.offer_sku
                                break
                    
                    if manomano_offer_sku_id:
                        shipment_data = {
                            "carrier": picking.mirakl_carrier_name,
                            "order_reference": picking.sale_id.manomano_order_id,
                            "seller_contract_id": picking.sale_id.manomano_shop_id.seller_contract_id,
                            "tracking_number": picking.shipping_tracking,
                            "tracking_url":  picking.shipping_tracking_url,
                            "products": [
                                {
                                    "seller_sku": manomano_offer_sku_id,
                                    "quantity": int(picking.move_line_ids_without_package.product_uom_qty)
                                },
                            ]
                        }
                        picking_data.append(shipment_data)
                        picking.is_tracking_updated = True
                    else:
                        _logger.info(" ~~~~~~~ Manomano Offer Id is missing in the offer id ______;;;;;;")
                else:
                    if not picking.is_tracking_updated:
                        raise ValidationError(_("Please add tracking info inside the delivery -    %r  ;;;;;",picking.name))
                    else:
                        _logger.info(" ~~~~~~~ Manomano order shipment already updated on Manomano ______;;;;;;")
        return picking_data
                
    def process(self):

        shop_wise_delivery = self.devide_per_shop_manomano(self.pick_ids)
        # Data Preparation & Mirakl Update
        if len(shop_wise_delivery.keys()) >= 1:
            for shop in shop_wise_delivery.keys():
                if len(shop_wise_delivery[shop]) > 0:
                    picking_data = self.shop_shipment_info_prepration_manomano(shop_wise_delivery[shop])
                    response = self.env['manomano.seller'].send_shipment_tracking_manomano(picking_data, shop)
                    if response:
                        _logger.info("........Multiple Tracking Updation Successful...........")
                    else:
                        _logger.info("........Multiple Tracking Updation Error...........")

        return super(StockImmediateTransfer, self).process()
                
