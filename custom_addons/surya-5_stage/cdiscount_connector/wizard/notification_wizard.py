 # -*- coding: utf-8 -*-

from odoo import fields, models, _, api
from odoo.exceptions import Warning

class Marketplace_Wizard(models.TransientModel):
    _name = "cdiscount.wizard"
    _description = "Cdiscount Notification Wizard"

    # wizard_message = fields.Text(string="", readonly=True)
    new_added_so = fields.Integer("New Added Sale Order",default=0)
    new_added_line = fields.Integer("New Added Line",default=0)
    existing_updated_line = fields.Integer("Updated Orders",default=0)

    def show_wizard_message(self, new_added_so, new_added_line, existing_updated_line):

        message_id = self.create({'new_added_so': new_added_so,'new_added_line':new_added_line, 'existing_updated_line': existing_updated_line }).id
        return {'name': 'Order Counts', 'res_model': 'cdiscount.wizard', 'view_id': 'cdiscount_wizard_form', 'res_id': message_id, 'type': 'ir.actions.act_window', 'view_mode': 'form', 'domain': '[]', 'target': 'new'}
