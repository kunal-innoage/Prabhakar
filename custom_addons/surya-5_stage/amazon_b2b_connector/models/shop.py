from odoo import fields,api, models,_
import logging
_logger = logging.getLogger(__name__)

class AmazonB2bShop(models.Model):
    _name = 'amazon.b2b.shop'
    _description = 'Amazon B2B Shop'

    name = fields.Char("Name")
    shop_code = fields.Char("Shop Code")
    warehouse_id = fields.Many2one("stock.warehouse", "Warehouse",required=True)


    def action_view_amazon_b2b_sale_order(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _("%s's Orders", self.name),
            'view_mode': 'list,form',
            'res_model': 'amazon.b2b.sale.order',
            'context': {
                'search_default_today': 1,
            },
            'domain': [('amazon_b2b_shop_id', '=', self.id),]
        }

    def action_view_sale_orders(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _("Sales Orders Generated from Amazon B2B"),
            'view_mode': 'list,form',
            'res_model': 'sale.order',
            'context': {
                'search_default_groub_by_date': 1,
            },
            'domain': [('amazon_b2b_order_id', '!=', False)],
        }
    
