from odoo import fields, models, _ , api


class Purchasee(models.Model):


    _name = "purchasee"
    _inherit=["mail.thread","mail.activity.mixin"]
    # _rec_name="purchasee"

    reference =fields.Char("Refernce")
    vendor = fields.Char("Vendor")
    company = fields.Char("Company")
    vendor_reference=fields.Char("Vendor Reference") 
    # currency=fields.Char("Currency")
    order_deadline=fields.Datetime("Order Deadline")
    receipt_date=fields.Date("Receipt Date")
    product=fields.Char("Product")
    description=fields.Char("Description")
    quantity=fields.Integer("Quantity")
    unit_price=fields.Integer("Unit Price")
    taxes=fields.Integer("Taxes")
    subtotal=fields.Integer("Subtotal")
    # purchase_seq=fields.Char(string="Purchase Number",readonly=1, required=1 ,copy=False,default=lambda self:_('New'))


    product_ids=fields.One2many("inno.inventory.management","purchase_id","Products")
    vendor_id=fields.Many2one("vendor","Vend")

    currency=fields.Selection([('eur','EUR'),('usd','USD')],string="Currency")
    # cost=fields.Integer("Cost")

    # @api.moedel
    # def create(self, vals):
    #     if not vals.get('note'):
    #         vals[]
    #     return super().create(vals_list)

    # domain="[('vendor_name')]

    def test(self):
        pass