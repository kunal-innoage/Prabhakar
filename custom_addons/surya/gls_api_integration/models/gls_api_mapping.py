from odoo import fields , models , api

class GlsApiMapping(models.Model):
    _name = 'gls.api.mapping'
    _description = 'GLS Api Mapping'
    
    packet_number = fields.Char("Packet Number")
    
    # def get_packet_number(self):
    #     url = ""
    #     if not self.api_login or not self.api_password:
    #         raise UserError(_("Please Enter login ID and password for API"))
    #     else:
    #         response = requests.get(url, auth=(self.api_login, self.api_password))
    #     data = xmltodict.parse(response.text)
    #     self.write({'seller_token': data['string']['#text']})
    #     print(data)
    
