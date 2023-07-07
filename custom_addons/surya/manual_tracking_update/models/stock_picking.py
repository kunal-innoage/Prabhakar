from odoo import models, fields



class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def action_send_tracking_info_manually(self):
        pass