from odoo import fields , api , models , _
import logging
_logger = logging.getLogger(__name__)

class Seller(models.Model):
    _name = "bol.seller"
    _description = "Bol Seller Management"
    
    
    name = fields.Char("Name")
    activate = fields.Boolean("Activate")
    warehouse_id = fields.Many2one("stock.warehouse", "Warehouse",required=True)
    
    # Only authorized person view
    api_key = fields.Char("API Key" , required=True )
    bol_url = fields.Char("Bol Shop URL" , required=True)
    
    ####################
    # Offer Update API #
    ####################
    
    def bol_inventory_offers(self):
        pass
    
    
    
    
    