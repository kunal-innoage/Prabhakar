from odoo import fields , models  , _ , api
from odoo.fields import Datetime
from datetime import datetime, timedelta


import logging
_logger = logging.getLogger(__name__)


class MarketplaceWarehouse(models.Model):
    _inherit = "marketplace.warehouse"

    stock_analysis_mapped = fields.Boolean("Stock Aanalysis Mapped", default = False)


    def purchase_stock_analysis_action(self):
        for warehouse in self:
            warehouse.purchase_stock_mapping_action()
            return {
                    'type': 'ir.actions.act_window',                                            
                    'name': ("Stock Analysis" ),
                    'view_mode': 'list,form',
                    'res_model': 'purchase.analysis',
                    # 'domain': [('warehouse_id.id', '=', warehouse.id)],
                    'domain': [('warehouse_id.id', 'in', [self.warehouse_id.id])],
                    'context': {'search_default_group_by_date': 1,},

                    # domain warehouse_id
                }

    ###################################################
    # MAPPING INVENTORY UPDATE WITH PURCHASE ANALYSIS #
    ###################################################
    
    def purchase_stock_mapping_action(self):
        for rec in self:
                
            # if rec.warehouse_id:
                products = self.env['warehouse.inventory'].search([("warehouse_id","=",rec.id), ('create_date', '>=', Datetime.to_string(Datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)))], order='create_date desc')
                
                if products:
                    rec.stock_analysis_mapped = True
                    for product in products:

                        # prod_id = self.env['purchase.analysis'].search([('warehouse_id','=', rec.id),('sku','=',product.odoo_product_id.default_code),('create_date', '>=', Datetime.to_string(Datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)))])
                        prod_id = self.env['purchase.analysis'].search([('sku','=',product.odoo_product_id.default_code), ('create_date', '>=', Datetime.to_string(Datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)))] , order='create_date desc')

                        if not prod_id:
                            product_current_stock = self.env['purchase.analysis'].create({
                                'sku': product.odoo_product_id.default_code,
                                'current_stock': product.available_stock_count,
                                'product_id': product.odoo_product_id.id,
                                'warehouse_id': rec.warehouse_id.id,
                            })
                            
                        else:   
                            prod_id.current_stock = product.available_stock_count
                            prod_id.product_id = product.odoo_product_id.id
                            prod_id.warehouse_id = rec.warehouse_id.id
                        
                        # IF NOT CONDITION
                        
                if not products:
                    
                    yesterday = datetime.now().date() + timedelta(days=-1)
                    new_products = self.env['warehouse.inventory'].search([("warehouse_id","=",rec.id), ('create_date', '>=', yesterday )], order='create_date desc')
                    
                    rec.stock_analysis_mapped = True
                    for product in new_products:

                        prod_id = self.env['purchase.analysis'].search([('sku','=',product.odoo_product_id.default_code), ('create_date', '>=', Datetime.to_string(Datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)))] , order='create_date desc')

                        if not prod_id:
                            product_current_stock = self.env['purchase.analysis'].create({
                                'sku': product.odoo_product_id.default_code,
                                'current_stock': product.available_stock_count,
                                'product_id': product.odoo_product_id.id,
                                'warehouse_id': rec.warehouse_id.id,
                            })
                            
                        else:
                            prod_id.current_stock = product.available_stock_count
                            prod_id.product_id = product.odoo_product_id.id
                            prod_id.warehouse_id = rec.warehouse_id.id