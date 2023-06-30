from odoo import fields , models
import logging
_logger = logging.getLogger(__name__)

class SkuExpenseAnalysis(models.Model):
    _name  = 'sku.expense.analysis' 
    _description = 'SKU Expense Analysis'
    _rec_name = 'product'
    
    product_id = fields.Many2one("marketplace.product","Product ID")
    product = fields.Char("Product")
    vat_inclusive = fields.Float("Vat Inclusive")
    vat_exclusive = fields.Float("Vat Exclusive")
    
    comission  = fields.Float("Comission")
    total_cogs  = fields.Integer("Total COGS")
    net_margin  = fields.Char("Net Margin")
    replenishment_period = fields.Integer("Replenishment Period (Months)")
    storage = fields.Float("Storage")
    pick_pack = fields.Float("Pick & Pack")
    adv_cost = fields.Float("Adv Cost")
    shipping_cost = fields.Float("Shipping Cost")
    salary_cost = fields.Float("Salary Cost")
    
    carrer_admin_cost = fields.Float("Carrer Admin Cost")
    
    shop_id = fields.Char("Shop")
    sale_order_line_ids = fields.One2many("sale.order.line", "expanse_product_id", "SALE ORDER LINES")
    
    # MIRAKL MARKETPLACE
     
    def mirakl_static_values(self):
        for rec in self:
            static_values = self.env["shop.integrator"].search([('name','=',rec.shop_id)])
            if static_values:
                rec.replenishment_period = static_values.replenishment_period
                rec.storage = static_values.storage
                rec.pick_pack = static_values.pick_pack
                rec.adv_cost = static_values.adv_cost
                rec.shipping_cost = static_values.shipping_cost
                rec.salary_cost = static_values.salary_cost
                rec.carrer_admin_cost = static_values.carrer_admin_cost
                rec.comission = static_values.comission 
    
    # CDISCOUNT MARKETPLACE
    
    def cdiscount_seller_static_values(self):
        for rec in self:
            static_values = self.env["cdiscount.seller"].search([('name','=',rec.shop_id)])
            if static_values:
                rec.replenishment_period = static_values.replenishment_period
                rec.storage = static_values.storage
                rec.pick_pack = static_values.pick_pack
                rec.adv_cost = static_values.adv_cost
                rec.shipping_cost = static_values.shipping_cost
                rec.salary_cost = static_values.salary_cost
                rec.carrer_admin_cost = static_values.carrer_admin_cost
                rec.comission = static_values.comission
                
    # MANOMANO MARKETPLACE    
    
    def manomano_seller_static_values(self):
        for rec in self:
            static_values = self.env["manomano.seller"].search([('name','=',rec.shop_id)])
            if static_values:
                rec.replenishment_period = static_values.replenishment_period
                rec.storage = static_values.storage
                rec.pick_pack = static_values.pick_pack
                rec.adv_cost = static_values.adv_cost
                rec.shipping_cost = static_values.shipping_cost
                rec.salary_cost = static_values.salary_cost
                rec.carrer_admin_cost = static_values.carrer_admin_cost
                rec.comission = static_values.comission
                
    def compute_commission(self):
        for rec in self:
            rec.comission = rec.vat_inclusive * rec.comission
            
    def compute_total_cogs(self):
        for rec in self:
            rec.total_cogs = rec.storage + rec.pick_pack + rec.adv_cost + rec.comission + rec.shipping_cost + rec.salary_cost + rec.carrer_admin_cost
            
    def compute_net_margin(self):
        for rec in self:
            try:
                net_margin = round((((rec.vat_exclusive - rec.total_cogs)/rec.vat_exclusive)*100))      
                rec.net_margin = f"{net_margin}%" 
            except:
                rec.net_margin == 0
            
    def cogs_mapping_server_action(self):
        for rec in self:
            if rec.sale_order_line_ids:
                for line in  rec.sale_order_line_ids:
                    line.total_cogs = rec.total_cogs * line.product_uom_qty 
        
    def mapping_all_static_fields(self):
        for rec in self:
            rec.mirakl_static_values()
            rec.cdiscount_seller_static_values()
            rec.manomano_seller_static_values()
            rec.compute_commission()
            rec.compute_total_cogs()
            rec.compute_net_margin()
            rec.cogs_mapping_server_action()

class MarketplaceProduct(models.Model):
    _inherit = "marketplace.product"
    
    def create_products(self):
        for rec in self:
            order_line_ids = self.env["sale.order.line"].search([('product_id', '=', rec.product_id.id)])
            _logger.info("~~~~~ORDER LINE IDS~~~~~~~~~~~%r~~~~~~~~~~~~",order_line_ids)
            shop_wise_ol = {}
            for line in order_line_ids:
                
                shop_name = line.order_id.market_place_shop
                if shop_name in shop_wise_ol.keys():
                    shop_wise_ol[shop_name] += [line]
                else:
                    shop_wise_ol[shop_name] = [line]
            _logger.info("~~~~~~~~SHOP WISE OL(AFTER) %r",shop_wise_ol)
            
            for shop in shop_wise_ol.keys():
                price_inclusive = 0.0
                price_exclusive = 0.0
                if shop not in ["Amazon UK","Amazon DE","Wayfair DS DE","Wayfair DS UK","Wayfair DS IE","Amazon FR B2B","Amazon DE B2B","Amazon UK B2B","Wayfair CG DE","Wayfair CG UK"]:
                    exp_product_id = self.env["sku.expense.analysis"].search([('product','=',rec.sku),("shop_id",'=',shop)],limit = 1)
                    if not exp_product_id:
                        exp_product_id = self.env["sku.expense.analysis"].create({
                            'product' : rec.sku,
                            'product_id' : rec.id,
                            'shop_id' : shop,
                        })
                    else:
                        _logger.info("~~~old_exp_id~~~~~~%r~~~~~~~~~~",exp_product_id)
                    
                    for line in shop_wise_ol[shop]:         
                        line.expanse_product_id = exp_product_id.id
                        price_inclusive += line.price_unit
                        price_exclusive += line.price_subtotal
                    _logger.info("~~~~~~~~~~EXCLUSIVE~~~%r",price_exclusive)
                    _logger.info("~~~~~~~~~~INCLUSIVE~~~%r",price_inclusive)    
                        
                    
                    if price_inclusive:
                        exp_product_id.vat_inclusive = price_inclusive / len(shop_wise_ol[shop])
                        _logger.info("~~~~~~~~exp_product_id.vat_inclusive    %r     %r   ...", exp_product_id.vat_inclusive, len(shop_wise_ol[shop]))
                        
                    if price_exclusive:
                        exp_product_id.vat_exclusive = price_exclusive / len(shop_wise_ol[shop])
                        _logger.info("~~~~~~~~exp_product_id.vat_exclusive    %r     %r   ...", exp_product_id.vat_exclusive, len(shop_wise_ol[shop]))


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    
    expanse_product_id = fields.Many2one("sku.expense.analysis","Expense Product")
    total_cogs = fields.Float(string="Total COGS")