from odoo import fields, models, _

class AccountMove(models.Model):
    _inherit = 'account.move'

    order_id = fields.Many2one('sale.order', compute='_get_sale_order')
    mirakl_invoice_id = fields.Char(related='order_id.mirakl_order_id', store=True)

    def _get_sale_order(self):
        for rec in self:
            if rec.invoice_origin:
                rec.order_id = self.env['sale.order'].search([('name', '=', rec.invoice_origin)])
            else:
                rec.order_id = False
