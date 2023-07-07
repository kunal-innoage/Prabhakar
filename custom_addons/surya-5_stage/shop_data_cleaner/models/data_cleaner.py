from odoo import fields, models, api
from datetime import datetime , timedelta
import logging
_logger = logging.getLogger(__name__)

class DataCleaner(models.Model):
    _name = "data.cleaner"
    _inherit = "warehouse.inventory"
    _description = "Data Cleaner"
    _rec_name = "name"

    name = fields.Char("Name")

    label_deletion  = fields.Boolean("Order Label Deletion")
    label_days = fields.Integer("Days after labels are Deleted")

    order_deletion  = fields.Boolean("Imported Order Deletion")
    order_days = fields.Integer("Days after imported orders are Deleted")

    warehouse_deletion  = fields.Boolean("Warehouse Record Deletion")
    warehouse_days = fields.Integer("Days after warehouse records are Deleted")

    po_deletion  = fields.Boolean("Replenishment PO Deletion")
    po_days = fields.Integer("Days after RPOs are Deleted")

    

    ###########################
    # INVENTORY DATA DELETION #
    ###########################
    
    @api.model
    def delete_warehouse_inventory_update_old_records(self):
        cleaners = self.search([])
        for cleaner in cleaners:
            # _logger.info(">>>>>>>............  %r ,...........",cleaner)
            if cleaner.warehouse_deletion:
                days_before = datetime.now() - timedelta(days=cleaner.warehouse_days)

                # inventory cleaner
                records = self.env['warehouse.inventory'].search([('create_date', '<', days_before)])
                records.unlink()

                # process order cleaner
                records = self.env['processed.order'].search([('create_date', '<', days_before)])
                records.unlink()

                # order tracking cleaner
                records = self.env['marketplace.order.tracking'].search([('create_date', '<', days_before)])
                records.unlink()

        
    # ########################
    # PURCHASE DATA DELETION #
    # ########################


    @api.model
    def delete_replenishment_purchase_order_old_records(self):
        cleaners = self.search([])
        for cleaner in cleaners:
            
            if cleaner.po_deletion:
                days_before = datetime.now() - timedelta(days=cleaner.warehouse_days)

                # REPLENISHMENT POs

                records = self.env['warehouse.purchase.order'].search([('create_date', '<', days_before)])
                records.unlink()

                
    ########################
    # IMPORT DATA DELETION #
    ########################

    @api.model
    def delete_import_data_old_records(self):
        cleaners = self.search([])
        for cleaner in cleaners:
            # _logger.info(">>>>>>>............  %r ,...........",cleaner)
            if cleaner.order_deletion:
                days_before = datetime.now() - timedelta(days=cleaner.warehouse_days)

                # amazon imported data cleaner
                records = self.env['amazon.orders'].search([('create_date', '<', days_before)])
                records.unlink()

                # retail shop Love Rugs imported data cleaner
                records = self.env['retail.shop.orders'].search([('create_date', '<', days_before)])
                records.unlink()

                # wayfair imported data cleaner
                records = self.env['wayfair.orders'].search([('create_date', '<', days_before)])
                records.unlink()
                
                # amazon b2b imported data cleaner
                records = self.env['amazon.b2b.sale.order'].search([('create_date', '<', days_before)])
                records.unlink()
                
                # wayfair b2b imported data cleaner
                records = self.env['wayfair.b2b.sale.order'].search([('create_date', '<', days_before)])
                records.unlink()


    #############################
    # ORDER LABEL DATA DELETION #
    #############################


    @api.model
    def delete_labels_old_records(self):
        cleaners = self.search([])
        for cleaner in cleaners:
            # _logger.info(">>>>>>>............  %r ,...........",cleaner)
            if cleaner.warehouse_deletion:
                days_before = datetime.now() - timedelta(days=cleaner.warehouse_days)

                # amazon labels
                records = self.env['amazon.labels'].search([('create_date', '<', days_before)])
                records.unlink()

                