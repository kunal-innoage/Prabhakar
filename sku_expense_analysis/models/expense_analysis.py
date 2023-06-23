from odoo import fields , models
import logging
_logger = logging.getLogger(__name__)

class SkuExpenseAnalysis(models.Model):
    _name  = 'sku.expense.analysis' 
    _description = 'SKU Expense Analysis'
    
    product_id = fields.Many2one("marketplace.product","Product ID")
    product = fields.Char("Product")
    vat_inclusive = fields.Float("Vat Inclusive")
    vat_exclusive = fields.Float("Vat Exclusive")
    comission  = fields.Float("Comission")
    total_cogs  = fields.Integer("Total COGS")
    net_margin  = fields.Integer("Net Margin")
    replenishment_period = fields.Integer("Replenishment Period (Months)")
    storage = fields.Float("Storage")
    pick_pack = fields.Float("Pick & Pack")
    adv_cost = fields.Float("Adv Cost")
    shipping_cost = fields.Float("Shipping Cost")
    salary_cost = fields.Float("Salary Cost")
    carrer_admin_cost = fields.Float("Carrer Admin Cost")
    shop_id = fields.Char("Shop")
    
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
            _logger.info("~~~~COMMISSION~~~~~~%r",static_values.comission)
                
    def compute_commission(self):
        for rec in self:
            rec.comission = rec.vat_inclusive * rec.comission
            
    def compute_total_cogs(self):
        for rec in self:
            rec.total_cogs = rec.storage + rec.pick_pack + rec.adv_cost + rec.comission + rec.shipping_cost + rec.salary_cost + rec.carrer_admin_cost
            # _logger.info("~~~~COMMISSION~~~~~~%r",rec.total_cogs)
            
            
                
    def mapping_all_static_fields(self):
        for rec in self:
            rec.mirakl_static_values()
            rec.cdiscount_seller_static_values()
            rec.manomano_seller_static_values()
            rec.compute_commission()
            rec.compute_total_cogs()

            

class MarketplaceProduct(models.Model):
    _inherit = "marketplace.product"
    
    def create_products(self):
        for rec in self:
            order_line_ids = self.env["sale.order.line"].search([('product_id', '=', rec.product_id.id)])
            shop_wise_ol = {}
            for line in order_line_ids:
                # rec.product_id = line.product_id.id 
                # _logger.info("~~~~~~~~line.product_id~~%r~~",)
                shop_name = line.order_id.market_place_shop
                if shop_name in shop_wise_ol.keys():
                    shop_wise_ol[shop_name] += [line]
                else:
                    shop_wise_ol[shop_name] = [line]
                    
                for shop in shop_wise_ol.keys():
                    price_inclusive = 0.0
                    price_exclusive = 0.0
                    if shop not in ["Amazon UK","Amazon DE","Wayfair DS DE","Wayfair DS UK","Wayfair DS IE","Amazon FR B2B","Amazon DE B2B"]:
                        for line in shop_wise_ol[shop]:
                            price_inclusive += line.price_unit
                            price_exclusive += line.price_subtotal
                        avg_inclusive_price = price_inclusive / len(line)
                        
                        avg_exclusive_price = price_exclusive / len(line)
                    
                    
                        products = self.env["sku.expense.analysis"].search([('product','=',rec.sku),("shop_id",'=',shop_name)],limit = 1)
                        
                        if not products:
                            self.env["sku.expense.analysis"].create({
                                'product' : rec.sku,
                                'vat_inclusive' : avg_inclusive_price ,
                                'vat_exclusive' : avg_exclusive_price ,
                                'shop_id' : shop_name
                                
                            })
                        else :
                            products.vat_inclusive = avg_inclusive_price 
                            products.vat_exclusive = avg_exclusive_price 
                            
                            
                        
    
        


                    
