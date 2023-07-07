from asyncio.log import logger
from dataclasses import field
from odoo import fields,api, models,_
import base64
import datetime
from datetime import timedelta
import json
import requests
from odoo.exceptions import UserError, ValidationError
import logging
_logger = logging.getLogger(__name__)

class Seller(models.Model):
    _name = 'wayfair.seller'
    _description = 'Wayfair Seller Managment'


    name = fields.Char("name")
    seller_id = fields.Char("Seller Id")
    seller_token = fields.Char("Seller Access Token",store=True)
    product_count = fields.Integer("")
    state = fields.Selection([
        ('draft','Draft'),
        ('done','Confirmed'),
        ('cancel','Cancelled'),
    ])
    api_login = fields.Char("Login ID")
    api_password = fields.Char("Password")
    auth_token = fields.Char("Auth Toekn")
    warehouse_id = fields.Many2one("stock.warehouse", "Warehouse",required=True)
    # api_config_id = fields.Many2one('wayfair.api.config','Api Config')
    token_expiry = fields.Date("Token Expires at")
    sale_count = fields.Integer("Total Sale Orders", compute="_sale_order_count")
    shipped_sale_count = fields.Integer("Shipped Sale Orders", compute="_sale_order_count")
    shipping_sale_count = fields.Integer("Shipping Sale Orders", compute="_sale_order_count")
    awaiting_accept_sale_count = fields.Integer("Waiting for Accept", compute="_sale_order_count")
    offer_count = fields.Integer("Offers", compute="_sale_order_count")
    is_filter_activate = fields.Boolean("Activate Filter")
    date_created_start = fields.Date(string='Date From')
    order_number = fields.Char("Order Number")
    starting_number = fields.Char("Starting Number")
    


    def action_view_waiting_orders(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _("Sales Orders Waiting for acceptance"),
            'view_mode': 'list,form',
            'res_model': 'sale.order',
            'domain': [('wayfair_order_id', '!=', False),('wayfair_shop_id','=',self.id),('mirakl_order_state','=','waiting_acceptance')],
        }
    
    def action_view_shipping_orders(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _("Shipping Sales Orders"),
            'view_mode': 'list,form',
            'res_model': 'sale.order',
            'domain': [('wayfair_order_id', '!=', False),('wayfair_shop_id','=',self.id),('mirakl_order_state','=','shipping')],
        }
    

    @api.onchange('seller_token')
    def onchange_token(self):
        if not self.seller_token:
            self.write({'product_count': 0})

    def process_shipping_orders(self):
        sale_orders = self.env['sale.order'].search([ ('wayfair_order_id', '!=', False), ('mirakl_order_state','=','shipping')])
        self.env['shop.integrator'].separate_warehouse_orders(sale_orders)
        return True

    def map_shop_id(self):
        mapped_records = self.env['wayfair.orders'].search([('order_id','!=', False),('shop_id', '=', self.id)])
        for rec in mapped_records:
            rec.order_id.wayfair_shop_id = self.id
            rec.order_id.market_place_shop = self.name
        non_mapped_records = self.env['sale.order'].search([('wayfair_shop_id', '=', False),('wayfair_order_id','!=',False)])
        # uk_wayfair = self.env['wayfair.seller'].search([('')])

        for rec in non_mapped_records:
            rec.wayfair_shop_id = self.id
            rec.market_place_shop = 'Wayfair UK' if rec.wayfair_order_id.startswith("UK") else 'Wayfair DE'

    def get_orders(self,OrderNumber=False):
        from_date = self.date_created_start or (datetime.datetime.now().date() - timedelta(days=3))
        API_URL = 'https://api.wayfair.com/v1/graphql'
        QUERY = "{\"query\":\"query getDropshipPurchaseOrders {\\n\\tgetDropshipPurchaseOrders (\\n        limit: 5000,\\n        fromDate: \\\"%s\\\"\\n\\t\\thasResponse: false\\n\\t) {\\n\\t\\tpoNumber,\\n\\t\\tpoDate,\\n\\t\\torderId,\\n\\t\\testimatedShipDate,\\n\\t\\tcustomerName,\\n\\t\\tcustomerAddress1,\\n\\t\\tcustomerAddress2,\\n\\t\\tcustomerCity,\\n\\t\\tcustomerState,\\n\\t\\tcustomerPostalCode,\\n\\t\\tcustomerEmail,\\n\\t\\torderType,\\n\\t\\tshippingInfo {\\n\\t\\t\\tshipSpeed,\\n\\t\\t\\tcarrierCode\\n\\t\\t},\\n\\t\\tpackingSlipUrl,\\n\\t\\twarehouse {\\n\\t\\t\\tid,\\n\\t\\t\\tname,\\n\\t\\t\\taddress {\\n\\t\\t\\t\\tname,\\n\\t\\t\\t\\taddress1,\\n\\t\\t\\t\\taddress2,\\n\\t\\t\\t\\taddress3,\\n\\t\\t\\t\\tcity,\\n\\t\\t\\t\\tstate,\\n\\t\\t\\t\\tcountry,\\n\\t\\t\\t\\tpostalCode\\n\\t\\t\\t}\\n\\t\\t},\\n\\t\\tproducts {\\n\\t\\t\\tpartNumber,\\n\\t\\t\\tquantity,\\n\\t\\t\\tprice,\\n\\t\\t\\tevent {\\n\\t\\t\\t\\tid,\\n\\t\\t\\t\\ttype,\\n\\t\\t\\t\\tname,\\n\\t\\t\\t\\tstartDate,\\n\\t\\t\\t\\tendDate\\n\\t\\t\\t}\\n\\t\\t},\\n\\t\\tshipTo {\\n\\t\\t\\tname,\\n\\t\\t\\taddress1,\\n\\t\\t\\taddress2,\\n\\t\\t\\taddress3,\\n\\t\\t\\tcity,\\n\\t\\t\\tstate,\\n\\t\\t\\tcountry,\\n\\t\\t\\tpostalCode,\\n\\t\\t\\tphoneNumber\\n\\t\\t}\\n\\t}\\n}\",\"variables\":{}}" % (str(from_date))
        if self.order_number or OrderNumber:
            QUERY = "{\"query\":\"query getDropshipPurchaseOrders {\\n\\tgetDropshipPurchaseOrders (\\n\\t\\thasResponse: false,\\n        poNumbers: \\\"%s\\\",\\n\\t) {\\n\\t\\tpoNumber,\\n\\t\\tpoDate,\\n\\t\\torderId,\\n\\t\\testimatedShipDate,\\n\\t\\tcustomerName,\\n\\t\\tcustomerAddress1,\\n\\t\\tcustomerAddress2,\\n\\t\\tcustomerCity,\\n\\t\\tcustomerState,\\n\\t\\tcustomerPostalCode,\\n\\t\\tcustomerEmail,\\n\\t\\torderType,\\n\\t\\tshippingInfo {\\n\\t\\t\\tshipSpeed,\\n\\t\\t\\tcarrierCode\\n\\t\\t},\\n\\t\\tpackingSlipUrl,\\n\\t\\twarehouse {\\n\\t\\t\\tid,\\n\\t\\t\\tname,\\n\\t\\t\\taddress {\\n\\t\\t\\t\\tname,\\n\\t\\t\\t\\taddress1,\\n\\t\\t\\t\\taddress2,\\n\\t\\t\\t\\taddress3,\\n\\t\\t\\t\\tcity,\\n\\t\\t\\t\\tstate,\\n\\t\\t\\t\\tcountry,\\n\\t\\t\\t\\tpostalCode\\n\\t\\t\\t}\\n\\t\\t},\\n\\t\\tproducts {\\n\\t\\t\\tpartNumber,\\n\\t\\t\\tquantity,\\n\\t\\t\\tprice,\\n\\t\\t\\tevent {\\n\\t\\t\\t\\tid,\\n\\t\\t\\t\\ttype,\\n\\t\\t\\t\\tname,\\n\\t\\t\\t\\tstartDate,\\n\\t\\t\\t\\tendDate\\n\\t\\t\\t}\\n\\t\\t},\\n\\t\\tshipTo {\\n\\t\\t\\tname,\\n\\t\\t\\taddress1,\\n\\t\\t\\taddress2,\\n\\t\\t\\taddress3,\\n\\t\\t\\tcity,\\n\\t\\t\\tstate,\\n\\t\\t\\tcountry,\\n\\t\\t\\tpostalCode,\\n\\t\\t\\tphoneNumber\\n\\t\\t}\\n\\t}\\n}\",\"variables\":{}}" % (self.order_number or OrderNumber)
        # VARIABLES = None
        api_config = self.env['wayfair.b2c.orders'].sudo().search([('id','=',1)],limit=1)

        if not api_config:
            raise UserError("Api Configration is not set. Please contact your Administrator")
        else:
            #Check auth token
            auth_token = self.get_new_token()
            if auth_token:
                headers = {
                    'content-type': 'application/json',
                    'cache-control': 'no-cache',
                    'authorization': 'Bearer ' + auth_token              }
                
                response = False

                try:
                    logger.info("Api Called with url %s", API_URL)
                    response = requests.request(method='POST', url=API_URL, data=QUERY, headers=headers).json()
                except Exception as err:
                    logger.info(err)
                if response:
                    logger.info(response)
                    self.map_sale_orders(response.get('data'),OrderNumber)
            else:
                logger.info("Error in Api connection")
            
    def map_sale_orders(self,data,OrderNumber):
        new_added = updated = 0
        data = data.get('getDropshipPurchaseOrders')
        sale_orders = self.env['sale.order'].search([('wayfair_order_id','!=',False)]).ids
        for order in data:
            so = self.create_sale_order(order)
            if so.id not in sale_orders:
                new_added += 1
            else:
                updated += 1

        if not OrderNumber:
            raise UserError(_("New Added Orders: %s \n Updated Orders: %s ", str(new_added),str(updated)))



    def check_auth_token(self):
        if self.auth_token:
            d1 = datetime.datetime.strptime(str(datetime.datetime.now().date()),"%Y-%m-%d")
            d2 = datetime.datetime.strptime(str(self.token_expiry), "%Y-%m-%d")
            if d2 > d1:
                logger.info("valid token exits")
                return True
            else:
                #Get token from api
                return self.get_new_token()
        else:
            return self.get_new_token()
               
    def get_new_token(self):
        api_config = self.env['wayfair.b2c.orders'].sudo().search([('id','=',1)], limit=1).wayfair_api_id
        if api_config:
            is_prod = api_config.is_prod
            if api_config:
                url = "https://sso.auth.wayfair.com/oauth/token"
                payload =  {
                    "grant_type":"client_credentials",
                    "client_id": api_config.sb_client_id if not is_prod else api_config.prod_client_id ,
                    "client_secret": api_config.sb_client_secret if not is_prod else api_config.prod_client_secret,
                    "audience": api_config.sb_audience if not is_prod else api_config.prod_audience
                }
                headers = {
                    'content-type': "application/json",
                    'cache-control': "no-cache",
                }
                response = False
                try:
                    response = requests.request("POST", url, data=json.dumps(payload), headers=headers).json()
                except Exception as err:
                    logger.info(err)
                if response:
                    self.auth_token = response.get("access_token")
                    self.token_expiry = datetime.datetime.now() + timedelta(1)
                    return response.get("access_token")
        else:
            logger.info("")
            raise UserError("No Api Confiration found for this shop.Please contact your Administrator")
    

    def get_wayfair_shop(self,orderNumber):
        starting_number = orderNumber[:2]
        return self.env['wayfair.seller'].search([('starting_number','ilike',starting_number)],limit=1)
        

    def get_warehouse(self,warehouse, shipping_address):
        warehouse_name = warehouse.get('name')
        wh = None
        etl_warehouse = self.env['stock.warehouse'].search([('code','=','ETL')],limit=1)
        iful_warehouse = self.env['stock.warehouse'].search([('code','=','IFUL')],limit=1)
        if warehouse_name == 'Surya B.V.-Christchurch':
            wh = iful_warehouse
        else:
            wh = etl_warehouse
        return wh

    def create_sale_order(self,order):
        new_order = updated_order = 0
        sale_order = self.env['sale.order'].search([('wayfair_order_id', '=', order.get('poNumber'))], limit=1) or False
        order_date = order.get('poDate').split()[0]
        if not sale_order:
            customer_id = self._create_customer(order)
            billing_id = self._create_billing_customer(order, customer_id)
            shipping_id = self._create_shipping_customer(order.get("shipTo"), customer_id,order)
            warehouse = self.get_warehouse(order.get('warehouse'),order.get("shipTo"))
            wayfair_shop = self.get_wayfair_shop(str(order.get('poNumber')))
            if customer_id:
                
                partner = self.env["res.partner"].search([('id', 'in', [shipping_id])])
                if not partner.country_id:
                    if "DE" in self.name:
                        country_id = self.env['res.country'].search([('code', '=', 'DE')])
                    if "GB" in self.name:
                        country_id = self.env['res.country'].search([('code', '=', 'GB')])
                    if "UK" in self.name:
                        country_id = self.env['res.country'].search([('code', '=', 'GB')])
                    partner.country_id = country_id
                company_id = self.env.company
                fiscal_id = self.env['account.fiscal.position'].with_company(company_id).get_fiscal_position(partner.id)

                sale_order = self.env['sale.order'].sudo().create({
                    'partner_id': customer_id,
                    'partner_invoice_id':billing_id,
                    'partner_shipping_id': shipping_id,
                    'wayfair_order_id': order.get('poNumber'),
                    'wayfair_platform_order_id': order.get('orderId'),
                    'state': 'draft',
                    'mirakl_order_state': 'waiting_acceptance',
                    'date_order': order_date,
                    'warehouse_id': warehouse.id,
                    'wayfair_shop_id': wayfair_shop.id,
                    'market_place_shop': wayfair_shop.name,
                    'wayfair_estimated_ship_date': order.get('estimatedShipDate'),
                    'wayfair_order_date': order.get("poDate"),
                    'wayfair_carrier_code': order.get('shippingInfo').get('carrierCode') if order.get('shippingInfo') and order.get('shippingInfo').get('carrierCode') else False,
                    'warehouse': order.get('warehouse').get('name') if order.get('warehouse') and order.get('warehouse').get('name') else False, 
                    'delivery_country': order.get("shipTo").get('country') if order.get("shipTo") and order.get("shipTo").get('country') else False,
                    'fiscal_position_id': fiscal_id.id,
                })
                if sale_order:
                    _logger.info("Sale Order Created~~~~~~%r ;;;;;", sale_order)
                    new_order += 1
            logger.info("New Sale Order %s Created ", sale_order)
            lines = self.get_sale_order_lines(order,sale_order)
            self.env.cr.commit()
        else:
            order_date = order.get('poDate').split()[0]

            warehouse = self.get_warehouse(order.get('warehouse'),order.get("shipTo"))
            wayfair_shop = self.get_wayfair_shop(str(order.get('poNumber')))
            _logger.info("Sale Order Already Exist~~~~~~%r ;;;;;", sale_order)
            customer_id = self._create_customer(order)
            billing_id = self._create_billing_customer(order, customer_id)
            shipping_id = self._create_shipping_customer(order.get("shipTo"), customer_id,order)

            # Fiscal Postion
            partner = sale_order.partner_shipping_id
            if not partner.country_id:
                if "DE" in sale_order.wayfair_shop_id.name:
                    country_id = self.env['res.country'].search([('code', '=', 'DE')])
                if "GB" in sale_order.wayfair_shop_id.name:
                    country_id = self.env['res.country'].search([('code', '=', 'GB')])
                if "UK" in sale_order.wayfair_shop_id.name:
                    country_id = self.env['res.country'].search([('code', '=', 'GB')])
                partner.country_id = country_id
            company_id = self.env.company
            fiscal_id = self.env['account.fiscal.position'].with_company(company_id).get_fiscal_position(sale_order.partner_shipping_id.id)
            if fiscal_id and sale_order.fiscal_position_id != fiscal_id:
                _logger.info("Fiscal Position updated in the order -  %r  .......", sale_order)
                sale_order.fiscal_position_id = fiscal_id
                sale_order.order_line._compute_tax_id()
            
            sale_order.write({'partner_id': customer_id, 'date_order': order_date, 'wayfair_estimated_ship_date':order.get('estimatedShipDate'), 'partner_invoice_id': billing_id, 'partner_shipping_id': shipping_id,'wayfair_shop_id': wayfair_shop,'warehouse_id': warehouse.id})
            self.env.cr.commit()
            updated_order += 1
        return sale_order

        


    def get_sale_order_lines(self, order,sale_order):
        lines = order.get("products")
        sale_order_lines = []
        for line in lines:
            product = self.env['product.product'].search([('name','=',line.get('partNumber'))],limit=1)
            if product:
                order_line = self.env['sale.order.line'].create({
                    'product_id': product.id,
                    'name': product.name,
                    'order_id': sale_order.id,
                    'product_uom' : product.uom_id.id,
                    'product_uom_qty': line.get('quantity'),
                    'price_unit': line.get('price'),
                })
                sale_order_lines.append(order_line)
            else:
                logger.info('Product with sku %s not found', line.get('partNumber'))   
        return sale_order_lines

    def _create_shipping_customer(self, billing_address, customer_id,order):
        shipping_customer = self.env['res.partner'].search([('type', '=', 'delivery'), ('parent_id', '=', customer_id)])
        if not shipping_customer:
            shipping_customer = self.env['res.partner'].create({
                'company_type': 'person',
                'type': 'delivery',
                'parent_id': customer_id,
                'name': billing_address.get("name") if billing_address.get("name") else False,
                'email': order.get('customerEmail') if order.get('customerEmail') else False,
                'street': billing_address.get("address1") if billing_address.get("address1") else False,
                'street2': billing_address.get("address2") if billing_address.get("address2") else False,
                'street_name': billing_address.get("address3") if billing_address.get("address3") else False,
                'phone': billing_address.get("phoneNumber") if billing_address.get("phoneNumber") else False,
                'city': billing_address.get("city") if billing_address.get("city") else False,
                'country_id': self.env['res.country'].search([('code', '=', billing_address.get('country'))]).id,
                'zip': billing_address.get("postalCode") if billing_address.get("postalCode") else False,
            })
        else:
            #Update Shipping customer details
            logger.info("Shipping Customer Already found. Checking for updates")
            if billing_address.get('address1') and shipping_customer.street != billing_address.get('address1'):
                shipping_customer.street =  billing_address.get('address1')
            if billing_address.get('address2') and shipping_customer.street2 != billing_address.get('address2'):
                shipping_customer.street2 =  billing_address.get('address2')
            if billing_address.get('postalCode') and shipping_customer.zip != billing_address.get('postalCode'):
                shipping_customer.zip =  billing_address.get('postalCode')
            if billing_address.get("city") and shipping_customer.city != billing_address.get('city'):
                shipping_customer.city =  billing_address.get('city')

            if order.get("customerEmail") and shipping_customer.email != order.get('customerEmail'):
                shipping_customer.email =  order.get('customerEmail')

            if billing_address.get('country') and shipping_customer.country_id.code != billing_address.get('country'):
                shipping_customer.country_id = self.env['res.country'].search([('code', '=', billing_address.get('country'))]).id

        return shipping_customer.id

    def _create_billing_customer(self, order, customer_id):
        customer = self.env['res.partner'].search([('type', '=', 'invoice'), ('name', '=', order.get("customerName"))],limit=1)
        if not customer:
            customer = self.env['res.partner'].create({
                'company_type': 'person',
                'type': 'invoice',
                'parent_id': customer_id,
                'name': order.get("customerName") if order.get("customerName") else False,
                'street': order.get("customerAddress1") if order.get("customerAddress1") else False,
                'street2': order.get("customerAddress2") if order.get("customerAddress2") else False,
                'city': order.get("customerCity") if order.get("customerCity") else False,
                'zip': order.get("customerPostalCode") if order.get("customerPostalCode") else False,
                'email': order.get("customerEmail") if order.get("customerEmail") else False,
                'country_id': self.env['res.country'].search([('code', '=', order.get('customerCountry'))]).id
            })
        else:
            logger.info("Billing Customer already found. Checking for updates")
            if order.get('customerAddress1') and customer.street != order.get('customerAddress1'):
                customer.street =  order.get('customerAddress1')
            if order.get('customerAddress2') and customer.street2 != order.get('customerAddress2'):
                customer.street2 =  order.get('customerAddress2')
            if order.get('customerPostalCode') and customer.zip != order.get('customerPostalCode'):
                customer.zip =  order.get('customerPostalCode')
            if order.get("customerCity") and customer.city != order.get('customerCity'):
                customer.city =  order.get('customerCity')
            if order.get('customerCountry') and customer.country_id.code != order.get('customerCountry'):
                customer.country_id = self.env['res.country'].search([('code', '=', order.get('customerCountry'))]).id
            if order.get("customerEmail") and customer.email != order.get('customerEmail'):
                customer.email =  order.get('customerEmail')
        return customer.id

    def _create_customer(self, order):
        customer_env = self.env['res.partner']
        customer = customer_env.search([('name', '=', order.get("customerName")), ('email','=',order.get("customerEmail"))],limit=1)
        if not customer:
            customer = customer_env.create({
                'company_type': 'person',
                'name': order.get("customerName") if order.get("customerName") else False,
                'street': order.get("customerAddress1") if order.get("customerAddress1") else False,
                'street2': order.get("customerAddress2") if order.get("customerAddress2") else False,
                'city': order.get("customerCity") if order.get("customerCity") else False,
                # 'state': order.get("customerState") if order.get("customerState") else False,
                'zip': order.get("customerPostalCode") if order.get("customerPostalCode") else False,
                'email': order.get("customerEmail") if order.get("customerEmail") else False,
                'country_id': self.env['res.country'].search([('code', '=', order.get('customerCountry'))]).id
            })
        else:
            #Update data of customer
            logger.info("Customer already found. Checking for updates")
            if order.get('customerAddress1') and customer.street != order.get('customerAddress1'):
                customer.street =  order.get('customerAddress1')
            if order.get('customerAddress2') and customer.street2 != order.get('customerAddress2'):
                customer.street2 =  order.get('customerAddress2')
            if order.get('customerPostalCode') and customer.zip != order.get('customerPostalCode'):
                customer.zip =  order.get('customerPostalCode')
            if order.get("customerCity") and customer.city != order.get('customerCity'):
                customer.city =  order.get('customerCity')
            if order.get('customerCountry') and customer.country_id.code != order.get('customerCountry'):
                customer.country_id = self.env['res.country'].search([('code', '=', order.get('customerCountry'))]).id
            if order.get("customerEmail") and customer.email != order.get('customerEmail'):
                customer.email =  order.get('customerEmail')
        return customer.id

    def _sale_order_count(self):
        for rec in self:
            sale_orders = self.env['sale.order'].search([ ('wayfair_order_id', '!=', False),('wayfair_shop_id','=',self.id)])
            rec.write({'sale_count': len(sale_orders)})
            shipped_sale_orders = self.env['sale.order'].search([ ('wayfair_order_id', '!=', False),('wayfair_shop_id','=',self.id),('mirakl_order_state','in', ['shipped'])])
            rec.write({'shipped_sale_count': len(shipped_sale_orders)})
            shipping_sale_orders = self.env['sale.order'].search([ ('wayfair_order_id', '!=', False),('wayfair_shop_id','=',self.id),('mirakl_order_state','in', ['shipping'])])
            rec.write({'shipping_sale_count': len(shipping_sale_orders)})
            waiting_accpetance_orders = self.env['sale.order'].search([ ('wayfair_order_id', '!=', False),('wayfair_shop_id','=',self.id),('mirakl_order_state','in', ['waiting_acceptance'])])
            rec.write({'awaiting_accept_sale_count': len(waiting_accpetance_orders)})

    @api.onchange('is_filter_activate')
    def onchange_date_filter_check(self):
        if not self.is_filter_activate:
            self.write({'date_created_start': False, 'order_number': False})
            

    def action_view_wayfair_sale_order(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _("%s's Orders", self.name),
            'view_mode': 'list,form',
            'res_model': 'wayfair.orders',
            'context': {
                'search_default_group_status': 1,
                'search_default_today': 1,
                'warehouse_id': self.warehouse_id.id,
                'shop_id': self.id
            },
            'domain': [('shop_id', '=', self.id)],
        }

    def action_view_sale_orders(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _("Sales Orders Generated from Wayfair"),
            'view_mode': 'list,form',
            'res_model': 'sale.order',
            'domain': [('wayfair_order_id', '!=', False),('wayfair_shop_id','=',self.id)],
        }

    def import_wayfair_labels(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _("Labels Uploaded for wayfair Wayfair"),
            'view_mode': 'list,form',
            'res_model': 'wayfair.labels',
            'domain': [('shop_id','=',self.id)],
        }

    def action_view_wayfair_products(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _("Wayfair Products"),
            'view_mode': 'list,form',
            'res_model': 'wayfair.product.description',
        }

    def prepare_inventory_data(self,records,shop):
        inventory_data = []
        for rec in records:
            vals =  """{
                "supplierId": %s,
                "supplierPartNumber": %s,
                "quantityOnHand": %s,
                "quantityBackordered": 0,
                "quantityOnOrder": 0,
                "itemNextAvailabilityDate": "",
                "productNameAndOptions": %s,
                "discontinued": False
		    }""" % (rec.warehouse_id.wayfair_supplier_id,rec.product_id,rec.available_stock_count,rec.odoo_product_id.wayfair_product_desc)
            inventory_data.append(vals)
        return inventory_data
            
    def register_order_for_shipping(self,order):
        wayfair_order = self.env['sale.order'].search([('wayfair_order_id','=', order),('registered_for_shipping','=',False)],limit=1)
        if wayfair_order:
            marketplace_warehouse = self.env['marketplace.warehouse'].search([('warehouse_code','=',wayfair_order.warehouse_id.code)],limit=1)
            warehouse_id = marketplace_warehouse.wayfair_supplier_id
            ship_date = wayfair_order.wayfair_estimated_ship_date
            API_URL = 'https://api.wayfair.com/v1/graphql'
            payload="{\"query\":\"mutation register {\\n\\tpurchaseOrders {\\n\\t\\tregister (\\n\\t\\t\\tregistrationInput: {\\n\\t\\t\\t\\tpoNumber: \\\"%s\\\",\\n\\t\\t\\t\\twarehouseId: %s,\\n\\t\\t\\t\\trequestForPickupDate: \\\"%s\\\"\\n\\t\\t\\t}\\n\\t\\t) {\\n\\t\\t\\teventDate,\\n\\t\\t\\tpickupDate,\\n\\t\\t\\tconsolidatedShippingLabel {\\n\\t\\t\\t\\turl\\n\\t\\t\\t},\\n\\t\\t\\tshippingLabelInfo {\\n\\t\\t\\t\\ttrackingNumber\\n\\t\\t\\t},\\n\\t\\t\\tpurchaseOrder {\\n\\t\\t\\t\\tpoNumber,\\n\\t\\t\\t\\tshippingInfo {\\n\\t\\t\\t\\t\\tcarrierCode\\n\\t\\t\\t\\t}\\n\\t\\t\\t}\\n\\t\\t}\\n\\t}\\n}\",\"variables\":{}}" % (order, warehouse_id,ship_date)
            
            headers = {
                'Authorization': 'Bearer ' + self.auth_token,
                'Content-Type': 'application/json',
            }
            response = False
            auth_token = self.check_auth_token()
            if auth_token:
                headers = {
                    'Authorization': 'Bearer ' + self.auth_token,
                    'Content-Type': 'application/json',
                }
                try:
                    response = requests.request("POST", url=API_URL, headers=headers, data=payload)
                except Exception as err:
                    logger.info(err)

                if response:
                    logger.info("Order Registered for shipping")
                else:
                    logger.info("Error In API Call")
            else:
                raise UserError("Token Expired")
        else:
            logger.info("Order already registered for shipping")


    def get_wayfair_label(self,order):
        auth_token = self.check_auth_token()
        url = "https://api.wayfair.com/v1/shipping_label/" + order
        if auth_token:
            headers = {
                'Content-Type': 'application/octet-stream',
                'Authorization': 'Bearer ' + self.auth_token
            }
            try:
                response = requests.request("GET", url, headers=headers)
            except Exception as err:
                logger.info("Error in API")
            if response:
                self.write_labels_to_attachment(order,response.content)
        else:
            logger.info("Error while checking ")
    
    def write_labels_to_attachment(self,orderNumber,B64FILE):
        # file_string = B64FILE.encode('utf-8')
        # file_string = B64FILE.encode('ascii')
        wayfair_order = self.env['sale.order'].search([('wayfair_order_id','=', orderNumber),('is_label_attached','=',False)],limit=1)
        attachment = self.env['ir.attachment'].create({'name': 'label','res_model': 'sale.order', 'res_id': wayfair_order.id, 'datas': B64FILE,'raw': B64FILE})
        if attachment:
            logger.info("label attached to order")
            wayfair_order.write({'mirakl_order_state': 'shipping', 'state': 'sale','is_label_attached': True})
            wayfair_order.action_confirm()



    def send_api_call(self,shop,inventory_data,records):
        API_URL = 'https://api.wayfair.com/v1/graphql'
        warehouse = shop.warehouse_id
        api_config = self.env['wayfair.b2c.orders'].sudo().search([('shop_id','=',self.id)], limit=1).wayfair_api_id
        headers = {
            'Content-Type': 'application/json',
            'Cache-Control': 'no-cache',
            'Authorization': 'Bearer ' + shop.auth_token
        }
        data = self.prepare_inventory_data(records,shop)
        QUERY = 'mutation save ($inventory: [inventoryInput]!,$feedKind: inventoryFeedKind) {inventory {save (inventory: $inventory,feedKind: $feedKind) {handle,submittedAt,errors {key,message}}}}'
        VARIABLES = '''{
                        "inventory": %s,
                        "feedKind": "DIFFERENTIAL
                    "}''' % (data)
        graphql_payload = '''{"query": "%s","variables": %s}''' % (QUERY, VARIABLES)
        try:
            response = requests.request("POST", API_URL, headers=headers, data=graphql_payload)
        except Exception as err:
            logger.info(err)
        if response:
            if response.get('inventory'):
                if response.get('inventory').get('save'):
                    errors = response.get('inventory').get('save').get('errors')
                    if not len(errors) > 0:
                        logger.info("Inventory Submitted")
                        logger.info(response.get('data'))
                    else:
                        logger("Error in api %s", errors)
    
    def action_update_marketplace_shop_name(self):
        wayfair_orders = self.env['sale.order'].search([('wayfair_order_id','!=',False)])
        for order in wayfair_orders:
            if order.wayfair_order_id:
                shop = self.get_wayfair_shop(order.wayfair_order_id)
                order.wayfair_shop_id = shop.id
                order.market_place_shop = shop.name
                logger.info(order.market_place_shop)
                
            
