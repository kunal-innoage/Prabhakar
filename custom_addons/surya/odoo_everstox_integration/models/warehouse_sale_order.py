from odoo import fields,api, models,_
import requests
import base64
from odoo.http import request
import json, datetime
import pytz
from odoo.tools import float_compare

import logging
_logger = logging.getLogger(__name__)

class EverstoxShopOrder(models.Model):
    _name = 'everstox.shop.order'
    _description = 'Everstox Shop Orders'
    _inherit = 'mail.thread'
    _rec_name = "order_number"


    # Billing Address
    billing_vat_number = fields.Char("Billing Vat Number")
    billing_address_1 = fields.Char("Billing Address 1")
    billing_address_2 = fields.Char("Billing Address 2")
    billing_address_type = fields.Selection([ ("private", "Private"), ("business", "Business") ], "Billing Address Type")
    billing_city = fields.Char("Billing City")
    billing_company = fields.Char("Billing Company")
    billing_contact_person = fields.Char("Billing Contact Person")
    billing_country = fields.Char("Billing Country")
    billing_country_code = fields.Char("Billing Country Code")
    billing_first_name = fields.Char("Billing First Name")
    billing_last_name = fields.Char("Billing Last Name")
    billing_latitude = fields.Char("Billing Latitude")
    billing_longitude = fields.Char("Billing Longitude")
    billing_phone = fields.Char("Billing Phone")
    billing_province = fields.Char("Billing Province")
    billing_province_code = fields.Char("Billing Province Code")
    billing_department = fields.Char("Billing Department")
    billing_sub_department = fields.Char("Billing Sub Department")
    billing_title = fields.Char("Billing Title")
    billing_zip = fields.Char("Billing Zip")

    # Shipping Address
    shipping_address_1 = fields.Char("Shipping Address 1")
    shipping_address_2 = fields.Char("Shipping Address 2")
    shipping_address_type = fields.Char("Shipping Address Type")
    shipping_city = fields.Char("Shipping City")
    shipping_company = fields.Char("Shipping Company")
    shipping_contact_person = fields.Char("Shipping Contact Person")
    shipping_country = fields.Char("Shipping Country")
    shipping_country_code = fields.Char("Shipping Country Code")
    shipping_department = fields.Char("Shipping Department")
    shipping_first_name = fields.Char("Shipping First Name")
    shipping_last_name = fields.Char("Shipping Last Name")
    shipping_latitude = fields.Char("Shipping Latitude")
    shipping_longitude = fields.Char("Shipping Longitude")
    shipping_phone = fields.Char("Shipping Phone")
    shipping_province = fields.Char("Shipping Province")
    shipping_province_code = fields.Char("Shipping Province Code")
    shipping_sub_department = fields.Char("Shipping Sub Department")
    shipping_title = fields.Char("Shipping Title")
    shipping_zip = fields.Char("Shipping Zip")

    # Order Details
    creation_date = fields.Char("Creation Date")
    custom_email = fields.Char("Custom Email")
    financial_status = fields.Selection([ 
        ("pending", "Pending"),
        ("authorized", "Authorized"), 
        ("paid", "Paid"), 
        ("partially_paid", "Partially Paid"),
        ("refunded", "Refunded"),
        ("partially_refunded", "Partially Refunded"),
        ("voided", "Voided") ],"Financial Status"
    )
    hours_late = fields.Char("Hours Late")
    order_id = fields.Char("Order ID")
    order_date = fields.Char("Order Date")
    order_number = fields.Char("Order Number")
    order_priority = fields.Char("Order Priority")
    out_of_stock_hours = fields.Char("Out Of Stock Hours")
    payment_methods = fields.Char("Payment Methods")
    requested_delivery_date = fields.Char("Requested Delivery Date")
    requested_warehouse_id = fields.Char("Requested Warehouse ID")
    order_shop_id = fields.Char("Order Shop ID")
    shop_instance_id = fields.Char("Shop Instance ID")
    shop_instance_name = fields.Char("Shop Instance Name")
    state = fields.Selection([
        ('created','Created'),
        ('in_fulfillment','In Fulfillment'),
        ('shipped','Shipped'),
        ('completed','Completed'),
        ('canceled','Canceled'),
    ], string="State")
    udpated_date = fields.Char("Updated Date")
    order_errors = fields.Char("Order Errors")
    order_returns = fields.Char("Order Returns")
    order_attachments = fields.Char("Order Attachment")
    order_custom_attributes = fields.Char("Order Custom Attributes")

    # Shipping Price 
    shipping_price_currency = fields.Char("Shipping Price Currency")
    shipping_price_discount = fields.Char("Shipping Price Discount")
    shipping_price_discount_gross = fields.Char("Shipping Price Discount Gross")
    shipping_price_discount_net = fields.Char("Shipping Price Discount Net")
    shipping_price = fields.Char("Shipping Price Price")
    shipping_price_gross = fields.Char("Shipping Price Price Gross")
    shipping_price_net_after_discount = fields.Char("Shipping Price Net After Discount")
    shipping_price_net_before_discount = fields.Char("Shipping Price Net Before Discount")
    shipping_price_tax = fields.Char("Shipping Price Tax")
    shipping_price_tax_amount = fields.Char("Shipping Price Tax Amount")
    shipping_price_tax_rate = fields.Char("Shipping Price Tax Rate")

    order_attachment = fields.Boolean("Label")
    shop_order_line_ids = fields.One2many("everstox.shop.order.line", "shop_order_id", string="Order Items")
    shop_order_fulfillment_ids = fields.One2many("everstox.shop.order.fulfillment", "shop_order_id", string="Fulfillments")
    shop_order_return_ids = fields.One2many("everstox.order.return", "shop_order_id", string="Returns")
    shop_order_shipment_ids = fields.One2many(related="shop_order_fulfillment_ids.shipment_ids", string="Shipments")

    everstox_shop_id = fields.Many2one("everstox.shop", string= "Shop")
    sale_order_id = fields.Many2one("sale.order", string= "Sale Order")
    everstox_mapped_state = fields.Selection([('mapped', 'Mapped'), ('unmapped', 'Unmapped')])


    def get_order_line_data(self, order):
        order_line_data = []
        for order_line in order.shop_order_line_ids:
            data  = {
                # "custom_attributes": order_line.order_line_custom_attributes,
                "price_set": [
                    {
                    "currency": order_line.order_line_currency,
                    "quantity": int(order_line.order_line_quantity),               
                    "tax_amount": order_line.order_line_tax_amount,
                    "tax_rate": order_line.order_line_tax_rate
                    }
                ],
                "product": {
                    "sku": order_line.order_line_product_sku,
                },
                "quantity": int(order_line.order_line_quantity),
                "requested_batch": order_line.order_line_requested_batch,
                "shipment_options": [
                    {
                    "id": order_line.order_line_shipment_options_id if order_line.order_line_shipment_options_id else "a3ac86ab-5140-4c1a-bcc8-b5a0d65252ae",
                    "name": order_line.order_line_shipment_options_name if order_line.order_line_shipment_options_name else "GLS"
                    }
                ]
            }
            order_line_data.append(data)
        return order_line_data


    def get_attachment(self, order):
        attachment_data = []
        sale_order = self.env['sale.order'].search([('id','=',order.sale_order_id.id)],limit=1)
        attachments = self.env['ir.attachment'].search([('res_model','=','sale.order'),('res_id','=',sale_order.id)])
        for attachment in attachments:
            if sale_order:

                attachment = self.env['ir.attachment'].create({'name': 'Label','res_model': 'everstox.shop.order', 'res_id': order.id, 'datas': attachment.datas})
                if attachment:
                    print("Sale Orders Mapped %s", attachment)
                    data= "data:application/pdf;base64," + str(attachment.datas)[2:-1]
                    if not data.endswith("=="):
                        data += "=="
                    if data.endswith("==="):
                        data = data[:-1]
                    attachment_data += [{
                        "attachment_type": "shipping_label",
                        "content": data,
                        "file_name": attachment.name,
                    }]
        if attachment_data:
            return attachment_data
        else:
            return []


    def prepare_order_and_order_data(self):
        data = {}
        for order in self:
            order_line_data = self.get_order_line_data(order)
            attachments = self.get_attachment(order)

            # Priority
            order_priority = 1
            if order.order_priority:
                order_priority = order.order_priority
            if order.sale_order_id.amazon_order_id:
                order_priority = 99

            order_data = {
                "attachments": attachments,
                "billing_address": {
                    "address_1": order.billing_address_1 if order.billing_address_1 else "",
                    "address_2": order.billing_address_2 if order.billing_address_2 else "",
                    "address_type": "private",
                    "city": order.billing_city if order.billing_city else "",
                    "company": order.billing_company if order.billing_company else "",
                    "contact_person": order.billing_contact_person,
                    "country": order.billing_country if order.billing_country else "",
                    "country_code": order.billing_country_code if order.billing_country_code else "",
                    "department": order.billing_department if order.billing_department else "",
                    "first_name": order.billing_first_name,
                    "last_name": order.billing_last_name,
                    "latitude": order.billing_latitude if order.billing_latitude else 0,
                    "longitude": order.billing_longitude if order.billing_longitude else 0,
                    "phone": order.billing_phone if order.billing_phone else "",
                    "province": order.billing_province if order.billing_province else "",
                    "province_code": order.billing_province_code if order.billing_province_code else "",
                    "sub_department": order.billing_sub_department if order.billing_sub_department else "",
                    "zip": order.billing_zip if order.billing_zip else "",
                    "VAT_number": order.billing_vat_number if order.billing_vat_number else ""
                },
                "financial_status": order.financial_status,
                "order_date": order.order_date,
                "order_items": order_line_data,
                "order_priority": int(order_priority),
                "order_number": order.order_number,
                "shipping_address": {
                    "address_1": order.shipping_address_1 if order.shipping_address_1 else "",
                    "address_2": order.shipping_address_2 if order.shipping_address_2 else "",
                    "address_type": "private",
                    "city": order.shipping_city if order.shipping_city else "",
                    "company": order.shipping_company if order.shipping_company else "",
                    "contact_person": order.shipping_contact_person,
                    "country": order.shipping_country,
                    "country_code": order.shipping_country_code,
                    "department": order.shipping_department if order.shipping_department else "",
                    "first_name": order.shipping_first_name,
                    "last_name": order.shipping_last_name,
                    "latitude": order.shipping_latitude if order.shipping_latitude else 0,
                    "longitude": order.shipping_longitude if order.shipping_longitude else 0,
                    "phone": order.shipping_phone if order.shipping_phone else "",
                    "province": order.shipping_province if order.shipping_province else "",
                    "province_code": order.shipping_province_code if order.shipping_province_code else "",
                    "sub_department": order.shipping_sub_department if order.shipping_sub_department else "",
                    "zip": order.shipping_zip if order.shipping_zip else ""
                },
                "shipping_price": {
                    "currency": "EUR",
                    "price": order.shipping_price if order.shipping_price else "0",
                    "price_net_after_discount": order.shipping_price_net_after_discount if order.shipping_price_net_after_discount else "0",
                    "tax_amount": order.shipping_price_tax_amount if order.shipping_price_tax_amount else "0",
                    "tax_rate": order.shipping_price_tax_rate if order.shipping_price_tax_rate else "0"
                },
                "shop_instance_id": order.shop_instance_id
            }
            
            order.everstox_shop_id.send_order_data_to_everstox(order, order_data)
        

    # Process Get Shipment Tracking
    def process_shipment_trackings(self, order, data):
        for shipment in data.get("shipments"):
            for odoo_shipment in order.shop_order_shipment_ids:
                odoo_shipment.carrier_id = shipment.get("carrier").get("id")
                odoo_shipment.carrier_name = shipment.get("carrier").get("name")
                odoo_shipment.forwarded_to_shop = shipment.get("forwarded_to_shop")
                odoo_shipment.tracking_codes = shipment.get("tracking_codes")
                odoo_shipment.tracking_urls = shipment.get("tracking_urls")


    def get_shipment_tracking(self):
        for order in self:
            response = False
            call = order.everstox_shop_id.shop_url+ "/api/v1/shops/" + order.everstox_shop_id.shop_id + "/orders/"+ order.order_id + "/shipments/tracking"
            try:
                _logger.info("........... Get Shipment Tracking Call  %r ...........",call)
                response = requests.get(call,headers={'everstox-shop-api-token': order.everstox_shop_id.shop_api_key,'Content-Type': 'application/json'})
            except Exception as err:
                _logger.info("Get Shipment Tracking API fail     %r  !!!!!!!!!", err)

            if response:
                if response.status_code == 200:
                    data = response.json()
                    _logger.info("........%r.....", response.json())
                    
                    self.process_shipment_trackings(order, data)
    

    def update_order(self):
        for order in self:
            call = order.everstox_shop_id.shop_url + "api/v1/shops/" + order.everstox_shop_id.shop_id + "/orders?order_number=" + order.order_number
            order.everstox_shop_id.get_warehouse_orders(call)
        pass


    def delete_order(self):
        for order in self:
            call = order.everstox_shop_id.shop_url + "api/v1/shops/" + order.everstox_shop_id.shop_id + "/orders/" + order.order_id
            order.everstox_shop_id.delete_order_on_everstox(call)
        pass


    def cancel_order(self):
        for order in self:
            call = order.everstox_shop_id.shop_url + "api/v1/shops/" + order.everstox_shop_id.shop_id + "/orders/" + order.order_id + "/cancel"
            order.everstox_shop_id.cancel_order_on_everstox(call)


    def bulk_upload_orders(self):
        data = False
        shop_id = False
        
        # Prepare bulk data
        for order in self:
            if not shop_id:
                shop_id = order.everstox_shop_id
                
    

        shop_id.update_bulk_orders(data)
        

class EverstoxShopOrderLine(models.Model):
    _name = 'everstox.shop.order.line'
    _description = 'Everstox Shop Orders Line'

    shop_order_id = fields.Many2one("everstox.shop.order", string="Sale Order")

    order_line_custom_attributes = fields.Char("Custom Attributes")
    order_line_errors = fields.Char("Errors")
    order_line_id = fields.Char("Order Line ID")
    order_line_product_name = fields.Char("Product Name")
    order_line_product_sku = fields.Char("Product SKU")
    order_line_quantity = fields.Char("Quantity")
    order_line_requested_batch = fields.Char("Requested Batch")
    order_line_requested_batch_expiration_date = fields.Char("Requested Batch Expiration Date")
    order_line_state = fields.Char("State")
    order_line_shipment_options_id = fields.Char("Shipment Options ID")
    order_line_shipment_options_name = fields.Char("Shipment Options Name")
    order_line_currency = fields.Char("Currency")
    order_line_discount = fields.Char("Discount")
    order_line_discount_gross = fields.Char("Discount Gross")
    order_line_discount_net = fields.Char("Discount Net")
    order_line_price = fields.Char("Price")
    order_line_price_gross = fields.Char("Price Gross")
    order_line_price_net_after_discount = fields.Char("Price Net After Discount")
    order_line_price_net_before_discount = fields.Char("Price Net Before Discount")
    order_line_price_set_quantity = fields.Char("Price Set Quantity")
    order_line_tax = fields.Char("Tax")
    order_line_tax_amount = fields.Char("Tax Amount")
    order_line_tax_rate = fields.Char("Tax Rate")


class EverstoxShopOrderFulfillment(models.Model):
    _name = 'everstox.shop.order.fulfillment'
    _description = 'Everstox Shop Orders Fulfillment'
    _rec_name = "fulfillment_id"

    shop_order_id = fields.Many2one("everstox.shop.order", string="Sale Order")
    shipment_ids = fields.One2many("everstox.order.shipment", "fulfillment_id", string="Shipments")

    fulfillment_cancellations = fields.Char("Fulfullment Cancellations")
    fulfillment_errors = fields.Char("Fulfullment Errors")
    fulfillment_hours_late = fields.Char("Fulfullment Hours Late")
    fulfillment_id = fields.Char("Fulfullment ID")
    fulfillment_warehouse_id = fields.Char("Fulfullment Warehouse ID")
    fulfillment_warehouse_name = fields.Char("Fulfullment Warehouse Name")

    fulfillment_item_error = fields.Char("Fulfillment Item Errors")
    fulfillment_item_id = fields.Char("Fulfillment ID")
    fulfillment_order_item_id = fields.Char("Order Item ID")
    fulfillment_product_id = fields.Char("Product ID")
    fulfillment_product_name = fields.Char("Product Name")
    fulfillment_product_sku = fields.Char("Product SKU")
    fulfillment_quantity = fields.Char("Quantity")
    fulfillment_state = fields.Selection([
        ('new','New'),
        ('warehouse_confirmation_pending','Warehouse Confirmation Pending'),
        ('accepted_by_warehouse','Accepted By Warehouse'),
        ('rejected_by_warehouse','Rejected By Warefulfillment_idhouse'),
        ('in_fulfillment','In fulfillment'),
        ('partially_shipped','Partially Shipped'),
        ('shipped','Shipped'),
        ('canceled','Canceled'),
    ], string="State")

    def cancel_fulfillment(self):
        for flmt in self:
            reponse = False
            call  = flmt.shop_order_id.everstox_shop_id.shop_url + "/api/v1/shops/" + flmt.shop_order_id.everstox_shop_id.shop_id +"/fulfillment/" + flmt.fulfillment_id + "/cancel"
            try:
                _logger.info("Fulfillment Cancelation call- %r", call)
                # response = requests.post(call,headers={'everstox-shop-api-token': flmt.shop_order_id.everstox_shop_id.shop_api_key,'Content-Type': 'application/json'})
            except Exception as err:
                _logger.info("Fulfillment Cancelation API fail   %r   !!!!", err)

            if response:
                if response.status_code == 200:
                    flmt.fulfillment_state = "canceled"
                    _logger.info("............... Order Fulfillment Canceled ...............")


class EverstoxShopOrderShipment(models.Model):
    _name = "everstox.order.shipment"
    _description = "Everstox Order Shipment"
    _rec_name = "shipment_id"

    carrier_id = fields.Char("Carrier ID")
    carrier_name = fields.Char("Carrier Name")
    forwarded_to_shop = fields.Boolean("Forwarded To Shop")
    rma_num = fields.Char("RMA Number")
    shipment_id = fields.Char("Shipment ID")
    shipment_date = fields.Char("Shipment Date")
    tracking_code = fields.Char("Tracking Code")
    tracking_codes = fields.Char("Tracking Codes")
    tracking_urls = fields.Char("Tracking URLs")
    processing_time = fields.Selection([
        ('first','First Half'),
        ('second','Second Half')
    ])

    shipment_items = fields.One2many("everstox.order.shipment.item", "shipment_id", "Shipment Ids")
    fulfillment_id = fields.Many2one("everstox.shop.order.fulfillment","Fulfillment")
    shop_order_id = fields.Many2one("everstox.shop.order", string="Sale Order")
    everstox_shop_id = fields.Many2one("everstox.shop", string= "Shop")
    sale_order_id = fields.Many2one("sale.order", string= "Odoo Order")
    tracking_id = fields.Many2one("marketplace.order.tracking", string= "Tracking")




    @api.model_create_multi
    def create(self, values):

        res = super(EverstoxShopOrderShipment, self).create(values)

        tracking_ids = tracking_obj = self.env["marketplace.order.tracking"]
        for shipment in self:
            if shipment.fulfillment_id.shop_order_id:
                processing_shift = None
                IST = pytz.timezone('Asia/Kolkata')
                time_now = datetime.datetime.strftime(datetime.datetime.now(IST), "%Y-%m-%d %H:%M:%S")
                if int(time_now.split(' ')[1][:2]) <= 18:
                    processing_shift = 'first'
                else:
                    processing_shift = 'second'
                date = datetime.datetime.now()
                warehouse = self.env["marketplace.warehouse"].search([('warehouse_code','=', shipment.everstox_shop_id.warehouse_id.code)])
                tracking_id = tracking_obj.create({
                    "order":  shipment.fulfillment_id.shop_order_id.order_number,
                    "customer": shipment.fulfillment_id.shop_order_id.shipping_contact_person,
                    "warehouse_id": warehouse.id,
                    "carrier" : shipment.carrier_name,
                    "tracking_code": shipment.tracking_codes[2:-2] if shipment.tracking_codes else "",
                    "marketplace": shipment.fulfillment_id.shop_order_id.sale_order_id.market_place_shop,
                    "tracking_date": date,
                    "processing_time": processing_shift,
                })
                if not shipment.processing_time:
                    shipment.processing_time = processing_shift
                if tracking_id:
                    tracking_ids += tracking_id
                    process_order = self.env["processed.order"].search([('order_id','like', tracking_id.order),('warehouse','=',warehouse.warehouse_code)])
                    # If Mirakl Order OR Cdiscount Order
                    if process_order.sale_order_id.mirakl_order_id or process_order.sale_order_id.cdiscount_order_id:
                        pass
                    else:
                        for delivery in process_order.sale_order_id.picking_ids:
                            if delivery.products_availability == "Available":
                                delivery.action_assign()
                                for move in delivery.move_lines.filtered(lambda m: m.state not in ["done", "cancel"]):
                                    rounding = move.product_id.uom_id.rounding

                                    if (
                                        float_compare(
                                            move.quantity_done,
                                            move.product_qty,
                                            precision_rounding=rounding,
                                        )
                                        == -1
                                    ):
                                        for move_line in move.move_line_ids:
                                            move_line.qty_done = move_line.product_uom_qty
                                delivery.with_context(skip_immediate=True, skip_sms=True).button_validate()
                                process_order.sale_order_id.invoice_status = 'to invoice'
                        

        return res
        



    def map_tracking_info(self):
        tracking_mapped_count = 0
        tracking_error_count = 0
        for shipment in self:
            try:
                if shipment.fulfillment_id.shop_order_id:
                    
                    processing_shift = None
                    IST = pytz.timezone('Asia/Kolkata')
                    time_now = datetime.datetime.strftime(datetime.datetime.now(IST), "%Y-%m-%d %H:%M:%S")
                    if int(time_now.split(' ')[1][:2]) <= 18:
                        processing_shift = 'first'
                    else:
                        processing_shift = 'second'
                    date = datetime.datetime.now()
                    
                    existing_tracking_id = self.env["marketplace.order.tracking"].search([('order', '=', shipment.fulfillment_id.shop_order_id.order_number)])
                    existing_tracking_id.unlink()
                    warehouse = self.env["marketplace.warehouse"].search([('warehouse_code','=', shipment.everstox_shop_id.warehouse_id.code)])
                    if shipment.tracking_codes:
                        tracking = eval(shipment.tracking_codes)
                        for code in tracking:
                            tracking_mapped_count += 1
                            tracking_id = self.env["marketplace.order.tracking"].create({
                                "order":  shipment.fulfillment_id.shop_order_id.order_number,
                                "customer": shipment.fulfillment_id.shop_order_id.shipping_contact_person,
                                "warehouse_id": warehouse.id,
                                "carrier" : shipment.carrier_name,
                                "tracking_code": code,
                                "marketplace": shipment.fulfillment_id.shop_order_id.sale_order_id.market_place_shop,
                                "tracking_date": date,
                                "processing_time": processing_shift,
                            })
                            shipment.tracking_id = tracking_id.id
                            shipment.processing_time = processing_shift
                            shipment.forwarded_to_shop = True
                    else:
                        tracking_id = self.env["marketplace.order.tracking"].create({
                            "order":  shipment.fulfillment_id.shop_order_id.order_number,
                            "customer": shipment.fulfillment_id.shop_order_id.shipping_contact_person,
                            "warehouse_id": warehouse.id,
                            "carrier" : shipment.carrier_name,
                            # "tracking_code": code,
                            "marketplace": shipment.fulfillment_id.shop_order_id.sale_order_id.market_place_shop,
                            "tracking_date": date,
                            "processing_time": processing_shift,
                        })
                        shipment.tracking_id = tracking_id.id
                        shipment.processing_time = processing_shift
                        shipment.forwarded_to_shop = True
                        tracking_mapped_count += 1

            except Exception as e:
                tracking_error_count +=1 
        return self.show_tracking_map_wizards(tracking_mapped_count, tracking_error_count)



    
    #######################
    # tracking wizards message
    #######################
    def show_tracking_map_wizards(self,tracking_mapped_count, tracking_error_count):

        message = ""
        name = "Tracking Report"
        message = ("Tracking Mapped in  -  "+str(tracking_mapped_count )+" Deliveries<br/>")
        message += ("Tracking Mapping Erorr in - "+str(tracking_error_count)+"<br/>")
        if message:
            return self.env['everstox.shop.wizard'].show_wizard_message(message, name)



    # Process Shipment Tracking Updates
    def process_shipment_tracking(self, shipment, data):
        if shipment.forwarded_to_shop != data.get("forwarded_to_shop"):
            shipment.forwarded_to_shop = data.get("forwarded_to_shop")
        if shipment.tracking_codes != data.get("tracking_codes"):
            shipment.tracking_codes = data.get("tracking_codes")
        if shipment.tracking_urls != data.get("tracking_urls"):
            shipment.tracking_urls = data.get("tracking_urls")
        if shipment.rma_num != data.get("rma_num"):
            shipment.rma_num = data.get("rma_num")


    ###########
    # API CALLS
    ###########

    def get_shipment_tracking_by_id(self):
        for shipment in self:
            response = False
            call = shipment.everstox_shop_id.shop_url+ "/api/v1/shops/" + shipment.everstox_shop_id.shop_id + "/shipments/" + shipment.shipment_id
            try:
                _logger.info("........... Get Single Shipment Tracking Call  %r ...........",call)
                response = requests.get(call,headers={'everstox-shop-api-token': shipment.everstox_shop_id.shop_api_key,'Content-Type': 'application/json'})
            except Exception as err:
                _logger.info("Get Single Shipment Tracking API fail     %r  !!!!!!!!!", err)

            if response:
                if response.status_code == 200:
                    data = response.json()
                    _logger.info("........%r.....", response.json())
                    
                    self.process_shipment_tracking(shipment, data)

    def put_forwarded_to_shop_true(self):

        for shipment in self:
            call = shipment.everstox_shop_id.shop_url+ "/api/v1/shops/" + shipment.everstox_shop_id.shop_id + "/shipments/" + shipment.shipment_id
            data = {
                "forwarded_to_shop": True
            }
            data = json.dumps(data)
            response = ""
            try:
                response = requests.put(call,headers={'everstox-shop-api-token': shipment.everstox_shop_id.shop_api_key,'Content-Type': 'application/json'},data = data)
            except Exception as err:
                _logger.info("~~~Forward To Shop API fail~~~~~~~~%r~~~~~~~~~", err)

            if response:
                if response.status_code == 200:
                    _logger.info("~~~~~~%r~~~~~",response)
                    # response = response.json()
                    # import pdb; pdb.set_trace()
                    _logger.info("Shipment Updated Successfully      %r   ", response.text)
                else:
                    _logger.info("!!!!!!!! ERROR Response    %r    ", response.text)


class EverstoxShopShipmentItem(models.Model):
    _name = "everstox.order.shipment.item"
    _description = "Everstox Order Shipment Item"

    fulfillment_item_id = fields.Char("Fulfillment Item ID")
    shipment_item_id = fields.Char("Shipment Item ID")
    quantity = fields.Integer("Quantity")

    shipment_batch_ids = fields.One2many("everstox.order.shipped.batches","shipment_item_id","Shipment Batches")
    shipment_id = fields.Many2one("everstox.order.shipment", "Shipment")


class EverstoxShopShipedBatches(models.Model):
    _name = "everstox.order.shipped.batches"
    _description = "Everstox Shipped Batches"

    batch = fields.Char("Batch")
    expiration_date = fields.Char("Expiration Date")    
    batch_id = fields.Char("Batch ID")
    quantity = fields.Integer("Quantity")
    sku = fields.Char("SKU")

    shipment_item_id = fields.Many2one("everstox.order.shipment.item", "Shipment Item")


class EverstoxShopReturn(models.Model):
    _name = "everstox.order.return"
    _description = "Everstox Order Return"
    _rec_name = "return_id"

    return_id = fields.Char("Return ID")
    order_number = fields.Char("Order Number")
    return_reference = fields.Char("Return Reference")
    state = fields.Char("State")
    return_date = fields.Char("Return Date")
    updated_date = fields.Char("Updated Date")
    return_warehouse_id = fields.Char("Warehouse ID")
    return_warehouse_name = fields.Char("Warehouse Name")

    return_item_ids = fields.One2many("everstox.order.return.item", "return_id", "Return Items")
    shop_order_id = fields.Many2one("everstox.shop.order", "Order")
    everstox_shop_id = fields.Many2one("everstox.shop", string= "Shop")
    sale_order_id = fields.Many2one("sale.order", string= "Odoo Order")


class EvertsoxShopReturnItem(models.Model):
    _name = "everstox.order.return.item"
    _description = "Everstox Return Item"
    _rec_name = "return_item_id"

    customer_service_state = fields.Selection([("waiting_for_decision", "Waiting For Decision"),("refunded", "Refunded"),("no_refund", "No Refund"),("replacement_shipped", "Replacement Shipped")],"Customer Service State")
    return_item_id = fields.Char("Return Item ID")
    return_product_id = fields.Char("Return Product ID")
    return_product_name = fields.Char("Return Product Name")
    return_product_sku = fields.Char("Return Product Sku")
    quantity = fields.Integer("Quantity")
    return_reason = fields.Char("Return Reason")
    return_reason_code = fields.Char("Return Reason Code")
    stock_state = fields.Char("Stock State")

    return_id = fields.Many2one("everstox.order.return", "Return")
