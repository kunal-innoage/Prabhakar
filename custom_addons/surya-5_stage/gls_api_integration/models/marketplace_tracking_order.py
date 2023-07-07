from odoo import fields , models , api

class MarketpalceOrderTracking(models.Model):
    _inherit = "marketplace.order.tracking"
    
    
    packet_number = fields.Char("Packet Number")
    
    def get_tracking_status(self):
        pass