from odoo import fields , models 
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import logging
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
    avg = fields.Float("SALES AVERAGE")
    var1 = fields.Float("VAR 1")
    var2 = fields.Float("VAR 2")
    var3 = fields.Float("VAR 3")
    var4 = fields.Float("VAR 4")
    current_stock = fields.Float("CURRENT STOCK")
    qty_on_po = fields.Float("UPCOMING STOCK")
    net_stock = fields.Float("CURRENT + UPCOMING STOCK")
    stock_8weeks = fields.Float("STOCK(8 Weeks)")
    lead_time = fields.Float("LEAD TIME +SHIPPING  (STOCK)")
    order_quantity = fields.Float("ORDER QUANTITY")
    sales_span_stock = fields.Selection([('moving','MOVING'),('non_moving','NON-MOVING'),('slow_moving','SLOW-MOVING')],"Moving , Non-Moving SKUs")
    date_of_first_receipt = fields.Date("Date of first recipt")
    age_of_stock = fields.Integer("AGE (MONTHS)")
    alert = fields.Selection([('excess','EXCESS'),('place_order','PLACE ORDER')])
    warehouse_id = fields.Many2one("stock.warehouse" , "Warehouse" )
    product_id = fields.Many2one("product.product", "Product ID")



    # LTM sales

    def _compute_last_twelve_month_sales(self):
        for rec in self:
            if rec.product_id:
                period = ( datetime.now().date() - timedelta(days=365) )
                order_line_ids = self.env['sale.order.line'].search([("product_id" , "=" , rec.product_id.id),("order_id.date_order" , ">" , period),("warehouse_id","=", rec.warehouse_id.id )])
                total_ordered_qty = 0
                for line in order_line_ids: 
                    total_ordered_qty += line.product_uom_qty
                    rec.ltm_avg = total_ordered_qty / 12
                if not len(order_line_ids) > 0:
                    rec.ltm_avg = False 
            else:
                rec.ltm_avg = False

    # L9M sales

    def _compute_last_nine_month_sales(self):
        for rec in self:
            if rec.product_id:
                period = ( datetime.now().date() - timedelta(days=275) )
                order_line_ids = self.env['sale.order.line'].search([("product_id" , "=" , rec.product_id.id),("order_id.date_order" , ">" , period),("warehouse_id","=", rec.warehouse_id.id )])
                total_ordered_qty = 0
                for line in order_line_ids: 
                    total_ordered_qty += line.product_uom_qty
                    rec.l9m_avg = total_ordered_qty / 9
                if not len(order_line_ids) > 0:
                    rec.l9m_avg = False 
            else:
                rec.l9m_avg = False

    # L6M sales

    def _compute_last_six_month_sales(self):
        for rec in self:
            if rec.product_id:
                period = ( datetime.now().date() - timedelta(days=183) )
                order_line_ids = self.env['sale.order.line'].search([("product_id" , "=" , rec.product_id.id),("order_id.date_order" , ">" , period),("warehouse_id","=", rec.warehouse_id.id )])
                total_ordered_qty = 0
                for line in order_line_ids: 
                    total_ordered_qty += line.product_uom_qty
                    rec.l6m_avg = total_ordered_qty / 6
                if not len(order_line_ids) > 0:
                    rec.l6m_avg = False 
            else:
                rec.l6m_avg = False

    # L3M sales

    def _compute_last_three_month_sales(self):
        for rec in self:
            if rec.product_id:
                period = ( datetime.now().date() - timedelta(days=92) )
                order_line_ids = self.env['sale.order.line'].search([("product_id" , "=" , rec.product_id.id),("order_id.date_order" , ">" , period),("warehouse_id","=", rec.warehouse_id.id )])
                # order_line_ids = self.env['sale.order'].search([("product_id" , "=" , rec.product_id.id),("warehouse_id" , '=', "Cella IW (ETL) Logistik Center GmbH"),("order_id.date_order",">", period)])
                total_ordered_qty = 0
                for line in order_line_ids: 
                    total_ordered_qty += line.product_uom_qty
                    rec.l3m_avg = total_ordered_qty / 3
                if not len(order_line_ids) > 0:
                    rec.l3m_avg = False 
            else:
                rec.l3m_avg = False

    # LM sales

    def _compute_last_month_sales(self):
        for rec in self:
            if rec.product_id:
                period = ( datetime.now().date() - timedelta(days=31) )
                order_line_ids = self.env['sale.order.line'].search([("product_id" , "=" , rec.product_id.id),("order_id.date_order" , ">" , period),("warehouse_id","=", rec.warehouse_id.id )])
                total_ordered_qty = 0
                for line in order_line_ids: 
                    total_ordered_qty += line.product_uom_qty
                    rec.lm_avg = total_ordered_qty
                if not len(order_line_ids) > 0:
                    rec.lm_avg = False 
            else:
                rec.lm_avg = False

    # AVERAGE SALES

    def calculate_average(self):

        for record in self:
            if record.age_of_stock:
                age = record.age_of_stock
                if age < 3:
                    average = record.lm_avg
                elif age < 6:
                    average = (record.l6m_avg  + record.l3m_avg  )/2
                elif age < 9:
                    average = (record.l9m_avg + record.l6m_avg  + record.l3m_avg  )/3
                else:
                    average = (record.ltm_avg + record.l9m_avg + record.l6m_avg  + record.l3m_avg  )/4
            else:
                average = record.lm_avg
            record.avg = average
                

    # VARIANCE (LTM - L9M)

    def _compute_variance_twelve_and_nine_months(self):
        for record in self:
            try:
                record.var1 = (record.ltm_avg - record.l9m_avg)/record.l9m_avg
            except:
                record.var1 == 0
            

    # VARIANCE (L9M - L6M)
    
    def _compute_variance_nine_and_six_months(self):
        for record in self:
            try:
                record.var2 = (record.l9m_avg - record.l6m_avg)/record.l6m_avg
            except:
                record.var2 == 0

    # VARIANCE (L6M - L3M)
    
    def _compute_variance_six_and_three_months(self):
        for record in self:
            try:
                record.var3 = (record.l6m_avg - record.l3m_avg)/record.l3m_avg
            except:
                record.var3 == 0
                

    # VARIANCE (L3M - LM)
    
    def _compute_variance_three_and_last_months(self):
        for record in self:
            try:
                record.var4 = (record.l3m_avg - record.lm_avg)/record.lm_avg
            except:
                record.var4 == 0
                

    # QTY ON PO

    def _compute_quantity_on_po(self):
        for record in self:
            total_qty_ordered = 0
            total_qty_rec = 0
            orders = self.env['purchase.report'].search([('picking_type_id','=',record.warehouse_id.id),("product_id","=", record.product_id.id),('state', 'not in', ['done', 'cancel'])])
            for order in orders:
                total_qty_ordered += order.qty_ordered     
                total_qty_rec += order.qty_received
          
                record.qty_on_po = total_qty_ordered - total_qty_rec
           
        
   
        
    # NET STOCK

    def net_stock_purchase_analysis(self):
        for record in self:
            record.net_stock = record.current_stock + record.qty_on_po

    # STOCK(8 Weeks)

    def stocks_eight_weeks(self):
        for record in self:
            record.stock_8weeks = 2* record.avg

    # LEAD TIME +SHIPPING  (STOCK)

    def lead_time_shipping_stock(self):
        for record in self:
            record.lead_time = 2* record.avg

    # Order Quantity

    def order_quantity_stock(self):
        for record in self:
            record.order_quantity = round((record.stock_8weeks + record.lead_time) - record.net_stock)

    # Alert

    def alert_for_quantity(self):
        for record in self:
            if record.order_quantity > 0:
                record.alert = "place_order"
            
            else :
                record.alert = "excess"
                
    # AGE (MONTHS)

    def calculate_age_of_stocks_in_months(self):
        for rec in self:
                if not rec.date_of_first_receipt:
                    prod_ext_id = self.env["purchase.extension"].search([('sku','=', 'rec.sku')], limit=1)
                    if prod_ext_id:
                        rec.date_of_first_receipt = prod_ext_id.date_of_first_receipt
                if rec.date_of_first_receipt:
                    date_of_first_receipt = datetime.strptime(str(rec.date_of_first_receipt), '%Y-%m-%d')
                    today = datetime.now().date()
                    age = relativedelta(today, date_of_first_receipt)
                    age_in_months = age.years * 12 + age.months

                    rec.age_of_stock = age_in_months
                
    # date of first receipt and increased_stock
        
    def map_date_of_first_receipt_and_increased_stock(self):

        for rec in self:
            rec.ensure_one()
            rec_id = self.env["purchase.extension"].search([('sku', '=', rec.sku),('warehouse', '=' , rec.warehouse_id.code)])
            if rec_id:
                # rec.date_of_first_receipt = rec_id.date_of_first_receipt
                rec.date_of_first_receipt = rec_id.date_of_first_receipt
            
                # rec.increased_stock = rec_id.increased_stock
            else:
                rec.date_of_first_receipt = None    
                # rec.increased_stock = None    
                
    # MAPPING WHETHER THE STOCK IS MOVING OR NOT
    
    def map_whether_the_stock_is_moving_or_not(self):
        for rec in self :
            if rec.age_of_stock >= 6:
                if rec.ltm_avg == 0:
                    if rec.l3m_avg == 0:
                        if rec.l6m_avg == 0:
                            if rec.l9m_avg ==0:
                                if rec.lm_avg ==0:
                                    if rec.avg == 0:
                                        rec.sales_span_stock = 'non_moving'
                                    else:
                                        rec.sales_span_stock = 'moving'
                                else:
                                    rec.sales_span_stock = 'moving'
                            else:
                                rec.sales_span_stock = 'moving'
                        else:
                            rec.sales_span_stock = 'moving'
                    else:
                        rec.sales_span_stock = 'moving'
                else:
                    rec.sales_span_stock = 'moving'
            else:
                rec.sales_span_stock = 'moving'
                                        
                            
                
    # MAPPING Average

    def mapping_till_last_tweleve_month_average(self):
        for rec in self:
            rec._compute_last_twelve_month_sales()
            rec._compute_last_nine_month_sales()
            rec._compute_last_six_month_sales()
            rec._compute_last_three_month_sales()
            rec._compute_last_month_sales()
            rec.calculate_average()

    # Mapping Variance

    def mapping_till_last_tweleve_month_variance(self):
        for rec in self:
            rec._compute_variance_twelve_and_nine_months()
            rec._compute_variance_nine_and_six_months()
            rec._compute_variance_six_and_three_months()
            rec._compute_variance_three_and_last_months()

    # MAPPING REMAINING FIELDS

    def mapping_stock_order_quantity(self):
        for rec in self:
            rec.map_date_of_first_receipt_and_increased_stock()
            rec.calculate_age_of_stocks_in_months()
            rec._compute_quantity_on_po()
            rec.net_stock_purchase_analysis()
            rec.stocks_eight_weeks()
            rec.lead_time_shipping_stock()
            rec.order_quantity_stock()
            rec.alert_for_quantity()
            rec.map_whether_the_stock_is_moving_or_not()

    # MAPPING ALL FIELDS AT ONCE

    def mapping_sales_stock_analysis(self):
        for rec in self:
            rec.map_date_of_first_receipt_and_increased_stock()
            rec.calculate_age_of_stocks_in_months()
            rec._compute_last_twelve_month_sales()
            rec._compute_last_nine_month_sales()
            rec._compute_last_six_month_sales()
            rec._compute_last_three_month_sales()
            rec._compute_last_month_sales()
            rec.calculate_average()
            rec._compute_variance_twelve_and_nine_months()
            rec._compute_variance_nine_and_six_months()
            rec._compute_variance_six_and_three_months()
            rec._compute_variance_three_and_last_months()
            rec._compute_quantity_on_po()
            rec.net_stock_purchase_analysis()
            rec.stocks_eight_weeks()
            rec.lead_time_shipping_stock()
            rec.order_quantity_stock()
            rec.alert_for_quantity()
            rec.map_whether_the_stock_is_moving_or_not()
