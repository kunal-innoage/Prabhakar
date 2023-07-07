from odoo import api, fields, models


class MarketPlaceOrderTracking(models.Model):
    _inherit = 'marketplace.order.tracking'
    
    picking_id = fields.Many2one("stock.picking", "Odoo Delivery")

    @api.model_create_multi
    def create(self, vals):
        res = super(MarketPlaceOrderTracking, self).create(vals)
        for tracking_order in res:
            order_export_id = self.env['processed.order'].search([('order_id', '=', tracking_order.order)])
            if order_export_id.sale_order_id.cdiscount_order_id:
                tracking_order.marketplace = order_export_id.sale_order_id.cdiscount_shop_id.name
        return res

    def is_empty_picking_id(self, order, product, picking_id):
        for picking in order.sale_order_id.picking_ids:
            # if product == picking.move_line_ids_without_package[0].product_id:
            if not picking.shipping_tracking or not picking.mirakl_carrier_name or not picking.shipping_tracking_url:
                if picking.id == picking_id:
                    return True
            # else:
            #     continue
        return False 

    def update_tracking_info(self):

        #Tracking info code for orders from Cdiscount Portal. Overriding Mirakl method to use same functionality

        for order in self:
            order_export_id = self.env['processed.order'].search(['|',('order_id', '=', order.order),('order_id','ilike',order.order + '-')],limit=1)
            order.sale_order_id = order_export_id.sale_order_id
            if len(order.sale_order_id) > 0 and order.sale_order_id.cdiscount_order_id:
                carrier_id = self.env['cdiscount.carrier'].search([('label', '=', order.carrier)],limit=1)
                if len(carrier_id) > 0:
                    if len(order.sale_order_id.picking_ids) > 0:
                        for picking in order.sale_order_id.picking_ids:
                            order.picking_id = picking.id
                            if self.warehouse_id.warehouse_code == "ETL":
                                if self.is_empty_picking_id(order, order_export_id.product_id, picking.id):
                                    picking.shipping_tracking = order.tracking_code
                                    picking.shipping_tracking_url = (carrier_id.tracking_url if carrier_id.tracking_url else '')  + (order.tracking_code if order.tracking_code else '')
                                    picking.mirakl_carrier_name = order.carrier
                                    break
                                else:
                                    continue
        return super(MarketPlaceOrderTracking, self).update_tracking_info()
        
