from odoo import fields,api, models,_
import datetime
from odoo.exceptions import UserError
import json
from asyncio.log import logger
import requests
from odoo.tools import float_compare
import logging
_logger = logging.getLogger(__name__)

class WayfairB2bShop(models.Model):
    _name = 'wayfair.b2b.shop'
    _description = 'Wayfair B2B Shop'

    name = fields.Char("Name")
    shop_code = fields.Char("Shop Code")
    auth_token = fields.Char("Auth TOken")
    date_created_start = fields.Date(string='From Date')
    token_expiry = fields.Date("Token Expiry")
    
    warehouse_id = fields.Many2one("stock.warehouse", "Warehouse",required=True)
    stock_picking_type_id = fields.Many2one("stock.picking.type", "Replenishment Operation", domain="[('warehouse_id', '=', warehouse_id)]")



    def action_view_wayfair_b2b_replenishment(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _("%s's Replenishment", self.name),
            'view_mode': 'list,form',
            'res_model': 'wayfair.b2b.replenishment',
            'context': {
                'search_default_today': 1,
            },
            'domain': [('wayfair_b2b_shop_id', '=', self.id),]
        }

    def action_view_wayfair_b2b_sale_order(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _("%s's Orders", self.name),
            'view_mode': 'list,form',
            'res_model': 'wayfair.b2b.sale.order',
            'context': {
                'search_default_today': 1,
            },
            'domain': [('wayfair_b2b_shop_id', '=', self.id),]
        }

        


    def action_view_sale_orders(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _("Sales Orders Generated from Wayfair B2B"),
            'view_mode': 'list,form',
            'res_model': 'sale.order',
            'context': {
                'search_default_groub_by_date': 1,
            },
            'domain': [('wayfair_b2b_shop_id', '=', self.id)],
        }
    

    def get_orders(self,order=False):
        orderNumber = False
        if order:
            orderNumber = order.wayfair_b2b_order_number or order.wayfair_b2b_order_id.purchase_order
        api_config = self.env['wayfair.b2b.orders'].sudo().search([('id','=',1)],limit=1)
        from_date = self.date_created_start or (datetime.datetime.now().date() - datetime.timedelta(days=3))
        API_URL = False
        if api_config.wayfair_api_id.is_prod:
            API_URL = 'https://api.wayfair.com/v1/graphql'
        else:
            API_URL = 'https://sandbox.api.wayfair.com/v1/graphql'
            
        QUERY = "{\"query\":\"query getCastleGatePurchaseOrders {\\n\\tgetCastleGatePurchaseOrders (\\n\\t\\thasResponse: false,\\n        limit: 1000,\\n        fromDate: \\\"%s\\\"\\n\\t) {\\n\\t\\tpoNumber,\\n\\t\\tpoDate,\\n\\t\\torderId,\\n\\t\\testimatedShipDate,\\n\\t\\tcustomerName,\\n\\t\\tcustomerAddress1,\\n\\t\\tcustomerAddress2,\\n\\t\\tcustomerCity,\\n\\t\\tcustomerState,\\n\\t\\tcustomerPostalCode,\\n\\t\\tcustomerEmail,\\n\\t\\torderType,\\n\\t\\tshippingInfo {\\n\\t\\t\\tshipSpeed,\\n\\t\\t\\tcarrierCode\\n\\t\\t},\\n\\t\\tpackingSlipUrl,\\n\\t\\twarehouse {\\n\\t\\t\\tid,\\n\\t\\t\\tname,\\n\\t\\t\\taddress {\\n\\t\\t\\t\\tname,\\n\\t\\t\\t\\taddress1,\\n\\t\\t\\t\\taddress2,\\n\\t\\t\\t\\taddress3,\\n\\t\\t\\t\\tcity,\\n\\t\\t\\t\\tstate,\\n\\t\\t\\t\\tcountry,\\n\\t\\t\\t\\tpostalCode\\n\\t\\t\\t}\\n\\t\\t},\\n\\t\\tproducts {\\n\\t\\t\\tpartNumber,\\n\\t\\t\\tquantity,\\n\\t\\t\\tprice,\\n\\t\\t\\tevent {\\n\\t\\t\\t\\tid,\\n\\t\\t\\t\\ttype,\\n\\t\\t\\t\\tname,\\n\\t\\t\\t\\tstartDate,\\n\\t\\t\\t\\tendDate\\n\\t\\t\\t}\\n\\t\\t},\\n\\t\\tshipTo {\\n\\t\\t\\tname,\\n\\t\\t\\taddress1,\\n\\t\\t\\taddress2,\\n\\t\\t\\taddress3,\\n\\t\\t\\tcity,\\n\\t\\t\\tstate,\\n\\t\\t\\tcountry,\\n\\t\\t\\tpostalCode,\\n\\t\\t\\tphoneNumber\\n\\t\\t}\\n\\t}\\n}\",\"variables\":{}}" % (from_date)
        if orderNumber:
            QUERY = "{\"query\":\"query getCastleGatePurchaseOrders {\\n\\tgetCastleGatePurchaseOrders (\\n\\t\\thasResponse: false,\\n        poNumbers: \\\"%s\\\",\\n\\t) {\\n\\t\\tpoNumber,\\n\\t\\tpoDate,\\n\\t\\torderId,\\n\\t\\testimatedShipDate,\\n\\t\\tcustomerName,\\n\\t\\tcustomerAddress1,\\n\\t\\tcustomerAddress2,\\n\\t\\tcustomerCity,\\n\\t\\tcustomerState,\\n\\t\\tcustomerPostalCode,\\n\\t\\tcustomerEmail,\\n\\t\\torderType,\\n\\t\\tshippingInfo {\\n\\t\\t\\tshipSpeed,\\n\\t\\t\\tcarrierCode\\n\\t\\t},\\n\\t\\tpackingSlipUrl,\\n\\t\\twarehouse {\\n\\t\\t\\tid,\\n\\t\\t\\tname,\\n\\t\\t\\taddress {\\n\\t\\t\\t\\tname,\\n\\t\\t\\t\\taddress1,\\n\\t\\t\\t\\taddress2,\\n\\t\\t\\t\\taddress3,\\n\\t\\t\\t\\tcity,\\n\\t\\t\\t\\tstate,\\n\\t\\t\\t\\tcountry,\\n\\t\\t\\t\\tpostalCode\\n\\t\\t\\t}\\n\\t\\t},\\n\\t\\tproducts {\\n\\t\\t\\tpartNumber,\\n\\t\\t\\tquantity,\\n\\t\\t\\tprice,\\n\\t\\t\\tevent {\\n\\t\\t\\t\\tid,\\n\\t\\t\\t\\ttype,\\n\\t\\t\\t\\tname,\\n\\t\\t\\t\\tstartDate,\\n\\t\\t\\t\\tendDate\\n\\t\\t\\t}\\n\\t\\t},\\n\\t\\tshipTo {\\n\\t\\t\\tname,\\n\\t\\t\\taddress1,\\n\\t\\t\\taddress2,\\n\\t\\t\\taddress3,\\n\\t\\t\\tcity,\\n\\t\\t\\tstate,\\n\\t\\t\\tcountry,\\n\\t\\t\\tpostalCode,\\n\\t\\t\\tphoneNumber\\n\\t\\t}\\n\\t}\\n}\",\"variables\":{}}" % (orderNumber)
        # VARIABLES = None

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
                    self.map_sale_orders(response.get('data'),orderNumber)
            else:
                logger.info("Error in Api connection")

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
        api_config = self.env['wayfair.b2b.orders'].sudo().search([('id','=',1)], limit=1).wayfair_api_id
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
                    # self.token_expiry = datetime.datetime.now() + datetime.timedelta(1)
                    return response.get("access_token")
        else:
            logger.info("")
            raise UserError("No Api Confiration found for this shop.Please contact your Administrator")
    
    def map_sale_orders(self,data,orderNumber):
        new_added = updated = 0
        data = data.get('getCastleGatePurchaseOrders')
        sale_orders = self.env['sale.order'].search([('wayfair_b2b_order_number','!=',False)]).ids
        for order in data:
            so = self.create_sale_order(order)
            self.process_to_done(so)
            if so:
                if so.id not in sale_orders:
                    new_added += 1
                else:
                    updated += 1

        if not orderNumber:
            raise UserError(_("New Added Orders: %s \n Updated Orders: %s ", str(new_added),str(updated)))
    
    def process_to_done(self, sale_order):
        # Validate Delivery 
        if sale_order and sale_order.picking_ids and len(sale_order.picking_ids) > 0:
            for delivery in sale_order.picking_ids:
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

    def create_sale_order(self,order):
        new_order = updated_order = 0
        sale_order = self.env['sale.order'].search([('wayfair_b2b_order_number', '=', order.get('poNumber'))], limit=1) or False
        order_date = order.get('poDate').split()[0]
        if not sale_order:
            customer_id = self._create_customer(order)
            billing_id = self._create_billing_customer(order, customer_id)
            shipping_id = self._create_shipping_customer(order.get("shipTo"), customer_id,order)
            warehouse = self.get_warehouse(order.get('warehouse'),str(order.get('poNumber')))
            wayfair_shop = self.get_wayfair_shop(str(order.get('poNumber')),order.get('warehouse'))
            if warehouse and wayfair_shop:
                if customer_id:
                    sale_order = self.env['sale.order'].sudo().create({
                        'partner_id': customer_id,
                        'partner_invoice_id':billing_id,
                        'partner_shipping_id': shipping_id,
                        'state': 'sale',
                        'mirakl_order_state': 'closed',
                        'wayfair_b2b_order_number': order.get('poNumber'),
                        # 'wayfair_b2b_order_id': order.get('poNumber'),
                        'date_order': order_date,
                        'warehouse_id': warehouse.id,
                        'wayfair_shop_id': wayfair_shop,
                        'wayfair_estimated_ship_date': order.get('estimatedShipDate'),
                        'market_place_shop': self.name,
                        'wayfair_b2b_shop_id': wayfair_shop,
                        'warehouse': order.get('warehouse').get('name') if order.get('warehouse') and order.get('warehouse').get('name') else False, 
                        'delivery_country': order.get("shipTo").get('country') if order.get("shipTo") and order.get("shipTo").get('country') else False

                    })
                    if sale_order:
                        _logger.info("Sale Order Created~~~~~~%r ;;;;;", sale_order)
                        new_order += 1
                logger.info("New Sale Order %s Created ", sale_order)
                lines = self.get_sale_order_lines(order,sale_order)
                self.env.cr.commit()
                        # self.process_to_done(sale_order)
            else:
                logger.info("Order Does not match warehouse and shop condition")
        else:
            # self.process_to_done(sale_order)
            order_date = order.get('poDate').split()[0]
            warehouse = self.get_warehouse(order.get('warehouse'),str(order.get('poNumber')))
            wayfair_shop = self.get_wayfair_shop(str(order.get('poNumber')),order.get('warehouse'))
            _logger.info("Sale Order Already Exist~~~~~~%r ;;;;;", sale_order)
            customer_id = self._create_customer(order)
            billing_id = self._create_billing_customer(order, customer_id)
            shipping_id = self._create_shipping_customer(order.get("shipTo"), customer_id,order)
            sale_order.write({'wayfair_b2b_order_number':order.get('poNumber'),'wayfair_b2b_shop_id':wayfair_shop,'partner_id': customer_id, 'date_order': order_date,  'partner_invoice_id': billing_id, 'partner_shipping_id': shipping_id,'wayfair_shop_id': wayfair_shop,'warehouse_id': warehouse.id})
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
                'street2': billing_address.get("address1") if billing_address.get("address1") else False,
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
    
    def get_wayfair_shop(self,orderNumber,warehouse):
        
        shops = self.env['wayfair.b2b.shop'].search([])
        way_de_shop = way_uk_shop = None
        for shop in shops:
            if shop.warehouse_id.code == 'WAYDE':
                way_de_shop = shop
            else:
                way_uk_shop = shop
        shop_id = False
        if orderNumber.startswith("UK") and warehouse.get('name') == 'CastleGate Surya B.V. WH27':
            shop_id = way_uk_shop.id
        elif orderNumber.startswith("DE") and warehouse.get('name') in ['CastleGate Surya B.V. WH27', 'CastleGate Surya B.V. WH33' ]:
            shop_id = way_de_shop.id
        return shop_id

    def get_warehouse(self,warehouse, orderNumber):
        warehouse_name = warehouse.get('name')
        wh = None
        cg_uk = self.env['stock.warehouse'].search([('code','=','CGUK')],limit=1)
        wayfair_de = self.env['stock.warehouse'].search([('code','=','WAYDE')],limit=1)
        if (orderNumber.startswith('UK') or orderNumber.startswith('DE'))  and warehouse_name == 'CastleGate Surya B.V. WH27':
            wh = cg_uk
        elif orderNumber.startswith('DE') and warehouse.get('name') == 'CastleGate Surya B.V. WH33':
            wh = wayfair_de
        return wh
