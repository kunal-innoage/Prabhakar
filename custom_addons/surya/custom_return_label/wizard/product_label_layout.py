from odoo import models,fields,_
from odoo.exceptions import UserError
from asyncio.log import logger

class ProductLabelReturn(models.TransientModel):
    _inherit = 'product.label.layout'

    print_format = fields.Selection([
        ('dymo', 'Return Label'),], string="Format", default='dymo', required=True)
    
    picking_quantity = fields.Selection([
        ('custom', 'Custom')], string="Quantity to print", required=True, default='custom')
    

    def _prepare_report_data(self):
        if self.custom_quantity <= 0:
            raise UserError(_('You need to set a positive quantity.'))

        # Get layout grid
        if self.print_format == 'dymo':
            xml_id = 'product.report_product_template_label_dymo'
        elif 'x' in self.print_format:
            xml_id = 'product.report_product_template_label'
        else:
            xml_id = ''

        active_model = ''
        if self.product_tmpl_ids:
            products = self.product_tmpl_ids.ids
            active_model = 'product.template'
        elif self.product_ids:
            products = self.product_ids.ids
            active_model = 'product.product'
        else:
            raise UserError(_("No product to print, if the product is archived please unarchive it before printing its label."))
        
        #Add Picking Data
        if self.env.context and self.env.context.get('active_model'):
            if self.env.context.get('active_model') == 'stock.picking':
                picking = self.env['stock.picking'].search([('id','=',self.env.context.get('active_id'))])
                marketplace, order_number = self.get_order_data(picking)
        # Build data to pass to the report
        data = {
            'active_model': active_model,
            'quantity_by_product': {p: self.custom_quantity for p in products},
            'layout_wizard': self.id,
            'price_included': 'xprice' in self.print_format,
        }
        if order_number and marketplace:
            data['marketplace'] = marketplace
            data['order_number'] = order_number
            data['customer'] = picking.sale_id.partner_shipping_id.name
        return xml_id, data
    

    def get_order_data(self, picking):
        marketplace = orderNumber = False
        if picking.sale_id:
            #check marketplace name
            order = picking.sale_id

            if order.mirakl_order_id:
                orderNumber = order.mirakl_order_id

            if order.amazon_order_id:
                orderNumber = order.amazon_order_id

            if order.wayfair_order_id:
                orderNumber = order.wayfair_order_id
                
            if order.cdiscount_order_id:
                orderNumber = order.cdiscount_order_id
            
            if order.retail_order_id:
                orderNumber = order.retail_order_id
            
            marketplace = order.market_place_shop
            return marketplace,orderNumber

        else:
            logger.info("Related order data not found")
            return False,False
