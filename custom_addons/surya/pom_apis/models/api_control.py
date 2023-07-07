from odoo import api, fields, models
import string    
import random

class PomApiControl(models.Model):
    _name = 'pom.api.control'
    _description = 'Pom Api Control'

    name = fields.Char(string='Name',required=True)
    desc = fields.Text(string='Description',required=True)
    api_key = fields.Char("Api Key")


    def generate_api_key(self):
        key = ''.join(random.choices(string.ascii_lowercase + string.digits, k = 100))
        self.write({'api_key': key})
