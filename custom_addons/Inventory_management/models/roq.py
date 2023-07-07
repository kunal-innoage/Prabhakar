from odoo import fields, models, _ , api



class Request(models.Model):
    _name = "request"
    _inherit=["mail.thread","mail.activity.mixin"]
    _description = "Request for quotation"
    _rec_name = "vendor_id"


    # request_seq=fields.Char(string="Request Number",readonly=1, required=1 ,copy=False,default=lambda self:_('New'))
    vendor_id=fields.Many2one("vendor","Vendor")
    vendor_reference=fields.Char("Vendor Reference")
    order_deadline=fields.Datetime("Order Deadline")
    receipt_date=fields.Datetime("Receipt Date")
    request_order_lines =fields.One2many("request.line","request_id","Requests")


    def test(self):
        self.ensure_one()
        return {
            'name': "Vendor",
            'type': 'ir.actions.act_window',
            
            'view_mode': 'tree,form',
            'res_model': 'vendor',
            
        }
        

class RequestLines(models.Model):

    _name='request.line'  
    _description='request lines'

    request_id =fields.Many2one("request","Request Line")
    product_ids=fields.Many2one("inventory.management","Products")
    quantity=fields.Integer("Quantity")
    unit_price=fields.Integer("Unit Price")
    taxes=fields.Integer("Taxes")
    subtotal=fields.Float(compute="compute_subtotal")

    @api.depends("quantity","unit_price","taxes")
    def compute_subtotal(self):
        
        for record in self:
            record.subtotal=(record.unit_price*record.quantity+record.taxes)    

    def test(self):
        pass