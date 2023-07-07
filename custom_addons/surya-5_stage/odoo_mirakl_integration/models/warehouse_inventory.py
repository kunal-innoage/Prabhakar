# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from odoo import models, fields, _,api
from odoo.exceptions import ValidationError, UserError
import pytz
import datetime

import logging
_logger = logging.getLogger(__name__)


class WarehouseInventory(models.Model):
    _name = 'warehouse.inventory'
    _inherit = 'mail.thread'
    _description = 'Warehouse Inventory'
    _rec_name = 'product_id'
    
    product_id = fields.Char("SKU")
    available_stock_count = fields.Float("Current Stock")
    today_spent_stock_count = fields.Float("Used Stock")
    warehouse_id = fields.Many2one("marketplace.warehouse", "Warehouse")
    onhand_stock_count = fields.Float("Onhand Stock", readonly=True)
    stock_matched = fields.Boolean("Stock Mapped", readonly=True)
    odoo_product_id = fields.Many2one('product.product', 'Product', readonly=True)
    purchase_order_id = fields.Many2one("purchase.order", "Purchase Order", readonly=True)
    uploaded_file = fields.Binary("Inventory File")
    last_updated_date = fields.Datetime("Last Updated On")

    processing_time = fields.Selection([
        ('morning','First Shift'),
        ('evening','Second Shift')
    ])
    stock_in_sync = fields.Boolean("Stock in Sync", compute="_compute_stock_sync")
    shop_offer_ids = fields.One2many("mirakl.offers", "inventory_id", "Shop Offers", compute="_compute_offers")
        
    @api.model_create_multi
    def create(self, vals):
        res = super(WarehouseInventory, self).create(vals)
        if res._context.get('import_file'):
            processing_shift = None
            IST = pytz.timezone('Asia/Kolkata')
            time_now = datetime.datetime.strftime(datetime.datetime.now(IST), "%Y-%m-%d %H:%M:%S")
            if int(time_now.split(' ')[1][:2]) <= 12:
                processing_shift = 'morning'
            else:
                processing_shift = 'evening'
            
            warehouse = self.env['marketplace.warehouse'].search([('id', '=', res._context.get('active_id'))])
            for product in res:
                product_id = self.env['product.product'].search([('default_code','in', [product.product_id])])
                if warehouse:
                    product.warehouse_id = warehouse
                product.odoo_product_id = product_id
                product.processing_time = processing_shift
        return res

    @api.depends("available_stock_count")
    def _compute_stock_sync(self):
        for rec in self:
            rec.stock_in_sync = False
            if rec.odoo_product_id and rec.product_id:
                for offer in rec.shop_offer_ids:
                    if offer.quantity and rec.available_stock_count:
                        if offer.quantity != rec.available_stock_count:
                            rec.stock_in_sync = False
                            break
                        else:
                            rec.stock_in_sync = True
            else:
                rec.stock_in_sync = False

    @api.depends("odoo_product_id")
    def _compute_offers(self):
        for rec in self:
            if rec.odoo_product_id and rec.product_id:
                offers = self.env['mirakl.offers'].search([('product_id','=',rec.odoo_product_id.id)])
                for offer in offers:
                    rec.shop_offer_ids = rec.shop_offer_ids + offer
                if not len(offers):
                    rec.shop_offer_ids = None
            else:
                rec.shop_offer_ids = None

    def update_current_stock_count(self):
        for prod in self:
            stocks = self.env['stock.quant'].search([('product_id','=',prod.odoo_product_id.id)])
            final = 0
            for stock in stocks:
                if stock.location_id.warehouse_id.code == prod.warehouse_id.warehouse_code:
                    final += stock.quantity
            prod.onhand_stock_count = final

    def update_inventory_info(self):
        po_obj = self.env['purchase.order']
        landed_product_id = self.env['product.product'].search([('landed_cost_ok', '=', True)])

        for prod in self:
            if len(prod.odoo_product_id) <= 0 or len(prod.purchase_order_id) <= 0 :
                # Map Product
                stock_prod = prod.odoo_product_id
                if len(stock_prod) > 0 :
                    if len(prod.purchase_order_id) <= 0:
                        needed_stock_count = prod.available_stock_count - prod.onhand_stock_count
                        purchase_order = []
                        seller_info = False
                        for seller in stock_prod.seller_ids:
                            seller_info = seller
                        try:
                            if seller_info and needed_stock_count > 0:
                                #Get Purchase Order 
                                picking_type_id = prod.warehouse_id.stock_picking_type_id.id
                                product_taxes = stock_prod.supplier_taxes_id.filtered(lambda x: x.company_id.id == self.env.company.id)
                                taxes = po_obj.fiscal_position_id.map_tax(product_taxes)
                                try:
                                    purchase_order = po_obj.create({
                                        "partner_id": seller_info.name.id,
                                        "picking_type_id": picking_type_id,
                                        "order_line": [(0,0, {
                                            'name': stock_prod.default_code,
                                            'product_id': stock_prod.id,
                                            'product_uom': stock_prod.uom_id.id,
                                            'price_unit': seller_info.price,
                                            'product_qty': needed_stock_count,
                                            'taxes_id': [(6, 0, taxes.ids)],
                                        })],
                                    })
                                except Exception as err:
                                    _logger.info("~~PO Failed~~~~1~~~~%r~~~~~~~~~~",err)
                            # Process PO
                            if len(purchase_order):
                                prod.purchase_order_id = purchase_order
                                purchase_order.button_confirm()
                                lots = self.env['stock.production.lot']
                                _logger.info("~purchase_order~~~~~%r~~~~~~~~~~~~~~", purchase_order)
                                for picking in purchase_order.picking_ids:
                                    if picking.has_tracking:
                                        for move_line in picking.move_ids_without_package:
                                            # NXT serial no 
                                            last_serial_number  = lots.search([('product_id','=', stock_prod.id)], order='id desc', limit=1)
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

                                        landed_cost = self.env['stock.landed.cost']
                                        landed_cost_id = landed_cost.create({
                                            'target_model': 'picking',
                                            'picking_ids': picking,
                                            'cost_lines': [(0, 0, {
                                                'product_id': landed_product_id.id,
                                                'price_unit': stock_prod.average_landed_cost*needed_stock_count,
                                                'split_method': 'equal'
                                            })],
                                        })
                                        landed_cost_id.button_validate()
                                prod.stock_matched = True
                                # prod.onhand_stock_count = prod.odoo_product_id.qty_available
                        except Exception as err:
                            _logger.info("~~PO Failed~~~~~~~~%r~~~~~~~~~~",err)
                else:
                    _logger.info("~~~~~~~~~~~~product_not_found~~~~~~~%r~~~~~~~~~", prod.product_id)
        self.update_current_stock_count()
        pass

    

    def update_shops_inventory(self):
        return {
            'name': "Select Shops to Update",
            'type': 'ir.actions.act_window',
            'res_model': 'bulk.inventory.update',
            'target': 'new',
            'view_mode': 'form',
            'context': {
                'selected_record': self.ids
            }

        }
    

    #Pass on invenotry notification button
    def pass_call(self):
        pass
