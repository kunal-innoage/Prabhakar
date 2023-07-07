from asyncio.log import logger
from dataclasses import field
from odoo import fields,api, models,_
from odoo.tools import float_compare
import requests
import pytz
import datetime
from odoo.exceptions import UserError
from datetime import timedelta
import json
import logging
_logger = logging.getLogger(__name__)

class Seller(models.Model):
    _name = 'cdiscount.seller'
    _description = 'CDiscount Seller Managment'


    name = fields.Char("name")
    seller_id = fields.Char("Seller Id")
    seller_token = fields.Char("Seller Access Token",store=True)
    seller_id = fields.Char("Seller ID",store=True)
    product_count = fields.Integer("")
    state = fields.Selection([
        ('draft','Draft'),
        ('done','Confirmed'),
        ('cancel','Cancelled'),
    ])
    api_login = fields.Char("Client ID")
    api_password = fields.Char("Client Secret")
    test_token = fields.Char("",default="")
    warehouse_id = fields.Many2one("stock.warehouse", "Warehouse",required=True)
    sale_count = fields.Integer("Total Sale Orders", compute="_sale_order_count")
    shipped_sale_count = fields.Integer("Shipped Sale Orders", compute="_sale_order_count")
    shipping_sale_count = fields.Integer("Shipping Sale Orders", compute="_sale_order_count")
    offer_count = fields.Integer("Offers", compute="_sale_order_count")
    is_filter_activate = fields.Boolean("Activate Filter")
    order_filter_by_state = fields.Selection([
        ('Accepted', 'Accepted'),
        ('InPreparation','Shipping'),
        ('Shipped','Shipped'),
        ('refuse','Refused'),
        ('Cancelled','Cancelled'),
    ])
    is_business_order = fields.Boolean("Business Order")
    is_date_filter_activate = fields.Boolean("Date Filters")
    date_created_start = fields.Date("Created Start Date")
    date_created_end = fields.Date("Created End Date")
    date_updated_start = fields.Datetime("Updated Start Date")
    date_updated_end = fields.Datetime("Updated End Date")
    recall_order_date = fields.Datetime("Recall Order Date")
    pages_remaining = fields.Integer("Pages Fetched", default=1)
    filter_start_date = fields.Datetime("Initial Start Date")

    new_so_line = fields.Integer("New added line")
    new_added_so = fields.Integer("New added so")
    total_count = fields.Integer("Total Added Orders")
    existing_updated = fields.Integer("Existing updated")

    def _sale_order_count(self):
        for rec in self:
            sale_orders = self.env['sale.order'].search([ ('cdiscount_order_id', '!=', False),('cdiscount_shop_id','=',self.id)])
            rec.write({'sale_count': len(sale_orders)})
            shipped_sale_orders = self.env['sale.order'].search([ ('cdiscount_order_id', '!=', False),('cdiscount_shop_id','=',self.id),('mirakl_order_state','in', ['shipped'])])
            rec.write({'shipped_sale_count': len(shipped_sale_orders)})
            shipping_sale_orders = self.env['sale.order'].search([ ('cdiscount_order_id', '!=', False),('cdiscount_shop_id','=',self.id),('mirakl_order_state','in', ['shipping'])])
            rec.write({'shipping_sale_count': len(shipping_sale_orders)})
            offers = self.env['cdiscount.offers'].search([ ('cdiscount_shop_id','=',self.id)])
            rec.write({'offer_count': len(offers)})

    @api.onchange('seller_token')
    def onchange_token(self):
        if not self.seller_token:
            self.write({'product_count': 0})


    #Onchnge Methods
    @api.onchange('is_date_filter_activate')
    def onchange_date_filter_check(self):
        if not self.is_date_filter_activate:
            self.write({'date_created_start': False,'date_created_end': False,'date_updated_start': False,'date_updated_end': False,})
    
    @api.onchange('is_filter_activate')
    def onchange_date_filter_check(self):
        if not self.is_filter_activate:
            self.write({'date_created_start': False,'is_date_filter_activate':False,'date_created_end': False,'date_updated_start': False,'date_updated_end': False,'order_filter_by_state': False})

    # Buisiness logic methods
    def process_shipping_orders(self):
        sale_orders = self.env['sale.order'].search([ ('cdiscount_order_id', '!=', False), ('mirakl_order_state','=','shipping')])
        self.env['shop.integrator'].separate_warehouse_orders(sale_orders)
        return True

    def cdiscount_order_mapping(self):
        sale_orders = self.env['sale.order'].search([('cdiscount_order_id', '!=', False)])
        for order in sale_orders:
            order.cdiscount_shop_id = self.id
        return True



    # Method to add filters
    def get_filters(self, call,filter_exist):

        # Adding filter params
        if self.is_filter_activate == True:
            # filter_exist = False
            # Adding Different Filters
        # if not special_call:
            if self.order_filter_by_state:
                call += ("&" if filter_exist == True else "?") + 'status=' + self.order_filter_by_state
                filter_exist = True
            # if self.refunded:
            #     call += ("&" if filter_exist == True else "?") + 'refunded =' + self.refunded
            #     filter_exist = True
            # if self.refund_reason_code:
            #     call += ("&" if filter_exist == True else "?") + 'refund_reason_code=' + self.refund_reason_code
            #     filter_exist = True
            if self.date_created_start:
                call += ("&" if filter_exist == True else "?") + 'createdAtMin=' + self.get_cdiscount_date_format(self.date_created_start)
                filter_exist = True
            if self.date_created_end:
                call += ("&" if filter_exist == True else "?") + 'createdAtMax=' + self.get_cdiscount_date_format(self.date_created_end)
                filter_exist = True
            if self.date_updated_start:
                call += ("&" if filter_exist == True else "?") + 'updatedAtMin=' + self.get_cdiscount_date_format(self.date_updated_start)
                filter_exist = True
            if self.date_updated_end:
                call += ("&" if filter_exist == True else "?") + 'updatedAtMax=' + self.get_cdiscount_date_format(self.date_updated_end)
                filter_exist = True
            if self.is_business_order:
                call += ("&" if filter_exist == True else "?") + 'businessOrder=' + 'true'
                filter_exist = True
            # else:
            #     if self.date_created_start:
            #         call += "?" + 'start_date=' + self.get_mirakl_date_format(self.date_created_start)
            #         filter_exist = True
        return call

    def get_cdiscount_date_format(self, odoo_date_format):
        if odoo_date_format:
            date_time_string = fields.Datetime.to_string(odoo_date_format).replace(" ", "T") + "Z"
        else:
            date_time_string = False
        return date_time_string


    def get_orders(self,page=1):
        # raise UserError(_("Order Refreshed successfully"))
        page = self.pages_remaining if self.pages_remaining > 0 else page
        # if self.is_filter_activate:
        #     page = 1
        self.env.cr.commit()
        url = "https://api.octopia-io.net/seller/v2/orders?pageIndex=" + str(page) + "&pageSize=100"
        
        url = self.get_filters(url,True)
        response = None
        if self.seller_token and self.seller_id:
            headers = {
                'Authorization': 'Bearer ' + self.seller_token, 'sellerId': self.seller_id
            }
        else:
            raise UserError(_("Please enter seller id and seller secret key"))
        try:
            response = requests.get(url, headers=headers).json()
            logger.info("Called api with url %s", url)
            logger.info(len(response.get('items')))
        except Exception as err:
            logger.info(err)
        
        if response:
            orders = response.get('items')
            if orders:
                total_count = 0
                new_added_so = new_added_line = 0
                sale_orders = self.env['sale.order'].search([('cdiscount_order_id','!=',False)]).ids

                for order in orders:
                    total_count +=1
                    so = self.create_sale_order(order)
                    if so[0].id not in sale_orders:
                        new_added_so += 1
                        # order.order_id = res[0].id
                    if len(so) > 2:
                        new_added_line += 1
                    self.check_for_delivery_validation(so[0])
                logger.info("Data fetched for page %s", str(page))
                page += 1    
                self.write({'pages_remaining': page,'new_added_so': self.new_added_so + new_added_so , 'new_so_line' : self.new_so_line + new_added_line, 'total_count': self.total_count + total_count, })
                return self.get_orders(page)
            else:
                logger.info("No orders left to get, %s", response)
                updated = self.total_count - (self.new_so_line + self.new_added_so)
                new_added_so, new_added_line, = self.new_added_so, self.new_so_line
                self.write({'new_so_line': 0, 'new_added_so': 0, 'existing_updated': 0,'total_count': 0, 'pages_remaining': 0,'date_created_start': False,'is_filter_activate': False, 'is_date_filter_activate': False})
                self.env.cr.commit()
                raise UserError(_("New Added Order : %s \nUpdated Orders : %s",new_added_so, updated))
            # return self.env['cdiscount.wizard'].show_wizard_message(new_added_so, 0, updated)
            # return self.env['amazon.wizard'].show_wizard_message(self.new_added_so, self.new_so_line, self.total_count - (self.new_so_line + self.new_added_so),self.id,'cdiscount.seller')
            
    def check_for_delivery_validation(self, sale_order):
        if sale_order.mirakl_order_state in ["shipped" ,"closed", "received",'fulfill']:
            if len(sale_order.picking_ids) > 0:
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
        sale_order = self.env['sale.order'].search([('cdiscount_order_id', '=', order.get('orderId'))], limit=1) or False
        if not sale_order:
            customer_id = self._create_customer(order)
            billing_id = self._create_billing_customer(order.get("billingAddress"), customer_id)
            lines = order.get('lines')
            shipping_id = self._create_shipping_customer(lines[0].get("shippingAddress"), customer_id)

            #Check state and assign to vars
            odoo_state, mirakl_state = self.update_order_status(order.get('status'),order)
            warehouse = self.warehouse_id
            etl = self.env['stock.warehouse'].search([('code', '=', 'ETL')])
            for line in lines:
                offer = line.get('offer')
                if offer.get('supplyMode') != 'Fulfillment':
                    warehouse = etl

            if customer_id:
                created_at = order.get("createdAt")
                s1 = created_at.split("T")
                s2 = s1[0] + ' ' + s1[1][:8]
                
                # Fiscal Position
                try:
                    company_id = self.env.company
                    partner = self.env["res.partner"].search([('id', '=', shipping_id)])
                    fiscal_id = self.env['account.fiscal.position'].with_company(company_id).get_fiscal_position(partner.id)
                except Exception as e:
                    _logger.info("~~~~Error while getting the fiscal position~~~~")

                # Sale Order Creation 
                sale_order = self.env['sale.order'].sudo().create({
                        'partner_id': customer_id,
                        'partner_invoice_id': billing_id,
                        'partner_shipping_id': shipping_id ,
                        'cdiscount_order_id': order.get('orderId'),
                        'cdiscount_shop_id': self.id,
                        'market_place_shop': self.name,
                        'date_order': s2,
                        'warehouse_id': warehouse.id,
                        'is_cdisc_business_order': order.get('businessOrder') if order.get('businessOrder') else False,
                        'mirakl_order_state': mirakl_state,
                        'state': odoo_state,
                        'cdisc_purchased_at': order.get('purchasedAt') if order.get('purchasedAt') else False,
                        'cdisc_updated_at': order.get('updatedAt') if order.get('updatedAt') else False,
                        'cdisc_shipped_at_max': order.get('shippedAtMax') if order.get('shippedAtMax') else False,
                        'order_status': order.get('status'),
                        'fiscal_position_id': fiscal_id.id,
                    })
                _logger.info("Sale Order Created~~~~~~%r ;;;;;", sale_order)
            for picking in sale_order.picking_ids:
                picking.cdiscount_order_id = sale_order.cdiscount_order_id
            order_line = self.get_sale_order_lines(lines,sale_order)
        else:
            created_at = order.get("createdAt")
            _logger.info("Sale Order Already Exist~~~~~~%r  Checking for updates;;;;;", sale_order)
            #update state
            logger.info(created_at)
            s1 = created_at.split("T")

            s2 = s1[0] + ' ' + s1[1][:8]
            
            sale_order.sudo().write({'date_order': s2})
            sale_order.sudo().write({'create_date': s2})
            logger.info("After change date >>>>>>" +str(sale_order.date_order))
            odoo_state, mirakl_state = self.update_order_status(order.get('status'),order)
            #update customer and shipping address
            customer_id = self._create_customer(order)
            billing_id = self._create_billing_customer(order.get("billingAddress"), customer_id)
            lines = order.get('lines')
            for picking in sale_order.picking_ids:
                picking.cdiscount_order_id = sale_order.cdiscount_order_id
            shipping_id = self._create_shipping_customer(lines[0].get("shippingAddress"), customer_id)
            sale_order.write({'partner_id':customer_id, 'partner_invoice_id':billing_id, 'partner_shipping_id' : shipping_id, 'state': odoo_state, 'mirakl_order_state' : mirakl_state, 'cdiscount_shop_id': self.id or sale_order.cdiscount_shop_id,'market_place_shop': self.name or sale_order.cdiscount_shop_id.name})
            # Fiscal Position
            company_id = self.env.company
            partner = sale_order.partner_shipping_id
            fiscal_id = self.env['account.fiscal.position'].with_company(company_id).get_fiscal_position(partner.id)
            if fiscal_id and sale_order.fiscal_position_id != fiscal_id:
                sale_order.fiscal_position_id = fiscal_id
                sale_order.order_line._compute_tax_id()

        return (sale_order)
    
    def update_order_status(self, state,order):
        cancellation_details = order.get('cancellationDetails')
        lines = order.get('lines')
        odoo_state = mirakl_state = None
        single_full = False

        if len(lines) >= 0:
            offer = lines[0].get('offer')
            if offer.get('supplyMode') == 'Fulfillment':
                logger.info('/n ********single order line with fullfilment found********** /n')
                single_full = True

        if state == 'Shipped':
            odoo_state = 'sale'
            if single_full:
                mirakl_state = 'fulfill'
            else:
                mirakl_state = 'shipped'
        elif state in ['Accepted','InPreparation']:
            odoo_state = 'sale'
            if single_full:
                mirakl_state = 'fulfill'
            else:
                mirakl_state = 'shipping'
        elif state == 'Cancelled':
            if single_full:
                mirakl_state = 'fulfill'
            else:
                mirakl_state = 'canceled'
            odoo_state = 'cancel'
        
        elif state == 'Refused':
            if single_full:
                mirakl_state = 'fulfill'
            else:
                mirakl_state = 'refused'
            odoo_state = 'cancel'
        if cancellation_details:
            odoo_state = 'cancel'
        return odoo_state,mirakl_state


    def get_sale_order_lines(self, order_lines,sale_order):
        sale_order_lines = []
        if len(order_lines) > 1:
            full = seller = False
            last_order = None
            for line in order_lines:
                if full and seller:
                    logger.info("Inside condition")
                offer = line.get('offer')
                if offer and offer.get('supplyMode') == 'Seller':
                    seller = True
                elif offer and offer.get('supplyMode') =='Fulfillment':
                    full = True
                # last_order = line
                

        for line in order_lines:
            offer = line.get('offer')
            product = self.env['product.product'].search([('name','=',offer.get('sellerProductId'))])
            


            if product:
                order_line = self.env['sale.order.line'].create({
                    'product_id': product.id,
                    'name': product.name,
                    'order_id': sale_order.id,
                    'product_uom' : product.uom_id.id,
                    'product_uom_qty': line.get('quantity'),
                    # 'warehouse_id': warehouse,
                    'price_unit': line.get('totalPrice').get('sellingPrice'),
                    'supply_mode': offer.get('supplyMode') if offer.get('supplyMode') else None
                })
                sale_order_lines.append(order_line)
            else:
                logger.info('Product with sku %s not found', offer.get('sellerProductId') )            
        return sale_order_lines

    def _create_billing_customer(self, billing_address, customer_id):
        billing_customer = self.env['res.partner'].search([('type', '=', 'invoice'), ('parent_id', '=', customer_id)])
        if not billing_customer:
            country = full_name = False
            country = self.env['res.country'].search([('code', '=', billing_address.get('countryCode'))])
            if billing_address.get('firstName'):
                full_name = billing_address.get('firstName')
                if billing_address.get('lastName'):
                    full_name += " "+ billing_address.get('lastName')
            else:
                if billing_address.get('lastName'):
                    full_name = billing_address.get('lastName')
            billing_customer = self.env['res.partner'].create({
                'company_type': 'person',
                'type': 'invoice',
                'name': full_name if full_name else False,
                'parent_id': customer_id,
                'street': billing_address.get('addressLine1') if billing_address.get('addressLine1') else False,
                'street2': billing_address.get('addressLine2') if billing_address.get('addressLine2') else False,
                # 'phone': billing_customer.get("Phone") if billing_customer.get("Phone") != "None" else False,  #Phone number not coming from Api
                'city': billing_address.get("city") if billing_address.get("city") else False,
                # 'state_id': state.id if state else False,
                'country_id': country.id if country else False,
                'country_code': billing_address.get('countryCode') if billing_address.get('countryCode') else False,
                'zip': billing_address.get("postalCode") if billing_address.get("postalCode") != "None" else False,
            })
        else:
            #Check for update
            logger.info("Customer already exist. checking for updates")
            billing_customer.street = billing_address.get('addressLine1') if billing_address.get('addressLine1') else False
            billing_customer.street2 = billing_address.get('addressLine2') if billing_address.get('addressLine2') else False
            billing_customer.city = billing_address.get("city") if billing_address.get("city") else False
            billing_customer.zip = billing_address.get("postalCode") if billing_address.get("postalCode") != "None" else False

            if billing_address.get('addressLine1'):
                if billing_customer.street != billing_address.get('addressLine1'):
                    billing_customer.street =  billing_address.get('addressLine1')
            if billing_address.get('addressLine2'):
                if billing_customer.street2 != billing_address.get('addressLine2'):
                    billing_customer.street2 =  billing_address.get('addressLine2')
            if billing_address.get('postalCode'):
                if billing_customer.zip != billing_address.get('postalCode'):
                    billing_customer.zip =  billing_address.get('postalCode')
            if billing_address.get('phone') and billing_customer.phone != billing_address.get('phone'):
                billing_customer.phone = billing_address.get('phone')
            if billing_address.get('city') and billing_customer.city != billing_address.get('city'):
                billing_customer.city = billing_address.get('city')
            if billing_address.get('email') and billing_customer.email != billing_address.get('email'):
                billing_customer.email = billing_address.get('email')

        return billing_customer.id



    def _create_shipping_customer(self, shipping_address, customer_id):
        shipping_customer = self.env['res.partner'].search([('type', '=', 'delivery'), ('parent_id','=',customer_id)],limit=1)
        if not shipping_customer:
            country = full_name = False
            country = self.env['res.country'].search([('code', '=', shipping_address.get('countryCode'))])
            #Name Formation
            if shipping_address.get('firstName'):
                full_name = shipping_address.get('firstName')
                if shipping_address.get('lastName'):
                    full_name += " "+ shipping_address.get('lastName')
            else:
                if shipping_address.get('lastName'):
                    full_name = shipping_address.get('lastName')
            
            shipping_customer = self.env['res.partner'].create({
                'company_type': 'person',
                'type': 'delivery',
                'name': full_name,
                'parent_id': customer_id,
                'street': shipping_address.get('addressLine1') if shipping_address.get('addressLine1') else False,
                'street2': shipping_address.get('addressLine2') if shipping_address.get('addressLine2') else False,
                'phone': shipping_address.get("phone") if shipping_address.get('phone') else False,
                'city': shipping_address.get('city') if shipping_address.get('city') else False,
                'email': shipping_address.get('email') if shipping_address.get('email') else False,
                # 'state_id': state.id if state else False,
                'country_id': country.id if country else False,
                'country_code': country.code if country else False,
                'zip': shipping_address.get('postalCode') if shipping_address.get('postalCode') else False ,
            })

        else:
            #Check for update
            logger.info("Customer already exist. checking for updates")

            if shipping_address.get('addressLine1'):
                if shipping_customer.street != shipping_address.get('addressLine1'):
                    shipping_customer.street =  shipping_address.get('addressLine1')
            if shipping_address.get('addressLine2'):
                if shipping_customer.street2 != shipping_address.get('addressLine2'):
                    shipping_customer.street2 =  shipping_address.get('addressLine2')
            if shipping_address.get('postalCode'):
                if shipping_customer.zip != shipping_address.get('postalCode'):
                    shipping_customer.zip =  shipping_address.get('postalCode')
            if shipping_address.get('phone') and shipping_customer.phone != shipping_address.get('phone'):
                shipping_customer.phone = shipping_address.get('phone')
            if shipping_address.get('city') and shipping_customer.city != shipping_address.get('city'):
                shipping_customer.city = shipping_address.get('city')
            if shipping_address.get('email') and shipping_customer.email != shipping_address.get('email'):
                shipping_customer.email = shipping_address.get('email')

        return shipping_customer.id

    def _create_customer(self, order):
        customer_data = order.get('billingAddress') if order.get('billingAddress') else False
        full_name = False
        if customer_data.get('firstName'):
            full_name = customer_data.get('firstName')
            if customer_data.get('lastName'):
                full_name += " "+ customer_data.get('lastName')
        else:
            if customer_data.get('lastName'):
                full_name = customer_data.get('lastName')
        if customer_data:
            customer_env = self.env['res.partner']
            customer = customer_env.search([('name', 'ilike', full_name),('cdiscount_customer_id','=', order.get("customer").get('reference'))],limit=1)
            if not customer:
                customer = customer_env.create({
                    'company_type': 'person',
                    'name': full_name,
                    # 'phone': customer_data.get("MobilePhone") if customer_data.get("MobilePhone") else False,  #Phone number not coming from api
                    'cdiscount_customer_id': order.get("customer").get('reference') if order.get("customer") else False,
                    'street': customer_data.get('addressLine1') if customer_data.get('addressLine1') else False,
                    'street2': customer_data.get('addressLine2') if customer_data.get('addressLine2') else False,
                    'zip': customer_data.get('postalCode') if customer_data.get('postalCode') else False,
                    'country_id': self.env['res.country'].search([('code', '=', customer_data.get('countryCode'))]).id,
                })
                logger.info("<<<<<-------------Created new customer  with %s ----------->>>>>>>>>", customer)

            else:
                logger.info("Customer already exist. checking for updates")
                if customer_data.get('addressLine1'):
                    if customer.street != customer_data.get('addressLine1'):
                        customer.street =  customer_data.get('addressLine1')
                if customer_data.get('addressLine2'):
                    if customer.street2 != customer_data.get('addressLine2'):
                        customer.street2 =  customer_data.get('addressLine2')
                if customer_data.get('postalCode'):
                    if customer.zip != customer_data.get('postalCode'):
                        customer.zip =  customer_data.get('postalCode')

                # Customer Data Update
            return customer.id

        else:
            #Check for update
            logger.info("Customer details not found in api data")
        return False

    def update_shop_sale_orders(self, order_data):
        # for order_data in order_data.get("orders"):
        order_id = self.env['sale.order'].search([('cdiscount_order_id', '=', order_data.get('orderId'))], limit=1)
        if order_id:
            self.create_sale_order(order_data)
            # customer_id = self._create_customer(order_data)
            # billing_id = self._create_billing_customer(order_data, customer_id)
            # shipping_id = self._create_shipping_customer(order_data,customer_id)
            self.check_for_delivery_validation(order_id)


    def update_shops_orders(self):
        sale_orders = self.env['sale.order'].search([('cdiscount_shop_id', 'in', [self.id]), ('mirakl_order_state', 'not in', ['shipped','closed','received','refused','canceled','fulfill'])])
        if len(sale_orders) > 0:
            self.get_order_by_ids(self, sale_orders)

    # Method to update orders
    def get_order_by_ids(self, shop_id, sale_orders):
        order_100 = ""
        count = 1
        seller_id = seller_token =  False
        if shop_id:
            seller_id = shop_id.seller_id
            seller_token = shop_id.seller_token
        else:
            seller_token = self.seller_token
            seller_id = self.seller_id
        remaining_order_count = len(sale_orders)
        for order in sale_orders:
                if order.cdiscount_order_id :
                # Hit API
                    call = "https://api.octopia-io.net/seller/v2/orders/" +  order.cdiscount_order_id

                    # TO DO in future if needed
                    # if order.cdiscount_shop_id.shop_id:
                    #     call += "&shop_id=" + order.mirakl_shop_id.shop_id
                    
                    response = False
                    try:
                        _logger.info("Get Order Update for %s~~~~~~~~~%r ;;;;;",order,call)
                        response = requests.get(call,headers={'Authorization': 'Bearer ' + seller_token, 'sellerId': seller_id}).json()
                    except Exception as err:
                        _logger.info("!!!!! Error in Order Updation ~~~~~~~~%s ;;;;;",err)
                    if response:
                        if not response.get('orderId'):
                            # raise UserError(_(self.show_error(response)))
                            logger.info(">>>>> Error in response %s", response)

                        else:
                            # Send order updates 
                            self.update_shop_sale_orders(response)
                    else:
                        _logger.info("Response Error~~~~~~~~%r ;;;;;",response)
                
                #Reset Values
                remaining_order_count -= count
                count = 1
                order_100 = ""
                _logger.info("Remaining Orders to Update for this Shop~~~~~~~~~~%r;;;;;", remaining_order_count)

    def get_last_days_orders(self):
        self.is_filter_activate = True
        self.new_added_so = self.new_so_line = self.total_count = self.existing_updated = 0
        self.pages_remaining = 0
        self.is_date_filter_activate = True
        self.date_created_start = (datetime.datetime.now() - timedelta(days=1)).date()
        self.get_orders(1)
    
    def get_token(self):
        all_shops = self.env['cdiscount.seller'].search([])
        for shop in all_shops:
            url = "https://auth.octopia.com/auth/realms/maas/protocol/openid-connect/token"
            if not shop.api_login or not shop.api_password:
                raise UserError(_("Please Enter login ID and password for API for %s", shop.name))
            else:
                data = {'client_id': shop.api_login, 'client_secret': shop.api_password, 'grant_type': 'client_credentials'}
                try:
                    # response = requests.post(url,data=data).json()
                    shop.write({'seller_token': response.get('access_token')})
                    logger.info("Token generated")
                except Exception as err:
                    logger.info(err)                


    def action_view_cdiscount_sale_order(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _("%s's CDiscount Orders", self.name),
            'view_mode': 'list,form',
            # 'view_ids': [(self.env.ref('odoo_mirakl_integration.view_mirakl_sales_order_tree').id, 'list'), (self.env.ref('odoo_mirakl_integration.view_sales_order_form').id, 'form')],
            'res_model': 'cdiscount.orders',
            'context': {
                'search_default_group_status': 1,
                'search_default_today': 1,
                'warehouse_id': self.warehouse_id.id,
                'shop_id': self.id
            },
            'domain': [('shop_id', '=', self.id)],
        }

    def action_view_shipped_sale_order(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _("%s's Shipped Sale Orders", self.name),
            'view_mode': 'list,form',
            'res_model': 'sale.order',
            'context': {
                'search_default_group_status': 1,
                'search_default_today': 1,
                'warehouse_id': self.warehouse_id.id,
                'shop_id': self.id
            },
            'domain': [('cdiscount_shop_id','=', self.id),('mirakl_order_state','=',['shipped'])],
        }

    def action_view_shipping_sale_order(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _("%s's In Shipping Sale Orders", self.name),
            'view_mode': 'list,form',
            'res_model': 'sale.order',
            'context': {
                'search_default_group_status': 1,
                'search_default_today': 1,
                'warehouse_id': self.warehouse_id.id,
                'shop_id': self.id
            },
            'domain': [('cdiscount_shop_id','=', self.id),('mirakl_order_state','=',['shipping'])],
        }

    def action_view_sale_orders(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _("Sales Orders Generated from Cdiscount"),
            'view_mode': 'list,form',
            # 'view_ids': [(self.env.ref('odoo_mirakl_integration.view_mirakl_sales_order_tree').id, 'list'), (self.env.ref('odoo_mirakl_integration.view_sales_order_form').id, 'form')],
            'res_model': 'sale.order',
            'context': {
                'search_default_groub_by_date': 1,
                # 'search_default_order_logs': 1,
            },
            'domain': [('cdiscount_order_id', '!=', False),('cdiscount_shop_id','=', self.id)],
        }
    
    def action_view_cdiscount_offers(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _("Offers Generated from Cdiscount"),
            'view_mode': 'list,form',
            'res_model': 'cdiscount.offers',
            # 'context': {
            #     # 'search_default_groub_by_date': 1,
            #     # 'search_default_order_logs': 1,
            # },
            # 'domain': [('cdiscount_order_id', '!=', False),('cdiscount_shop_id','=', self.id)],
        }

    def cdsicount_inventory_offers(self,page_number=1):
        # raise UserError("Offers Mapped")
        payload = json.dumps({})
        page_count = page_number
        url = "https://api.octopia-io.net/seller/v2/offers/search?$page=" + str(page_count)
        headers = {
            'Content-Type': 'application/json',
            'SellerId': self.seller_id,
            'Authorization': 'Bearer ' + self.seller_token
        }
        logger.info("Api Call >>> %s", url)
        try:
            response = requests.request("POST", url, headers=headers, data=payload).json()
        except Exception as err:
            logger.info(">>> Error in api %s", err)
        if response:
            total_pages = response.get('page_count')
            offers = response.get('items')
            if len(offers):
                self.map_offers(offers)
            if page_count < response.get('page_count'):
                self.cdsicount_inventory_offers(page_count + 1)
            else:
                logger.info("No new offers left to get from api")



    def map_offers(self,offers):
        offer_obj = self.env['cdiscount.offers']
        for offer in offers:
            stock_id = qty = sold_qty = False
            stock = offer.get('stocks')
            if len(stock) > 0:
                stock = stock[0]
                stock_id = stock.get('stock_id') if stock.get('stock_id') else False
                qty = stock.get('quantity') if stock.get('quantity') else False
                sold_qty = stock.get('sold_quantity') if stock.get('sold_quantity') else False
            cdiscount_offer = offer_obj.search([('offer_id', '=', offer.get('offer_id'))],limit=1)
            if not cdiscount_offer and offer.get('offer_id'):
                odoo_product = self.env['product.product'].search([('default_code','=', offer.get('seller_product_id'))], limit=1)
                created_offer = offer_obj.create({
                    'offer_id': offer.get('offer_id'),
                    'offer_state': offer.get('offer_state') if offer.get('offer_state') else False,
                    'ean': offer.get('product_ean') if offer.get('product_ean') else False,
                    'product_sku': offer.get('seller_product_id') if offer.get('seller_product_id') else False,
                    'parent_product_id': offer.get('parent_product_id') if offer.get('parent_product_id') else False,
                    'product_state': offer.get('product_state') if offer.get('product_state') else False,
                    'product_condition_id': offer.get('product_condition_name') if offer.get('product_condition_name') else False,
                    'cdiscount_product_id': offer.get('cdiscount_product_id') if offer.get('cdiscount_product_id') else False,
                    'present_in_odoo': True if odoo_product else False,
                    'price': offer.get('price') if offer.get('price') else False,
                    'product_id': odoo_product.id if odoo_product else False,
                    'eco_tax': offer.get('eco_tax') if offer.get('eco_tax') else False,
                    'vat_rate': offer.get('vat_rate') if offer.get('vat_rate') else False,
                    'dea_tax': offer.get('dea_tax') if offer.get('dea_tax') else False,
                    'price_must_be_aligned': offer.get('price_must_be_aligned') if offer.get('price_must_be_aligned') else False,
                    'minimum_price_for_price_alignment': offer.get('minimum_price_for_price_alignment') if offer.get('minimum_price_for_price_alignment') else False,
                    'best_shipping_charges': offer.get('best_shipping_charges') if offer.get('best_shipping_charges') else False,
                    'product_packaging_unit': offer.get('product_packaging_unit') if offer.get('product_packaging_unit') else False,
                    'product_packaging_unit_price': offer.get('product_packaging_unit_price') if offer.get('product_packaging_unit_price') else False,
                    'product_packaging_value': offer.get('product_packaging_value') if offer.get('product_packaging_value') else False,
                    'cdiscount_shop_id': self.id,
                    'creation_date': offer.get('creation_date') if offer.get('creation_date') else False,
                    'last_update_date': offer.get('last_update_date') if offer.get('last_update_date') else False,
                    'stock_id': stock_id,
                    'quantity': qty,
                    'sold_qty': sold_qty
                })
                if not odoo_product:
                    logger.info("Warning : Product with sku %s not found in odoo", offer.get('seller_product_id'))

                # if created_offer:
                #     logger.info("Offer created with ID %s", created_offer.offer_id)
                #     #Populate shipping information
                #     shipping_info_list = offer.get('shipping_information_list')
                #     if shipping_info_list:
                #         for shipping in shipping_info_list:
                #             ship_obj = self.env['cdiscount.shipping.details'].create({
                #                 'name': shipping.get('name') if shipping.get('name') else False,
                #                 'shipping_charges': shipping.get('shipping_charges') if shipping.get('shipping_charges') else False,
                #                 'additional_shipping_charges': shipping.get('additional_shipping_charges') if shipping.get('additional_shipping_charges') else False,
                #                 'min_lead_time': shipping.get('')
                #             })



                # else:
                #     logger.info(">>>>>> Product with SKU %s not found in odoo database", offer.get('seller_product_id'))
            else:
                logger.info("Offer %s already found. Checking for updates", offer.get('offer_id'))
                cdiscount_offer.price = offer.get('price') if offer.get('price') else False
                cdiscount_offer.stock_id = stock_id
                cdiscount_offer.quantity = qty
                cdiscount_offer.sold_qty = sold_qty


        # print(response.text)

    # Method to update tracking in CDiscount Marketplace
    def update_bulk_shipment_tracking(self, data,cdiscount_order_id,shop_id):
        if cdiscount_order_id:
            call = "https://api.octopia-io.net/seller/v2/orders/" + cdiscount_order_id + "/shipments"
            
            picking_data = json.dumps(data)
            response = False
            # Authorization': 'Bearer ' + shop_id.seller_token
            try:
                _logger.info("Multiline Tracking Updation Call______ %r   Pickings Being Updated _____ %r  ;;;;;",call, data)
                # response = requests.post(call,headers={ 'Authorization': 'Bearer ' + shop_id.seller_token,'sellerId': shop_id.seller_id, 'Content-Type': 'application/json'},data=picking_data)
            except Exception as err:
                _logger.info("!!!!! Error in Multi Line Tracking Updation ~~~~~~~~%r ;;;;;",err)
            
            if response:
                # rejectted_orders = []
                # logger.info("Status Code ******%s",response.status_code) 
                status = response.status_code
                if status and status in [200,201]:
                    logger.info("Tracking Successfully updated in cdiscount portal for %s", cdiscount_order_id)
                else:
                    logger.info("Error in Tracking updation at cdiscount portal")
                    return cdiscount_order_id
                logger.info(response)
            else:
                _logger.info("!!!!!!!!! No response received from shop for shipment update   ;;;;;")
                return cdiscount_order_id
    
    def cdiscount_carrier_mapping(self):
        
        url = "https://api.octopia-io.net/seller/v2/carriers"
        response = None
        if self.seller_token and self.seller_id:
            headers = {
                'Authorization': 'Bearer ' + self.seller_token, 'sellerId': self.seller_id
            }
        else:
            raise UserError(_("Please enter seller id and seller secret key"))
        try:
            # response = requests.get(url, headers=headers).json()
            response = requests.request("GET", url, headers=headers).json()
            if response:
                logger.info(response)
                self.map_carriers(response)
        except Exception as err:
            logger.info(err)

    def map_carriers(self,carriers):
        for carrier in carriers:
            carrier_obj = self.env['cdiscount.carrier'].search([('code','=',carrier.get('code') if carrier.get('code') else False)],limit=1)
            if not carrier_obj:
                carrier_obj = self.env['cdiscount.carrier'].create({
                    'shop_id': self.id,
                    'label': carrier.get('label') if carrier.get('label') else False, 
                    'code': carrier.get('code') if carrier.get('code') else False, 
                })
                # logger.info(carrier_obj)
            else:
                logger.info("Carrier already exist, Updating data")
                carrier_obj.label = carrier.get('label') if carrier.get('label') else False
                carrier_obj.code = carrier.get('code') if carrier.get('code') else False

    def view_cdiscount_carriers(self):
        return {
            'name': ('Cdiscount Carriers'),
            'type': 'ir.actions.act_window',
            'res_model': 'cdiscount.carrier',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'target': 'current',
        }

            
