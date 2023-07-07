from odoo import models,_

class StockPicking(models.Model):
    _inherit = 'stock.picking'
    
    def action_open_label_layout(self):
        view = self.env.ref('stock.product_label_layout_form_picking')
        return {
            'name': _('Choose Labels Layout'),
            'type': 'ir.actions.act_window',
            'res_model': 'product.label.layout',
            'views': [(view.id, 'form')],
            'target': 'new',
            'context': {
                'default_product_ids': self.move_lines.product_id.ids,
                'default_move_line_ids': self.move_line_ids.ids,
                },
            }