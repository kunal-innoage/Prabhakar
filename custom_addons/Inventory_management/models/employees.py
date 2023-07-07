from odoo import fields, models

class Employees(models.Model):
    _name = "employee"
    _inherit=["mail.thread","mail.activity.mixin"]
    # _rec_name = "employee"

       
    employee_name=fields.Char("Employee's Name")
    job_position = fields.Char("Job Position")
    domain=fields.Selection([('us','US'),('india','India'),('europe','Europe'),('other','Others')],string="Team")
    work_mobile=fields.Integer("Work Mobile") 
    work_phone=fields.Integer("Work Phone") 
    gender=fields.Selection([('male','Male'),('female','Female')],string="Gender")
    marital_status=fields.Selection([('married','Married'),('single','Single'),('divorced','Divorced')],string="Marital Status")
    manager=fields.Char("Manager")
    address=fields.Char("Current Address")
    addresss=fields.Char("Permanent Address")
    email=fields.Char("Personal E-mail")
    employee_id=fields.Char("Employee ID")
    emergency_contact_number=fields.Integer("Emergency Contact Number")
    check_in_time=fields.Datetime(String="Check In", Widget='time')
    check_out_time=fields.Datetime(String="Check Out",Widget='time')
    emaill=fields.Char("Office E-mail")
    cab_location1=fields.Char("Cab Pick-up Location")
    cab_location2=fields.Char("Cab Drop-off Location")
    image=fields.Binary("Image")
    