from odoo import fields , models , api
import requests
import logging
_logger = logging.getLogger(__name__)


class GlsApiConfig(models.Model):
    _name = 'gls.api.config'
    _description = 'GLS Api Config'
    
    name = fields.Char(string = 'Name' , required = True)
    description = fields.Char(string='Description')
    is_prod = fields.Boolean("Production")
    sb_client_id = fields.Char("SandBox Client ID")
    sb_client_secret = fields.Char("SandBox Client Secret")
    sb_audience = fields.Char("Sandbox Audience")
    prod_client_id = fields.Char("Production Client ID")
    prod_client_secret = fields.Char("Production Client Secret")
    prod_audience = fields.Char("Production Audience")
    token_id = fields.Char("Token ID")
    
    def get_token(self):
        for rec in self:
            

            # url = "https://api-sandbox.gls-group.net/oauth2/v2/token"
            url = "https://shipit-wbm-de03.gls-group.eu:8443"

            payload = 'grant_type=client_credentials&client_id='+rec.sb_client_id+'&client_secret='+rec.sb_client_secret
            headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json'
            }
            _logger.info("~~~~~~~~~%r~~~~~~~",payload)

            response = requests.request("POST", url, headers=headers, data=payload).json()
            _logger.info("RESPONSE~~~~~~~~~%r~~~~~~~",response)
            rec.token_id = response['access_token']

            print(response['access_token'])