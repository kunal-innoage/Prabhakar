from odoo import api, fields, models
import logging
_logger = logging.getLogger(__name__)


class MarketPlaceOrderTracking(models.Model):
    _inherit = 'marketplace.order.tracking'
    

    @api.model_create_multi
    def create(self, vals):
        res = super(MarketPlaceOrderTracking, self).create(vals)
        for tracking_order in res:
            order_export_id = self.env['processed.order'].search([('order_id', '=', tracking_order.order)])
            if order_export_id.sale_order_id.manomano_order_id:
                tracking_order.marketplace = order_export_id.sale_order_id.manomano_shop_id.name
        return res

    def is_empty_picking_id(self, order, product, picking_id):
        for picking in order.sale_order_id.picking_ids:
            if not picking.shipping_tracking or not picking.mirakl_carrier_name or not picking.shipping_tracking_url:
                if picking.id == picking_id:
                    return True
        return False 

    def check_for_high_quantity(self, order, product):
        count = 0
        for line in order.sale_order_id.order_line:
            if line.product_id == product:
                count +=1
        if count >1:
            return True
        for line in order.sale_order_id.order_line:
            if line.product_id == product:
                if line.product_uom_qty > 1:
                    return True
                else:
                    return False
            else:
                continue
    
    def update_tracking_info(self):
        res =  super(MarketPlaceOrderTracking, self).update_tracking_info()

        for order in self:
            order_export_id = self.env['processed.order'].search(['|',('order_id', '=', order.order),('order_id','ilike',order.order + '-')],limit=1)
            order.sale_order_id = order_export_id.sale_order_id

            if len(order.sale_order_id) > 0 and order.sale_order_id.manomano_order_id:
                if len(order.sale_order_id.picking_ids) > 0:
                    for picking in order.sale_order_id.picking_ids:
                        
                        order.picking_id = picking.id
                        carrier_id = self.env['manomano.carrier'].search([('shop_id', 'in', [order.sale_order_id.manomano_shop_id.id]),('code', '=', order.carrier)])
                        
                        if len(carrier_id) >0:
                            if self.warehouse_id.warehouse_code == "CDISC":
                                if self.check_for_high_quantity(order, order_export_id.product_id):
                                    if self.is_empty_picking_id(order, order_export_id.product_id, picking.id):
                                        picking.shipping_tracking = order.tracking_code
                                        picking.shipping_tracking_url = carrier_id.tracking_url.replace('{trackingId}',str(order.tracking_code))
                                        if not order.tracking_url:
                                            order.tracking_url = picking.shipping_tracking_url
                                        picking.mirakl_carrier_name = carrier_id.label
                                        picking.mirakl_carrier_code = carrier_id.code
                                        order.picking_id = picking.id
                                        break
                                    else:
                                        continue
                                else:
                                    picking.shipping_tracking = order.tracking_code
                                    picking.shipping_tracking_url = carrier_id.tracking_url.replace('{trackingId}',str(order.tracking_code))
                                    if not order.tracking_url:
                                            order.tracking_url = picking.shipping_tracking_url
                                    picking.mirakl_carrier_name = carrier_id.label
                                    picking.mirakl_carrier_code = carrier_id.code
                                    order.picking_id = picking.id
                                    break
                            if self.warehouse_id.warehouse_code == "ETL":
                                if self.check_for_high_quantity(order, order_export_id.product_id):
                                    if self.is_empty_picking_id(order, order_export_id.product_id, picking.id):
                                        picking.shipping_tracking = order.tracking_code
                                        picking.shipping_tracking_url = carrier_id.tracking_url.replace('{trackingId}',str(order.tracking_code))
                                        if not order.tracking_url:
                                            order.tracking_url = picking.shipping_tracking_url
                                        picking.mirakl_carrier_name = carrier_id.label
                                        picking.mirakl_carrier_code = carrier_id.code
                                        order.picking_id = picking.id
                                        break
                                    else:
                                        continue
                                else:
                                    picking.shipping_tracking = order.tracking_code
                                    picking.shipping_tracking_url = carrier_id.tracking_url.replace('{trackingId}',str(order.tracking_code))
                                    if not order.tracking_url:
                                            order.tracking_url = picking.shipping_tracking_url
                                    picking.mirakl_carrier_name = carrier_id.label
                                    picking.mirakl_carrier_code = carrier_id.code
                                    order.picking_id = picking.id
                                    break  
        
        return res
