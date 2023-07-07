# -*- coding: utf-8 -*-

# from math import prod
from odoo import models, fields, _, api

import logging
_logger = logging.getLogger(__name__)


class WarehousePurchaseOrder(models.Model):
    _name = 'warehouse.purchase.order'
    _description = 'Warehouse Purchase Order'
    _rec_name = 'vendor'
    
    vendor = fields.Char("VENDOR")
    sku = fields.Char("SKU")
    vendor_id = fields.Char("VENDOR ID")
    upc = fields.Char("UPC")
    quantity = fields.Char("QTY")
    sqm = fields.Char("SQM")
    per_piece_price = fields.Char("Per Piece Price")
    total_price = fields.Char("Total Price")
    warehouse = fields.Char("Warehouse")
    existing_po = fields.Char("PO")

    purchase_order_id = fields.Many2one("purchase.order", "Purchase Order", readonly=True)
    product_id = fields.Many2one("product.product", "Product", readonly=True)
    warehouse_id = fields.Many2one("stock.warehouse", "Stock Warehouse", readonly=True)

    @api.model_create_multi
    def create(self, vals):
        res = super(WarehousePurchaseOrder, self).create(vals)
        if res._context['import_file']:
            for line in res:
                product_id = self.env['product.product'].search([('default_code','in', [line.sku])])
                warehouse = self.env['stock.warehouse'].search([('code', '=', line.warehouse)])
                if product_id:
                    line.product_id = product_id
                if warehouse:
                    line.warehouse_id = warehouse
        return res

    def map_with_purchase_order_lines(self):
        
        # Group Different PO's seprately 
        group_po = {}
        existing_po_group = {}
        for po_line in self:
            if po_line.existing_po:
                if not existing_po_group.get(po_line.create_date):
                    existing_po_group[po_line.create_date] = [po_line]
                else:
                    existing_po_group[po_line.create_date].append(po_line)
            else:
                if po_line.product_id:
                    if not group_po.get(po_line.create_date):
                        group_po[po_line.create_date] = [po_line]
                    else:
                        group_po[po_line.create_date].append(po_line)



        # Create Group Replishment POs 
        purchase_order = self.env['purchase.order']
        for group in group_po.keys():
            lines=[]
            seller_info = False
            warehouse_id = False
            for order_line in group_po[group]:
                if order_line.product_id:
                    # Create PO lines 
                    lines +=  [(0,0, {
                                'name': order_line.product_id.default_code,
                                'product_id': order_line.product_id.id,
                                'product_uom': order_line.product_id.uom_id.id,
                                'price_unit': float(order_line.per_piece_price),
                                'product_qty': int(order_line.quantity),
                                'taxes_id': [(6, 0, [])],
                            })]
                        
                # get seller
                if not seller_info:
                    for seller in order_line.product_id.seller_ids:
                        seller_info = seller
                        if seller_info:
                            break
                # get warehouse
                if not warehouse_id:
                    warehouse_id = order_line.warehouse_id or self.env["stock.warehouse"].search([('code','=', order_line.warehouse)])
            
            # get picking_type_id
            pick_in = False
            if warehouse_id:
                pick_in = self.env['stock.picking.type'].search(
                    [('warehouse_id', '=', warehouse_id.id), ('code', '=', 'incoming')],
                    limit=1,
                )

            # Create Purchase Order 
            if pick_in:
                purchase_order_id = purchase_order.create({
                    "partner_id": seller_info.name.id,
                    "currency_id": self.env['res.currency'].search([('name', '=', 'USD')]).id,
                    "order_line": lines,
                    "picking_type_id": pick_in.id if pick_in else False,
                })

                for order_line in group_po[group]:
                    order_line.purchase_order_id = purchase_order_id
                
                # Update SQM and TSQM 
                total_sqm = 0.0
                for line in purchase_order_id.order_line:
                    line.total_sqm = float(line.per_piece_sqm )* line.product_qty
                    total_sqm += float(line.total_sqm)

                purchase_order_id.total_sqm = total_sqm

        # Write Group Replishment POLines 
        for group in existing_po_group.keys():
            lines=[]
            purchase_order_id = False
            
            for order_line in existing_po_group[group]:
                if order_line.existing_po and not purchase_order_id:
                    purchase_order_id = purchase_order.search([("name", "=", order_line.existing_po)], limit=1)
                 
                if order_line.product_id  and order_line.product_id not in [line.product_id for line in purchase_order_id.order_line]:
                    # Create PO lines 
                    _logger.info("!!!!!!!  Entry")

                    try:
                        self.env["purchase.order.line"].create({
                                    'name': order_line.product_id.default_code,
                                    'product_id': order_line.product_id.id,
                                    'product_uom': order_line.product_id.uom_id.id,
                                    'price_unit': float(order_line.per_piece_price),
                                    'product_qty': int(order_line.quantity),
                                    'order_id': purchase_order_id.id,
                                    'taxes_id': [(6, 0, [])],
                                })
                        order_line.purchase_order_id = purchase_order_id
                    except Exception as e:
                        _logger.info("!!!!!!!   Error while adding new replenishment lines - %r", e)
                else:
                    _logger.info("!!!!!!!  Product already Exists or product doesn't exist")

                    
