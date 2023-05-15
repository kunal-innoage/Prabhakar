from odoo import fields , models 
from odoo.fields import Datetime
from datetime import datetime, timedelta

import logging
_logger = logging.getLogger(__name__)


class MarketplaceWarehouse(models.Model):
    _inherit = "marketplace.warehouse"

    stock_analysis_mapped = fields.Boolean("Stock Aanalysis Mapped", default = False)

    def purchase_stock_analysis_action(self):
        # _logger.info("~~~~~~~~~~~~  %r ,...........",self)
        for warehouse in self:
            # warehouse.purchase_stock_mapping_action()
            return {
                    'type': 'ir.actions.act_window',                                            
                    'name': ("Stock Analysis" ),
                    'view_mode': 'list,form',
                    'res_model': 'purchase.analysis',
                    # domain warehouse_id
                }
         
    def purchase_stock_mapping_action(self):
        for rec in self:
            if rec.warehouse_id:
                # date filter_ 
                products = self.env['warehouse.inventory'].search([('warehouse_id','=', rec.id)])
                _logger.info("~~~~~~~~~~~~  %r ,...........",products)
                rec.stock_analysis_mapped = True
                for product in products:

                    prod_id = self.env['purchase.analysis'].search([('sku','=',product.odoo_product_id.default_code),('create_date', '>=', Datetime.to_string(Datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)))])
                    # _logger.info("~~~~~~~~~~~~  %r ,...........",prod_id)

                    if not prod_id:
                        product_current_stock = self.env['purchase.analysis'].create({
                            'sku': product.odoo_product_id.default_code,
                            'current_stock': product.available_stock_count,
                            'product_id': product.odoo_product_id.id,
                            'warehouse_id': product. 
                        })
                        _logger.info("CREATED~~~~~~~~~~~~  %r ,...........",product_current_stock)
                        
                    else:
                        prod_id.current_stock = product.available_stock_count
                        prod_id.product_id = product.odoo_product_id.id

    
    




    

    
