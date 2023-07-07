from odoo import fields, models


class Vendor(models.Model):
    _name = "vendor"
    _inherit=["mail.thread","mail.activity.mixin"]
    _rec_name = "vendor_name"


    vendor_name = fields.Char("Vendor Name",Help="Enter vendor's name", required=True)
    vendor_id=fields.Char("Vendor ID") 
    location=fields.Char("Location")
    company_name=fields.Char("Company Name")
    contact_number=fields.Integer("Contact Number")
    product_ids=fields.One2many("inno.inventory.management","vendor_id","Products")
    year_the_company_was_founded=fields.Integer("Year Company was Established")
    vendor_type=fields.Selection([('international','International'),('local','Local')],string="Vendor Type")
    payment_through=fields.Char("Payment")
    email=fields.Char("E-mail")
    transport_facility=fields.Char("Transport Facility")
    