from dataclasses import field
from odoo import fields,api, models,_
import requests
import pytz
import json
import datetime
from odoo.exceptions import UserError, ValidationError, MissingError
import pprint
from odoo.tools import float_compare
from asyncio.log import logger

import logging
_logger = logging.getLogger(__name__)

class Seller(models.Model):
    _name = 'manomano.seller'
    _description = 'ManoMano Seller Managment'

    activate = fields.Boolean("Activate")
    name = fields.Char("Name")
    warehouse_id = fields.Many2one("stock.warehouse", "Warehouse",required=True)

    # Only authorize person view
    api_key = fields.Char("Seller API Key", required = True)
    geting_url = fields.Char("Seller URL", required = True) 
    seller_contract_id = fields.Integer("Seller Contract Id",required = True)
    least_qty_to_zero = fields.Integer(string='Leaset Quantity to make zero')
    

    #order management field
    order_reference = fields.Char("Order Refrence")
    manomano_status = fields.Selection([
        ('PENDING','Pending'),
        ('WAITING_PAYMENT','Waiting Payment'),
        ('REFUSED','Refused'),
        ('PREPARATION','Preparation'),
        ('SHIPPED','Shipped'),
        ('REFUNDED','Refunded'),
        ('REFUNDING','Refunding'),
        ('REMORSE_PERIOD','Remorse Period'),
    ])
    carrier =fields.Char("Carrier")

    # Date Filter
    created_at_start = fields.Datetime("Create Date",default=fields.Datetime.now())
    created_at_end = fields.Date("End Date")
    status_updated_at_start = fields.Date("Status Start")
    status_updated_at_end = fields.Date("Status End")
    limit = fields.Integer("Limit", default="50")
    page = fields.Integer("Page")
    is_filter_activate = fields.Boolean("Activate Filters")
    date_filter = fields.Boolean("Date Filter")

    # Counter
    total_offer_count = fields.Integer("Total Offer Count", compute="_get_offer_count")
    offer_created_count = fields.Integer("Offer Created Count", default=0) 
    offer_updated_count = fields.Integer("Offer Updated Count", default=0) 
    manomano_sale_order_waiting_count = fields.Integer("Waiting Sale Orders", compute = "_sale_order_count")
    manomano_sale_order_waiting_payment_count = fields.Integer("Waiting Payment Sale Orders", compute = "_sale_order_count")
    manomano_sale_order_shipping_count = fields.Integer("Shipping Sale Orders", compute = "_sale_order_count")
    manomano_sale_order_shipped_count = fields.Integer("Shipped Sale Orders", compute = "_sale_order_count")
    total_sale_order_count = fields.Integer("Total Sale Order Count", compute="_get_sale_order_count")
    order_created_count = fields.Integer("Order Created Count", default=0) 
    order_updated_count = fields.Integer("Order Updated Count", default=0) 
    order_error_count = fields.Integer("Order Error Count", default=0)

    carrier_count = fields.Integer("ManoMano Carriers", compute = "_shop_carrier_count")
   

    #################
    # Helper Methods
    ##################

    # Compute Shop Offer Count 
    def _shop_carrier_count(self):
        for shop in self:
            shop.carrier_count = self.env["manomano.carrier"].search_count([('shop_id', '=', self.id)])
    
    # Compute SO Count Of This Shop
    def _get_sale_order_count(self):
        for shop in self:
            shop.total_sale_order_count = self.env["sale.order"].search_count([('manomano_order_id', '!=', ''), ('manomano_shop_id','in',[shop.id])])
            
    # Compute SO Count In Different Stages
    def _sale_order_count(self):
        for shop in self:
            order_count = 0
            waiting_count = 0
            payment_count = 0
            shipping_count = 0
            shipped_count = 0
            sale_orders = self.env['sale.order'].search([('manomano_order_id', '!=', ''), ('manomano_shop_id', 'in', [shop.id])])
            for order in sale_orders:
                if order.manomano_shop_id.id == shop.id:
                    order_count +=1
                    if order.status == "PENDING":
                        waiting_count +=1
                    if order.status == "WAITING_PAYMENT":
                        payment_count +=1
                    if order.status == "PREPARATION":
                        shipping_count +=1
                    if order.status == "SHIPPED":
                        shipped_count +=1
            shop.manomano_sale_order_waiting_count = waiting_count
            shop.manomano_sale_order_waiting_payment_count = payment_count
            shop.manomano_sale_order_shipping_count = shipping_count
            shop.manomano_sale_order_shipped_count = shipped_count

    #Method to convert Odoo date format to Manomanao date format.......
    def get_manomano_date_format(self, odoo_date_format):
        if odoo_date_format:
            date_time_string = fields.Datetime.to_string(odoo_date_format).replace("/", "-").replace(" ", "T")+ 'Z'
        else:
            date_time_string = False
        return date_time_string
    
    #method getting odoo date_time_format
    def get_odoo_date_format(self, manomano_date_format):
        if manomano_date_format:
            date_time_string = manomano_date_format.replace("T", " ")[0:manomano_date_format.find(":")+6] if manomano_date_format else False
        else:
            date_time_string = False
        if "+" in date_time_string:
            date_time_string = date_time_string.split("+")[0]
        return date_time_string


    ###############
    # Get Order API
    ###############

    # Get Orders Call Generator
    def get_all_orders(self):
        call = self.geting_url+"/orders/v1/orders"
        # Add Seller Id 
        if self.seller_contract_id:
            call += "?seller_contract_id=" + str(self.seller_contract_id)
            
            # filters
            if self.limit:
                call += "&limit=" + str(self.limit)

            if self.env.context.get('skip_filter'):
                if self.env.context.get("waiting"):
                    call += "&status=PENDING"
                if self.env.context.get("shipping"):
                    call += "&status=PREPARATION"
                
            else:
                if self.is_filter_activate:
                    if self.manomano_status:
                        call += "&status=" + self.manomano_status 
                    if self.order_reference:
                        call += "&order_reference=" + self.order_reference 
                    if self.carrier:
                        call+= "&carrier=" + self.carrier
                    if self.created_at_start:
                        call += '&created_at_start='+ self.get_manomano_date_format(self.created_at_start)
                    if self.created_at_end:
                        call += '&created_at_end=' + self.get_manomano_date_format(self.created_at_end)
                    if self.status_updated_at_start:
                        call += '&status_updated_at_start=' + self.get_manomano_date_format(self.status_updated_at_start)
                    if self.status_updated_at_end:
                        call += '&status_updated_at_end=' + self.get_manomano_date_format(self.status_updated_at_end)
            
            # Pagingation 
            page = 0
            self.order_created_count = 0
            self.order_updated_count = 0
            self.order_error_count = 0
            while(True):
                if "&page=" in call:
                    to_remove = "&page="+ str(page)
                    call = call.replace(to_remove, "")
                page += 1
                call += "&page=" + str(page)
                response = self.get_new_order(call)
                if not response:
                    break
            return self.show_order_message()
            
    # Get Orders API
    def get_new_order(self,call):

        _logger.info("Get All Orders API Call ............... %r  ",call)
        try:
            response = requests.get(call,headers={'x-api-key': self.api_key,'Accept':'application/json'}).json()
        except Exception as err:
             _logger.info("Getting Order API call error........... %r ;;;;;",err)
             return False
        if not response.get("content"):
            return False
        else:
            for order in response.get("content"):
                self.create_sale_order_api(order)
            if len(response.get("content"))< 50:
                return False
            return True
    
    
    #######################
    # order wizards message
    #######################
    def show_order_message(self):

        message = ""
        name = "Order Report"
        if self.order_created_count:
            message = ("Order Created  -  "+str(self.order_created_count )+"<br/>")
            if self.order_updated_count:
                message += ("Order Updated - "+str(self.order_updated_count)+"<br/>")
                if self.order_error_count:
                    message += ("Error  -  "+str(self.order_error_count )+"<br/>")
        elif self.order_updated_count:
            message = ("Order Updated  -  "+str(self.order_updated_count )+"<br/>")
            if self.order_error_count:
                message += ("Order Error - "+str(self.order_error_count))
        else:
            if self.order_error_count:
                message = ("Order Error -  "+str(self.order_error_count))
        if message:
            return self.env['manomano.wizard'].show_wizard_offer_message(message, name)
        else:
            return self.env['manomano.wizard'].show_wizard_offer_message("No Order To Get", name)

    # Get Product
    def get_product_api(self, line):
        product_env = self.env['product.product']
        prod = product_env.search([('default_code', '=', line.get("seller_sku"))])
        if len(prod) <= 0:
            prod = product_env.search([('barcode', '=', line.get('seller_sku'))])
        return prod

    # Get Warehouse
    def _get_warehouse(self):
        warehouse = self.warehouse_id
        if not warehouse:
            raise MissingError(_('Please assign a Warehouse to this shop first - (Shop: )'))
        else:
            return warehouse.id
    
    # Create Sale Order
    def create_sale_order_api(self, order):

        sale_order_id = self.env['sale.order'].search([('manomano_order_id', '=', order.get('order_reference'))], limit=1)
        
        if  sale_order_id:
            # Update Sale Order
            self.order_update(order)
            self.order_updated_count += 1
            _logger.info("~~Order Updated~~~~~~~~~%r~~~~~~~~~~", sale_order_id)
        else:
            # Create Sale Order
            sale_order_id = False
            try:
                customer_id = self._create_customer_api(order)
            except Exception as e:
                _logger.info("Customer creation error~~~~~~~   %r     %r;;;;;",order.get('customer'),e)
                customer_id = False
            if customer_id:
                try:
                    billing_id = self._create_billing_customer_api(order.get('addresses').get("billing"), customer_id)
                except Exception as e:
                    _logger.info("Billing creation error~~~~~~~   %r     %r;;;;;",order.get('addresses').get("billing"), e)
                    billing_id = False
                try:
                    shipping_id = self._create_shipping_customer_api(order.get('addresses').get("shipping"), customer_id)
                except Exception as e:
                    _logger.info("Shipping creation error~~~~~~   %r    %r    ;;;;", order.get('addresses').get("shipping"), e)
                    shipping_id = False

            # Assign Warehouse            
            warehouse_id = False
            try:
                warehouse_id = self._get_warehouse()
            except:
                _logger.info("Warehouse not assigned error in the shop ;;;;;")
                warehouse_id = False

            # Create Order Lines
            try:
                order_line = self.get_sale_order_lines_api(order.get('products'))
            except:
                _logger.info("Order Line creation error ;;;;;")
                order_line = False

            # Fiscal Postion
            partner = self.env["res.partner"].search([('id', 'in', [shipping_id])])
            if not partner.country_id:
                if "DE" in order.manomano_shop_id.name:
                    country_id = self.env['res.country'].search([('code', '=', 'DE')])
                if "GB" in order.manomano_shop_id.name:
                    country_id = self.env['res.country'].search([('code', '=', 'GB')])
                if "FR" in order.manomano_shop_id.name:
                    country_id = self.env['res.country'].search([('code', '=', 'FR')])
                if "ES" in order.manomano_shop_id.name:
                    country_id = self.env['res.country'].search([('code', '=', 'ES')])
                if "IT" in order.manomano_shop_id.name:
                    country_id = self.env['res.country'].search([('code', '=', 'IT')])
                partner.country_id = country_id
            company_id = self.env.company
            fiscal_id = self.env['account.fiscal.position'].with_company(company_id).get_fiscal_position(partner.id)

            # Set Order Status
            odoo_state = None
            if order.get("status"):
                if order.get("status") == 'SHIPPED':
                    mirakl_state = 'shipped'
                    odoo_state = 'sale'
                elif order.get("status") == 'PENDING':
                    mirakl_state = 'waiting_acceptance'
                    odoo_state = 'draft'
                elif order.get("status") == 'REFUNDED':
                    mirakl_state = 'canceled'
                    odoo_state = 'cancel'
                elif order.get("status") == 'REFUSED':
                    mirakl_state = 'refused'
                    odoo_state = 'cancel'
                elif order.get("status") == 'PREPARATION':
                    odoo_state = 'sale'
                    mirakl_state = 'shipping'
                else:
                    mirakl_state = 'closed'
                    odoo_state = 'sale'

            # Create Order
            if customer_id and billing_id and shipping_id and warehouse_id and order_line:
                try:
                    sale_order = self.env['sale.order'].create({
                        'partner_id': customer_id,
                        'partner_invoice_id': billing_id,
                        'partner_shipping_id': shipping_id,
                        'manomano_shop_id': self.id,
                        'market_place_shop': self.name,
                        'warehouse_id': warehouse_id if warehouse_id else False,
                        'order_line': order_line,
                        'manomano_order_id': order.get("order_reference"),
                        'mirakl_order_state': mirakl_state,
                        'status': order.get("status") if order.get("status") else False,
                        'state': odoo_state,
                        'total_price_amount':order.get("total_price").get("amount") if order.get("total_price").get("amount") else  False,
                        'total_price_currency':order.get("total_price").get("currency") if order.get("total_price").get("currency") else  False,
                        'total_price_vat_amount':order.get("total_price_vat").get("amount") if order.get("total_price").get("amount") else  False,
                        'total_price_vat_currency':order.get("total_price").get("currency") if order.get("total_price").get("currency") else  False,
                        'shipping_price_vat_rate':order.get("shipping_price_vat_rate") if order.get("shipping_price_vat_rate") else False,
                        'products_price_amount':order.get("products_price").get("amount") if order.get("products_price").get("amount")  else  False,
                        'products_price_currency':order.get("products_price").get("currency") if order.get("products_price").get("currency") else  False,
                        'products_price_excluding_vat_amount':order.get("products_price_excluding_vat").get("amount") if order.get("products_price_excluding_vat").get("amount") else  False,
                        'products_price_excluding_vat_currency':order.get("products_price_excluding_vat").get("currency") if order.get("products_price_excluding_vat").get("currency") else  False,
                        'products_price_vat_amount':order.get("products_price_vat").get("amount") if order.get("products_price_vat").get("amount") else  False,
                        'products_price_vat_currency':order.get("products_price_vat").get("currency") if order.get("products_price_vat").get("currency") else  False,
                        'manomano_discount_amount':order.get("manomano_discount").get("amount") if order.get("manomano_discount").get("amount") else  False,
                        'manomano_discount_currency':order.get("manomano_discount").get("currency") if order.get("manomano_discount").get("currency") else  False,
                        'order_reference':order.get("order_reference") if order.get("order_reference") else  False,
                        'shipping_discount_amount':order.get("shipping_discount").get("amount") if order.get("shipping_discount").get("amount") else  False,
                        'shipping_discount_currency':order.get("shipping_discount").get("currency") if order.get("shipping_discount").get("currency") else  False,
                        'customer_firstname':order.get("customer").get("firstname") if order.get("customer").get("firstname") else  False,
                        'customer_lastname':order.get("customer").get("lastname") if order.get("customer").get("lastname")  else  False,
                        'is_mmf':order.get("is_mmf") if order.get("is_mmf") else  False,
                        'is_professional':order.get("is_professional") if order.get("is_professional") else  False,
                        'billing_fiscal_number':order.get("billing_fiscal_number") if order.get("billing_fiscal_number") else  False,
                        'fiscal_position_id': fiscal_id.id,
                    })
                    self.order_created_count +=1
                    _logger.info("Sale Order Created............ %r .............", sale_order)
                except Exception as err:
                    self.order_error_count +=1
                    _logger.info("Sale Order Creation Error...........%r ;;;;;",err)

    # Create Customer
    def _create_customer_api(self, order):

        customer_data = order.get('customer')
        if customer_data:

            customer_env = self.env['res.partner']
            customer = customer_env.search([('manomano_customer_id', '=', (customer_data.get('firstname') + ' ' + customer_data.get('lastname')))], limit=1)
            country = False
            if order.get('addresses').get('billing').get("country"):
                country = self.env['res.country'].search([('name', '=', order.get('addresses').get('billing').get("country"))])  
            if len(country) <= 0 and order.get('addresses').get('billing').get("country_iso"):
                country = self.env['res.country'].search([('code', '=', order.get('addresses').get('billing').get("country_iso"))])
            if not customer:
                customer = customer_env.create({
                   'company_type': 'person',
                    'name': customer_data.get('firstname') + ' ' + customer_data.get('lastname'),

                    'phone': order.get('addresses').get('billing').get("phone") if customer_data.get('billing_address') else False,
                    'email': order.get('addresses').get('billing').get('email'),
                    'city': order.get('addresses').get('billing').get("city") if order.get('addresses').get('billing').get("city") else False,
                    'street':order.get('addresses').get('billing').get("address_line1"), 
                    'street2':order.get('addresses').get('billing').get("address_line2"), 
                    'country_id': country.id if country else False,
                    'zip': order.get('addresses').get('billing').get("zipcode") if order.get('addresses').get('billing').get("zipcode") else False,
                    'manomano_customer_id': customer_data.get('firstname') + ' ' + customer_data.get('lastname'),
                })
            return customer.id
        return False

    # Create Billing Address
    def _create_billing_customer_api(self, billing_addresses, customer_id):
        billing_customer = self.env['res.partner'].search([('type', '=', 'invoice'), ('parent_id', '=', customer_id)], limit=1)
        if not billing_customer:

            country = state = full_name = False
            if billing_addresses.get("country"):
                country = self.env['res.country'].search([('name', '=', billing_addresses.get("country"))])  
            if len(country) <= 0 and billing_addresses.get("country_iso"):
                country = self.env['res.country'].search([('code', '=', billing_addresses.get("country_iso"))])
            if billing_addresses.get('firstname'):
                full_name = billing_addresses.get('firstname')
                if billing_addresses.get('lastname'):
                    full_name += " "+ billing_addresses.get('lastname')
            else:
                if billing_addresses.get('lastname'):
                    full_name = billing_addresses.get('lastname')
              
            billing_customer = self.env['res.partner'].create({
                'company_type': 'person',
                'type': 'invoice',
                'name': full_name,
                'parent_id': customer_id,
                'phone': billing_addresses.get("phone") if billing_addresses.get("phone") else False,
                'city': billing_addresses.get("city") if billing_addresses.get("city") else False,
                'street':billing_addresses.get("address_line1"), 
                'street2':billing_addresses.get("address_line2"), 
                'country_id': country.id if country else False,
                'zip': billing_addresses.get("zipcode") if billing_addresses.get("zipcode") else False,
            })
        return billing_customer.id
    
    # Create Shipping Address
    def _create_shipping_customer_api(self, shipping_address, customer_id):
        shipping_customer = self.env['res.partner'].search([('type', '=', 'delivery'), ('parent_id', '=', customer_id)], limit=1)
        if not shipping_customer:
            country = state = full_name = False
            if shipping_address['country']:
                country = self.env['res.country'].search([('name', '=', shipping_address['country'])])
            if len(country) <= 0:
                country = self.env['res.country'].search([('code', '=', shipping_address['country_iso'])])
            if shipping_address.get('firstname'):
                full_name = shipping_address.get('firstname')
                if shipping_address.get('lastname'):
                    full_name += " "+ shipping_address.get('lastname')
            else:
                if shipping_address.get('lastname'):
                    full_name = shipping_address.get('lastname')
            
            shipping_customer = self.env['res.partner'].create({
                'company_type': 'person',
                'type': 'delivery',
                'name': full_name,
                'parent_id': customer_id,
                'street': shipping_address['address_line1'],
                'street2':shipping_address.get("address_line2"), 
                'phone': shipping_address["phone"],
                'city': shipping_address['city'],
                'country_id': country.id if country else False,
                'zip': shipping_address['zipcode'],
            })
        return shipping_customer.id
    
    # Get Order Lines
    def get_sale_order_lines_api(self, products):
        sale_order_lines = []   
        added_line = False
        for line in products:
            try:
                product_id = self.get_product_api(line)
                if len(product_id) > 0:
                    added_line = (0, 0, {
                        'product_id': product_id.id,
                        'name':line.get('title') if line.get('title') else False,
                        'price_unit':line.get('price').get("amount") if line.get('price') else False,
                        'offer_sku': line.get('seller_sku') if line.get('seller_sku') else False,
                        'product_uom_qty':line.get('quantity') if line.get('quantity') else False,
                    })
            except Exception as err:
                _logger.info("Sale Order Line Creation Error~~~~~~~~~~~%r~~~~~~~~~~",err)
            sale_order_lines.append(added_line)
        return sale_order_lines


    #####################
    #Import Order Methods
    #####################

    def process_shipping_orders(self):
        sale_orders = self.env['sale.order'].search([ ('manomano_order_id', '!=', False), ('mirakl_order_state','=','shipping')])
        self.env['shop.integrator'].separate_warehouse_orders(sale_orders)
        return True
        
    def create_sale_order(self,order):
        sale_order = self.env['sale.order'].search([('cdiscount_order_id', '=', order.get('OrderNumber'))], limit=1) or False

        if not sale_order:
            customer_id = self._create_customer(order)
            shipping_id = self._create_shipping_customer(order.get("ShippingAddress"), customer_id)
            order_line = self.get_sale_order_lines(order.get('OrderLineList'),sale_order)
            if customer_id and shipping_id and order_line:
                sale_order = self.env['sale.order'].sudo().create({
                        'partner_id': customer_id,
                        'partner_shipping_id': shipping_id ,
                        'cdiscount_order_id': order.get('OrderNumber'),
                        'order_line': order_line,
                    })
                _logger.info("Sale Order Created~~~~~~%r ;;;;;", sale_order)
                return sale_order
        else:
                _logger.info("Sale Order Already Exist~~~~~~%r ;;;;;", sale_order)

    def get_sale_order_lines(self, order_lines,sale_order):
        sale_order_lines = []
        if isinstance(order_lines['OrderLine'], list):
            for line in order_lines['OrderLine']:
                product_id =  self._create_product(line)
                if product_id and product_id > 0:
                    added_line = (0, 0, {
                            'product_id': product_id,
                            'commission_fee': line.get('commission_fee') if line.get('commission_fee') else False,
                            'description': line.get('Name') if line.get('Name') else False,
                            'offer_sku': line.get('offer_sku') if line.get('offer_sku') else False,
                            'offer_state_code': line.get('offer_state_code') if line.get('offer_state_code') else False,
                            'order_line_index': line.get('order_line_index') if line.get('order_line_index') else False,
                            'order_line_state_reason_code': line.get('order_line_state_reason_code') if line.get('order_line_state_reason_code') else False,
                            'order_line_state_reason_label': line.get('order_line_state_reason_label') if line.get('order_line_state_reason_label') else False,
                            'order_line_index': line.get('order_line_index') if line.get('order_line_index') else False,
                            'price_additional_info': line.get('price_additional_info') if line.get('price_additional_info') else False,
                            'shipping_price': line.get('shipping_price') if line.get('shipping_price') else False,
                            'shipping_price_additional_unit': line.get('shipping_price_additional_unit') if line.get('shipping_price_additional_unit') else False,
                            'shipping_price_unit': line.get('shipping_price_unit') if line.get('shipping_price_unit') else False,
                            'total_commission': line.get('total_commission') if line.get('total_commission') else False,
                        })
                    sale_order_lines.append(added_line)
        else:
            prod_id = self.env['product.product'].search([('name', '=', order_lines['OrderLine']['SellerProductId'])]).id
            line = order_lines['OrderLine']
            if prod_id > 0:
                added_line = (0, 0, {
                    'product_id': prod_id,
                            'commission_fee': line.get('commission_fee') if line.get('commission_fee') else False,
                            'description': line.get('Name') if line.get('Name') else False,
                            'offer_sku': line.get('offer_sku') if line.get('offer_sku') else False,
                            'offer_state_code': line.get('offer_state_code') if line.get('offer_state_code') else False,
                            'order_line_index': line.get('order_line_index') if line.get('order_line_index') else False,
                            'order_line_state_reason_code': line.get('order_line_state_reason_code') if line.get('order_line_state_reason_code') else False,
                            'order_line_state_reason_label': line.get('order_line_state_reason_label') if line.get('order_line_state_reason_label') else False,
                            'order_line_index': line.get('order_line_index') if line.get('order_line_index') else False,
                            'price_additional_info': line.get('price_additional_info') if line.get('price_additional_info') else False,
                            'shipping_price': line.get('shipping_price') if line.get('shipping_price') else False,
                            'shipping_price_additional_unit': line.get('shipping_price_additional_unit') if line.get('shipping_price_additional_unit') else False,
                            'shipping_price_unit': line.get('shipping_price_unit') if line.get('shipping_price_unit') else False,
                            'total_commission': line.get('total_commission') if line.get('total_commission') else False,
                        })
                sale_order_lines.append(added_line)
        return sale_order_lines

    def _create_product(self, line):
        product_env = self.env['product.product']

        prod = product_env.search([('name', '=', line.get('SellerProductId'))])
        return prod.id

    def _create_billing_customer(self, billing_address, customer_id):
        billing_customer = self.env['res.partner'].search([('type', '=', 'invoice'), ('parent_id', '=', customer_id)])
        if not billing_customer:
            country = state = full_name = False
            if billing_address['Country'] == "Espagne":
                country = self.env['res.country'].search([('name', '=', 'Spain')])
            else:
                country = self.env['res.country'].search([('code', '=', billing_address['Country'])])
            if billing_address.get('FirstName'):
                full_name = billing_address.get('FirstName')
                if billing_address.get('LastName'):
                    full_name += " "+ billing_address.get('LastName')
            else:
                if billing_address.get('LastName'):
                    full_name = billing_address.get('LastName')
            billing_customer = self.env['res.partner'].create({
                'company_type': 'person',
                'type': 'invoice',
                'name': full_name,
                'parent_id': customer_id,
                'street': billing_address['Street'],
                'city': billing_address.get("City") if billing_address.get("City") != "None" else False,
                'country_id': country.id if country else False,
                'country_code': country.code if country else False,
                'zip': billing_address.get("ZipCode") if billing_address.get("ZipCode") != "None" else False,
            })
        return billing_customer.id

    def _create_shipping_customer(self, shipping_address, customer_id):
        shipping_customer = self.env['res.partner'].search([('type', '=', 'delivery'), ('phone', '=', shipping_address.get("phone"))],limit=1)
        if not shipping_customer:
            country = state = full_name = False
            if shipping_address['country'] == "Espagne":
                country = self.env['res.country'].search([('name', '=', 'Spain')])
            else:
                country = self.env['res.country'].search([('name', '=', shipping_address['Country'])])
            if shipping_address.get('FirstName'):
                full_name = shipping_address.get('FirstName')
                if shipping_address.get('LastName'):
                    full_name += " "+ shipping_address.get('LastName')
            else:
                if shipping_address.get('LastName'):
                    full_name = shipping_address.get('LastName')
            
            shipping_customer = self.env['res.partner'].create({
                'company_type': 'person',
                'type': 'delivery',
                'name': full_name,
                'parent_id': customer_id,
                'street': shipping_address['Street'],
                'city': shipping_address['City'],
                'country_id': country.id if country else False,
                'country_code': country.code if country else False,
                'zip': shipping_address['ZipCode'],
            })
        return shipping_customer.id

    def _create_customer(self, order):
        customer_data = order.get('Customer')
        if customer_data:
            customer_env = self.env['res.partner']
            customer = customer_env.search([('cdiscount_customer_id', '=', customer_data.get("CustomerId"))])
            if not customer:
                customer = customer_env.create({
                    'company_type': 'person',
                    'name': customer_data.get('FirstName') + ' ' + customer_data.get('LastName'),
                    'phone': customer_data.get("MobilePhone"),
                    'email': customer_data.get('Email'),
                    'cdiscount_customer_id': customer_data.get("CustomerId"),
                    # 'mirakl_locale': customer_data.get("locale"),
                })
            return customer.id
        return False

   
    ###########
    # Offer API
    ###########

    def manomano_inventory_offers(self):
        call = self.geting_url+'/api/v1/offer-information/offers'
        if self.seller_contract_id:
            call += "?seller_contract_id=" + str(self.seller_contract_id)+ "&limit=1000"

        _logger.info("Getting Offer Call ~~~~~~~~%r ;;;;;", call)

        #Getting data
        response = False
        try:
            response = requests.get(call,headers={'x-api-key': self.api_key,'Accept': 'application/json'}).json()
        except Exception as err:
            _logger.info("!!!!!Offer Getting Error~~~~~~~~%r ;;;;;",err)
            raise UserError(_("Offer Getting Error  -  %s", err))
        if response:
            if response.get("content"):
                self.offer_created_count = 0
                self.offer_updated_count = 0
                for offer in response.get("content"):
                    self.create_offers(offer)
                return self.show_offer_message()

    def show_offer_message(self):

        message = ""
        name = "Offer Report"
        if self.offer_created_count:
            message = ("Offer Created  -  "+str(self.offer_created_count))
            if self.offer_updated_count:
                message += ("\nOffer Updated - "+str(self.offer_updated_count))
        else:
            if self.offer_updated_count:
                message = ("Offer Updated -  "+str(self.offer_updated_count))
        if message:
            return self.env['manomano.wizard'].show_wizard_offer_message(message, name)
                
                    
    
     # method for created the offers
    
    def create_offers(self,offer):
        manomano_offer = self.env['manomano.offers'].search([('product_sku', '=', offer.get('sku')),('shop_id','=',self.id)], limit=1) or False
        if not manomano_offer:
            product_id = self.env["product.product"].search([("default_code", "=", offer.get("sku"))], limit =1)
            manomano_offer= self.env["manomano.offers"].create({
                "product_id": product_id.id,
                "product_sku": offer.get("sku"),
                "quantity"  : offer.get("stock"),
                "price"     : offer.get("price"),
                "carrier"   : offer.get("carrier"),
                "offer_id" : offer.get("id_me"),
                "shop_id" :  self.id,
            })
            self.offer_created_count +=1
            _logger.info("Offer Created   ~~~~~~    %r ;;;;;", manomano_offer)
            return manomano_offer
        else:
            self.offer_updated_count += 1
            _logger.info("Offer Updated    ~~~~~~    %r ;;;;;", manomano_offer)
            manomano_offer.shop_id = self.id
            manomano_offer.quantity = offer.get("stock")
            manomano_offer.price = offer.get("price")

    def _get_offer_count(self):
        for shop in self:
            shop.total_offer_count = self.env['manomano.offers'].search_count([('shop_id', '=', shop.id)])

    
    ##################
    # Order Update API
    ##################
 
    def order_update_per_shop(self, shop, orders):
        for order in orders:
            call = "https://partnersapi.manomano.com/orders/v1/orders/"
            call += order.manomano_order_id
            if self.seller_contract_id:
                call += "?seller_contract_id=" + str(shop.seller_contract_id)
            _logger.info("Order Update Call ~~~~~~~~%r ;;;;;", call)

            response = False
            try:
                response = requests.get(call,headers={'x-api-key': shop.api_key,'Accept': 'application/json'}).json()
            except Exception as err:
                _logger.info("!!!!!Update Order Error~~~~~~~~%r ;;;;;",err)
            if response:
                if response.get("content"):
                    self.order_update(response.get("content"))   

    def order_update(self, order_data):
        order_id = self.env['sale.order'].search([('manomano_order_id', '=', order_data.get('order_reference'))], limit=1)
        if order_id:
            self.check_for_customer_updates_manomano(order_data, order_id)
            self.check_for_order_data_changes(order_data, order_id)
            self.sale_order_workflow(order_id)
            self.check_for_delivery_validation(order_id)

    def sale_order_workflow(self, order):
        if order.status in ['WAITING_PAYMENT', 'PREPARATION', "SHIPPED","REFUNDED","REFUNDING","REFUSED"]:
            if order.status in ["REFUNDED","REFUNDING","REFUSED"]:
                order.action_cancel()
            else:
                order.action_confirm()
        if order.mirakl_order_state in ['canceled']:
            order.action_cancel()

    def check_for_customer_updates_manomano(self, order, sale_order):
        # Customer Data
        customer_data = order.get("addresses")
        billing_data = customer_data.get('billing') or False
        shipping_data = customer_data.get('shipping') or False
        
        billing_address = sale_order.partner_invoice_id
        shipping_address = sale_order.partner_shipping_id
        customer_address=  sale_order.partner_id

        if billing_data and shipping_data:
            # Update Billing Address 
            if len(billing_address) > 0:

                biller_name = billing_data.get('firstname') + ' ' + billing_data.get('lastname') if billing_data.get('firstname') else billing_data.get('lastname') if billing_data.get('lastname') else sale_order.partner_id.name
                if billing_address.name != biller_name:
                    billing_address.name = biller_name
                if billing_address.street != billing_data.get("address_line1"):
                    billing_address.street = billing_data.get("address_line1")
                if billing_address.street2 != billing_data.get("address_line2"):
                    billing_address.street2 = billing_data.get("address_line2")
                if billing_address.zip != billing_data.get("zipcode"):
                    billing_address.zip = billing_data.get("zipcode")
                if billing_address.phone != shipping_data.get("phone"):
                    if shipping_data.get("phone"):
                        billing_address.phone = shipping_data.get("phone")
                        sale_order.partner_id.phone = shipping_data.get("phone") or False
                if billing_address.city != billing_data.get('city'):
                    billing_address.city= billing_data.get("city") if billing_data.get("city") != "None" else False
                if billing_address.email != billing_data.get("email"):
                    billing_address.email= billing_data.get("email") if billing_data.get("email") != "None" else False
                
                if len(billing_address.country_id) > 0:
                    if billing_address.country_id.code != billing_data.get('country_iso'):
                        billing_address.country_id = self.env['res.country'].search([('code', '=', billing_data.get('country_iso'))]) or self.env['res.country'].search([('name', '=', billing_data['country'])])
                else:
                    billing_address.country_id = self.env['res.country'].search([('code', '=', billing_data.get('country_iso'))]) or self.env['res.country'].search([('name', '=', billing_data['country'])]) or False
            
            #Update Shipping Address
            if len(shipping_address)>0:
                
                shipper_name = shipping_data.get('firstname') + ' ' + shipping_data.get('lastname') if shipping_data.get('firstname') else shipping_data.get('lastname') if shipping_data.get('lastname') else sale_order.partner_id.name
                if shipping_address.name != shipper_name:
                    shipping_address.name = shipper_name
                if shipping_address.street != shipping_data.get("address_line1"):
                    shipping_address.street = shipping_data.get("address_line1")
                if billing_address.street2 != billing_data.get("address_line2"):
                    billing_address.street2 = billing_data.get("address_line2")
                if shipping_address.zip != shipping_data.get('zipcode'):
                    shipping_address.zip = shipping_data.get('zipcode')
                if shipping_address.phone != shipping_data.get('phone'):
                    if shipping_data.get("phone"):
                        billing_address.phone = shipping_data.get("phone")
                        sale_order.partner_id.phone = shipping_data.get("phone") or False
                if shipping_address.city != shipping_data.get('city'):
                    billing_address.city= shipping_data.get("city") if shipping_data.get("city") != "None" else False
                if shipping_address.email != shipping_data.get('email'):
                    shipping_address.email= shipping_data.get("email") if shipping_data.get("email") != "None" else False
                
                if len(shipping_address.country_id) > 0:
                    if shipping_address.country_id.code != shipping_data.get('country_iso'):
                        shipping_address.country_id = self.env['res.country'].search([('code', '=', shipping_data.get('country_iso'))]) or self.env['res.country'].search([('name', '=', shipping_data['country'])])
                else:
                    shipping_address.country_id = self.env['res.country'].search([('code', '=', shipping_data.get('country_iso'))]) or self.env['res.country'].search([('name', '=', shipping_data['country'])]) or False
            
            # Updata Customer Details
            if len(customer_address)>0:
                
                customer_name = billing_data.get('firstname') + ' ' + billing_data.get('lastname') if billing_data.get('firstname') else billing_data.get('lastname') if billing_data.get('lastname') else sale_order.partner_id.name
                if customer_address.name != customer_name:
                    customer_address.name = customer_name
                if customer_address.street_name != billing_data.get('address_line1'):
                    customer_address.street_name = billing_data.get('address_line1')
                if billing_address.street2 != billing_data.get("address_line2"):
                    billing_address.street2 = billing_data.get("address_line2")
                if customer_address.zip != billing_data.get('zipcode'):
                    customer_address.zip = billing_data.get('zipcode')
                if customer_address.phone != billing_data.get('phone'):
                    if billing_data.get("phone"):
                        sale_order.partner_id.phone = billing_data.get("phone") or False
                if customer_address.city != billing_data.get('city'):
                    customer_address.city= billing_data.get("city") if billing_data.get("city") != "None" else False
                if customer_address.email != billing_data.get('email'):
                    customer_address.email= billing_data.get("email") if billing_data.get("email") != "None" else False
                
                if len(customer_address.country_id) > 0:
                    if customer_address.country_id.code != billing_data.get('country_iso'):
                        customer_address.country_id = self.env['res.country'].search([('code', '=', billing_data.get('country_iso'))]) or self.env['res.country'].search([('name', '=', billing_data['country'])])
                    else:
                        customer_address.country_id = self.env['res.country'].search([('name', '=', billing_data['country'])])
                else:
                    customer_address.country_id = self.env['res.country'].search([('code', '=', billing_data.get('country_iso'))]) or self.env['res.country'].search([('name', '=', billing_data['country'])]) or False

    def check_for_order_data_changes(self, order, sale_order):

        sale_order.market_place_shop =  self.name
        sale_order.created_at = self.get_odoo_date_format(order.get('created_at'))
        if sale_order.created_at:
            sale_order.update_date()

        # Fiscal Postion
        company_id = self.env.company
        fiscal_id = self.env['account.fiscal.position'].with_company(company_id).get_fiscal_position(sale_order.partner_shipping_id.id)
        if fiscal_id and sale_order.fiscal_position_id != fiscal_id:
            _logger.info("Fiscal Position updated in the order -  %r  .......", sale_order)
            sale_order.fiscal_position_id = fiscal_id
            sale_order.order_line._compute_tax_id()
    
        # State Change Check
        if sale_order.status != order.get('status'):
            sale_order.status = order.get('status')

        # Mirakl State Change
        if sale_order.status == 'SHIPPED':
            sale_order.mirakl_order_state = 'shipped'
        elif sale_order.status == 'PENDING':
            sale_order.mirakl_order_state = 'waiting_acceptance'
        elif sale_order.status == 'REFUNDED':
            sale_order.mirakl_order_state = 'canceled'
        elif sale_order.status == 'REFUNDING':
            sale_order.mirakl_order_state = 'canceled'
        elif sale_order.status == 'REFUSED':
            sale_order.mirakl_order_state = 'refused'
        elif sale_order.status == 'PREPARATION':
            sale_order.mirakl_order_state = 'shipping'
        else:
            sale_order.mirakl_order_state = 'closed'

        # Shipping Details Update 
        if sale_order.shipping_price_vat_rate != order.get('shipping_price_vat_rate'):
            sale_order.shipping_price_vat_rate = order.get('shipping_price_vat_rate')

        # Update Order Lines 
        self.check_for_order_line_updates(order.get('products'), sale_order)
    
    def check_for_order_line_updates(self, order_lines, sale_order):
        line_obj = self.env["sale.order.line"]
        for line in order_lines:
            try:
                product_id = self.get_manomano_product(line)
                if product_id :
                    skip = False
                    for ol in sale_order.order_line:
                        if product_id == ol.product_id:
                            skip = True
                            ol.product_uom_qty = line.get("quantity")
                            ol.price_unit = line.get('price').get("amount")
                    if not skip:
                        line_id = line_obj.create({
                            'product_id': product_id.id,
                            'product_uom_qty': line.get('quantity') if line.get('quantity') else False,
                            'price_unit': line.get('price').get("amount") if line.get('price').get("amount") else False,
                            'order_id': sale_order.id,
                        })
                        _logger.info("Sale Order Line Updated.....  %r .........", line_id)
            except Exception as err:
                _logger.info("Sale Order Line Updation Error~~~~~~~~~~~%r~~~~~~~~~~",err)

    def check_for_delivery_validation(self, sale_order):
        if sale_order.status in ["SHIPPED"]:
            if len(sale_order.picking_ids) > 0: 
                for delivery in sale_order.picking_ids:
                    if delivery.state in ["assigned"]:
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
                            delivery.mirakl_carrier_name  = sale_order.carrier
                            delivery.with_context(skip_immediate=True, skip_sms=True).button_validate()
                            sale_order.invoice_status = "to invoice"

        elif sale_order.status in ["REFUNDED"]:
            sale_order.action_cancel()

    def get_manomano_product(self, line):
        product_id = self.env['product.product'].search([('default_code', '=', line.get("seller_sku"))])
        if product_id:
            return product_id
        return False


    ##############
    # Shipment API
    ##############

    def send_shipment_tracking_manomano(self, data, shop_id):
        call = "https://partnersapi.manomano.com/orders/v1/shippings"
        data = json.dumps(data)

        _logger.info("!!!!!~~~~~Shipment Tracking~~~~~~%r~~~~%r~~~~~~",call, data)
        response = False
        try:
            # response = requests.post(call,headers={'x-api-key': shop_id.api_key,'Content-Type': 'application/json'}, data = data)
            pass
        except Exception as err:
            _logger.info("~~~Shipment Tracking API failed~~~~~~~~%r~~~~~~~~~", err)
            response = False
        if response:
            if response.status_code == 400:
                if response.json().get("error").get("message") != "Product already in package":
                    return True
            if response.status_code == 204:
                return True
        else:
            _logger.info(".......Manomano Shipment Updation Error .............")
        return False


    ################
    # Server Actions 
    ################

    # Method to see this shop's all waiting orders
    def action_view_marketplace_waiting_orders(self):
        self.ensure_one()
        # search_view_ref = self.env.ref('odoo_mirakl_integration.mirakl_sale_order_search_inherit_sale', False)
        
        return {
            'type': 'ir.actions.act_window',
            'name': _("%s's Pending Sale Orders", self.name),
            'view_mode': 'list,form',
            'view_ids': [(self.env.ref('manomano_connector.sale_manomano_view_form').id, 'form')],
            'res_model': 'sale.order',
            # 'search_view_id': search_view_ref and [search_view_ref.id],
            'context': {
                'search_default_order_logs': 1,
            },
            'domain': [('manomano_shop_id', 'in', [self.id]), ('status', '=', 'PENDING')],
        }


     # Method to see this shop's all payments pending
    
    # Method to see this shop's all waiting orders
    def action_view_marketplace_waiting_debit_payment_orders(self):
        self.ensure_one()
        # search_view_ref = self.env.ref('manomano_connector.mirakl_sale_order_search_inherit_sale', False)
        
        return {
            'type': 'ir.actions.act_window',
            'name': _("%s's Pending Sale Orders", self.name),
            'view_mode': 'list,form',
            'view_ids': [(self.env.ref('manomano_connector.sale_manomano_view_form').id, 'form')],
            'res_model': 'sale.order',
            # 'search_view_id': search_view_ref and [search_view_ref.id],
            'context': {
                'search_default_order_logs': 1,
            },
            'domain': [('manomano_shop_id', 'in', [self.id]), ('status', '=', 'WAITING_PAYMENT')],
        }

    # Method to see this shop's all shipping orders
    def action_view_marketplace_shipping_orders(self):
        self.ensure_one()
        # search_view_ref = self.env.ref('manomano_connector.mirakl_sale_order_search_inherit_sale', False)
        
        return {
            'type': 'ir.actions.act_window',
            'name': _("%s's Pending Sale Orders", self.name),
            'view_mode': 'list,form',
            'view_ids': [(self.env.ref('manomano_connector.sale_manomano_view_form').id, 'form')],
            'res_model': 'sale.order',
            # 'search_view_id': search_view_ref and [search_view_ref.id],
            'context': {
                'search_default_order_logs': 1,
            },
            'domain': [('manomano_shop_id', 'in', [self.id]), ('status', '=', 'PREPARATION')],
        }

    # Method to see this shop's all shipped orders
    def action_view_marketplace_shipped_orders(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _("%s's Pending Sale Orders", self.name),
            'view_mode': 'list,form',
            'view_ids': [(self.env.ref('manomano_connector.sale_manomano_view_form').id, 'form')],
            'res_model': 'sale.order',
            'context': {
                'search_default_order_logs': 1,
            },
            'domain': [('manomano_shop_id', 'in', [self.id]), ('status', '=', 'SHIPPED')],
        }

    # Method to see this shop's imported today
    def action_view_manomano_sale_order(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _("%s's Manomano Orders", self.name),
            'view_mode': 'list,form',
            'res_model': 'manomano.orders',
            
            'context': {
                'search_default_group_status': 1,
                'search_default_today': 1,
                'warehouse_id': self.warehouse_id.id,
                'shop_id': self.id
            },
            'domain': [('shop_id','=',self.id)]
        }
    
    # Method to see this shop's created by import
    def action_view_sale_orders(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _("Sales Orders Generated from ManoMano"),
            'view_mode': 'list,form',
            'res_model': 'sale.order',
            'search_view_id': [self.env.ref('manomano_connector.view_sale_order_search_manomano').id],
            'context': {
                'search_default_groub_by_date': 1,
                'search_default_status': 1,
            },
            'domain': [('manomano_order_id', '!=', False),('market_place_shop','=',self.name)],
        }

    # Method to see this shop's offers
    def action_view_marketplace_offers(self):
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': _("%s's Offers", self.name),
            'view_mode': 'list,form',
            'view_ids': [(self.env.ref('manomano_connector.view_manomano_offers').id, 'list'), (self.env.ref('manomano_connector.view__manomano_offers_form').id, 'form')],
            'res_model': 'manomano.offers',
            'domain': [('shop_id', 'in', [self.id])],
        }
    
    # Method to see this shop's carrier
    def action_view_marketplace_carriers(self):
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': _("%s's Carriers", self.name),
            'view_mode': 'list,form',
            'view_ids': [(self.env.ref('manomano_connector.view_manomano_carrier').id, 'list'), (self.env.ref('manomano_connector.view_manomano_carrier_form').id, 'form')],
            'res_model': 'manomano.carrier',
            'domain': [('shop_id', 'in', [self.id])],
        }

    
    ###########################
    # Multi Shop Server Actions
    ###########################

    # Method to get all waiting orders
    def get_all_shop_waiting_orders(self):
        for shop in self:
            shop.with_context(skip_filter = True, waiting = True).get_all_orders()

    # Method to get all shipping orders
    def get_all_shop_shipping_orders(self):
        for shop in self:
            shop.with_context(skip_filter = True, shipping = True).get_all_orders()
    
    # Method to Update All waiting and shipping orders
    def update_all_shop_waiting_orders(self):
        for shop in self:
            to_update_orders = self.env["sale.order"].search([('status','in', ['PREPARATION', "PENDING", "WAITING_PAYMENT"]),('manomano_order_id', '!=', False),("manomano_shop_id", "=", shop.id)])
            shop.order_update_per_shop(shop, to_update_orders)

    # Method to accept all waiting orders
    def accept_all_shops_waiting_orders(self):
        for shop in self:
            orders = self.env['sale.order'].search([('manomano_shop_id', 'in', [shop.id]), ('status', '=', 'PENDING')])
            orders.accept_order_maomano()

    # Method to process all shops shipping orders
    def process_all_shop_orders(self):
        for shop in self:
            orders = self.env['sale.order'].search([('manomano_shop_id', 'in', [shop.id]), ('status', '=', 'PREPARATION')])
            orders.export_warehouse_orders()


    def bulk_inventory_update(self,records,shops):
        selected_records = self.env['warehouse.inventory'].browse(records)
        data = []
        _logger.info(selected_records)
        for shop in shops:
            vals = {
                "seller_contract_id": shop.seller_contract_id,
                "items": self.get_items(selected_records,shop)
            }
            data.append(vals)

        inventory_data = {
            "content": data
        }
        logger.info(inventory_data)
        if inventory_data:
            self.send_inventory_update(inventory_data,shops[0])   

    def send_inventory_update(self,data,shop):
        url = "https://partnersapi.manomano.com/api/v2/offer-information/offers"

        payload = json.dumps(data)
        headers = {
            'x-api-key': shop.api_key,
            'Content-Type': 'application/json'
        }
        response = False
        try:
            response = requests.request("PATCH", url, headers=headers, data=payload).json()
            logger.info(response)
        except Exception as err:
            logger.info(err)



    def get_items(self,records,shop):
        data = []
        for record in records:
            etl_warehouse = self.env['marketplace.warehouse'].search([('warehouse_code','=','ETL')])
            cdisc_warehouse = self.env['marketplace.warehouse'].search([('warehouse_code','=','CDISC')])
            inventory = self.env['warehouse.inventory'].search([('warehouse_id','in',[etl_warehouse.id,cdisc_warehouse.id]),('product_id', '=', record.product_id),('create_date', '>=', datetime.datetime.now().strftime('%Y-%m-%d 00:00:00')),('create_date', '<=',datetime.datetime.now().strftime('%Y-%m-%d 23:23:59'))])
            
            stock_count = 0
            if inventory:
            #Adding Cdiscount and ETL inventory stock count
                for inv in inventory:
                    stock_count += inv.available_stock_count
                if stock_count < shop.least_qty_to_zero:
                    stock_count = 0
                vals = {
                    "sku": record.product_id,
                    "stock": {
                        "quantity": int(stock_count)
                    }
                }
                data.append(vals)
            else:
                logger.info("Inventory not found for today")
        return data
