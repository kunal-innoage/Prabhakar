from odoo import fields , models 
# from odoo.fields import Datetime
from odoo.fields import Datetime
from datetime import datetime, timedelta
import logging
import datetime
from odoo.tools import float_compare
_logger = logging.getLogger(__name__)


class PurchaseStockAnalysis(models.Model):
    _name="purchase.analysis"
    _description="Purchase Stock analysis"
    _rec_name="sku"

    sku=fields.Char("Products/SKU")
    ltm_avg = fields.Float("LTM AVG.")
    l9m_avg = fields.Float("L9M AVG.")
    l6m_avg = fields.Float("L6M AVG.")
    l3m_avg = fields.Float("L3M AVG.")
    lm_avg = fields.Float("LM AVG.")
    avg = fields.Float("AVERAGE")
    var1 = fields.Float("VAR 1")
    var2 = fields.Float("VAR 2")
    var3 = fields.Float("VAR 3")
    var4 = fields.Float("VAR 4")
    current_stock = fields.Float("Current Stock")
    qty_on_po = fields.Float("QTY ON P.O (NOT RECEIVED)")
    net_stock = fields.Float("NET STOCK")
    stock_8weeks = fields.Float("STOCK(8 Weeks)")
    lead_time = fields.Float("LEAD TIME +SHIPPING  (STOCK)")
    order_quantity = fields.Float("ORDER QUANTITY")
    increased_stock = fields.Float("INCREASED Stock")
    date_of_first_receipt = fields.Date("Date of first recipt")
    age_of_stock = fields.Float("AGE (MONTHS)")
    alert = fields.Float("ALERT")
    warehouse_id = fields.Many2one("stock.warehouse" , "Warehouse ID" )
    product_id = fields.Many2one("product.product", "Product ID")


    def assign_warehouse(self):
        for rec in self:
            if rec.product_id:
                warehouses = self.env['stock.warehouse'].search([ ])
                for warehouse in warehouses:
                    


    # LTM sales

    def _compute_last_twelve_month_sales(self):
        for rec in self:
            if rec.product_id:
                _logger.info("QUANTITY ORDERED~~~~~~~~~~~~  %r ,...........",rec.product_id)
                period = ( datetime.datetime.now().date() - datetime.timedelta(days=365) )
                order_line_ids = self.env['sale.order.line'].search([("product_id" , "=" , rec.product_id.id),("order_id.date_order" , ">" , period),('warehouse_id', '=', rec.warehouse_id.id)])
                # order_line_ids = self.env['sale.order'].search([("product_id" , "=" , rec.product_id.id),("warehouse_id" , '=', "Cella IW (ETL) Logistik Center GmbH"),("order_id.date_order",">", period)])
                _logger.info("TOTAL~~~~~~~~~~~~~~~~ %r , ~~~~~~~~~~~~~~~~~~",order_line_ids)
                total_ordered_qty = 0
                for line in order_line_ids: 
                    total_ordered_qty += line.product_uom_qty
                    _logger.info("UOM~~~~~~~~~~~~~~~~ %r , ~~~~~~~~~~~~~~~~~~",line.warehouse_id, rec.warehouse_id)
                    rec.ltm_avg = total_ordered_qty / 12
                if not len(order_line_ids) > 0:
                    rec.ltm_avg = False 
            else:
                rec.ltm_avg = False

    # L9M sales

    def _compute_last_nine_month_sales(self):
        for rec in self:
            if rec.product_id:
                _logger.info("QUANTITY ORDERED~~~~~~~~~~~~  %r ,...........",rec.product_id)
                period = ( datetime.datetime.now().date() - datetime.timedelta(days=273) )
                order_line_ids = self.env['sale.order.line'].search([("product_id" , "=" , rec.product_id.id),("order_id.date_order" , ">" , period)])
                # order_line_ids = self.env['sale.order'].search([("product_id" , "=" , rec.product_id.id),("warehouse_id" , '=', "Cella IW (ETL) Logistik Center GmbH"),("order_id.date_order",">", period)])
                _logger.info("TOTAL~~~~~~~~~~~~~~~~ %r , ~~~~~~~~~~~~~~~~~~",order_line_ids)
                total_ordered_qty = 0
                for line in order_line_ids: 
                    total_ordered_qty += line.product_uom_qty
                    _logger.info("UOM~~~~~~~~~~~~~~~~ %r , ~~~~~~~~~~~~~~~~~~",total_ordered_qty)
                    rec.l9m_avg = total_ordered_qty / 9
                if not len(order_line_ids) > 0:
                    rec.l9m_avg = False 
            else:
                rec.l9m_avg = False

    # L6M sales

    def _compute_last_six_month_sales(self):
        for rec in self:
            if rec.product_id:
                _logger.info("QUANTITY ORDERED~~~~~~~~~~~~  %r ,...........",rec.product_id)
                period = ( datetime.datetime.now().date() - datetime.timedelta(days=182) )
                order_line_ids = self.env['sale.order.line'].search([("product_id" , "=" , rec.product_id.id),("order_id.date_order" , ">" , period)])
                # order_line_ids = self.env['sale.order'].search([("product_id" , "=" , rec.product_id.id),("warehouse_id" , '=', "Cella IW (ETL) Logistik Center GmbH"),("order_id.date_order",">", period)])
                _logger.info("TOTAL~~~~~~~~~~~~~~~~ %r , ~~~~~~~~~~~~~~~~~~",order_line_ids)
                total_ordered_qty = 0
                for line in order_line_ids: 
                    total_ordered_qty += line.product_uom_qty
                    _logger.info("UOM~~~~~~~~~~~~~~~~ %r , ~~~~~~~~~~~~~~~~~~",total_ordered_qty)
                    rec.l6m_avg = total_ordered_qty / 6
                if not len(order_line_ids) > 0:
                    rec.l6m_avg = False 
            else:
                rec.l6m_avg = False



