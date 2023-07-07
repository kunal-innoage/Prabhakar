# -*- coding: utf-8 -*-

from odoo import models, fields, _
from odoo.tools import float_compare


import logging
_logger = logging.getLogger(__name__)


class WayfairB2bReplenishment(models.Model):
    _name = 'wayfair.b2b.replenishment'
    _description = 'Wayfair B2B Replenishment'
    _rec_name = 'purchase_order'
    
    purchase_order = fields.Char("Supplier PO")
    product_number = fields.Char("Part Number")
    quantity = fields.Char("Quantity")
    item_wholesale_price_eur = fields.Char("Item Wholesale EUR")
    item_cube = fields.Char("Item Cube")
    item_weight = fields.Char("Item Weight")
    source_warehouse = fields.Char("Source")
    destination_warehouse = fields.Char("Desitnation Warehouse")

    wayfair_b2b_shop_id = fields.Many2one("wayfair.b2b.shop", "Shop", readonly=True)
    product_id = fields.Many2one("product.product", "Product", readonly=True)
    picking_id = fields.Many2one("stock.picking", "Delivery", readonly=True)
    warehouse_id = fields.Many2one("stock.warehouse", "Warehouse", readonly=True)


    def create(self, vals):
        res = super(WayfairB2bReplenishment, self).create(vals)
        if res._context['import_file']:
            shop_id = self.env['wayfair.b2b.shop'].search([('id', '=', res._context.get('active_id'))])
            for order in res:
                if shop_id:
                    order.wayfair_b2b_shop_id = shop_id
                if order.product_number:
                    order.product_id = self.env['product.product'].search([('default_code', 'in', [order.product_number])])
                if order.destination_warehouse:
                    if order.destination_warehouse == "	UK - Mallow":
                        order.warehouse_id = self.env['stock.warehouse'].search([('code', '=', 'CGUK')])
        return res


    def map_with_bulk_order(self):
        # Group Different PO's seprately 
        group_po = {}
        for po_line in self:
            if po_line.product_id:
                if not group_po.get(po_line.purchase_order):
                    group_po[po_line.purchase_order] = [po_line]
                else:
                    group_po[po_line.purchase_order].append(po_line)

        # Create Group Replishment POs 
        picking_obj = self.env['stock.picking']
        for group in group_po.keys():
            lines=[]
            stock_picking_type_id = False
            picking_id = False
            existing_picking_id = False
            name= False
            for order_line in group_po[group]:
                existing_picking_id = picking_obj.search([('name', '=', order_line.purchase_order)])

                if not stock_picking_type_id:
                    if order_line.source_warehouse and order_line.destination_warehouse:
                        if order_line.wayfair_b2b_shop_id.stock_picking_type_id:
                            stock_picking_type_id = order_line.wayfair_b2b_shop_id.stock_picking_type_id

                if not existing_picking_id:
                    if not name:
                        if order_line.purchase_order:
                            name= order_line.purchase_order

                    if order_line.product_id and stock_picking_type_id:
                        # Create Stock Move Lines
                        lines +=  [(0,0, {
                                    'name': order_line.product_id.default_code,
                                    'product_id': order_line.product_id.id,
                                    'product_uom_qty': int(order_line.quantity),
                                    'product_uom': order_line.product_id.uom_id.id,
                                    'location_id': stock_picking_type_id.default_location_src_id.id,
                                    'location_dest_id': stock_picking_type_id.default_location_dest_id.id,
                                })]
                else:
                    if order_line.product_id and stock_picking_type_id:
                        # Create Stock Move Lines
                        skip = False
                        for stock_move in existing_picking_id.move_ids_without_package:
                            if stock_move.product_id == order_line.product_id:
                                skip = True
                                break 
                        if not skip:
                            lines +=  [(0,0, {
                                        'name': order_line.product_id.default_code,
                                        'product_id': order_line.product_id.id,
                                        'product_uom_qty': int(order_line.quantity),
                                        'product_uom': order_line.product_id.uom_id.id,
                                        'location_id': stock_picking_type_id.default_location_src_id.id,
                                        'location_dest_id': stock_picking_type_id.default_location_dest_id.id,
                                    })]

            # Create Delivery 
            if stock_picking_type_id:
                if not existing_picking_id:
                    try:
                        picking_id = picking_obj.create({
                            "name": name,
                            "move_ids_without_package": lines,
                            "picking_type_id": stock_picking_type_id.id if stock_picking_type_id else False,
                            "move_type": "direct",
                            "location_id": stock_picking_type_id.default_location_src_id.id,
                            "location_dest_id": stock_picking_type_id.default_location_dest_id.id,
                        })
                        for order_line in group_po[group]:
                            order_line.picking_id = picking_id
                    except Exception as err:
                        _logger.info("Replenishment error ~~~  %r ~~~", err)
                else:
                    try:
                        picking_id = existing_picking_id.write({
                            "move_ids_without_package": lines,
                        })
                        for order_line in group_po[group]:
                            order_line.picking_id = existing_picking_id.id
                    except Exception as err:
                        _logger.info("Replenishment error ~~~  %r ~~~", err)
            else:
                _logger.info("Replenishment method is not selected in the shop.")



        