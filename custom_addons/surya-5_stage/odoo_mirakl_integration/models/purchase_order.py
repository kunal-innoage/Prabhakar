# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

import logging
_logger = logging.getLogger(__name__)

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.onchange('order_line.per_piece_sqm')
    def get_final_sqm(self):
        for rec in self:
            total_sqm_order = 0
            for line in rec.order_line:
                if line.per_piece_sqm:
                    line.total_sqm = "{:.2f}".format(float(line.per_piece_sqm)*line.product_qty)
                    total_sqm_order += float(line.per_piece_sqm)*line.product_qty
            rec.total_sqm = total_sqm_order


    total_sqm = fields.Float("Total SQM", compute= "get_final_sqm", default="0.0", digits= (16,2))


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    # @api.depends('per_piece_sqm')
    # def get_total_sqm(self):
    #     for line in self:
    #         total_sqm_order = 0
    #         if line.per_piece_sqm:
    #             line.total_sqm = float(line.per_piece_sqm) * line.product_qty
    #             total_sqm_order += float(line.total_sqm)

    barcode = fields.Char(related="product_id.barcode", string="UPC Code")
    vendor_ref_number = fields.Char(related="product_id.vendor_reference" ,string = "Vendor Reference")
    per_piece_sqm = fields.Float(related="product_id.marketplace_product_id.total_area" ,string = "Per Piece SQM", digits=(16,2))
    total_sqm = fields.Float(string = "Total SQM", default="0.0", digits=(16,2))

    def create(self, vals_list):
        res = super(PurchaseOrderLine, self).create(vals_list)
        for line in self:
            total_sqm_order = 0
            if line.per_piece_sqm:
                line.total_sqm = float(line.per_piece_sqm) * line.product_qty
                line.per_piece_sqm = "{:.2f}".format(line.per_piece_sqm)
                line.total_sqm = "{:.2f}".format(line.total_sqm)

        return res
    

