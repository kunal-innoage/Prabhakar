import base64

from odoo import fields, api, models, _
import logging, json, base64, requests

_logger = logging.getLogger(__name__)


class Seller(models.Model):
    _name = "bol.seller"
    _description = "Bol Seller Management"

    name = fields.Char("Name")
    activate = fields.Boolean("Activate")
    warehouse_id = fields.Many2one("stock.warehouse", "Warehouse", required=True)

    # Only authorized person view
    # api_key = fields.Char("API Key", required=True)
    # bol_url = fields.Char("Bol Shop URL", required=True)
    token_id = fields.Char("Token ID" , required = True )
    bol_client_id= fields.Char("Client ID" , required = True)
    bol_client_secret = fields.Char("Client Secret")
    token = fields.Text("Token")

    ##################
    # AUTHENTICATION #
    ##################

    def get_token(self):

        final = self.bol_client_id + ":" + self.bol_client_secret
        x = final.encode("ascii")
        aa = base64.b64encode(x)
        a= aa.decode("ascii")
        a = "Basic " + a
        self.token_id = (a)

        url = "https://login.bol.com/token?grant_type=client_credentials"
        payload = {}
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded','Accept': 'application/json','Authorization': self.token_id
        }
        response = requests.request("POST" , url , headers = headers , data = payload)
        self.token = json.loads(response.content).get('access_token') \
            if response.status_code == 200 else False


    ####################
    # Offer Update API #
    ####################

    def bol_inventory_offers(self):
        pass

