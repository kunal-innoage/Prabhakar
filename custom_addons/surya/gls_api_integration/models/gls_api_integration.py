from odoo import fields , models , api
import requests
import logging
_logger = logging.getLogger(__name__)
import base64
import json



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


            url = "https://api-sandbox.gls-group.net/oauth2/v2/token"
            # url = "https://shipit-wbm-de03.gls-group.eu:8443"



            payload = 'grant_type=client_credentials&client_id='+rec.sb_client_id+'&client_secret='+rec.sb_client_secret
            headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json'
            }
            # _logger.info("GLS~~~~~~~~~%r~~~~~~~",payload)

            response = requests.request("POST", url, headers=headers, data=payload).json()
            _logger.info("RESPONSE~~~~~~~~~%r~~~~~~~",response)
            rec.token_id = response['access_token']

            print(response['access_token'])
            
    # def get_token(self):
    #     for rec in self:


    #         url = "https://shipit-wbm-de03.gls-group.eu:8443/backend/rs/shipments/endofday?date=2023-06-11"

    #         payload = {}
    #         headers = {
    #         'Accept': 'application/glsVersion1+json, application/json',
    #         'Content-Type': 'application/glsVersion1+json',
    #         'Authorization': 'Basic cmVzdHVzZXI6c2VjcmV0'
    #         }

    #         response = requests.request("POST", url, headers=headers, data=payload)

    #         print(response.text)

            
            # login_name = 'restuser'
            # password = 'secret'
            
            
            # payload = 'basic' + base64.b64encode('restuser:secret')
            # headers = {
            #     "Accept",  "application/glsVersion1+json, application/json" ,
            #     "Content-Type",  "application/glsVersion1+json"
            # }
            # response = requests.request("POST", login_name , password , headers=headers, data=payload).json()
            # _logger.info("RESPONSE~~~~~~~~~%r~~~~~~~",response)
            # rec.token_id = response['access_token']
            
    def get_token(self):
        # s = "Basic " + base64.b64encode((user+password)
        final = self.sb_client_id + ":" + self.sb_client_secret
        
        x = final.encode("ascii")
        
        aa = base64.b64encode(x)
        
        a = aa.decode("ascii")
        
        a = "Basic " + a
        self.token_id = (a)
        
        # https://shipit-wbm-de03.gls-group.eu:8443/backend/rs/shipments/endofday?date=2023-06-11
