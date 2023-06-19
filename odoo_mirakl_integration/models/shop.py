# -*- coding: utf-8 -*-

from itertools import product
import re
from xmlrpc.client import DateTime

# from pyrfc3339 import generate
from odoo import fields, models, _, api
from odoo.exceptions import ValidationError, UserError
import requests
from odoo.http import request
import pytz
import json, datetime
from datetime import timedelta
import csv


import logging
_logger = logging.getLogger(__name__)


class ShopIntegrator(models.Model):
    _name = 'shop.integrator'
    _description = 'Shop Integrators'
    _rec_name = 'name'

    def _default_pricelist(self):
        return self.env['product.pricelist'].search([('company_id', 'in', (False, self.env.company.id)), ('currency_id', '=', self.env.company.currency_id.id)], limit=1)

    def _default_team(self):
        default_team = self.env['helpdesk.team'].search([('name', '=', _('Return Request'))], limit=1)
        if not default_team:
            default_team = self.env['helpdesk.team'].create({
                'name': _('Return Request'),
                'use_product_returns': True
            })
        return default_team.id

    def action_view_sale_orders(self):
        list_view = self.env.ref('odoo_mirakl_integration.view_mirakl_sales_order_tree')
        return {
            'type': 'ir.actions.act_window',
            'name': _('Mirakl Sale Orders'),
            'res_model': 'sale.order',
            'view_mode': 'list,form',
            'views': [list_view.id, 'list'],
        }

    @api.depends('created_orders_count')
    def _sale_order_count(self):
        for shop in self:
            order_count = 0
            waiting_count = 0
            payment_count = 0
            shipping_count = 0
            shipped_count = 0
            sale_orders = self.env['sale.order'].search([('mirakl_order_id', '!=', ''), ('mirakl_shop_id', 'in', [shop.id])])
            for order in sale_orders:
                if order.mirakl_shop_id.id == shop.id:
                    order_count +=1
                    if order.mirakl_order_state == "waiting_acceptance":
                        waiting_count +=1
                    if order.mirakl_order_state in ['waiting_debit', 'waiting_debit_payment']:
                        payment_count +=1
                    if order.mirakl_order_state == "shipping":
                        shipping_count +=1
                    if order.mirakl_order_state == "shipped":
                        shipped_count +=1
            shop.mirakl_sale_order_count = order_count
            shop.mirakl_sale_order_waiting_count = waiting_count
            shop.mirakl_sale_order_waiting_payment_count = payment_count
            shop.mirakl_sale_order_shipping_count = shipping_count
            shop.mirakl_sale_order_shipped_count = shipped_count

    @api.depends('mirakl_sale_order_count')
    def _get_shops_product_count(self):
        for shop in self:
            shop.inventory_count = self.env['mirakl.stock'].search_count([('shop_id', '=', shop.id)])

    @api.depends('inventory_count')
    def _get_shops_offer_count(self):
        for shop in self:
            shop.total_offer_count = self.env['mirakl.offers'].search_count([('shop_id', '=', shop.id)])
    
    def _get_shops_carrier_count(self):
        for shop in self:
            shop.total_carrier_count = self.env['mirakl.carrier'].search_count([('shop_id', '=', shop.id)])

    #Required's
    name = fields.Char("Name", required=True)
    api_key = fields.Char("API Key", required=True)
    shop_url = fields.Char("Mirakl Shop URL", required=True, help="add your mirakl shop url like - https://maisonsdumonde-prod.mirakl.net")
    shop_code = fields.Char("Shop Code")
    shop_id = fields.Char("Shop Id")

    #Checks
    activate_shop = fields.Boolean("Activate")
    is_order_recall = fields.Boolean("Is order recall", default= False)
    is_offers_exist = fields.Boolean("Offers Exists", default= False)

    # Shop Configurations
    pricelist_id = fields.Many2one('product.pricelist', string='Pricelist', check_company=True, required=True,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]", default=_default_pricelist)
    company_id = fields.Many2one('res.company', 'Company', required=True, readonly=True, index=True, default=lambda self: self.env.company)
    # team_id = fields.Many2one('helpdesk.team', string='Team', required=True, default=_default_team)
    sale_workflow_process_id = fields.One2many("sale.workflow.process", 'shop_id', string="Shop Configuration", required=True)
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse', required=True)
    inventory_alert_limit = fields.Integer("Minimum Product On Shop Limit", default=10)

    #Inventory Fields
    min_qty_to_zero = fields.Integer("Least quantity to make zero")
    lead_time_to_ship = fields.Integer(string='Lead Time to ship',default=2)
    
    
    # Order Count
    mirakl_sale_order_count = fields.Integer("Sale Order Count", compute = "_sale_order_count")
    mirakl_sale_order_waiting_count = fields.Integer("Sale Order Waiting Count", compute = "_sale_order_count")
    mirakl_sale_order_waiting_payment_count = fields.Integer("Sale Order Waiting Payment Count", compute = "_sale_order_count")
    mirakl_sale_order_shipping_count = fields.Integer("Sale Order Shipping Count", compute = "_sale_order_count")
    mirakl_sale_order_shipped_count = fields.Integer("Sale Order Shipped Count", compute = "_sale_order_count")
    inventory_count = fields.Integer("Inventory Count", compute="_get_shops_product_count")
    total_order_count = fields.Integer("Total Filtered Order Count")
    total_offer_count = fields.Integer("Total Offer Count", compute="_get_shops_offer_count")
    total_carrier_count = fields.Integer("Total Carrier Count", compute="_get_shops_carrier_count")


    created_orders_count = fields.Integer("Created SO Count")
    existing_orders_count = fields.Integer("Existing SO Count")
    order_error_count = fields.Integer("Error SO Count")

    
    # Order Filters
    is_filter_activate = fields.Boolean("Activate Filters")
    mirakl_order_filter_by_state = fields.Selection([('STAGING','STAGING'), ('WAITING_ACCEPTANCE','Waiting Acceptance'), ('WAITING_DEBIT','Waiting Debit'), ('WAITING_DEBIT_PAYMENT','Waiting Debit Payment'), ('SHIPPING','Shipping'),  ('SHIPPED','Shipped'), ('TO_COLLECT','To Collect'), ('RECEIVED','Received'), ('CLOSED','Closed'), ('REFUSED','Refused'), ('CANCELLED','Cancelled')],"Order State")
    has_open_incident = fields.Boolean("Has Open Incident")
    # Date Filters
    is_date_filter_activate = fields.Boolean("Date Filters")
    date_created_start = fields.Datetime("Created Start Date")
    date_created_end = fields.Datetime("Created End Date")
    date_updated_start = fields.Datetime("Updated Start Date")
    date_updated_end = fields.Datetime("Updated End Date")
    recall_order_date = fields.Datetime("Recall Order Date")
    filter_start_date = fields.Datetime("Initial Start Date")
    # Refund Filter
    is_refund_filter_activate = fields.Boolean("Refund Filters")
    refunded = fields.Selection([('NO','NO'), ('PARTIAL', 'PARTIAL'), ('FULL', 'FULL')],"Refunded Orders")
    refund_reason_code = fields.Char("Reason Of Refund Code")    
    
    multi_shop_final_message = fields.Char("Multi Shop Call Message")

    is_cdiscount_priority = fields.Boolean("Set C-discount WH on priority")

    #Cron Fields
    accept_order_cron = fields.Boolean(string='Accept Order Automatically', default=True)
    get_waiting_order_cron = fields.Boolean(string='Get Waiting Order Automatically', default=True)

    def _set_warehouse(self):
        for rec in self:
            warehouse_rec = self.env['stock.warehouse'].search([('marketplace_id', '=', rec.id)])
            if warehouse_rec:
                rec.warehouse_id = warehouse_rec.id
            else:
                rec.warehouse_id = False

    #Method to convert Odoo date format to Mirakl date format
    def get_mirakl_date_format(self, odoo_date_format):
        if odoo_date_format:
            date_time_string = fields.Datetime.to_string(odoo_date_format).replace(" ", "T") + "Z"
        else:
            date_time_string = False
        return date_time_string

    ###############
    # Notifications
    ###############

    # Show Multi Shop Action Message
    def collect_message_and_post(self, shop_ids):
        final_message = ""
        name = "Multi Shop Orders Report"
        for shop in shop_ids:
            if len(shop.multi_shop_final_message) > 0:
                shop_name = "<h4>" + shop.name + "</h4>"
                final_message += shop_name + shop.multi_shop_final_message + "<br/>" + "<hr>"
        return self.env['marketplace.wizard'].show_wizard_message(final_message, name)

    # Error
    def show_error(self, response):
        message = False
        try:
            if response.get('status_code') or response.get('status'):
                if response.get('status_code') == 400 or response.get('status') == 400:
                    message = "Parameter errors or bad method usage.Bad usage of the resource. Example: a required parameter is missing, a parameter with bad format, query on data which are not in expected state."
                elif response.status_code == 401 or response.get('status') == 401:
                    message = "Unauthorized - Call of API without authentication Add authentication information or use a valid authentication token."
                elif response.status_code == 403 or response.get('status') == 403:
                    message = "Forbidden - Access to the resource is denied Current user can not access to the resource."
                elif response.status_code == 404 or response.get('status') == 404:
                    message = "Not Found - The resource does not exist The resource URI does not exist or the asking resource does not exist (for the current user)."
                elif response.status_code == 405 or response.get('status') == 405:
                    message = "Method Not Allowed - The http method (GET, POST, PUT, DELETE) is not allowed for this resource Refer to the documentation for the list of accepted methods."
                elif response.status_code == 406 or response.get('status') == 406:
                    message = "Not Acceptable - The requested response content type is not available for this resource. Refer to the documentation for the list of correct values of the Accept header for this request.'"
                elif response.status_code == 410 or response.get('status') == 410:
                    message = "Gone - Resource is gone. The resource requested is no longer available and will not be available again."
                elif response.status_code == 415 or response.get('status') == 415:
                    message = "Unsupported Media Type - The entity content type sent to the server is not supported. Refer to the documentation for the list of correct values of the Content-type header to send data.'"
                elif response.status_code == 429 or response.get('status') == 429:
                    message = "Too many requests - Rate limit exceeded. The user has sent too many requests in the last hour. Refer to the documentation for the maximum calls count per hour."
                elif response.status_code == 500 or response.get('status') == 500:
                    message = "Internal Server Error - The server encountered an unexpected error."
                else:
                    return False
        except:
            if response.get('error'):
                message = response.get('error')
            elif response.get("message"):
                message = response.get('message')
            else:
                return False
        return message
        
    # Success
    def show_order_success_count(self, is_multi_shop_call):
        name="Orders Updated"
        self.date_created_start = False
        if self.total_order_count != 0:
            message = "Total Orders Filtered "+ str(self.total_order_count) + '<br>' + "Created Order Count "+ str(self.created_orders_count) + '<br>' + "Updated Order Count " + str(self.existing_orders_count) + '<br>' + "Error Order Count "+ str(self.order_error_count)
            self.total_order_count = False
            self.created_orders_count = False
            self.existing_orders_count = False
            self.order_error_count = False
        else:
            message = "No new orders to add."
        if is_multi_shop_call:
            self.multi_shop_final_message += message
            return True
        return self.env['marketplace.wizard'].show_wizard_message(message, name)

    ##########################
    # Mirakl Orders Management
    ##########################

    # Method to get last days orders
    def get_last_days_orders(self):
        self.is_filter_activate = True
        self.date_created_start = datetime.datetime.now() - timedelta(days=1)
        response = self.get_all_orders(False, False, False, True)
        self.is_filter_activate = False
        return response

    # Method to add filters
    def get_filters(self, call, recall, had_start_date_initially, filter_exist, special_call):

        

        # Adding filter params
        if self.is_filter_activate == True or self.is_order_recall:
            filter_exist = False
            # Adding Different Filters
            if not special_call:
                if self.mirakl_order_filter_by_state:
                    call += ("&" if filter_exist == True else "?") + 'order_state_codes=' + self.mirakl_order_filter_by_state
                    filter_exist = True
                if self.refunded:
                    call += ("&" if filter_exist == True else "?") + 'refunded =' + self.refunded
                    filter_exist = True
                if self.refund_reason_code:
                    call += ("&" if filter_exist == True else "?") + 'refund_reason_code=' + self.refund_reason_code
                    filter_exist = True
                if self.date_created_start:
                    call += ("&" if filter_exist == True else "?") + 'start_date=' + self.get_mirakl_date_format(self.date_created_start)
                    filter_exist = True
                if self.date_created_end:
                    call += ("&" if filter_exist == True else "?") + 'end_date=' + self.get_mirakl_date_format(self.date_created_end)
                    filter_exist = True
                if self.date_updated_start:
                    call += ("&" if filter_exist == True else "?") + 'start_update_date=' + self.get_mirakl_date_format(self.date_updated_start)
                    filter_exist = True
                if self.date_updated_end:
                    call += ("&" if filter_exist == True else "?") + 'end_update_date=' + self.get_mirakl_date_format(self.date_updated_end)
                    filter_exist = True
            else:
                if self.date_created_start:
                    call += "?" + 'start_date=' + self.get_mirakl_date_format(self.date_created_start)
                    filter_exist = True
        return call, had_start_date_initially, filter_exist

    # Method to get orders 
    def get_all_orders(self, recall=False, had_start_date_initially=False, filter_exist=False, special_call=False, multi_shop_call=False):
        
        call = self.shop_url+"/api/orders"
        self.env.cr.commit()
        # Add Filters If Any
        call, had_start_date_initially, filter_exist = self.get_filters(call, recall, had_start_date_initially, filter_exist, special_call)
        
        #increase limit
        call = call + "&max=100" if filter_exist else call + "?max=100"

        # Add Shop Id 
        if self.shop_id:
            call += "&shop_id=" + self.shop_id

        _logger.info("Call~~~~~~~~%r ;;;;;", call)

        #Get data
        try:
            response = requests.get(call,headers={'Authorization': self.api_key,'Content-Type': 'application/json'}).json()
        except Exception as err:
            _logger.info("!!!!!Order Getting Error~~~~~~~~%r ;;;;;",err)
            response = {}
            
        # Check for errors
        if self.show_error(response):
            raise UserError(_(self.show_error(response)))
        else:
            _logger.info("Total recived number of orders~~~~~~~~~%r ;;;;;",response.get("total_count"))
            if response.get("total_count"):

                # Set initial values
                if not recall:
                    self.total_order_count = response.get("total_count")
                    self.created_orders_count = 0
                    self.existing_orders_count = 0
                    self.order_error_count = 0
                    self.recall_order_date = False
                    self.filter_start_date = False
                    recall = True

                # If order are more then 100 (max limit of getting orders) then call to get orders after updating filters
                if response.get("total_count") > 100:
                    self.is_order_recall = True

                    # Save the initial created date of filters
                    if call.find("start_date") > 0:
                        had_start_date_initially = True
                        self.filter_start_date = self.date_created_start

                    # Create Orders and start recalling
                    self.env['sale.order'].run_sale_orders(response, self.id, recall)
                    if multi_shop_call:
                        return self.get_all_orders(recall, had_start_date_initially, filter_exist, special_call, True)
                    else:
                        return self.get_all_orders(recall, had_start_date_initially, filter_exist, special_call, False)

                else:

                    # If no need for recall
                    self.is_order_recall = False

                    # Set previously default values
                    if not had_start_date_initially:
                        self.date_created_start = False
                        self.filter_start_date = False
                        self.recall_order_date = False
                    else:
                        self.date_created_start = self.filter_start_date
                    
                    # Create Orders
                    self.env['sale.order'].run_sale_orders(response, self.id, False)

                    # Show Success Message
                    return self.show_order_success_count(multi_shop_call)
            else:
                # Show Success Message
                self.date_created_start = False
                return self.show_order_success_count(multi_shop_call)

    # Method to accept orders 
    def accept_marketplace_orders(self, orders):
        responses = []
        for order in orders:
            if order.mirakl_order_id:
                call = order.mirakl_shop_id.shop_url + "/api/orders/"+ order.mirakl_order_id +"/accept"
                # Add Shop Id 
                if order.mirakl_shop_id.shop_id:
                    if "?" not in call:
                        call += "?shop_id=" + order.mirakl_shop_id.shop_id
                    else:
                        call += "&shop_id=" + order.mirakl_shop_id.shop_id
                call_data = {"order_lines": []}
                count = 1
                for line in order.order_line:
                    line_data = {"accepted": 'true', "id": line.mirakl_order_line_id}
                    call_data.get('order_lines').append(line_data)
                    count += 1
                response = False
                try:
                    _logger.info("Accept Order Call~~~%r~~~~~~%r ;;;;;",call_data,call)
                    response = requests.put(call,headers={'Authorization': order.mirakl_shop_id.api_key,'Content-Type': 'application/json'}, data=json.dumps(call_data)).json()
                except Exception as err:
                    _logger.info("!!!!! Error in Order acceptance ~~~~~~~~%r ;;;;;",err)
                if response:
                    if self.show_error(response):
                        _logger.info("~~~Accept Order Call Response Error~~~~~~~~~~~%r ;;;;;",self.show_error(response))
                    else:
                        responses.append(response)
                else:
                    _logger.info("~~~~~Response Error~~~~~~~~%r~~~~~~~~~",response)
        return responses

    # Method to accept shop's all waiting orders
    def accept_marketplace_sale_order(self):
        sale_orders = self.env['sale.order'].search([('mirakl_order_state', 'in', ['waiting_acceptance']),('mirakl_shop_id', 'in', [self.id])])
        sale_orders.action_confirm()

    # Method to update orders
    def get_order_by_ids(self, shop_id, sale_orders):
        order_100 = ""
        count = 1
        remaining_order_count = len(sale_orders)
        for order in sale_orders:
            if count < 100 and remaining_order_count != count:
                if order.mirakl_order_id :
                    order_100 += order.mirakl_order_id+","
                else:
                    _logger.info("!!!!!!! Mirakl Orders Id is missing inside sale order - %r ;;;;;", order.id)
                count += 1

            elif count == 100 or remaining_order_count == count:
                # Hit API
                call = self.shop_url + "/api/orders?order_ids=" + order_100 + order.mirakl_order_id + "&max=100"
                if order.mirakl_shop_id.shop_id:
                    call += "&shop_id=" + order.mirakl_shop_id.shop_id
                response = False
                try:
                    _logger.info("Get Order Update Call for a shop~~~~~~~~~%r ;;;;;",call)
                    response = requests.get(call,headers={'Authorization': self.api_key,'Content-Type': 'application/json'}).json()
                except Exception as err:
                    _logger.info("!!!!! Error in Order Updation ~~~~~~~~%r ;;;;;",err)
                if response:
                    if self.show_error(response):
                        raise UserError(_(self.show_error(response)))
                    else:
                        # Send order updates 
                        order.update_shop_sale_orders(response)
                else:
                    _logger.info("Response Error~~~~~~~~%r ;;;;;",response)
                
                #Reset Values
                remaining_order_count -= count
                count = 1
                order_100 = ""
                _logger.info("Remaining Orders to Update for this Shop~~~~~~~~~~%r;;;;;", remaining_order_count)

    #Method To Update Mirakl Shops Orders
    def update_shops_orders(self):
        sale_orders = self.env['sale.order'].search([('mirakl_shop_id', 'in', [self.id]), ('mirakl_order_state', 'not in', ['shipped','closed','received','refused','canceled'])])
        if len(sale_orders) > 0:
            self.get_order_by_ids(self, sale_orders)
    
    # Method to clear all other filters from selected shops
    def clear_other_filters(self):
        for shop in self:
            shop.is_filter_activate = False
            shop.mirakl_order_filter_by_state = False
            shop.has_open_incident = False
            shop.is_date_filter_activate = False
            shop.date_created_start = False
            shop.date_created_end = False
            shop.date_updated_start = False
            shop.date_updated_end = False
            shop.recall_order_date = False
            shop.filter_start_date = False
            shop.is_refund_filter_activate = False
            shop.refunded = False
            shop.refund_reason_code = False

    ##############
    # Cron Methods 
    ##############

    # Get Waiting Mirakl Orders
    def select_all_shopes_for_gwom(self):
        shops = self.search([])
        shops.get_multi_shop_waiting_orders()

    # Get Shipping Mirakl Orders
    def select_all_shopes_for_gsom(self):
        shops = self.search([])
        shops.get_multi_shop_shipping_orders()

    # Accept Mirakl Orders
    def select_all_shopes_for_amo(self):
        shops = self.search([('accept_order_cron','=', True)])
        shops.accept_multi_shop_waiting_orders()

    # Update Waiting Payment Orders
    def select_all_shopes_for_upmo(self):
        shops = self.search([])
        for shop in shops:
            sale_orders = self.env['sale.order'].search([('mirakl_order_id','!=', False), ('mirakl_shop_id', 'in', [shop.id]), ('mirakl_order_state', 'in', ['waiting_acceptance','waiting_debit', 'waiting_debit_payment'])])
            if len(sale_orders) > 0:
                shop.get_order_by_ids(shop, sale_orders)

    # Update Shipment Orders
    def select_all_shopes_for_uso(self):
        shops = self.search([])
        for shop in shops:
            sale_orders = self.env['sale.order'].search([('mirakl_order_id','!=', False), ('mirakl_shop_id', 'in', [shop.id]), ('mirakl_order_state', 'in', ['shipping'])])
            if len(sale_orders) > 0:
                shop.get_order_by_ids(shop, sale_orders)


    ##############
    # Shop Actions 
    ##############

    # Method to get all waiting orders of all selected shops
    def get_multi_shop_waiting_orders(self):
        self.clear_other_filters()
        for shop in self:
            shop.multi_shop_final_message = ""
            final_message = ""
            shop.is_filter_activate = True
            for state in ["WAITING_ACCEPTANCE", "WAITING_DEBIT", "WAITING_DEBIT_PAYMENT"]:
                shop.mirakl_order_filter_by_state = state
                shop.multi_shop_final_message = "<br/>" + "<h6>" + " ".join(shop.mirakl_order_filter_by_state.split("_")) + " Orders :" + "</h6>"
                shop.get_all_orders(False, False, False, False, True)
                final_message += shop.multi_shop_final_message
                if state != "WAITING_DEBIT_PAYMENT":
                    final_message += "<br/>"
            shop.multi_shop_final_message = final_message
            shop.mirakl_order_filter_by_state = False
            shop.is_filter_activate = False

        return self.collect_message_and_post(self)

    # Method to get all shipping orders of all selected shops
    def get_multi_shop_shipping_orders(self):
        self.clear_other_filters()
        for shop in self:
            shop.is_filter_activate = True
            shop.multi_shop_final_message = ""
            shop.mirakl_order_filter_by_state = "SHIPPING"
            shop.multi_shop_final_message = "<br/>" + "<h6>" + "Shipping Orders :" + "</h6>"
            shop.get_all_orders(False, False, False, False, True)
            shop.mirakl_order_filter_by_state = False
            shop.is_filter_activate = False

        return self.collect_message_and_post(self)
    
    # Method to update all waiting orders of all selected shops
    def update_multi_shop_waiting_orders(self):
        for shop in self:
            shop.update_shops_orders()

    # Method to accept all waiting acceptance order of all selected shops
    def accept_multi_shop_waiting_orders(self):
        for shop in self:
            so = self.env['sale.order'].search([('mirakl_order_id','!=', False), ('mirakl_order_state', '=', 'waiting_acceptance'), ('mirakl_shop_id', '=', shop.id)])
            so.action_confirm()

    # Method to process all shipping orders of all selected shops
    def process_multi_shop_orders(self):
        for shop in self:
            shop.update_shops_orders()
            so = self.env['sale.order'].search([('mirakl_order_id','!=', False), ('mirakl_shop_id', '=', shop.id), ('mirakl_order_state', '=', 'shipping')])
            so.export_warehouse_orders()


    #################
    # Special Methods
    #################

    # Method to see this shop's all waiting orders
    def action_view_marketplace_waiting_orders(self):
        self.ensure_one()
        search_view_ref = self.env.ref('odoo_mirakl_integration.mirakl_sale_order_search_inherit_sale', False)
        
        return {
            'type': 'ir.actions.act_window',
            'name': _("%s's Waiting Sale Orders", self.name),
            'view_mode': 'list,form',
            'view_ids': [(self.env.ref('odoo_mirakl_integration.view_mirakl_sales_order_tree').id, 'list'), (self.env.ref('odoo_mirakl_integration.view_sales_order_form').id, 'form')],
            'res_model': 'sale.order',
            'search_view_id': search_view_ref and [search_view_ref.id],
            'context': {
                'search_default_order_logs': 1,
            },
            'domain': [('mirakl_shop_id', 'in', [self.id]), ('mirakl_order_state', '=', 'waiting_acceptance')],
        }

    # Method to see this shop's all waiting debit payment orders
    def action_view_marketplace_waiting_debit_payment_orders(self):
        self.ensure_one()
        search_view_ref = self.env.ref('odoo_mirakl_integration.mirakl_sale_order_search_inherit_sale', False)
        
        return {
            'type': 'ir.actions.act_window',
            'name': _("%s's Waiting Sale Orders", self.name),
            'view_mode': 'list,form',
            'view_ids': [(self.env.ref('odoo_mirakl_integration.view_mirakl_sales_order_tree').id, 'list'), (self.env.ref('odoo_mirakl_integration.view_sales_order_form').id, 'form')],
            'res_model': 'sale.order',
            'search_view_id': search_view_ref and [search_view_ref.id],
            'context': {
                'search_default_order_logs': 1,
            },
            'domain': [('mirakl_shop_id', 'in', [self.id]), ('mirakl_order_state', 'in', ['waiting_debit', 'waiting_debit_payment'])],
        }

    # Method to see this shop's all shipping orders
    def action_view_marketplace_shipping_orders(self):
        self.ensure_one()
        search_view_ref = self.env.ref('odoo_mirakl_integration.mirakl_sale_order_search_inherit_sale', False)
        
        return {
            'type': 'ir.actions.act_window',
            'name': _("%s's Shipping Sale Orders", self.name),
            'view_mode': 'list,form',
            'view_ids': [(self.env.ref('odoo_mirakl_integration.view_mirakl_sales_order_tree').id, 'list'), (self.env.ref('odoo_mirakl_integration.view_sales_order_form').id, 'form')],
            'res_model': 'sale.order',
            'search_view_id': search_view_ref and [search_view_ref.id],
            'context': {
                'search_default_order_logs': 1,
            },
            'domain': [('mirakl_shop_id', 'in', [self.id]), ('mirakl_order_state', '=', 'shipping')],
        }

    # Method to see this shop's all shipped orders
    def action_view_marketplace_shipped_orders(self):
        self.ensure_one()
        search_view_ref = self.env.ref('odoo_mirakl_integration.mirakl_sale_order_search_inherit_sale', False)
        return {
            'type': 'ir.actions.act_window',
            'name': _("%s's Shipped Sale Orders", self.name),
            'view_mode': 'list,form',
            'view_ids': [(self.env.ref('odoo_mirakl_integration.view_mirakl_sales_order_tree').id, 'list'), (self.env.ref('odoo_mirakl_integration.view_sales_order_form').id, 'form')],
            'res_model': 'sale.order',
            'search_view_id': search_view_ref and [search_view_ref.id],
            'context': {
                'search_default_order_logs': 1,
            },
            'domain': [('mirakl_shop_id', 'in', [self.id]), ('mirakl_order_state', '=', 'shipped')],
        }

    # Method to see this shop's all orders
    def action_view_marketplace_sale_order(self):
        self.ensure_one()
        search_view_ref = self.env.ref('odoo_mirakl_integration.mirakl_sale_order_search_inherit_sale', False)

        return {
            'type': 'ir.actions.act_window',
            'name': _("%s's Sale Orders", self.name),
            'view_mode': 'list,form',
            'view_ids': [(self.env.ref('odoo_mirakl_integration.view_mirakl_sales_order_tree').id, 'list'), (self.env.ref('odoo_mirakl_integration.view_sales_order_form').id, 'form')],
            'res_model': 'sale.order',
            'search_view_id': search_view_ref and [search_view_ref.id],
            'context': {
                'search_default_order_logs': 1,
            },
            'domain': [('mirakl_shop_id', 'in', [self.id])],
        }

    # Method to see this shop's all products 
    def action_view_marketplace_products(self):
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': _("%s's Products", self.name),
            'view_mode': 'list,form',
            'view_ids': [(self.env.ref('odoo_mirakl_integration.view_shop_stock').id, 'list'), (self.env.ref('odoo_mirakl_integration.view_shop_stock_form').id, 'form')],
            'res_model': 'mirakl.stock',
            'context': {    
                'search_default_mirakl_stock_shops': 1,
            },
            'domain': [('shop_id', 'in', [self.id])],
        }

    # Method to see this shop's all offers 
    def action_view_marketplace_offers(self):
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': _("%s's Offers", self.name),
            'view_mode': 'list,form',
            'view_ids': [(self.env.ref('odoo_mirakl_integration.view_mirakl_offers').id, 'list'), (self.env.ref('odoo_mirakl_integration.view_mirakl_offers_form').id, 'form')],
            'res_model': 'mirakl.offers',
            'limit': 150,
            'context': {    
                'search_default_shop': 1,
            },
            'domain': [('shop_id', 'in', [self.id])],
        }

    # Method to see this shops's carriers
    def action_view_marketplace_carriers(self):
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': _("%s's Carriers", self.name),
            'view_mode': 'list,form',
            'view_ids': [(self.env.ref('odoo_mirakl_integration.view_mirakl_carrier').id, 'list'), (self.env.ref('odoo_mirakl_integration.view_mirakl_carrier_form').id, 'form')],
            'res_model': 'mirakl.carrier',
            'context': {    
                'search_default_shop': 1,
            },
            'domain': [('shop_id', 'in', [self.id])],
        }


    #####################
    # Shipping Management
    #####################

    #Method to Sync Carriers
    def map_carrier_of_this_shop(self):

        for shop in self:

            response = False
            call = shop.shop_url + '/api/shipping/carriers' 
            try:
                _logger.info("Carrier Updation of %r shop ___  %r  ;;;;;", shop.name, call)
                response = requests.get(call,headers={'Authorization': shop.api_key,'Content-Type': 'application/json'}).json()
            except Exception as err:
                _logger.info("!!!!! Error in Carrier Updation for %r shop~~~~~~~~%r ;;;;;", shop.name, err)
            if response:
                if self.show_error(response):
                    _logger.info(self.show_error(response))
                else:
                    return self.env['mirakl.carrier'].sync_shop_carriers(shop, response)
            else:
                return False

    # Method to get shipment of a particular order
    def get_shipment_tracking_info(self, order_id):

        call = self.shop_url + '/api/shipments?order_id=' + order_id
        if self.shop_id:
            call += "&shop_id=" + self.shop_id

        try:
            response = requests.get(call,headers={'Authorization': self.api_key,'Content-Type': 'application/json'}).json()
        except Exception as err:
            _logger.info("!!!!! Error in Getting Multi Line Tracking Info ~~~~~~~~%r ;;;;;",err)
    
        if response:
            if response.get('data'):
                return response.get('data')
        
        return False
                
    # Method to update tracking
    def update_bulk_shipment_tracking(self, data, shop_id):
        
        call = shop_id.shop_url + '/api/shipments'
        if shop_id.shop_id:
            call += "?shop_id=" + shop_id.shop_id
        picking_data = json.dumps(data)
        response = False
        try:
            _logger.info("Multiline Tracking Updation Call______ %r   Pickings Being Updated _____ %r  ;;;;;",call, picking_data)
            # response = requests.post(call,headers={'Authorization': shop_id.api_key,'Content-Type': 'application/json'},data=picking_data).json()
        except Exception as err:
            _logger.info("!!!!! Error in Multi Line Tracking Updation ~~~~~~~~%r ;;;;;",err)
        
        if response:
            if response.get('shipment_errors'):
                if len(response.get('shipment_errors')) > 0:
                    rejected_deliveries = []
                    for error in response.get('shipment_errors'):
                        if error.get('order_id'):
                            _logger.info("!!!!! Error in Multi Line Tracking Updation ~~~~~~  %r ;;;;;",error['message'])
                            rejected_deliveries.append(error['order_id'])
                    _logger.info("!!!!! Orders whose tracking is not updated~~~~~~  %r ;;;;;",rejected_deliveries)
                    return rejected_deliveries
                else:
                    _logger.info("Multi Line Tracking Updation Successful~~~~~~~~%r ;;;;;",response.get('shipment_success'))
                    return False
            else:
                _logger.info("Multi Line Tracking Updation Successful~~~~~~~~%r ;;;;;",response)
        else:
            _logger.info("!!!!!!!!! No response received from shop for shipment update   ;;;;;")
            return False


    #############################
    # Mirakl Inventory Management
    #############################

    # Method to convert mirakl date to odoo date format
    def get_odoo_date_format(self, mirakl_date_format):
        if len(mirakl_date_format) > 2:
            mirakl_date_format = mirakl_date_format.replace('"','')[mirakl_date_format.find('-')-3:]
            if mirakl_date_format:
                date_time_string = mirakl_date_format.replace("T", " ")[0:mirakl_date_format.find(":")+6] if mirakl_date_format else False
            else:
                date_time_string = False
            return date_time_string
        return False


    # Method to update product qty on shop   
    def add_stock_qty(self, product_id, qty):

        offer_id = self.env['mirakl.offers'].search([('product_sku','=',product_id)])
        
        response = False
        call = self.shop_url+'/api/offers/' + offer_id.offer_id

        if self.shop_id:
            call += "?shop_id=" + self.shop_id
        
        # Get Data From Shop
        try:
            response = requests.get(call,headers={'Authorization': self.api_key,'Content-Type': 'application/json'}).json()
        except:
            return False
       
        # Update Data On Shop
        if len(response):
            response_data = response
            discount = response.get('discount')
            for price in response_data['all_prices']:
                if not price.get('unit_discount_price') and price.get('channel_code'):
                    price['unit_discount_price'] = price['volume_prices'][0]['unit_discount_price']

            data = {
                "offers": [
                    {
                        "allow_quote_requests": False,
                        # "available_ended": "2019-05-29T22:00:00Z",
                        # "available_started": "2019-03-01T22:00:00Z",
                        "description": response_data.get('description'),
                        "discount": {
                            "end_date": discount['end_date'],
                            "price": discount['discount_price'],
                            "ranges": discount['ranges'],
                            "start_date": discount['start_date']
                        },
                        "internal_description": response_data['description'],
                        "leadtime_to_ship": response_data['leadtime_to_ship'],
                        "logistic_class": response_data['logistic_class']['code'],
                        # "max_order_quantity": 3,
                        # "min_order_quantity": 1,
                        "min_quantity_alert": response_data['min_quantity_alert'],
                        "offer_additional_fields": response_data.get('offer_additional_fields'),
                        # "package_quantity": "2",
                        "product_id": response_data['product_references'][0]['reference'],
                        "product_id_type": response_data['product_references'][0]['reference_type'],
                        "price": discount['origin_price'],
                        "price_additional_info": response_data['price_additional_info'],
                        "all_prices": response_data['all_prices'],
                        "quantity": qty,
                        "shop_sku": response_data['shop_sku'],
                        "state_code": response_data['state_code'],
                        "update_delete": "update"
                    }
                ]
            }
            if response_data.get('min_order_quantity'):
                data['offers'][0].update({'min_order_quantity': response_data.get('min_order_quantity')})
            if response_data.get('max_order_quantity'):
                data['offers'][0].update({'min_order_quantity': response_data.get('max_order_quantity')})
            
            # Send Data
            post_call = self.shop_url+'/api/offers/'
            if self.shop_id:
                post_call += "?shop_id=" + self.shop_id
            try:
                print("Quantity Change APi called for  Offer >> ", offer_id.offer_id)
                # response = requests.post(post_call,headers={'Authorization': self.api_key,'Content-Type': 'application/json'},data=json.dumps(data) ).json()
                _logger.info("~~~~~~~~~~~~~Stock Qty Updated~~~~~~~~~",response)
                if response and response.get('import_id'):
                    offer_record = self.env['mirakl.offers'].search([('offer_id','=',offer_id.offer_id)])
                    offer_record.write({'last_updated_import_id': response['import_id']})
                    return True
            except Exception as err:
                pass
                _logger.info("Error in changin Qty** ", err)
                return False
        else:
            return False


    # Listing Helper Methods
    def convert_to_proper_json(self, offer):
        o_keys, o_values = [], []
        import re
        if len(offer) != 0 and len(offer) == 1:
            for key in offer.keys():
                new_key = re.sub(';+', ';', key)
                o_keys = new_key.split(';')
                if offer[key]:
                    o_values = offer[key].split(';')
                else:
                    return {}
        elif len(offer) > 1:
            offer_keys = ''
            offer_values = ''
            for key in offer.keys():
                offer_keys += key or ''
                offer_values += offer[key] or ''
            o_keys = offer_keys.split(';')
            o_values = offer_values.split(';')
        else:
            raise UserError(_("Issue parsing the offer csv file."))
        return {k:v for (k,v) in zip(o_keys, o_values)}


    # Listing Helper Methods
    def map_offers(self, offers):
        try: 
            if len(offers) != 0:
                shop_offers = self.env['mirakl.offers']
                found_stock, found_offer = False, False
                product_id = False
                missing_products = []
                for offer in offers:
                    try:
                        product_id = self.env['product.product'].search([('default_code', '=', offer['shop-sku'].replace('"', ''))])
                        product_temp_id = self.env['product.template'].search([('default_code', '=', offer['shop-sku'].replace('"', ''))])
                        if len(product_id) == 0:
                            product_id = self.env['product.product'].search([('barcode', '=', offer['shop-sku'][1:])])
                        found_offer = shop_offers.search([('offer_id', '=', int(offer['offer-id']))])
                        if len(product_id) != 0:
                            found_stock = self.env["mirakl.stock"].search([('shop_id','=',self.id),('odoo_product_id', '=', product_id.id)], limit=1)
                    except:
                        pass
                    if not found_offer and product_id:
                        try:
                            created_offer_id = shop_offers.create({
                                "offer_id": offer['offer-id'],
                                "active": True if offer['active']== 'true' else False,
                                "shop_id": self.id,
                                "offer_update_date": datetime.datetime.now(),
                                "shop_stock_ids": found_stock.id if found_stock else False,
                                "product_id": product_id.id,
                                "product_sku": offer['product-sku'] if offer['product-sku'] else False,
                                "quantity": int(offer['quantity']) if offer['quantity'] else False,
                                "price": float(offer['price']) if offer['price'] else False,
                                "description": offer['description'] if offer['description'] else False,
                                "total_price": float(offer['total-price']) if offer['total-price'] else False,
                                "origin_price": float(offer['origin-price']) if offer['origin-price'] else False,
                                "discount_price": float(offer['discount-price']) if offer['discount-price'] else False,
                                # "discount_start_date": self.get_odoo_date_format(offer['discount-start-date']),
                                # "discount_end_date": self.get_odoo_date_format(offer['discount-end-date']),
                                # "available_start_date": self.get_odoo_date_format(offer['available-start-date']),
                                # "available_end_date": self.get_odoo_date_format(offer['available-end-date']),
                                "currency_iso_code": offer['currency-iso-code'] if offer['currency-iso-code'] else False,
                                "discount_ranges": offer['discount-ranges'] if offer['discount-ranges'] else False,
                                "min_shipping_price": offer['min-shipping-price'] if offer['min-shipping-price'] else False,
                                "min_shipping_price_additional": offer['min-shipping-price-additional'] if offer['min-shipping-price-additional'] else False,
                                "price_ranges": offer['price-ranges'] if offer['price-ranges'] else False,
                                "state_code": offer['state-code'] if offer['state-code'] else False,
                                "mirakl_shop_id": offer['shop-id'] if offer['shop-id'] else False,
                                "shop_name": offer['shop-name'] if offer['shop-name'] else False,
                                "professional": True if offer['professional'] == 'true' else False,
                                "premium": True if offer['premium']== 'true' else False,
                                "logistic_class": offer['logistic-class'] if offer['logistic-class'] else False,
                                "favorite_rank": offer['favorite-rank'] if offer['favorite-rank'] else False,
                                "channels": offer['channels'] if offer['channels'] else False,
                                "deleted": True if offer['deleted']== 'true' else False,
                                "leadtime_to_ship": offer['leadtime-to-ship'] if offer['leadtime-to-ship'] else False,
                                "allow_quote_requests": True if offer['allow-quote-requests']== 'true' else False,
                                "fulfillment_center_code": offer['fulfillment-center-code'] if offer['fulfillment-center-code'] else False,
                                # "origin": offer['origin'] if offer['origin'] else False,
                                "min_shipping_zone": offer['min-shipping-zone'] if offer.get('min-shipping-zone') else False,
                            })
                            _logger.info("Offer Created !!!!!!! ~~~~~~~~%r ;;;;;",created_offer_id)
                        except Exception as err:
                            _logger.info("!!!!! Error In Mapping ~~~~~~~~%r ;;;;;",err)

                    else:
                        if found_offer:
                            found_offer.quantity = int(offer['quantity']) if offer['quantity'] else found_offer.quantity
                            found_offer.description = offer['description'] if offer['description'] else found_offer.description
                            found_offer.price = float(offer['price']) if offer['price'] else found_offer.price
                            found_offer.total_price = float(offer['total-price']) if offer['total-price'] else found_offer.total_price
                            found_offer.discount_price = float(offer['discount-price']) if offer['discount-price'] else found_offer.discount_price
                            found_offer.offer_update_date = datetime.datetime.now()
                            _logger.info("~~~~~~~~Offer already exists~~~~~~%r~`",found_offer)
                        if not product_id:
                            missing_products.append(offer['shop-sku'])
                            _logger.info("~~~~~~~~~~~ Product not found ~~~~~~~~~~~~")
                if missing_products:
                    _logger.info("~~~~~~~~~ Missing Products ~~~~~~~%r~`",missing_products)
                
                return True
        except:
            return False


    # Listing Helper Methods
    def clear_empties(self, offers):
        if len(offers) != 0 :
            for offer  in offers:
                if offer:
                    for key in offer.keys():
                        if offer[key] == '""':
                            offer[key] = False
                        else:
                            offer[key] = offer[key].replace('"', '')
        return offers
            

    # Method to get offers listings for this shop
    def setup_offers(self, call):
        
        call += "/export"
        if self.shop_id:
            call += "?shop_id=" + self.shop_id
        try:
            response = requests.get(call,headers={'Authorization': self.api_key,'Accept': 'application/csv'})
        except Exception as err:
            _logger.info("!!!!! Error In Getting Offers Mapping ~~~~~~~~%r ;;;;;",err)
            response = False
        
        if response != False:
            
            # Convert response to json data 
            import csv , io
            reader = csv.DictReader(io.StringIO(response.text))
            json_data = json.loads(json.dumps(list(reader)))
            
            # Clear Data
            offers = []
            for offer in json_data:
                offers.append(self.convert_to_proper_json(offer))
            try:
                offers = self.clear_empties(offers)
            except:
                raise UserError(_("Issue clearing the data."))

            # Map Offers 
            return self.map_offers(offers)
        
        return False


    # To check for offers 
    def create_relevant_offer(self, stock_obj):
        # call = self.shop_url + ''
        pass


    # Method to create Mirakl to Odoo Inventory Mapping
    def mirakl_inventory_mapping(self):
        mirakl_stock_obj = self.env['mirakl.stock'].search([])
        call = self.shop_url + '/api/offers' 
        products = self.env['product.product'].search([])
        for prod in products:
            if prod.default_code:
                try:
                    if "adeo" in call:
                        new_call = call + "?sku=" + "0" + prod.barcode
                        if self.shop_id:
                            new_call += "&shop_id=" + self.shop_id
                        response = requests.get(new_call,headers={'Authorization': self.api_key,'Content-Type': 'application/json'}).json()
                    else:
                        new_call = call + "?sku=" + prod.default_code
                        if self.shop_id:
                            new_call += "&shop_id=" + self.shop_id
                        response = requests.get(new_call,headers={'Authorization': self.api_key,'Content-Type': 'application/json'}).json()
                except Exception as err:
                    _logger.info("!!!!! Error in Inventory Mapping ~~~~~~~~%r ;;;;;",err)
                    response = False
                if type(response) != type(True):
                    if self.show_error(response):
                        raise UserError(_(self.show_error(response)))
                    else:
                        if response.get("total_count") == 1:
                            if response.get('offers')[0].get("product_sku"):

                                # Get orders of this product
                                already_exist = self.env['mirakl.stock'].search(['&', ('odoo_product_id','=', prod.id), ('shop_id','=', self.id)])
                                
                                if not already_exist:
                                    # Create New Product Mapping
                                    try:
                                        created_stock = mirakl_stock_obj.create({
                                            'shop_id': self.id,
                                            'odoo_product_id': prod.id,
                                            'quantity': response.get('offers')[0].get("quantity"),
                                            'mirakl_product_ref': response.get('offers')[0].get("product_sku"),
                                            'last_updated_date': datetime.datetime.now(),
                                            'inventory_alert_limit': self.inventory_alert_limit
                                        })
                                        _logger.info("Created Inventory Mapping ~~~~~~~~%r ;;;;;",created_stock)
                                        self.create_relevant_offer(created_stock)
                                    except Exception as err:
                                        _logger.info("!!!!! Error in Inventory Mapping Creation ~~~~~~~~%r ;;;;;",err)
                                else:
                                    # Update Old Mapping And Delete Duplicates
                                    count = 1
                                    delete_list = []
                                    
                                    for shop_stock in already_exist:
                                        if count == 1:
                                            # Update Shop Stock Qty in Product Mapping
                                            shop_stock.update({
                                                'quantity': response.get('offers')[0].get("quantity"),
                                                'last_updated_date': datetime.datetime.now(),
                                                })
                                            count += 1
                                            _logger.info("Updated Inventory Mapping ~~~~~~~~%r ;;;;;",shop_stock)

                                        else:
                                            delete_list.append(shop_stock.id)
                                    
                                    #Delete Duplicates
                                    self.env['mirakl.stock'].search([('id', 'in', delete_list)]).unlink()
                        else:
                            _logger.info("~~~~~~~~Skip~~~~~~~~~~~~`")
        # Update latest inventory count 
        self.inventory_count = self.env["mirakl.stock"].search_count([('shop_id','=', self.id)])
        

    # Method to get the listing of offers
    def mirakl_inventory_offers(self):
        mirakl_stock_obj = self.env['mirakl.stock'].search([])
        
        call = self.shop_url + '/api/offers'

        safe = self.setup_offers(call)

        if safe:
            remove_scrap = self.env['mirakl.offers'].search([('shop_id', '=', self.id), ('offer_id', '=', False)])
            remove_scrap.unlink()
            shop_offers = self.env['mirakl.offers'].search([('shop_id', '=', self.id)])
            for offer in shop_offers:
                # Get stocks of this product
                if not offer.shop_stock_ids:
                    # Create New Product Mapping
                    try:
                        mirakl_stock_obj.create({
                            'shop_id': self.id,
                            'odoo_product_id': offer.product_id.id,
                            'quantity': offer.quantity,
                            'mirakl_product_ref': offer.product_sku,
                            'last_updated_date': datetime.datetime.now(),
                            'inventory_alert_limit': self.inventory_alert_limit
                        })
                        offer.shop_stock_ids = mirakl_stock_obj.search([('mirakl_product_ref', '=', offer.product_sku), ('shop_id', '=', self.id)], limit=1)
                    except Exception as err:
                        _logger.info("!!!!! Error in Inventory Mapping Creation ~~~~~~~~%r ;;;;;",err)
                else:
                    # Collect All Duplicates And Update Old Mapping
                    count = 1
                    delete_list = []
                    for shop_stock in offer.shop_stock_ids:
                        if count == 1:
                            shop_stock.update({
                                'quantity': offer.quantity,
                                'last_updated_date': datetime.datetime.now(),
                                })
                            count += 1
                        else:
                            delete_list.append(shop_stock.id)
                    
                    #Delete Duplicates
                    self.env['mirakl.stock'].search([('id', 'in', delete_list)]).unlink()
            return True
        else:
            raise UserError(_("No Offers Found For This Shop"))

    #######################
    # Order Processing
    #######################

    # Method to get shop ID
    def get_marketplace_shop(self, order):

        # Mirakl Order
        if order.mirakl_order_id:
            if order.mirakl_shop_id:
                if order.mirakl_shop_id.shop_code:
                    return order.mirakl_shop_id.shop_code
                else:
                    return order.mirakl_shop_id.name

        #Wayfair Order
        if order.wayfair_order_id:
            return order.market_place_shop
        
        #Cdiscount Order
        if order.cdiscount_order_id:
            return order.market_place_shop

        if order.amazon_order_id:
            return order.market_place_shop
        
        if order.manomano_order_id:
            return order.market_place_shop

        if order.amazon_b2b_order_id:
            return order.market_place_shop

    # Method to get order id
    def get_shop_orders_id(self, order):

        # Mirakl
        if order.mirakl_order_id:
            return order.mirakl_order_id
        
        #Wayfair
        if order.wayfair_order_id:
            return order.wayfair_order_id
        
        # Cdiscount
        if order.cdiscount_order_id:
            return order.cdiscount_order_id
        
        if order.amazon_order_id:
            return order.amazon_order_id
        
        if order.manomano_order_id:
            return order.manomano_order_id

        if order.amazon_b2b_order_id:
            return order.amazon_b2b_order_id.purchase_order
        
        return False

    # Method for processing orders for ETL
    def generate_etl_orders_data(self, sale_orders):
        for order in sale_orders:
            marketplace = ""
            data = {}
            order_id = self.get_shop_orders_id(order)
            if order_id:
                processed = True if len(self.env['processed.order'].search([('order_id','like', order_id)])) > 0 else False
                if not processed:

                    # Shop Name 
                    order.processed = True
                    marketplace = self.get_marketplace_shop(order)

                    if marketplace:
                        if order.partner_id.country_id.code:
                            marketplace = marketplace + "_" + (order.partner_shipping_id.country_id.code or order.partner_id.country_id.code)

                    # Shift
                    order_shift = None
                    IST = pytz.timezone('Asia/Kolkata')
                    time_now = datetime.datetime.strftime(datetime.datetime.now(IST), "%Y-%m-%d %H:%M:%S")
                    if int(time_now.split(' ')[1][:2]) <= 12:
                        order_shift = 'morning'
                    else:
                        order_shift = 'evening'
                    
                    # Basic Fileds
                    data = {
                        "name": order.partner_shipping_id.name,
                        "mail_address": order.customer_notification_email,
                        "street": order.partner_shipping_id.street,
                        "street2": order.partner_shipping_id.street2,
                        "country": self.get_country_value(order, True),
                        "postal_code": order.partner_shipping_id.zip,
                        "town": order.partner_shipping_id.city,
                        "phone": order.partner_shipping_id.phone or order.partner_id.phone,
                        "order_id": order_id,
                        "comment": order.mirakl_comment if order.mirakl_order_id else "",
                        "carrier": "",
                        "marketplace": marketplace,
                        "sale_order_id": order.id,
                        "stock_status": "check_available",
                        "order_processing_status": "unprocessed",
                        "mirakl_shop_id": order.mirakl_shop_id.id if order.mirakl_order_id else "",
                        "process_date": datetime.datetime.now(),
                        'processing_time': order_shift,
                        "warehouse": order.warehouse_id.code,
                    }

                    # Update Order Line Details and Carrier Update
                    if len(order.order_line) > 0:
                        count = 1
                        for line in order.order_line:
                            data.update({
                                "item_id": line.product_id.default_code,
                                "quantity": int(line.product_uom_qty),
                                "weight": line.product_id.weight,
                                "product_id": line.product_id.id,
                                "inventory_stock_count": line.product_id.qty_available,
                            })
                            #Update Order Name
                            if len(order.order_line) > 1:
                                data.update({
                                    "order_id": order_id + "-" + str(count),
                                })
                                count += 1
                            self.env['processed.order'].create_processed_orders(data)
                    else:
                        _logger.info("skipped order from processing because product is missing ~~~~~~~~~~~%r ;;;;;;",order.id)

    # Method for processing orders for IFUL
    def generate_ifull_orders_data(self, sale_orders):
        
        for order in sale_orders:
            
            marketplace = ""
            data = {}
            order_id = self.get_shop_orders_id(order)

            if order_id:
                processed = True if len(self.env['processed.order'].search([('order_id','like', order_id)])) > 0 else False
                if not processed:
                    order.processed = True
                    marketplace = self.get_marketplace_shop(order)

                    if marketplace:
                        if order.partner_id.country_id.code:
                            if order.partner_id.country_id.code not in marketplace:
                                marketplace = marketplace + "_" + (order.partner_shipping_id.country_id.code or order.partner_id.country_id.code)

                    order_shift = None
                    IST = pytz.timezone('Asia/Kolkata')
                    time_now = datetime.datetime.strftime(datetime.datetime.now(IST), "%Y-%m-%d %H:%M:%S")
                    if int(time_now.split(' ')[1][:2]) <= 12:
                        order_shift = 'morning'
                    else:
                        order_shift = 'evening'


                    ship_to_name = first_name = last_name = ""
                    if order.partner_shipping_id:
                        split_name = order.partner_shipping_id.name.split(" ")
                        if len(split_name) == 1:
                            ship_to_name = first_name = split_name[0]
                        else:
                            ship_to_name = first_name = "_".join(split_name[:-1])
                            last_name = split_name[-1]

                    # Basic Fileds
                    data = {
                        "name": order.partner_shipping_id.name,
                        'ship_to_name': ship_to_name,
                        "first_name": first_name,
                        "last_name": last_name,
                        "email": "customer@surya.com",
                        "address_one": order.partner_shipping_id.street,
                        "address_two": order.partner_shipping_id.street2,
                        "town": order.partner_shipping_id.city,
                        "country": self.get_country_value(order, False),
                        "postcode": order.partner_shipping_id.zip,
                        "county": "",
                        "phone_no": "+" + order.partner_shipping_id.phone if order.partner_shipping_id.phone else False,
                        "picking_instructions": "Print label and attach it to the rug",
                        "despatch_instructions": "Print label and attach it to the rug",
                        "company": "Surya",
                        "order_id": order_id,
                        "reference": order_id,
                        "carrier": "",
                        "marketplace": order.market_place_shop,
                        "sale_order_id": order.id,
                        "stock_status": "check_available",
                        "order_processing_status": "unprocessed",
                        "process_date": datetime.datetime.now(),
                        "date_placed": datetime.datetime.now(),
                        'processing_time': order_shift,
                        "warehouse": "BOH"
                    }

                    # Update Order Line Details and Carrier Update
                    if len(order.order_line) > 0:
                        count = 1
                        for line in order.order_line:
                            data.update({
                                "item_id": line.product_id.default_code,
                                "sku": line.product_id.default_code,
                                "quantity": int(line.product_uom_qty),
                                "line_net_price": 100,
                                "product_id": line.product_id.id,
                                "inventory_stock_count": line.product_id.qty_available,
                            })
                            #Update Order Name
                            if len(order.order_line) > 1:
                                data.update({
                                    "order_id": order_id + "-" + str(count),
                                })
                                count += 1
                            self.env['processed.order'].create_processed_orders(data)
                    else:
                        _logger.info("skipped order from processing because product is missing ~~~~~~~~~~~%r ;;;;;;",order.id)

    # Method for processing orders for CDISC
    def generate_cdisc_orders_data(self, sale_orders):
        for order in sale_orders:
            marketplace = ""
            data = {}
            order_id = self.get_shop_orders_id(order)

            if order_id:
                processed = True if len(self.env['processed.order'].search([('order_id','like', order_id),('warehouse','=',order.warehouse_id.code)])) > 0 else False
                if not processed:

                    # Shop Name 
                    order.processed = True
                    marketplace = self.get_marketplace_shop(order)

                    if marketplace:
                        if order.partner_id.country_id.code:
                            marketplace = marketplace + "_" + (order.partner_shipping_id.country_id.code or order.partner_id.country_id.code)

                    # Shift
                    order_shift = None
                    IST = pytz.timezone('Asia/Kolkata')
                    time_now = datetime.datetime.strftime(datetime.datetime.now(IST), "%Y-%m-%d %H:%M:%S")
                    if int(time_now.split(' ')[1][:2]) <= 12:
                        order_shift = 'morning'
                    else:
                        order_shift = 'evening'
                    
                    full_name = first_name = False
                    if order.partner_shipping_id.name:
                        full_name= order.partner_shipping_id.name
                        first_name = order.partner_shipping_id.name.split(' ')[0]

                    if order.partner_id.phone:
                        order.partner_id.phone = "0" + order.partner_id.phone[::-1][:9][::-1]

                    if order.partner_shipping_id.phone:
                        order.partner_shipping_id.phone = "0" + order.partner_shipping_id.phone[::-1][:9][::-1]

                    # Basic Fileds
                    data = {
                        "name": order.partner_shipping_id.name,
                        "customer_name": full_name,
                        "customer_first_name": first_name,
                        "email_cds": order.partner_id.email,
                        "delivery_address": order.partner_shipping_id.street,
                        "additional_address": order.mirakl_comment if order.mirakl_order_id else "",
                        "country": self.get_country_value(order, False),
                        "postal_code": order.partner_shipping_id.zip,
                        "city_cds": order.partner_shipping_id.city,
                        "mobile_no": order.partner_shipping_id.mobile,
                        "phone_no": order.partner_shipping_id.phone,
                        "order_id": order_id,
                        "customer_order_number": order_id,
                        "comment": order.mirakl_comment if order.mirakl_order_id else "",
                        "carrier": "",
                        "signboard": "AUTRE",
                        "marketplace": marketplace,
                        "sale_order_id": order.id,
                        "stock_status": "check_available",
                        "order_processing_status": "unprocessed",
                        "mirakl_shop_id": order.mirakl_shop_id.id if order.mirakl_order_id else "",
                        "process_date": datetime.datetime.now(),
                        'processing_time': order_shift,
                        "warehouse": order.warehouse_id.code,
                        "delivery_mode_cds": "Domicile standard"
                    }

                    # Update Order Line Details and Carrier Update
                    if len(order.order_line) > 0:
                        count = 1
                        for line in order.order_line:
                            data.update({
                                "ean_product": "0"+line.product_id.barcode,
                                "quantity": int(line.product_uom_qty),
                                "product_id": line.product_id.id,
                                "inventory_stock_count": line.product_id.qty_available,
                            })
                            #Update Order Name
                            if len(order.order_line) > 1:
                                data.update({
                                    "order_id": order_id + "-" + str(count),
                                })
                                count += 1
                            self.env['processed.order'].create_processed_orders(data)
                    else:
                        _logger.info("skipped order from processing because product is missing ~~~~~~~~~~~%r ;;;;;;",order.id)

    # Devide order to process among warehouses
    def separate_warehouse_orders(self, sale_orders):
        warehouses = [warehouse.warehouse_id for warehouse in self.env['marketplace.warehouse'].search([])]
        etl_orders = []
        ifull_orders = []
        cdisc_orders= []
        for order in sale_orders:
            if order.warehouse_id in warehouses and order.warehouse_id.code == "IFUL":
                ifull_orders.append(order)
            if order.warehouse_id in warehouses and order.warehouse_id.code in ["ETL"]:
                etl_orders.append(order)
            if order.warehouse_id in warehouses and order.warehouse_id.code == "CDISC":
                cdisc_orders.append(order)
        if etl_orders:
            self.generate_etl_orders_data(etl_orders)
        if ifull_orders:
            self.generate_ifull_orders_data(ifull_orders)
        if cdisc_orders:
            self.generate_cdisc_orders_data(cdisc_orders)
        return True

    # Btn to process orders of a particular shop
    def process_warehouse_orders(self):
        sale_orders = self.env['sale.order'].search([('mirakl_shop_id', '=', self.id), ('mirakl_order_id', '!=', False), ('mirakl_order_state', '=', 'shipping')])
        if len(sale_orders) > 0:
            self.separate_warehouse_orders(sale_orders)

    # Convert Country Language
    def get_country_value(self, order, check):
        countries = { 
            "espagne" : "Spanien",
            "spain" : "Spanien",
            "beligique" : "Belgien",
            "belgium": "Belgien",
            "france" : "Frankreich",
            "irlande" : "Irland",
            "irland" : "Irland",
            "uk" : "Großbritannien",
            "italie" : "Italien",
            "italy" : "Italien",
            "germany" : "Deutschland",
            "autriche" : "Österreich",
            "portugal" : "Portugal",
            "pays-bas" : "Niederlande",
            "pologne" : "Polen",
            "suisse" : "Schweiz"
        }
        if order.partner_shipping_id.country_id.name:
            if check:
                if countries.get(order.partner_shipping_id.country_id.name.lower()):
                    return countries.get(order.partner_shipping_id.country_id.name.lower())
            return order.partner_shipping_id.country_id.name
        if order.partner_id.country_id.name:
            if check:
                if countries.get(order.partner_id.country_id.name.lower()):
                    return countries.get(order.partner_id.country_id.name.lower())
            return order.partner_id.country_id.name
        return False
