from odoo import api, fields, models
import requests
import json
from asyncio.log import logger
import datetime
import base64

class BladeShopOrder(models.Model):
    _name = 'blade.shop.order'
    _description = 'Blade Shop Order'
    _rec_name = 'order_number'
    _inherit = 'mail.thread'

    name = fields.Char(string='Name')
    sale_order_id = fields.Many2one("sale.order","Sale Order")
    base_64 = fields.Html("Base64 file")
    billing_vat_number = fields.Char("Billing Vat Number")
    billing_address_1 = fields.Char("Billing Address 1")
    billing_address_2 = fields.Char("Billing Address 2")
    billing_address_type = fields.Char("Billing Address Type")
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
    picking_instructions = fields.Char("Picking Instructions")

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
    email = fields.Char("Customer Email")

    # Order Details
    creation_date = fields.Char("Creation Date")
    custom_email = fields.Char("Custom Email")
    financial_status = fields.Char("Financial Status")
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
    state = fields.Char("State")
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
    order_line_ids = fields.One2many('blade.shop.order.line','shop_order_id','Order Line')
    label_file = fields.Binary("Label")
    blade_mapped_state = fields.Selection([('mapped', 'Mapped'), ('unmapped', 'Unmapped')],default="unmapped")

    #Returned Fields
    blade_platform_id = fields.Char("Blade Platform ID")

    def prepare_order_and_order_data(self):
        print("Creating Blade Order")
        for order in self:
            shipping_code = False
            if order.sale_order_id.wayfair_order_id:
               shipping_code = "DHL_PrePaid"

            elif order.sale_order_id.amazon_order_id:
                if order.sale_order_id.ship_method_code == 'UPS_EU_DOM_GROUND_DF':
                    shipping_code = "UPS_PrePaid"
                elif order.sale_order_id.ship_method_code == 'ARROW_BULKY_DOM':
                    shipping_code = "Arrow_Collection"

            order_lines = self.get_order_lines(order.order_line_ids)
            order_data = {
                "warehouse": "BOH",
                "order": {
                    "channel": 926,
                    "reference": order.order_number,
                    "currency": "EUR",
                },
                "date_placed": str(datetime.datetime.now().date()),
                "shipping_address": {
                    "first_name": order.shipping_first_name,
                    "last_name": order.shipping_last_name,
                    "address_one": order.shipping_first_name,
                    "address_two": order.shipping_first_name,
                    "address_three": order.shipping_first_name,
                    "town": order.shipping_city,
                    "country_id": order.shipping_country_code,
                    "postcode": order.shipping_zip,
                    "mobile": order.shipping_phone,
                },
                "lines": order_lines,
                "shipping": {
                    "shipping_code": shipping_code,
                    "customer_principal": 0.0

                },
            }
            self.send_data_to_blade(order_data)

    def send_data_to_blade(self,data):
        blade_shop = self.env['blade.shop'].search([],limit=1)
        token = blade_shop.get_token(blade_shop)
        logger.info(token)
        # token = token.get('data')
        # token = token.get('session_token')
        url = blade_shop.production_url if blade_shop.is_prod else blade_shop.sandbox_url
        url += '/orders/goodsouts'
        payload = json.dumps(data)
        logger.info(payload)
        headers = {
            'Access-Token': token,
            'Content-Type': 'application/json'
        }
        response = False
        try:
            # import pdb;pdb.set_trace()
            response = requests.request("POST", url, headers=headers, data=payload).json()
        except Exception as err:
            logger.info(err)
        if response:
            if response.get('data'):
                logger.info("Order Created with %s ID", response.get('data').get('id'))
                self.write({'blade_platform_id': response.get('data').get('id'),'blade_mapped_state':'mapped'})
            else:
                logger.info(response)

    def get_order_lines(self,order_lines):
        lines = []
        for line in order_lines:
            data = {
                "variation": {
                    "sku": line.order_line_product_sku,
                    "channel": 573
                },
                "quantity": float(line.order_line_quantity),
                "net_unit_principal": 100.0,
                "principal_tax": 1619051
            }
            lines.append(data)
        return lines

    def send_labels_to_blade(self):
        for order in self:
            attachments = self.env['ir.attachment'].search([('res_model','=','blade.shop.order'),('res_id','=',order.id)])
            # if order.label_file:
            for attachment in attachments:
                self.send_label_to_api(attachment,order)

    def send_label_to_api(self,label,order):


        label = str(label.datas)
        label = label[2:-2]

        #Label Upload is only working in Blade Production Server for now
        blade_shop = self.env['blade.shop'].search([],limit=1)
        token = blade_shop.get_token(blade_shop)
        if token:
            url = blade_shop.production_url if blade_shop.is_prod else blade_shop.sandbox_url
            url += '/orders/goodsouts/' + order.blade_platform_id +  '/documents'
            for label_place in ['shipping_label', 'document']:
                logger.info("Label api called with %s url", url)
                payload= {
                    "file": label,
                    "name": "label.pdf",
                    "extension": "pdf",
                    "mime": "application/pdf",
                    "category": label_place
                }
                headers = {
                    'Access-Token': token,
                    'Content-Type': 'application/json'
                }
                response = False
                try:
                    response = requests.request("POST", url, headers=headers, data=json.dumps(payload)).json()
                except Exception as err:
                    logger.info(err)
                if response:
                    logger.info(response)
        else:
            logger.info("Error while generating authentication token")


class WarehouseSaleOrderLine(models.Model):
    _name = 'blade.shop.order.line'
    
    shop_order_id = fields.Many2one("blade.shop.order", string="Sale Order")

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
