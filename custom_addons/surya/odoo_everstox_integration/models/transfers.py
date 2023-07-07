# -*- coding: utf-8 -*-

from odoo import api, models, fields, _

import logging
_logger = logging.getLogger(__name__)

class EverstoxTransfers(models.Model):
    _name = "everstox.transfers"
    _description = "Everstox Transfers"
    _rec_name = "transfer_number"
    
    transfer_id = fields.Char("Transfer ID")
    transfer_number = fields.Char("Transfer Number")
    eta = fields.Datetime("ETA")
    source = fields.Char("Source")
    destination = fields.Char("Destination")
    destination_name = fields.Char("Destination Name")
    transfer_packing_type = fields.Char("Transfer Packing Type")
    shop_id = fields.Char("Shop ID")
    creation_date = fields.Datetime("Creation Date")
    updated_date = fields.Datetime("Updated Date")
    custom_attributes= fields.Char("Custom Attributes")
    state = fields.Selection([
        ('transmission_to_warehouse_pending', 'Transmission To Warehouse Pending'),
        ('transmitted_to_warehouse', 'Transmitted To Warehouse'),
        ('accepted_by_warehouse', 'Accepted To Warehouse'),
        ('rejected_by_warehouse', 'Rejected Warehouse'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('canceled', 'Canceled'),
        ] , "State")

    everstox_shop_id = fields.Many2one("everstox.shop", string = "Everstox Shop", readonly=True)
    purchase_order_id = fields.Many2one("purchase.order", string = "Purchase Order", readonly=True)
    transfer_item_ids = fields.One2many("everstox.transfer.item", "transfer_id", "Transfer Items")
    transfer_shipment_ids = fields.One2many("everstox.transfer.shipment", "transfer_id", "Shipments")


    def get_everstox_date_format(self, eta):
        date = str(eta).replace(" ", "T")+"Z"
        return date


    def get_odoo_date_format(self, everstox_date_format):
        if everstox_date_format:
            date_time_string = everstox_date_format.replace("T", " ")[0:everstox_date_format.find(":")+6] if everstox_date_format else False
        else:
            date_time_string = False
        return date_time_string


    def process_transfer_response(self, transfer, response):
        try:
            transfer.transfer_id = response.get("id")
            transfer.state = response.get("state")
            transfer.shop_id = response.get("shop_id")
            transfer.creation_date = self.get_odoo_date_format(response.get("creation_date"))
            transfer.updated_date = self.get_odoo_date_format(response.get("updated_date"))
            for item in response.get("transfer_items"):
                transfer_item_id = transfer.transfer_item_ids.search([('sku', '=', item.get("sku")),('transfer_id', '=', transfer.id)])
                if len(transfer_item_id) == 1:
                    transfer_item_id.state = item.get("state")
                    transfer_item_id.quantity_received = item.get("quantity_received")
                    transfer_item_id.quantity_stocked = item.get("quantity_stocked")
                    transfer_item_id.product_id = item.get("id")
            _logger.info(".........Transfer Created ........ %r .......", transfer)
        except Exception as e:
            _logger.info("Error while processing transfer response .......... %r !!!!!!!!!!", e)


    # Server Actions
    ################


    def everstox_create_transfer(self):
        for transfer in self:
            transfer_items = []
            if transfer.transfer_item_ids:
                for item in transfer.transfer_item_ids:
                    transfer_items+= [{
                        "quantity_announced": item.quantity_announced,
                        "sku": item.sku,
                    }]
            data = {
                "ETA": self.get_everstox_date_format(transfer.eta),
                "source": transfer.source,
                "transfer_number": transfer.transfer_number,
                "transfer_packing_type": transfer.transfer_packing_type,
                "destination": transfer.destination,
                "destination_name": transfer.destination_name,
                "transfer_items": transfer_items,
                }
            response = transfer.everstox_shop_id.create_transfer(data)
            self.process_transfer_response(transfer, response)
            _logger.info("~~~~Create Transfer~~~~~%r~~~~~~~~~`", response)

    
    def get_everstox_update_transfer(self):
        for transfer in self:
            call = transfer.everstox_shop_id.shop_url + "api/v1/shops/" + transfer.everstox_shop_id.shop_id +"/transfers/" + transfer.transfer_id
            transfer.everstox_shop_id.get_transfer_update(call)


    def add_everstox_transfer_update(self):
        for transfer in self:
            data = False
            call = transfer.everstox_shop_id.shop_url + "api/v1/shops/" + transfer.everstox_shop_id.shop_id +"/transfers/" + transfer.transfer_id
            transfer.everstox_shop_id.add_transfer_update(call, data)


    def everstox_complete_transfer(self):
        for transfer in self:
            call = transfer.everstox_shop_id.shop_url + "api/v1/shops/" + transfer.everstox_shop_id.shop_id +"/transfers/" + transfer.transfer_id + "/complete"
            transfer.everstox_shop_id.complete_transfer(call)


    def everstox_cancel_transfer(self):
        for transfer in self:
            call = transfer.everstox_shop_id.shop_url + "api/v1/shops/" + transfer.everstox_shop_id.shop_id +"/transfers/" + transfer.transfer_id + "/mark-canceled"
            transfer.everstox_shop_id.cancel_transfers(call)


    def everstox_delete_transfer(self):
        for transfer in self:
            call = transfer.everstox_shop_id.shop_url + "api/v1/shops/" + transfer.everstox_shop_id.shop_id +"/transfers/" + transfer.transfer_id + "/mark-canceled"
            transfer.everstox_shop_id.delete_transfer(call)



class EverstoxTransferItem(models.Model):
    _name = "everstox.transfer.item"
    _description = "Everstox Transfer Item"

    product_id = fields.Char("Product ID")
    quantity_announced = fields.Integer("Quantity Announced")
    quantity_received = fields.Integer("Quantity Received")
    quantity_stocked = fields.Integer("Quantity Stocked")
    sku = fields.Char("SKU")
    custom_attributes = fields.Char("Custom Attributes")
    state = fields.Selection([
        ('transmission_to_warehouse_pending', 'Transmission To Warehouse Pending'),
        ('transmitted_to_warehouse', 'Transmitted To Warehouse'),
        ('accepted_by_warehouse', 'Accepted To Warehouse'),
        ('rejected_by_warehouse', 'Rejected Warehouse'),
        ('in_progress', 'In Progress'),
        ('stocked_partially', 'Stocked Partially'),
        ('stocked_completely', 'Stocked Completely'),
        ('canceled', 'Canceled'),
        ] , "State")

    everstox_shop_id = fields.Many2one("everstox.shop", string = "Everstox Shop", readonly=True)
    transfer_id = fields.Many2one("everstox.transfers", "Transfer")


class EverstoxTransferShipment(models.Model):
    _name = "everstox.transfer.shipment"
    _description = "Everstox Transfer Shipment"
    _rec_name = "transfer_shipment_id"
    
    forwarded_to_shop = fields.Boolean("Is Forwareded To Shop")
    transfer_shipment_id = fields.Char("Transfer Shipment ID")
    shipment_received_date = fields.Datetime("Shipment Received Date")

    everstox_shop_id = fields.Many2one("everstox.shop", string = "Everstox Shop", readonly=True)
    transfer_id = fields.Many2one("everstox.transfers", string = "Transfer", readonly=True)
    transfer_shipment_item_ids = fields.One2many("everstox.transfer.shipment.item", "shipment_id", "Shipment Items")

    @api.model_create_multi
    def create(self, values):
        res = super(EverstoxTransferShipment, self).create(values)
        for shipment in self:
            if shipment.transfer_id.purchase_order_id:
                lots = self.env['stock.production.lot']

                for picking in shipment.transfer_id.purchase_order_id.picking_ids:
                    if picking.has_tracking:
                        for move_line in picking.move_ids_without_package:
                            # NXT serial no 
                            last_serial_number  = lots.search([('product_id','=', move_line.product_id.id)], order='id desc', limit=1)
                            if len(last_serial_number) > 0:
                                lsn_preffix = last_serial_number[0].name[:-8]
                                lsn_suffix = last_serial_number[0].name[-8:]
                                lsn_suffix = str(int(lsn_suffix)+1).rjust(8,"0")
                                move_line.next_serial = lsn_preffix+lsn_suffix
                            else:
                                move_line.next_serial = move_line.product_id.name+'00000000'                               
                            lot_names = lots.generate_lot_names(move_line.next_serial, move_line.next_serial_count)
                            move_lines_commands = move_line._generate_serial_move_line_commands(lot_names)
                            move_line.write({'move_line_ids': move_lines_commands})
                        picking.button_validate()

                        # landed_cost = self.env['stock.landed.cost']
                        # landed_cost_id = landed_cost.create({
                        #     'target_model': 'picking',
                        #     'picking_ids': picking,
                        #     'cost_lines': [(0, 0, {
                        #         'product_id': landed_product_id.id,
                        #         'price_unit': stock_prod.average_landed_cost*needed_stock_count,
                        #         'split_method': 'equal'
                        #     })],
                        # })
                        # landed_cost_id.button_validate()

        return res


class EverstoxTransferShipmentItem(models.Model):
    _name = "everstox.transfer.shipment.item"
    _description = "Everstox Transfer Shipment Item"

    transfer_shipment_item_id = fields.Char("Shipment Item ID")
    product_id = fields.Char("Product ID")
    product_name = fields.Char("Product Name")
    product_sku = fields.Char("Product SKU")
    quantity_received = fields.Integer("Quantity Received")
    quantity_stocked = fields.Integer("Quantity Stocked")
    transfer_item_id = fields.Char("Transfer Item ID")

    everstox_shop_id = fields.Many2one("everstox.shop", string = "Everstox Shop", readonly=True)
    shipment_id = fields.Many2one("everstox.transfer.shipment", "Shipment")
    transfer_shipment_batch_ids = fields.One2many("everstox.transfer.shipment.batches", "shipment_item_id", "Shipment Batches")


class EverstoxTransferShipmentBatches(models.Model):
    _name = "everstox.transfer.shipment.batches"
    _description = "Everstox Transfer Shipment Batches"

    batch = fields.Char("Batch")
    batch_id = fields.Char("Batch ID")
    expiration_date = fields.Datetime("Expiration Date")
    quantity_received = fields.Integer("Quantity Reveived")
    quantity_stocked = fields.Integer("Quantity Stocked")

    everstox_shop_id = fields.Many2one("everstox.shop", string = "Everstox Shop", readonly=True)
    shipment_item_id = fields.Many2one("everstox.transfer.shipment.item", "Shipment Item")





