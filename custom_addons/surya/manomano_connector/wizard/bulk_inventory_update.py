from odoo import fields, models


class BulkIventoryUpdate(models.TransientModel):
    _inherit = 'bulk.inventory.update'

    manomano_shops = fields.Many2many(comodel_name='manomano.seller', string='Manomano Shops')
    

    def update_inventory_csv(self):
        selected_records = self.env.context.get('selected_record')
        if self.manomano_shops:
            self.env['manomano.seller'].search([],limit=1).bulk_inventory_update(selected_records,self.manomano_shops)
        return super(BulkIventoryUpdate, self).update_inventory_csv()