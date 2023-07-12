import requests, json , logging
_logger = logging.getLogger(__name__)

from odoo import fields , models , api

class MarketpalceOrderTracking(models.Model):
    _inherit = "marketplace.order.tracking"


    packet_number = fields.Char("Packet Number")
    token = fields.Many2one("gls.api.config" , "Token")
    status = fields.Char("Status")

    def get_tracking_status(self):
        try:
            for rec in self:
                token = self.env['gls.api.config'].search([]).token_id
                url = "https://api.gls-group.eu/public/v1/tracking//references/"+ rec.tracking_code
                payload = {}
                headers = {
                    'Authorization' : token
                }
                response = requests.get(url, headers = headers , data = payload)

                if response.status_code == 200:
                    rec.packet_number = json.loads(response.content).get('parcels')[0].get('trackid')
                    rec.status = json.loads(response.content).get('parcels')[0].get('status')
                else:
                    rec.packet_number = "NULL"
                    rec.status = "NULL"

        except Exception as e:
            _logger.info("Error Calling Packet Number API ~~~~~~~~~~%r~~~~~~`", e)
