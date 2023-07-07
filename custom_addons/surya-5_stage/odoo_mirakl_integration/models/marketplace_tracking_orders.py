# -*- coding: utf-8 -*-

from odoo import fields, models, _, api
import datetime
import pytz
from odoo.tools import float_compare

import logging
_logger = logging.getLogger(__name__)


class MarketpalceOrderTracking(models.Model):
    _name = "marketplace.order.tracking"
    _description = "Marketplace Order Tracking"
    _rec_name = "order"

    order = fields.Char("Order")
    customer = fields.Char("Customer")
    tracking_code = fields.Char("Code")
    carrier = fields.Char("Carrier")
    tracking_url = fields.Char("Tracking URL")
    sale_order_id = fields.Many2one('sale.order', string='Sale Order')
    marketplace = fields.Char( 'Marketplace')
    processing_time = fields.Selection([
        ('first','First Half'),
        ('second','Second Half')
    ])
    warehouse_id = fields.Many2one("marketplace.warehouse", "Warehouse")
    tracking_date = fields.Datetime("Tracking Date")

    # C-discount Fields 
    order_number = fields.Char('Notre n° de commande')
    ean_number = fields.Char('EAN')
    product_reference = fields.Char('Votre référence produit')
    warehouse_sku = fields.Char('SKU')
    product_description = fields.Char('Libellé Produit')
    quantity_ordered = fields.Char('Quantité commandée')
    cdisc_tracking_url = fields.Char('Lien de suivi du colis')
    quantity_shipped = fields.Char('Quantité expédiée')
    


    def is_empty_picking_id(self, order, product, picking_id):
        for picking in order.sale_order_id.picking_ids:
            if product == picking.move_line_ids_without_package[0].product_id:
                if not picking.shipping_tracking or not picking.mirakl_carrier_name or not picking.mirakl_carrier_code:
                    if picking.id == picking_id:
                        return True
            else:
                continue
        return False 

    def check_for_high_quantity(self, order, product):
        for line in order.sale_order_id.order_line:
            if line.product_id == product:
                if line.product_uom_qty > 1:
                    return True
                else:
                    return False
            else:
                continue

    
    @api.model_create_multi
    def create(self, vals):
        res = super(MarketpalceOrderTracking, self).create(vals)
        if res._context.get('import_file'):
            processing_shift = None
            IST = pytz.timezone('Asia/Kolkata')
            time_now = datetime.datetime.strftime(datetime.datetime.now(IST), "%Y-%m-%d %H:%M:%S")
            if int(time_now.split(' ')[1][:2]) <= 19:
                processing_shift = 'first'
            else:
                processing_shift = 'second'
            date = datetime.datetime.now()
            warehouse = self.env['marketplace.warehouse'].search([('id', '=', res._context.get("active_id"))])
            for tracking_order in res:
                tracking_order.processing_time = processing_shift
                order_export_id = self.env['processed.order'].search([('order_id', '=', tracking_order.order)])
                if order_export_id.sale_order_id.mirakl_order_id:
                    tracking_order.marketplace = order_export_id.sale_order_id.mirakl_shop_id.name
                tracking_order.warehouse_id = warehouse
                tracking_order.tracking_date = date
        return res

    def update_tracking_info(self):
        for order in self:
            order_export_id = self.env['processed.order'].search([('order_id', '=', order.order)])
            order.sale_order_id = order_export_id.sale_order_id
            if len(order.sale_order_id) > 0:

                # IF for Mirakl Order ELIF for Non Mirakl and Non Cdiscount shop order
                if order.sale_order_id.mirakl_order_id:
                    if len(order.sale_order_id.picking_ids) > 0:
                        for picking in order.sale_order_id.picking_ids:
                            if len(picking.move_line_ids_without_package) == 1:
                                if picking.move_line_ids_without_package[0].product_id == order_export_id.product_id:
                                    carrier_id = self.env['mirakl.carrier'].search([('shop_id', 'in', [order.sale_order_id.mirakl_shop_id.id]), ('activate', '=', True)])
                                    
                                    # IF for CDISCOUNT Warehouse ELSE for ETL Warehouse
                                    if self.warehouse_id.warehouse_code == "CDISC":
                                        carrier_id = self.env['mirakl.carrier'].search([('shop_id', 'in', [order.sale_order_id.mirakl_shop_id.id]),('label', '=', order.carrier)])
                                        if len(carrier_id) > 0:
                                            if self.check_for_high_quantity(order, order_export_id.product_id):
                                                if self.is_empty_picking_id(order, order_export_id.product_id, picking.id):
                                                    picking.shipping_tracking = order.tracking_code
                                                    picking.shipping_tracking_url = carrier_id.tracking_url.replace('{trackingId}',str(order.tracking_code))
                                                    picking.mirakl_carrier_name = carrier_id.label
                                                    picking.mirakl_carrier_code = carrier_id.code
                                                    order.picking_id = picking.id
                                                    break
                                                else:
                                                    continue
                                            else:
                                                picking.shipping_tracking = order.tracking_code
                                                picking.shipping_tracking_url = carrier_id.tracking_url.replace('{trackingId}',str(order.tracking_code))
                                                picking.mirakl_carrier_name = carrier_id.label
                                                picking.mirakl_carrier_code = carrier_id.code
                                                order.picking_id = picking.id
                                                break                                        
                                    else:
                                        if len(carrier_id) > 0:
                                            if self.check_for_high_quantity(order, order_export_id.product_id):
                                                if self.is_empty_picking_id(order, order_export_id.product_id, picking.id):
                                                    picking.shipping_tracking = order.tracking_code
                                                    picking.shipping_tracking_url = carrier_id.tracking_url.replace('{trackingId}',str(order.tracking_code))
                                                    picking.mirakl_carrier_name = carrier_id.label
                                                    picking.mirakl_carrier_code = carrier_id.code
                                                    order.picking_id = picking.id
                                                    break
                                                else:
                                                    continue
                                            else:
                                                picking.shipping_tracking = order.tracking_code
                                                picking.shipping_tracking_url = carrier_id.tracking_url.replace('{trackingId}',str(order.tracking_code))
                                                picking.mirakl_carrier_name = carrier_id.label
                                                picking.mirakl_carrier_code = carrier_id.code
                                                order.picking_id = picking.id
                                                break                                        
                elif not order.sale_order_id.cdiscount_order_id:
                    order.sale_order_id.mirakl_order_state = "shipped"
                    if len(order.sale_order_id.picking_ids) > 0:
                        for delivery in order.sale_order_id.picking_ids:
                            if delivery.products_availability == "Available":
                                delivery.action_assign()
                                for move in delivery.move_lines.filtered(lambda m: m.state not in ["done", "cancel"]):
                                    rounding = move.product_id.uom_id.rounding
                                    if (
                                        float_compare(
                                            move.quantity_done,
                                            move.product_qty,
                                            precision_rounding=rounding,
                                        )
                                        == -1
                                    ):
                                        for move_line in move.move_line_ids:
                                            move_line.qty_done = move_line.product_uom_qty
                                delivery.shipping_tracking = order.sale_order_id.shipping_tracking if order.sale_order_id.shipping_tracking else False
                                delivery.shipping_tracking_url = order.sale_order_id.shipping_tracking_url if order.sale_order_id.shipping_tracking_url else False
                                delivery.mirakl_carrier_name = order.sale_order_id.shipping_carrier_code
                                delivery.with_context(skip_immediate=True, skip_sms=True).button_validate()
                                order.sale_order_id.invoice_status = 'to invoice'
