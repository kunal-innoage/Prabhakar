# -*- coding: utf-8 -*-

from odoo import fields, models, _, api
import datetime
import pytz

import logging
_logger = logging.getLogger(__name__)


class OrderTrackingExport(models.Model):
    _name = "order.tracking.export"
    _description = "Order Tracking Export"
    _rec_name = "order_id"

    name = fields.Char("Name")
    mail_address = fields.Char("Mail")
    street = fields.Char("Street")
    street2 = fields.Char("Street2")
    country = fields.Char("Country")
    postal_code = fields.Char("Postal Code")
    town = fields.Char("Town")
    phone = fields.Char("Phone")
    picking_date = fields.Char("Picking Date")
    order_id = fields.Char("Order Nr")
    item_id = fields.Char("Item Nr")
    quantity = fields.Char("Quantity")
    comment = fields.Char("Comment")
    weight = fields.Char("Weight")
    carrier = fields.Char("Carrier")

    process_date = fields.Datetime("Processing Date")

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

    def create_export_lines(self, data):
        self.create(data)
        return True


    # Check for Availablity
    def check_for_availablity(self):
        
        # Collect sold qty of all selected sku and orders linked to them
        product_sold_count = {}
        for order in self:
            product_id = self.env['product.product'].search([('default_code', 'in', [order.item_id])])
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



class UKOrderTrackingExport(models.Model):
    _name = "uk.order.tracking.export"
    _description = "UK Order Tracking Export"
    _rec_name = "order_id"

    name = fields.Char("Name")
    mail_address = fields.Char("Mail")
    street = fields.Char("Street")
    street2 = fields.Char("Street2")
    country = fields.Char("Country")
    postal_code = fields.Char("Postal Code")
    town = fields.Char("Town")
    phone = fields.Char("Phone")
    picking_date = fields.Char("Picking Date")
    warehouse = fields.Char("warehouse")
    order_id = fields.Char("reference")
    item_id = fields.Char("Item Nr")
    quantity = fields.Char("Quantity")
    comment = fields.Char("Comment")
    weight = fields.Char("Weight")
    carrier = fields.Char("Carrier")
    process_date = fields.Datetime("Processing Date")

    #new 
    date_placed = fields.Char("date_placed")
    shipping_net_price = fields.Char("shipping_net_price")
    shipping_code = fields.Char("shipping_code")
    duty_paid = fields.Char("duty_paid")
    insured_value = fields.Char("insured_value")
    delivery_instructions = fields.Char("delivery_instructions")
    picking_instructions = fields.Char("picking_instructions")
    despatch_instructions = fields.Char("despatch_instructions")
    gift_message = fields.Char("gift_message")
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
    country = fields.Char("country")
    email = fields.Char("email")
    # phone = fields.Char("phone")
    vat = fields.Char("vat")
    xero_account_number = fields.Char("xero_account_number")
    sku = fields.Char("sku")
    quantity = fields.Char("quantity")
    line_net_price = fields.Char("line_net_price")

    marketplace = fields.Char("Marketplace")
    sale_order_id = fields.Many2one('sale.order', 'Sale Order')
    product_id = fields.Many2one('product.product', 'Product')
    mirakl_shop_id = fields.Many2one('shop.integrator', 'Mirakl Shop Id')
    stock_status = fields.Selection([('check_available','Check Availability'), ('available','Available'), ('not_available', 'Not Available'),  ('on_hold', 'On Hold')])
    order_processing_status = fields.Selection([('unprocessed','Not Processed'), ('processed', 'Processed')])
    inventory_stock_count = fields.Float('On Hand Qty')

    def create_export_lines(self, data):
        self.create(data)
        return True


    # Check for Availablity
    def check_for_availablity(self):
        
        # Collect sold qty of all selected sku and orders linked to them
        product_sold_count = {}
        for order in self:
            product_id = self.env['product.product'].search([('default_code', 'in', [order.item_id])])
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
