from odoo import http
from odoo.http import request, Response
from asyncio.log import logger
import datetime
import json
from werkzeug.datastructures import ImmutableMultiDict

class SaleOrder(http.Controller):


    @http.route(['/get_tracking_details'], type="json", auth="public", methods=['GET'])
    def get_tracking_details(self,**post):
        headers = request.httprequest.headers
        key_match = request.env['retail.shop.seller'].sudo().search([('api_login','=',headers.get('email_id')),('seller_token','=',headers.get('token'))])
        if key_match:
            orders = json.loads(request.httprequest.data).get('orders')
            order_data = []
            if len(orders):
                for orderNo in orders:
                    tracking = request.env['marketplace.order.tracking'].sudo().search([('order','=',orderNo)],limit=1)
                    if tracking:
                        vals = {
                            "order": orderNo,
                            "tracking_code": tracking.tracking_code,
                            "carrier": tracking.carrier,
                            "tracking_url": tracking.tracking_url
                        }
                        order_data.append(vals)
                return {"data": order_data}
        else:
            return {
                'message': "authentication error"
            }, 401



    @http.route(['/get_inentory_data'], type="http", auth="public", methods=['GET'])
    def get_inentory_data(self,**post):
        headers = request.httprequest.headers
        key_match = request.env['retail.shop.seller'].sudo().search([('api_login','=',headers.get('email_id')),('seller_token','=',headers.get('token') )])
        if key_match: 
            warehouse = key_match.warehouse_id
            inventory_data = request.env['warehouse.inventory'].sudo().search([])
            if len(inventory_data):
                data = []
                for inventory in inventory_data:
                    if inventory.product_id and inventory.create_date.date() == datetime.datetime.now().date() and inventory.warehouse_id.warehouse_code == key_match.warehouse_id.code:
                        
                        #Make qty zero if got less than equal to limit
                        qty = inventory.available_stock_count
                        if qty <= key_match.least_qty:
                            qty = 0
                        vals = {
                            "sku": inventory.product_id,
                            "available_quantity": qty
                        }
                        data.append(vals)
                    else:
                        logger.info("Data not found for this record %s", inventory)
                return json.dumps(data)
                        
            else:
                return "No Inventory data found for today"
        else:
            return http.Response(status="401", mimetype="application/json")


    @http.route(route='/create_order',type="json", auth="public", methods=['POST'])
    def create_order(self, **post):

        headers = request.httprequest.headers
        key_match = request.env['retail.shop.seller'].sudo().search([('api_login','=',headers.get('email_id')),('seller_token','=',headers.get('token') )])
        if key_match: 
            print(json.loads(request.httprequest.data))
            data = json.loads(request.httprequest.data)
            if data:
                result = self.validate_sale_order_data(data)
                if result == True:
                    #Data validated. Go ahead with the sale order creation

                    customer_id = self._create_customer(data)
                    if customer_id:
                        sale_order = request.env['sale.order'].sudo().create({
                            'partner_id': customer_id,
                            'state': 'sale',
                            'mirakl_order_state': 'shipping',
                            "retail_shop_id": key_match.id,
                            'retail_order_id': data.get('order_id'),
                            'warehouse_id': key_match.warehouse_id.id,
                        })
                        if sale_order:
                            print("Sale Oder created")
                            order_line = self.get_sale_order_lines(sale_order,data.get('lines'))

            return result

        else:
            print("Else Condition")
            return http.Response(status="401", mimetype="application/json")
            return http.Response("You are not authorized. Please check your credentials",status="401",mimetype="application/json")
        # return http.Response("Connected to api",status="200",mimetype="application/json")
    

    def get_sale_order_lines(self,order,lines):
        for line in lines:
            product = request.env['product.product'].sudo().search([('name','=',line.get('sku'))], limit=1)
            if product:
                line = request.env['sale.order.line'].sudo().create({
                                    'product_id': product.id,
                                    'name': product.name,
                                    'order_id': order.id,
                                    'product_uom' : product.uom_id.id,
                                    'product_uom_qty': line.get('quantity'),
                                    'price_unit': line.get('unit_price'),
                                    # 'price_subtotal': order1.total_price,
                })
                return line


    def _create_customer(self, order):
        customer_data = order.get('billing_address') if order.get('billing_address') else False
        if customer_data:
            customer_env = request.env['res.partner']
            customer = customer_env.search([('name', 'ilike', customer_data.get('name'))],limit=1)
            if not customer:
                customer = customer_env.create({
                    'company_type': 'person',
                    'name': customer_data.get('name'),
                    # 'phone': customer_data.get("MobilePhone") if customer_data.get("MobilePhone") else False,  #Phone number not coming from api
                    'street': customer_data.get('address1') if customer_data.get('address1') else False,
                    'street2': customer_data.get('address2') if customer_data.get('address2') else False,
                    'zip': customer_data.get('zip_code') if customer_data.get('zip_code') else False,
                    'country_id': request.env['res.country'].search([('code', '=', customer_data.get('country_code'))]).id,
                })
                print("<<<<<-------------Created new customer  with %s ----------->>>>>>>>>", customer)

            else:
                print.info("Customer already exist. checking for updates")
                customer.street = customer_data.get('address1') if customer_data.get('address1') else False
                customer.street2 = customer_data.get('address2') if customer_data.get('address2') else False
                customer.zip = customer_data.get('zip_code') if customer_data.get('zip_code') else False
                
            return customer.id

        else:
            #Check for update
            print("Customer details not found in api data")
        return False

    def validate_sale_order_data(self,order):
        #Warehouse check
        if order.get('warehouse'):
            warehouse = order.get('warehouse')
            if not warehouse.get('warehouse_id'):
                return http.Response("Warehouse code is required field",status="400",mimetype="application/json")
        else:
            return http.Response("Warehouse Information is missing",status="400",mimetype="application/json")
        
        #Billing Address Check

        if order.get('billing_address'):
            billing_address = order.get('billing_address')
            if not billing_address.get('name'):
                return http.Response("Name is required field in billing address",status="400",mimetype="application/json")
            if not billing_address.get('country_code'):
                return http.Response("Country Code is required field in billing address",status="400",mimetype="application/json")
            
            if not billing_address.get('address1') and not billing_address.get('address2') and not billing_address.get('address1'):
                return http.Response("Atleast One Address line is required in Billing address billing address",status="400",mimetype="application/json")
        
        else:
            return http.Response("Billing Address is missing",status="400",mimetype="application/json")
        
        #Shipping Address Check
        if order.get("shipping_address"):
            shipping_address = order.get("shipping_address")
            
            if not shipping_address.get('name'):
                return http.Response("Name is required field in billing address",status="400",mimetype="application/json")
            if not shipping_address.get('country_code'):
                return http.Response("Country Code is required field in billing address",status="400",mimetype="application/json")

            if not shipping_address.get('address1') and not shipping_address.get('address2') and not shipping_address.get('address1'):
                return http.Response("Atleast One Address line is required in Shipping address billing address",status="400",mimetype="application/json")

        else:
            return http.Response("Shipping Address is missing",status="400",mimetype="application/json")
        
        #Order Lines Check


        if order.get("lines"):
            lines = order.get("lines")
            for line in lines:
                if not line.get('sku'):
                    return "SKU is required field in Order Lines"
                if not line.get('quantity'):
                    return "Quantity is required in order line"
                if not line.get('unit_price'):
                    return "Unit Price is required in order line"
        else:
            return "Order line is missing"
        
        return True