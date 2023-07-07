# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SaleWorkflowProcess(models.Model):

    _name = "sale.workflow.process"
    _description = "Sale Workflow Process"

    create_invoice = fields.Boolean(string="Create Invoice")
    validate_invoice = fields.Boolean(string="Validate Invoice")
    create_picking = fields.Boolean(string="Create Transfer")
    validate_picking = fields.Boolean(string="Validate Transfer")
    shop_id = fields.Many2one("shop.integrator", string="Shop")

    @api.model
    def create(self, vals):
        if vals:
            data = self.env['shop.integrator'].browse(vals['shop_id'])
            data = self.search([('shop_id', '=', data.id)])
            if data:
                raise UserError(_("You should only add one sale order workflow setting."))
            else:
                return super(SaleWorkflowProcess, self).create(vals)
        else:
            return super(SaleWorkflowProcess, self).create(vals)
