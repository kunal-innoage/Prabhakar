from odoo import api, fields, models,_
import logging
from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    cdiscount_shop_id = fields.Many2one("cdiscount.seller",related = "sale_id.cdiscount_shop_id", string ="Cdiscount Shop")
    cdiscount_order_id = fields.Char("CDiscount Order")
    multi_line_data_updated = fields.Boolean("Multi line data updated")
    # single_line = fields.Boolean("Single Line Order", compute='_compute_order_lines',store=True)
    # multi_line_order = fields.Boolean("Multi Line Order",compute='_compute_order_lines', store=True)
    line_count = fields.Selection(selection=[('single', 'Single Line Order'), ('multi', 'Multi Line Order'),],compute='_compute_order_lines',store=True)

    @api.depends('cdiscount_order_id')
    def _compute_order_lines(self):
        so = []
        for rec in self:
            sale_order = self.env['sale.order'].search([('name','=',rec.origin)],limit=1)
            if len(rec.move_line_ids_without_package) > 0:
                if sale_order.warehouse_id.code != 'CDISC':
                    if not rec.origin in so:
                        so.append(rec.origin)
                        rec.line_count = 'single'
                    else:
                        #Multiline Order delivery found. Change status in every related delivery
                        for picking in sale_order.picking_ids:
                            picking.line_count = 'multi'
                else:
                    rec.line_count = False
            else:
                rec.line_count = False
            


class StockImmediateTransfer(models.TransientModel):
    _inherit = 'stock.immediate.transfer'



    def cdiscount_shipment_info_prepration(self, shipments):
        # Limitation of 1000 shipments
        shop = False
        picking_data = []
        for picking in shipments:
            count = 0
            if picking.sale_id.cdiscount_order_id and picking.sale_id.cdiscount_shop_id:
                if picking.shipping_tracking and picking.shipping_tracking_url and not picking.is_tracking_updated and picking.origin.startswith('S'): #startwith added to filer non returned order
                    if picking.line_count == 'single':
                        shipment_data = {
                            "carrierName": picking.mirakl_carrier_name,
                            "trackingUrl": picking.shipping_tracking_url,
                            "parcelNumber": picking.shipping_tracking,     
                            "orderLineIds": ["0"],   #TODO not clear in documentation
                        }
                        picking_data.append(shipment_data)
                        picking.is_tracking_updated = True
                        picking.sale_id.cdiscount_tracking_addded = True
                        shop = picking.sale_id.cdiscount_shop_id
                    else:
                        #Find all related deliveries and merge data at once
                        dls = self.env['stock.picking'].search([('origin','=',picking.origin)], order="name")
                        i = 0
                        for dl in dls:
                            if not picking.multi_line_data_updated:
                                shipment_data = {
                                    "carrierName": dl.mirakl_carrier_name,
                                    "trackingUrl": dl.shipping_tracking_url,
                                    "parcelNumber": dl.shipping_tracking,     
                                    "orderLineIds": [str(i)],   
                                }
                                i += 1
                                picking.multi_line_data_updated
                                picking_data.append(shipment_data)
                                picking.is_tracking_updated = True
                                picking.sale_id.cdiscount_tracking_addded = True
                                shop = picking.sale_id.cdiscount_shop_id
                        

                else:
                    if not picking.is_tracking_updated:
                        raise ValidationError(_("Please add tracking info inside the delivery -    %r  ;;;;;",picking.name))
                    else:
                        _logger.info(" ~~~~~~~ order shipment already updated on Cdiscount ______;;;;;;")
        return picking_data,shop


    def devide_per_order(self, pickings):
        order_wise_pickings = {}
        for picking in pickings:
            if picking.sale_id.cdiscount_order_id:
                if picking.sale_id.cdiscount_order_id not in order_wise_pickings.keys():
                    order_wise_pickings[picking.sale_id.cdiscount_order_id] = [picking]
                # else:
                #     _logger.info("only one cdiscount shipment can be send to cdsicount portal")
        return order_wise_pickings

    def process(self):
        order_wise_deliveries = self.devide_per_order(self.pick_ids) # Get delivery assigned to cdiscount order id. Only one delivery will be in case of cdiscount

        # Data Preparation & CDiscount Update

        if len(order_wise_deliveries) > 0:
            rejected_pickings = []
            for order in order_wise_deliveries.keys():
                if len(order_wise_deliveries[order]) > 0:
                    picking_data,shop = self.cdiscount_shipment_info_prepration(order_wise_deliveries[order])
                    if picking_data and shop:
                        rejected_picking = self.env['cdiscount.seller'].update_bulk_shipment_tracking(picking_data, order,shop)
                        if rejected_picking not in rejected_pickings:
                            rejected_pickings.append(rejected_picking)
                    else:
                        _logger.info("Shop data or tracking data missing from the delivery")
            # Remove Extra Pickings
            if rejected_pickings:
                picking_obj = self.env['stock.picking']
                for picking in self.pick_ids:
                    if picking.sale_id.cdiscount_order_id not in rejected_pickings:
                        picking_obj += picking
                    else:
                        picking.is_tracking_updated = False
                        picking.sale_id.cdiscount_tracking_addded = False
                self.pick_ids = picking_obj
                if not len(self.pick_ids) > 0:
                    _logger.info("Delivery for these CDiscount order cannot be validated %s", rejected_pickings)
                    return False
        else:
            _logger.info("No data found in cdiscount to send shipment")
            
        return super(StockImmediateTransfer, self).process()
