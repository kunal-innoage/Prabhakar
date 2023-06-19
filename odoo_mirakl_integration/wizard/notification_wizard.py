 # -*- coding: utf-8 -*-

from odoo import fields, models, _, api
from odoo.exceptions import Warning

class Marketplace_Wizard(models.TransientModel):
    _name = "marketplace.wizard"
    _description = "Marketplace Wizard"

    wizard_message = fields.Text(string="", readonly=True)

    def show_wizard_message(self, message, name):
        message_id = self.create({'wizard_message': message}).id
        return {'name': name, 'res_model': 'marketplace.wizard', 'res_id': message_id, 'type': 'ir.actions.act_window', 'view_mode': 'form', 'domain': '[]', 'target': 'new'}
