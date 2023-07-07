# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from datetime import timedelta


import logging
_logger = logging.getLogger(__name__)

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'


    def create_transfer(self):
        for po in self:
            transfer_id = transfer_obj = self.env["everstox.transfers"]
            if po.picking_type_id:
                warehouse_id = po.picking_type_id.warehouse_id
                shop_id = self.env["everstox.shop"].search([("warehouse_id", "=", warehouse_id.id)])
                if po.order_line and shop_id:
                    transfer_item_ids = self.prepare_transfer_items(po, shop_id)

                if shop_id:
                    transfer_id += transfer_obj.create({
                        "eta": po.date_planned,
                        # "custom_attributes": ,
                        "source": "Turkey",
                        "transfer_number": po.name,
                        "transfer_packing_type": "Pallet",
                        "destination": shop_id.everstox_warehouse_id.warehouse_id,
                        "destination_name": shop_id.everstox_warehouse_id.warehouse_name,
                        # "shop_id": shop_id.shop_id,
                        "transfer_item_ids": transfer_item_ids,
                        "everstox_shop_id": shop_id.id,
                        "purchase_order_id": po.id,
                    })

            _logger.info(".............. Transfer Created ....%r........", transfer_id)



    def prepare_transfer_items(self, po, shop_id):
        transfer_ids = transfer_item_obj = self.env["everstox.transfer.item"]
        for line in po.order_line:

            # Product Doesn't Exist
            if not line.product_id.everstox_product_id.item_id:
                self.env["everstox.shop.product"].create_missing_product(line, shop_id)

            # Create Transfer
            transfer_ids += transfer_item_obj.create({
                "quantity_announced": line.product_qty,
                "sku": line.product_id.default_code,
                "everstox_shop_id": shop_id.id,
            })
        return transfer_ids


    # For Cancelling Transfers 
    # def button_cancel(self):
    #     for order in self:
    #         for inv in order.invoice_ids:
    #             if inv and inv.state not in ('cancel', 'draft'):
    #                 raise UserError(_("Unable to cancel this purchase order. You must first cancel the related vendor bills."))

    #     self.write({'state': 'cancel', 'mail_reminder_confirmed': False})
