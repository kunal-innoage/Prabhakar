# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from odoo import models, fields, _
from odoo.exceptions import ValidationError, UserError

import logging
_logger = logging.getLogger(__name__)


class MarketplaceWarehouse(models.Model):
    _name = 'marketplace.warehouse'
    _description = 'Marketplace Warehouse'
    _rec_name = 'warehouse_code'
    

    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse', required=True)
    warehouse_code = fields.Char('Code Name', related = "warehouse_id.code", readonly = True)
    stock_picking_type_id = fields.Many2one("stock.picking.type", "Inventory Update Operation", domain="[('warehouse_id', '=', warehouse_id)]")




    # Special Buttons 


    # Server actions

    def warehouse_inventory_view_action_open(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _("%s's Daily Updated Inventory of", self.warehouse_code),
            'view_mode': 'list,form',
            'view_ids': [(self.env.ref('odoo_mirakl_integration.view_warehouse_inventory').id, 'list'), (self.env.ref('odoo_mirakl_integration.view_warehouse_inventory_form').id, 'form')],
            'res_model': 'warehouse.inventory',
            'limit': 200,
            'context': {'search_default_date':1},
            'domain': [('warehouse_id.id', 'in', [self.id])],
        }

    def warehouse_processed_orders_view_action_open(self):
        self.ensure_one()

        search_view_ref = self.env.ref('odoo_mirakl_integration.view_processed_order_filters', False)
        warehouse_code = self.warehouse_code
        if self.warehouse_code == 'IFUL':
            warehouse_code = 'BOH'

        return {
            'type': 'ir.actions.act_window',
            'name': _("%s's Daily Processed Orders of ", self.warehouse_code),
            'view_mode': 'list,form',
            'view_ids': [(self.env.ref('odoo_mirakl_integration.marketplace_processed_orders_tree_view').id, 'list'), (self.env.ref('odoo_mirakl_integration.marketplace_processed_orders_form_view').id, 'form')],
            'limit': 200,
            'res_model': 'processed.order',
            'search_view_id': search_view_ref and [search_view_ref.id],
            'context': {'search_default_date':1, 'search_default_stock_status':1},
            'domain': [('warehouse', '=', warehouse_code)]
        }
    
    def tracking_info_so_import_view_action_open(self):
        self.ensure_one()
        date_today = datetime.today()
        return {
            'type': 'ir.actions.act_window',
            'name': _("%s's Daily Updated Tracking of ", self.warehouse_code),
            'view_mode': 'list,form',
            'limit': 200,
            'view_ids': [(self.env.ref('odoo_mirakl_integration.view_marketplace_order_tracking_tree_view').id, 'list'), (self.env.ref('odoo_mirakl_integration.view_marketplace_order_tracking_form_view').id, 'form')],
            'res_model': 'marketplace.order.tracking',
            'context': {'search_default_date':1},
            'domain': [('warehouse_id', '=', self.id)]
        }
    
