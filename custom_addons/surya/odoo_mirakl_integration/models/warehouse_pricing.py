# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
# from math import prod
from odoo import models, fields, _
from odoo.exceptions import ValidationError, UserError

import logging
_logger = logging.getLogger(__name__)


class WarehousePrice(models.Model):
    _name = 'warehouse.price'
    _description = 'Warehouse Pricing'
    _rec_name = 'product_id'
    
    product_id = fields.Char("SKU")
    fob_cost = fields.Float("FOB Cost")
    landed_cost = fields.Float("Landed Cost")
    retail_price_fr_maison = fields.Float("Retail Price France Maison") 
    discount_price_fr_maison = fields.Float("Discount Price France Maison")
    odoo_product_id = fields.Many2one('product.product', 'Product', readonly=True)
    vendor = fields.Char("Vendor")


    sold_stock_count = fields.Float("Sold Stock Count")
    available_stock_count = fields.Float("Available Stock Count")

    purchase_order_id = fields.Many2one("purchase.order", "Purchase Order", readonly=True)

    def assign_landed_charge(self):
        for stock in self:
            if len(stock.odoo_product_id) > 0:
                stock.odoo_product_id.average_landed_cost = stock.landed_cost - stock.fob_cost
    
    def create_purchase_orders(self, stock):
        
        # DATA
        product_id = stock.odoo_product_id
        purchase_order = self.env['purchase.order']
        needed_stock_count = stock.sold_stock_count + stock.available_stock_count
        landing_charges = needed_stock_count * (stock.landed_cost - stock.fob_cost)
        landed_product_id = self.env['product.product'].search([('landed_cost_ok', '=', True)])

        # Get Seller Info
        seller_info = False
        for seller in product_id.seller_ids:
            seller_info = seller

        # Create Purchase Order
        try:
            if seller_info and needed_stock_count > 0:
                
                #Get Purchase Order 
                product_taxes = product_id.supplier_taxes_id.filtered(lambda x: x.company_id.id == self.env.company.id)
                taxes = purchase_order.fiscal_position_id.map_tax(product_taxes)
                try:
                    purchase_order = purchase_order.create({
                        "partner_id": seller_info.name.id,
                        "order_line": [(0,0, {
                            'name': product_id.default_code,
                            'product_id': product_id.id,
                            'product_uom': product_id.uom_id.id,
                            'price_unit': seller_info.price,
                            'product_qty': needed_stock_count,
                            'taxes_id': [(6, 0, taxes.ids)],
                        })],
                    })
                except:
                    return False
            # Process PO
            if len(purchase_order):
                stock.purchase_order_id = purchase_order
                purchase_order.button_confirm()
                for picking in purchase_order.picking_ids:
                    if picking.has_tracking:
                        for move_line in picking.move_ids_without_package:
                            move_line.next_serial = move_line.product_id.name+'00000000'
                            lot_names = self.env['stock.production.lot'].generate_lot_names(move_line.next_serial, move_line.next_serial_count)
                            move_lines_commands = move_line._generate_serial_move_line_commands(lot_names)
                            move_line.write({'move_line_ids': move_lines_commands})
                        picking.button_validate()

                        landed_cost = self.env['stock.landed.cost']
                        landed_cost_id = landed_cost.create({
                            'target_model': 'picking',
                            'picking_ids': picking,
                            'cost_lines': [(0, 0, {
                                'product_id': landed_product_id.id,
                                'price_unit': landing_charges,
                                'split_method': 'equal'
                            })],
                        })
                        landed_cost_id.button_validate()
                _logger.info("~~PO~~~~~~~~%r~~~~~%r~~~~~",purchase_order, landed_product_id.stock_quant_ids)
        except Exception as err:
            _logger.info("~~PO Failed~~~~~~~~%r~~~~~~~~~~",err)

        return purchase_order
    
    def update_product_fob_pricing(self):
        for product in self:
            try:
                    supplier = self.env['product.supplierinfo']
                    vendor_id = self.env['res.partner'].search([('name', '=', product.vendor.rstrip())])
                    currency_id = self.env.company.currency_id
                    
                    if len(vendor_id) > 0:
                        
                        if len(product.odoo_product_id.seller_ids)> 0:
                            main = False
                            for seller in product.odoo_product_id.seller_ids:
                                if vendor_id.id == seller.name.id:
                                    seller.min_qty = 1
                                    seller.price = product.fob_cost
                                    main = seller
                            if len(main) > 0:
                                product.odoo_product_id.seller_ids = main
                            else:
                                product.odoo_product_id.seller_ids = supplier.create({
                                    "name": vendor_id.id,
                                    "min_qty": 1,
                                    "currency_id": currency_id.id, 
                                    "price": product.fob_cost,
                                    "delay": 60,
                                })
                            _logger.info("Updated Supplier Details~~~~~~~~%r~~~~~~~~~`",product.odoo_product_id.seller_ids)
                        else:
                            product.odoo_product_id.seller_ids = supplier.create({
                                "name": vendor_id.id,
                                "min_qty": 1,
                                "currency_id": currency_id.id, 
                                "price": product.fob_cost,
                                "delay": 60, 
                            })
                            _logger.info("Added Supplier~~~~~~~~~~~~~%r~~~~~~~~~~",product.odoo_product_id.seller_ids)           
                    
                    else:
                        _logger.info("Missing Vendor~~~~~~~~~~~~~%r~~~~~~~~~", product.vendor)
                    
                    product.sold_stock_count = product.odoo_product_id.sales_count
                    product.odoo_product_id.tracking = "serial"

            except Exception as err:
                _logger.info("Product not found please check warehouse pricing for %r`~~~~~~~%r~~~~",product.product_id ,err)
        
    def update_product_landed_pricing(self):
        for product in self:
            if len(product.purchase_order_id) == 0:
                try:
                    if len(product.odoo_product_id.seller_ids)> 0:
                        purchase_order = self.create_purchase_orders(product)
                    else:
                        _logger.info("Missing Supplier For The Product - %r~~~~~~~~~~",product.odoo_product_id.name)           
                except Exception as err:
                    _logger.info("~~~~~~~~~~~Product not found please check warehouse pricing for %r`~~~~~~~%r~~~~",product.product_id ,err)

    def clear_previous_inventory(self):
        product_id = self.env['product.product']
        for product in self:
                try:
                    prod = product_id.search([('default_code', '=', product.product_id)])
                    if len(prod) > 0:
                        product.odoo_product_id = prod
                        product.sold_stock_count = prod.sales_count
                except Exception as err:
                    _logger.info("~~~~~~~~~~~Product not found please check warehouse pricing for %r`~~~~~~~%r~~~~",product.product_id ,err)

    def apply_latest_inventory(self):
        for product in self:
                try:
                    prod = product.odoo_product_id
                    if len(prod.stock_quant_ids) > 0:
                        for quantity in prod.stock_quant_ids:
                            quantity.inventory_quantity = 1.0
                            quantity.inventory_diff_quantity = 0.0
                            quantity.inventory_quantity_set = False
                            quantity.action_apply_inventory()
                except Exception as err:
                    _logger.info("~~~~~~~~~~~Product not found please check warehouse pricing for %r`~~~~~~~%r~~~~",product.odoo_product_id ,err)
                    
