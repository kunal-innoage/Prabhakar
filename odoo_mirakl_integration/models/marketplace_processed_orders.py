# -*- coding: utf-8 -*-

from odoo import fields, models, _, api
import datetime
import pytz

import logging
_logger = logging.getLogger(__name__)


class ProcessedOrder(models.Model):
    _name = "processed.order"
    _description = "Processed Order"

    # Common Fields 
    quantity = fields.Char("Quantity")
    marketplace = fields.Char("Marketplace")
    sale_order_id = fields.Many2one('sale.order', 'Sale Order')
    product_id = fields.Many2one('product.product', 'Product')
    mirakl_shop_id = fields.Many2one('shop.integrator', 'Mirakl Shop Id')
    stock_status = fields.Selection([('check_available','Check Availability'), ('available','Available'), ('not_available', 'Not Available'),  ('on_hold', 'On Hold')])
    order_processing_status = fields.Selection([('unprocessed','Not Processed'), ('processed', 'Processed')])
    inventory_stock_count = fields.Float('On Hand Qty')
    market_place_shop = fields.Char("Shop Name")
    processing_time = fields.Selection([
        ('morning','Morning'),
        ('evening','Evening')
    ])
    warehouse = fields.Char("Warehouse")


    # ETL Fields 
    name = fields.Char("Name")
    mail_address = fields.Char("Mailaddress")
    street = fields.Char("Street")
    street2 = fields.Char("Street2")
    country = fields.Char("Country")
    postal_code = fields.Char("Postal Code")
    town = fields.Char("Town")
    phone = fields.Char("Phone")
    picking_date = fields.Char("Picking Date")
    order_id = fields.Char("Order Nr")
    item_id = fields.Char("Item Nr")
    comment = fields.Char("Comment")
    weight = fields.Char("Weight")
    carrier = fields.Char("Carrier")
    process_date = fields.Datetime("Processing Date")


    #I-Fullfillment
    reference = fields.Char("reference")
    date_placed = fields.Char("date_placed")
    shipping_net_price = fields.Char("shipping_net_price")
    shipping_code = fields.Char("shipping_code")
    duty_paid = fields.Char("duty_paid")
    insured_value = fields.Char("insured_value")
    delivery_instructions = fields.Char("delivery_instructions")
    picking_instructions = fields.Char("picking_instructions")
    despatch_instructions = fields.Char("despatch_instructions")
    gift_message = fields.Char("gift_message")
    invoice_before_dispatch = fields.Char("invoice_before_dispatch")
    hold = fields.Char("hold")
    booking_required = fields.Char("booking_required")
    company = fields.Char("company")
    ship_to_name = fields.Char("ship_to_name")
    first_name = fields.Char("first_name")
    last_name = fields.Char("last_name")
    address_one = fields.Char("address_one")
    address_two = fields.Char("address_two")
    address_three = fields.Char("address_three")
    town = fields.Char("town")
    county = fields.Char("county")
    postcode = fields.Char("postcode")
    email = fields.Char("email")
    phone_no = fields.Char("phone")
    vat = fields.Char("vat")
    xero_account_number = fields.Char("xero_account_number")
    sku = fields.Char("sku")
    line_net_price = fields.Char("line_net_price")

    # Cdiscount 
    ean_product = fields.Char("EAN Product")
    customer_order_number = fields.Char("Your customer number order")
    signboard = fields.Char("Signboard")
    customer_name = fields.Char("Customer name")
    customer_first_name = fields.Char("Customer Firstname")
    delivery_address = fields.Char("Delivery address")
    additional_address = fields.Char("Additional address")
    bp_or_locality = fields.Char("BP or Locality")
    city_cds = fields.Char("City")
    mobile_no = fields.Char("Mobile number")
    phone_no = fields.Char("Phone number")
    email_cds = fields.Char("E-mail address")
    delivery_mode_cds = fields.Char("Mode of delivery")
    


    def create_processed_orders(self, data):
        self.create(data)
        return True


    # Check for Availablity
    def check_for_availablity(self):
        
        # Collect sold qty of all selected sku and orders linked to them
        product_sold_count = {}
        for order in self:
            product_id = self.env['product.product'].search([('default_code', 'in', [order.item_id])], limit=1)
            if order.item_id in product_sold_count:
                product_sold_count[order.item_id]['ordered_quantity'] += float(order.quantity)
                product_sold_count[order.item_id]['order_ids'].append(order.sale_order_id)
            else:
                product_sold_count[order.item_id] = {'ordered_quantity': float(order.quantity), 'available_quantity': product_id.qty_available, 'order_ids': [order.sale_order_id]}

        for order in self:
            if order.item_id in product_sold_count:
                if product_sold_count[order.item_id]['ordered_quantity'] > product_sold_count[order.item_id]['available_quantity']:
                    order.stock_status = 'not_available'
                else:
                    order.stock_status = 'available'


    # Move to Available
    def move_to_available(self):
        for order in self:
            order_shift = None
            IST = pytz.timezone('Asia/Kolkata')
            time_now = datetime.datetime.strftime(datetime.datetime.now(IST), "%Y-%m-%d %H:%M:%S")
            if int(time_now.split(' ')[1][:2]) <= 12:
                order_shift = 'morning'
            else:
                order_shift = 'evening'
            order.stock_status = "available"
            order.process_date = datetime.datetime.now()
            order.processing_time = order_shift

    # Move to Hold
    def move_to_onhold(self):
        for order in self:
            order_shift = None
            IST = pytz.timezone('Asia/Kolkata')
            time_now = datetime.datetime.strftime(datetime.datetime.now(IST), "%Y-%m-%d %H:%M:%S")
            if int(time_now.split(' ')[1][:2]) <= 12:
                order_shift = 'morning'
            else:
                order_shift = 'evening'
            order.stock_status = 'on_hold'
            order.process_date = datetime.datetime.now()
            order.processing_time = order_shift

