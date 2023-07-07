 # -*- coding: utf-8 -*-

from odoo import fields, models, _, api
from odoo.exceptions import Warning

class Manomano_Wizard(models.TransientModel):
    _name = "manomano.wizard"
    _description = "Manomano Wizard"

    message = fields.Char("Message")

    def show_wizard_offer_message(self, message, name):
        message_id = self.create({'message': message}).id
        return {'name': name, 'res_model': 'manomano.wizard', 'res_id': message_id, 'type': 'ir.actions.act_window', 'view_mode': 'form', 'domain': '[]', 'target': 'new'}

   
