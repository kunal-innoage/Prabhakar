from odoo import api, fields, models, _


class WarehouseInterTransfer(models.TransientModel):
    _name = 'warehouse.inter.transfer'
    _description = "Transfer"

    partner_id = fields.Many2one(
            'res.partner', string='Contact')
    picking_type_id = fields.Many2one(
        'stock.picking.type', 'Operation Type',
        required=True)
    location_id = fields.Many2one(
        'stock.location', "Source Location", required=True)
    location_dest_id = fields.Many2one(
        'stock.location', "Destination Location", required=True)
    product_id = fields.Many2one('product.product', string='Product To Transfer')
    qty = fields.Float('Quantity', default=1.00)

    def launch_transfer(self):
        delivery_order = self.env['stock.picking'].create({
            'partner_id': self.partner_id.id,
            'location_id': self.location_id.id,
            'location_dest_id': self.location_dest_id.id,
            'picking_type_id': self.picking_type_id.id,
            'is_mirakl_stock_transfer': True,
            'move_ids_without_package': [(0, 0, {
                'name': self.product_id.name,
                'product_id': self.product_id.id,
                'product_uom': self.product_id.uom_id.id,
                'location_id': self.location_id.id,
                'location_dest_id': self.location_dest_id.id,
                'quantity_done': self.qty,
            })]
        })
        delivery_order.button_validate()
