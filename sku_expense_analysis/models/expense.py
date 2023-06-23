from odoo import fields , models
import logging
_logger = logging.getLogger(__name__)

    # MIRAKL MARKETPLACE

class MarketplaceIntegration(models.Model):
    _inherit = "shop.integrator"
    
    replenishment_period = fields.Integer("Replenishment Period (Months)")
    storage = fields.Float("Storage")
    pick_pack = fields.Float("Pick & Pack")
    adv_cost = fields.Float("Adv Cost")
    shipping_cost = fields.Float("Shipping Cost")
    salary_cost = fields.Float("Salary Cost")
    carrer_admin_cost = fields.Float("Carrer Admin Cost")
    comission = fields.Float("Commission")
    
    # MANOMANO CONNECTOR

class ManomanoConnector(models.Model):
    _inherit = "manomano.seller"
    
    replenishment_period = fields.Integer("Replenishment Period (Months)")
    storage = fields.Float("Storage")
    pick_pack = fields.Float("Pick & Pack")
    adv_cost = fields.Float("Adv Cost")
    shipping_cost = fields.Float("Shipping Cost")
    salary_cost = fields.Float("Salary Cost")
    carrer_admin_cost = fields.Float("Carrer Admin Cost")
    comission  = fields.Integer("Commission")
    
    # CDISCOUNT CONNECTOR

class CdiscountConnector(models.Model):
    _inherit = "cdiscount.seller"
    
    replenishment_period = fields.Integer("Replenishment Period (Months)")
    storage = fields.Float("Storage")
    pick_pack = fields.Float("Pick & Pack")
    adv_cost = fields.Float("Adv Cost")
    shipping_cost = fields.Float("Shipping Cost")
    salary_cost = fields.Float("Salary Cost")
    carrer_admin_cost = fields.Float("Carrer Admin Cost")
    comission  = fields.Integer("Commission")
    
    # AMAZON CONNECTOR

class AmazonConnector(models.Model):
    _inherit = "amazon.seller"
    
    replenishment_period = fields.Integer("Replenishment Period (Months)")
    storage = fields.Float("Storage")
    pick_pack = fields.Float("Pick & Pack")
    adv_cost = fields.Float("Adv Cost")
    shipping_cost = fields.Float("Shipping Cost")
    salary_cost = fields.Float("Salary Cost")
    carrer_admin_cost = fields.Float("Carrer Admin Cost")
    comission  = fields.Integer("Commission")
    
    # WAYFAIR CONNECTOR

class WayfiarConnector(models.Model):
    _inherit = "wayfair.seller"
    
    replenishment_period = fields.Integer("Replenishment Period (Months)")
    storage = fields.Float("Storage")
    pick_pack = fields.Float("Pick & Pack")
    adv_cost = fields.Float("Adv Cost")
    shipping_cost = fields.Float("Shipping Cost")
    salary_cost = fields.Float("Salary Cost")
    carrer_admin_cost = fields.Float("Carrer Admin Cost")
    comission  = fields.Integer("Commission")

