from odoo import fields,api, models,_
import requests
from odoo.http import request
import json, datetime
import pytz

import logging
_logger = logging.getLogger(__name__)

class EverstoxShop(models.Model):
    _name = 'everstox.shop'
    _description = 'Everstox Shop'
    _rec_name = "name"


    @api.depends('warehouse_id')
    def _sale_order_count(self):
        for shop in self:
            if shop.warehouse_id:
                sale_orders = self.env['sale.order'].search([('warehouse_id', '=', shop.warehouse_id.id)])
                shop.same_warehouse_sale_order_count = len(sale_orders)


    shop_active = fields.Boolean("Activate", default=False)
    name = fields.Char("Name",required=True)
    shop_url = fields.Char("Shop URL", required=True)
    warehouse_id = fields.Many2one("stock.warehouse", "Warehouse",required=True)
    everstox_warehouse_id = fields.Many2one("everstox.shop.warehouse", "Everstox Warehouse", default=False)
    is_warehouse_mapped = fields.Boolean("Warehouse Added", default=False)

    shop_id = fields.Char("Shop Id",required=True)
    shop_instance_id = fields.Char("Shop Instance Id",required=True)
    shop_api_key = fields.Char("Shop API Key",required=True)

    same_warehouse_sale_order_count = fields.Integer("Warehouses Sale Order Count", compute = "_sale_order_count", default= 0)

    # Filters
    # Product Management Fields 
    activate_product_filters = fields.Boolean("Activate Product Filters")
    product_item_id = fields.Char("Everstox Product ID")


    # Order Management Fields 
    activate_order_filter = fields.Boolean("Activate Order Filters")
    order_state = fields.Selection([
        ('created','Created'),
        ('in_fulfillment','In Fulfillment'),
        ('shipped','Shipped'),
        ('completed','Completed'),
        ('canceled','Canceled'),
    ], string="State")
    order_status = fields.Selection([
        ('open', 'Open'),
        ('closed', 'Closed'),
        ('requires_attention', 'Requires Attention'),
        ('all', 'All')
    ], string="Status")
    order_number = fields.Char("Order Number")


    # Stock Management fields 
    activate_stock_filter = fields.Boolean("Activate Stock Filters")
    stock_status = fields.Selection([('all', 'ALL'), ('active', 'Active'), ('inactive', 'Inactive')], string="Stock Status")
    product_sku = fields.Char("Product SKU")
    stock_runway_lte = fields.Char("Stock Runaway <=")
    stock_runway_lt = fields.Char("Stock Runaway <")
    stock_runway_gte = fields.Char("Stock Runaway >=")
    last_stock_update_time = fields.Datetime("Stock Last Updated")
    is_stock_synced = fields.Boolean("Is Stock Synced")


    #Product Order Counter
    product_created_count = fields.Integer("Product Created Count", default=0) 
    product_updated_count = fields.Integer("Product Updated Count", default=0) 

    #Get Order Counter
    order_created_count = fields.Integer("Order Created Count", default=0) 
    order_updated_count = fields.Integer("Order Updated Count", default=0) 


    #Stock Counter
    stock_created_count = fields.Integer("Stock Created Count", default=0) 
    stock_updated_count = fields.Integer("Stock Updated Count", default=0)

    #Transfer Counter
    create_transfer_count = fields.Integer("Create Transfer Count", default=0) 
    update_transfer_count = fields.Integer("Update Transfer Count", default=0)

    #warehouse stock counter
    warehouse_stock_update_create_count =fields.Integer("Warehouse Stock Created Count", default=0) 
    warehouse_stock_update_updated_count =fields.Integer("Warehouse Stock Updated Count", default=0) 

   
   
    # Transfer Management Fields 
    activate_transfer_filter  = fields.Boolean("Activate Transfer Filter")
    transfer_number = fields.Char("Transfer Number")
    transfer_state = fields.Selection([('transmission_to_warehouse_pending','Transmission To Warehouse Pending'),('transmitted_to_warehouse','Transmitted To Warehouse'),('accepted_by_warehouse','Accepted By Warehouse'),('rejected_by_warehouse','Rejected By Warehouse'),('in_progress','In Progress'),('completed','Completed'),('canceled','Canceled')])
    transfer_stategroup = fields.Selection([('open','Open'),('closed','Closed'),('requires_attention','Requires Attention'),('all','All')])



    total_product = fields.Integer("Total Product", compute="_get_product_count")


    # Counter
    shop_order_count = fields.Integer("Shop Order Count", compute = "_shop_order_count")
    shipment_count = fields.Integer("Shipment Count", compute = "_shipment_count")
    return_count = fields.Integer("Return Count", compute = "_return_count")
    stock_count = fields.Integer("Stocks Count", compute = "_stocks_count")
    transfer_count = fields.Integer("Transfer Count", compute="_transfer_count")


    #################
    # Helper Methods
    ##################
    
    # Compute Product
    def _get_product_count(self):
        for shop in self:
            shop.total_product = self.env["everstox.shop.product"].search_count([('everstox_shop_id', '=', self.id)])


    def _shop_order_count(self):
        for shop in self:
            shop.shop_order_count = self.env["everstox.shop.order"].search_count([('everstox_shop_id', '=', self.id)])

    def _shipment_count(self):
        for shop in self:
            shop.shipment_count = self.env["everstox.order.shipment"].search_count([])

    def _return_count(self):
        for shop in self:
            shop.return_count = self.env["everstox.order.return"].search_count([('everstox_shop_id', '=', self.id)])

    def _stocks_count(self):
        for shop in self:
            shop.stock_count = self.env["everstox.warehouse.stock"].search_count([('everstox_shop_id', '=', self.id)])
    
    def _transfer_count(self):
        for shop in self:
            shop.transfer_count  = self.env["everstox.transfers"].search_count([('everstox_shop_id', '=', self.id)])

    #################
    # Special Buttons
    #################

    def action_view_everstox_product(self):
        self.ensure_one()
        
        return {
            'type': 'ir.actions.act_window',
            'name': _("%s's Shop Products", self.name),
            'view_mode': 'list,form',
            'res_model': 'everstox.shop.product',
            'context': {
                'search_default_mapping_status': 1,
            },
            'domain': [('everstox_shop_id', 'in', [self.id])],
        }


    
    # def action_view_everstox_Ifulfilments(self):
    #     self.ensure_one()
        
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'name': _("%s's Shop Products", self.name),
    #         'view_mode': 'list,form',
    #         'res_model': 'everstox.shop.product',
    #         'context': {
    #             'search_default_mapping_status': 1,
    #         },
    #         'domain': [('everstox_shop_id', 'in', [self.id])],
    #     }

    def action_view_warehouses_product_unit(self):
        self.ensure_one()
        
        return {
            'type': 'ir.actions.act_window',
            'name': _("%s's Product Units", self.name),
            'view_mode': 'list,form',
            'res_model': 'everstox.product.unit',
            'context': {
            },
            'domain': [('everstox_shop_id', 'in', [self.id])],
        }

    def action_view_everstox_sale_orders(self):
        self.ensure_one()
        
        return {
            'type': 'ir.actions.act_window',
            'name': _("%s's Shop Orders", self.name),
            'view_mode': 'list,form',
            'view_ids': [(self.env.ref('odoo_everstox_integration.everstox_shop_sale_order_view_tree').id, 'list'), (self.env.ref('odoo_everstox_integration.everstox_order_view_form').id, 'form')],
            'res_model': 'everstox.shop.order',
            'search_ids': [self.env.ref('odoo_everstox_integration.view_everstox_order_filters').id],
            'context': {
                'search_default_create_date': 1, 'search_default_everstox_mapped_state': 1, 'search_default_order_state': 1
            },
            'domain': [('everstox_shop_id', 'in', [self.id])],
        }

    def action_view_everstox_shipments(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _("%s's Shipments", self.name),
            'view_mode': 'list,form',
            'view_ids': [(self.env.ref('odoo_everstox_integration.everstox_order_shipment_view_tree').id, 'list'), (self.env.ref('odoo_everstox_integration.everstox_order_shipment_view_form').id, 'form')],
            'res_model': 'everstox.order.shipment',
            'search_id': [self.env.ref('odoo_everstox_integration.view_everstox_order_shipment_filters').id],
            'context': {
                'search_default_create_date': 1,
                'search_default_shift': 1,
            },
        }

    def action_view_everstox_fulfillments(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _("%s's Fulfillments", self.name),
            'view_mode': 'list,form',
            'view_ids': [(self.env.ref('odoo_everstox_integration.everstox_order_fulfillment_view_tree').id, 'list'), (self.env.ref('odoo_everstox_integration.everstox_order_fulfillment_view_form').id, 'form')],
            'res_model': 'everstox.order.fulfillment',
            'context': {
                # 'search_default_everstox_mapped_state': 1,
            },
        }

    def action_view_everstox_returns(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _("%s's Returns", self.name),
            'view_mode': 'list,form',
            'view_ids': [(self.env.ref('odoo_everstox_integration.everstox_order_return_view_tree').id, 'list'), (self.env.ref('odoo_everstox_integration.everstox_order_return_view_form').id, 'form')],
            'res_model': 'everstox.order.return',
            # 'search_ids': [self.env.ref('odoo_everstox_integration.view_everstox_order_filters').id],
            'context': {
                # 'search_default_everstox_mapped_state': 1,
            },
            # 'domain': [('everstox_shop_id', 'in', [self.id])],
        }

    def action_view_everstox_warehouse_stock(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _("%s's Stocks", self.name),
            'view_mode': 'list,form',
            'view_ids': [(self.env.ref('odoo_everstox_integration.everstox_warehouse_stock_view_tree').id, 'list'), (self.env.ref('odoo_everstox_integration.everstox_warehouse_stock_view_form').id, 'form')],
            'res_model': 'everstox.warehouse.stock',
            # 'search_ids': [self.env.ref('odoo_everstox_integration.view_everstox_order_filters').id],
            'context': {
                # 'search_default_everstox_mapped_state': 1,
            },
            'domain': [('everstox_shop_id', 'in', [self.id])],
        }

    def action_view_everstox_warehouse_stock_items(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _("%s's Stock Items", self.name),
            'view_mode': 'list,form',
            'view_ids': [(self.env.ref('odoo_everstox_integration.everstox_warehouse_stock_item_view_tree').id, 'list'), (self.env.ref('odoo_everstox_integration.everstox_warehouse_stock_item_view_form').id, 'form')],
            'res_model': 'everstox.warehouse.stock.item',
            # 'search_ids': [self.env.ref('odoo_everstox_integration.view_everstox_order_filters').id],
            'context': {
                # 'search_default_everstox_mapped_state': 1,
            },
            # 'domain': [('everstox_shop_id', 'in', [self.id])],
        }
        
    def action_view_everstox_warehouse_stock_quantities(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _("%s's Stock Quantities", self.name),
            'view_mode': 'list,form',
            'view_ids': [(self.env.ref('odoo_everstox_integration.everstox_warehouse_stock_quantities_view_tree').id, 'list'), (self.env.ref('odoo_everstox_integration.everstox_warehouse_stock_quantities_view_form').id, 'form')],
            'res_model': 'everstox.stock.quantities',
            # 'search_ids': [self.env.ref('odoo_everstox_integration.view_everstox_order_filters').id],
            'context': {
                # 'search_default_everstox_mapped_state': 1,
            },
            # 'domain': [('everstox_shop_id', 'in', [self.id])],
        }

    def action_view_everstox_warehouse_stock_updates(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _("%s's Stocks", self.name),
            'view_mode': 'list,form',
            'view_ids': [(self.env.ref('odoo_everstox_integration.everstox_warehouse_stock_updates_view_tree').id, 'list'), (self.env.ref('odoo_everstox_integration.everstox_warehouse_stock_updates_view_form').id, 'form')],
            'res_model': 'everstox.warehouse.stock.updates',
            # 'search_ids': [self.env.ref('odoo_everstox_integration.view_everstox_order_filters').id],
            'context': {
                # 'search_default_everstox_mapped_state': 1,
            },
            'domain': [('everstox_shop_id', 'in', [self.id])],
        }

    def action_view_warehouses_sale_orders(self):
        self.ensure_one()
        
        return {
            'type': 'ir.actions.act_window',
            'name': _("%s's Sale Orders", self.name),
            'view_mode': 'list,form',
            'res_model': 'sale.order',
            'context': {
            },
            'domain': [('warehouse_id', 'in', [self.warehouse_id.id])],
        }

    def action_view_everstox_tranfers(self):
        self.ensure_one()
        
        return {
            'type': 'ir.actions.act_window',
            'name': _("%s's Transfers", self.name),
            'view_mode': 'list,form',
            'res_model': 'everstox.transfers',
            'view_ids': [(self.env.ref('odoo_everstox_integration.everstox_transfer_view_tree').id, 'list'), (self.env.ref('odoo_everstox_integration.everstox_transfer_view_form').id, 'form')],
            'context': {
            },
            'domain': [('everstox_shop_id', 'in', [self.id])],
        }

    def action_view_everstox_tranfer_items(self):
        self.ensure_one()
        
        return {
            'type': 'ir.actions.act_window',
            'name': _("%s's Transfer Items", self.name),
            'view_mode': 'list,form',
            'res_model': 'everstox.transfer.item',
            'view_ids': [(self.env.ref('odoo_everstox_integration.everstox_transfer_item_view_tree').id, 'list'), (self.env.ref('odoo_everstox_integration.everstox_transfer_item_view_form').id, 'form')],
            'context': {
            },
            'domain': [('everstox_shop_id', 'in', [self.id])],
        }

    def action_view_everstox_tranfer_shipment(self):
        self.ensure_one()
        search_view_ref = self.env.ref('odoo_everstox_integration.view_everstox_order_shipment_filters', False)
        return {
            'type': 'ir.actions.act_window',
            'name': _("%s's Transfer Shipment", self.name),
            'view_mode': 'list,form',
            'res_model': 'everstox.transfer.shipment',
            'view_ids': [(self.env.ref('odoo_everstox_integration.everstox_transfer_shipment_view_tree').id, 'list'), (self.env.ref('odoo_everstox_integration.everstox_transfer_shipment_view_form').id, 'form')],
            'search_view_id': search_view_ref and [search_view_ref.id],
            'context': {
                'search_default_create_date': 1,
                'search_default_shift': 1,
            },
            'domain': [('everstox_shop_id', 'in', [self.id])],
        }

    def action_view_everstox_tranfer_shipment_item(self):
        self.ensure_one()
        
        return {
            'type': 'ir.actions.act_window',
            'name': _("%s's Transfer Shipment Items", self.name),
            'view_mode': 'list,form',
            'res_model': 'everstox.transfer.shipment.item',
            'view_ids': [(self.env.ref('odoo_everstox_integration.everstox_transfer_shipment_item_view_tree').id, 'list'), (self.env.ref('odoo_everstox_integration.everstox_transfer_shipment_item_view_form').id, 'form')],
            'context': {
            },
            'domain': [('everstox_shop_id', 'in', [self.id])],
        }

    def action_view_everstox_tranfer_shipment_batches(self):
        self.ensure_one()
        
        return {
            'type': 'ir.actions.act_window',
            'name': _("%s's Transfer Shipment Batches", self.name),
            'view_mode': 'list,form',
            'res_model': 'everstox.transfer.shipment.batches',
            'view_ids': [(self.env.ref('odoo_everstox_integration.everstox_transfer_shipment_batches_view_tree').id, 'list'), (self.env.ref('odoo_everstox_integration.everstox_transfer_shipment_batches_view_form').id, 'form')],
            'context': {
            },
            'domain': [('everstox_shop_id', 'in', [self.id])],
        }

    def action_view_shipment_options(self):
        self.ensure_one()
        
        return {
            'type': 'ir.actions.act_window',
            'name': _("%s's Shipment Options", self.name),
            'view_mode': 'list,form',
            'res_model': 'shipment.options',
            'context': {
            },
            'domain': [('everstox_shop_id', 'in', [self.id])],
        }

    def get_product(self):
        call = self.shop_url + "api/v1/shops/" + self.shop_id + "/products"
        if self.activate_product_filters and self.product_item_id:
            product_id = self.env["everstox.shop.product"].search([('item_id', '=', self.product_item_id)], limit=1)
            call += "/" + self.product_item_id
            self.get_warehouse_product_by_id(call, product_id)




    def get_orders(self):
        call = self.shop_url + "api/v1/shops/" + self.shop_id + "/orders?limit=500"
        if self.activate_order_filter:
            if self.order_number:
                call += "&order_number="+ self.order_number
            if self.order_state:
                call += "&fulfillment_stategroup="+ self.order_state
            if self.order_status:
                call += "&stategroup="+ self.order_status
        self.order_created_count = 0
        self.order_updated_count = 0 
        response = self.get_warehouse_orders(call)
        return self.show_get_order_wizards()
        # end_call = False
        # while end_call == False:
            # call = self.shop_url + "api/v1/shops/" + self.shop_id + "/orders?limit=100"
            # if self.activate_order_filter:
            #     if self.order_number:
            #         call += "&order_number="+ self.order_number
            #     if self.order_state:
            #         call += "&order_state="+ self.order_state
            #     if self.order_status:
            #         call += "&stategroup="+ self.order_status
            # response = self.get_warehouse_orders(call)
            # if response:
                # end_call = True

    #######################
    # get order wizards message
    #######################
    def show_get_order_wizards(self):

        message = ""
        name = "Warehouse Report"
        message = ("Order Created  -  "+str(self.order_created_count )+"<br/>")
        message += ("Order Updated - "+str(self.order_updated_count)+"<br/>")
        if message:
            return self.env['everstox.shop.wizard'].show_wizard_message(message, name)

    def sync_stock_with_odoo(self):
        self.sync_warehouse_stock()
        stock_ids = self.env['everstox.warehouse.stock'].search([('everstox_shop_id', 'in', [self.id])])
        inventory_ids = inventory_obj = self.env['warehouse.inventory']
        processing_shift = None
        IST = pytz.timezone('Asia/Kolkata')
        time_now = datetime.datetime.strftime(datetime.datetime.now(IST), "%Y-%m-%d %H:%M:%S")
        if int(time_now.split(' ')[1][:2]) <= 12:
            processing_shift = 'morning'
        else:
            processing_shift = 'evening'
        warehouse = self.env['marketplace.warehouse'].search([('warehouse_code', '=', self.warehouse_id.code)])
        for stock in stock_ids:
            product_id = self.env['product.product'].search([('default_code','in', [stock.sku])])
            inventory_ids += inventory_obj.create({
                "product_id": stock.sku,
                "warehouse_id": warehouse.id,
                "available_stock_count": stock.total_stock,
                "processing_time": processing_shift,
                "odoo_product_id": product_id.id,
            })


    ###########
    # API CALLS
    ###########

    # Get Warehouses 
    ################
    def get_warehouse(self):

        call = self.shop_url + "api/v1/shops/" + self.shop_id + "/warehouses"
        response = ""

        try:
            _logger.info("!!!!!~~~~~get_warehouse~~~~~~%r~~~~~~~~~~",call)
            response = requests.get(call,headers={'everstox-shop-api-token': self.shop_api_key,'Content-Type': 'application/json'})

        except Exception as err:
            _logger.info("~~~Get Orders API fail~~~~~~~~%r~~~~~~~~~", err)
        
        if response:
            if response.status_code == 200:
                response = response.json()
                
                # Manage Everstox Warehouses
                for item in response["items"]:
                    if not self.everstox_warehouse_id:
                        warehouse_id = self.env["everstox.shop.warehouse"].create({
                            "warehouse_id": item["id"],
                            "warehouse_name": item["name"],
                            "internal_reference": item["internal_reference"],
                            "creation_date": item["creation_date"],
                            "updated_date": item["updated_date"],
                            "cut_off_time": item["cut_off_time"],
                            "cut_off_window": item["cut_off_window"],
                            "onboarding": item["onboarding"],
                            "everstox_shop_id": self.id,
                        })
                        if warehouse_id:
                            self.everstox_warehouse_id = warehouse_id
                            self.is_warehouse_mapped = True
                            _logger.info("Warehouse Created~~~~~~~    %r   ",warehouse_id)
                    else:
                        self.is_warehouse_mapped = True

        pass


    # Get Carriers
    ##############
    def get_everstox_carriers(self):
        call = self.shop_url + "api/v1/shops/" + self.shop_id + "/shipment-options"
        response = ""

        try:
            _logger.info("!!!!!~~~~~get_warehouse_carriers~~~~~~%r~~~~~~~~~~",call)
            response = requests.get(call,headers={'everstox-shop-api-token': self.shop_api_key,'Content-Type': 'application/json'})

        except Exception as err:
            _logger.info("~~~Get Carriers API fail~~~~~~~~%r~~~~~~~~~", err)
        if response:
            self.process_everstox_carriers(response.json())
            _logger.info("Response~~~~~~~~~~~%r~~~~~~~~~~2",response.json())

        return True
    


    ##################
    # Stock Management
    ##################

    # Get Warehouse Stock
    #####################
    def sync_warehouse_stock(self):
        
        response = False
        call = self.shop_url + "api/v1/shops/" + self.shop_id + "/stocks"
        if self.activate_stock_filter:
            if self.stock_status:
                if "?" not in call:
                    call += "?status=" + self.stock_status
                else:
                    call += "&status=" + self.stock_status
            if self.product_sku:
                if "?" not in call:
                    call+= "?product_sku=" + self.product_sku
                else:
                    call += "&product_sku=" + self.product_sku
            if self.stock_runway_lte:
                if "?" not in call:
                    call += "?stock_runway_lte=" + self.stock_runway_lte
                else:
                    call += "&stock_runway_lte=" + self.stock_runway_lte
            if self.stock_runway_lt:
                if "?" not in call:
                    call += "?stock_runway_lt=" + self.stock_runway_lt
                else:
                    call += "&stock_runway_lt=" + self.stock_runway_lt
            if self.stock_runway_gte:
                if "?" not in call:
                    call += "?stock_runway_gte=" + self.stock_runway_gte
                else:
                    call += "&stock_runway_gte=" + self.stock_runway_gte
        if "?" not in call:
            call += "?limit=1000"
        else:
            call += "&limit=1000"

        try:
            _logger.info("...........Sync Warehouse Stock Call  %r   ...........", call)
            response = requests.get(call,headers={'everstox-shop-api-token': self.shop_api_key,'Content-Type': 'application/json'})
        except Exception as e:
            _logger.info("...........Sync Warehouse Stock API Call Fail  %r   !!!!!!!!!", e)

        if response:
            if response.status_code == 200:
                self.stock_created_count = 0
                self.stock_updated_count =0
                _logger.info(".....Sync Warheouse Stock Response  %r   ", response.json())
                self.process_stock_updates(response.json())
                return self.stock_wizards()
                

    

    #######################
    # get stock wizards message
    #######################
    def stock_wizards(self):

        message = ""
        name = "Stocks Report"
        message = ("Stock Created  -  "+str(self.stock_created_count )+"<br/>")
        message += ("Stock Updated - "+str(self.stock_updated_count)+"<br/>")
        if message:
            return self.env['everstox.shop.wizard'].show_wizard_message(message, name)


    # Get Warehouse Stock Updates
    #############################
    def get_warehouse_stock_updates(self):
        response = False
        call = self.shop_url + "api/v1/shops/" + self.shop_id + "/stock-updates"

        try:
            _logger.info("........... Warehouse Stock Update Call  %r   ...........", call)
            response = requests.get(call,headers={'everstox-shop-api-token': self.shop_api_key,'Content-Type': 'application/json'})
        except Exception as e:
            _logger.info("........... Warehouse Stock Update API Call Fail  %r   !!!!!!!!!", e)

        if response:
            if response.status_code == 200:
                try:
                    # _logger.info("..... Warheouse Stock Update Response  %r   ", response.json())
                    self.warehouse_stock_update_create_count = 0
                    self.warehouse_stock_update_updated_count = 0
                    self.process_get_warehouse_stock_updates_response(response.json())
                except Exception as e:
                    _logger.info("Error while processing warehouse stock updates - response - %r   !!!!!!!!", e, response.text)
            return self.show_warehouse_stock_updates_wizards()
                    

    #######################
    # Warehouse Stock wizards message
    #######################
    def show_warehouse_stock_updates_wizards(self):

        message = ""
        name = "Warehouse Stock Report"
        message = ("Stock Update Create  -  "+str(self.warehouse_stock_update_create_count )+"<br/>")
        message += ("Stock Update Updated - "+str(self.warehouse_stock_update_updated_count )+"<br/>")
        if message:
            return self.env['everstox.shop.wizard'].show_wizard_message(message, name)



    ####################
    # Product Management 
    ####################


    # Get All Products 
    ##################
    def get_warehouse_products(self):
        end_call = False
        while end_call == False:
            call = self.shop_url + "api/v1/shops/" + self.shop_id + "/products?limit=500"
            response = ""

            try:
                _logger.info("!!!!!~~~~~get_warehouse_products~~~~~~%r~~~~~~~~~~",call)
                response = requests.get(call,headers={'everstox-shop-api-token': self.shop_api_key,'Content-Type': 'application/json'})

            except Exception as err:
                _logger.info("~~~Get Product API fail~~~~~~~~%r~~~~~~~~~", err)
            if response:
                self.product_created_count = 0
                self.product_updated_count = 0
                res = self.process_recieved_products(response.json())
                if res:
                    end_call = True
        return self.show_order_message()

    
    #######################
    # product wizards message
    #######################
    def show_order_message(self):

        message = ""
        name = "Product Report"
        message = ("Product Created  -  "+str(self.product_created_count )+"<br/>")
        message += ("Product Updated - "+str(self.product_updated_count)+"<br/>")
        if message:
            return self.env['everstox.shop.wizard'].show_wizard_message(message, name)


    # Get Product By ID
    ###################
    def get_warehouse_product_by_id(self, call, product):
        response = ""
        try:
            _logger.info("!!!!!~~~~~get_selected_product_details~~~~~~%r~~~~~~~~~~",call)
            response = requests.get(call,headers={'everstox-shop-api-token': self.shop_api_key,'Content-Type': 'application/json'})

        except Exception as err:
            _logger.info("~~~Get Product API fail~~~~~~~~%r~~~~~~~~~", err)
        
        if response:
            _logger.info("Response~~~~~~~~~~~%r~~~~~~~~~~2",response.json())
            self.manage_product_creation_response(response.json(), product)

        return True
    


    # Create Productbulk_upload_products_on_everstox
    ################
    def _api_create_everstox_product(self, product_data, product):

        api_call = self.shop_url + "api/v1/shops/" + self.shop_id + "/products"
        data = json.dumps(product_data)
        response = ""

        try:
            _logger.info("!!!!!~~~~~create_product~~call~~~~%r~~~data~~%r~~~~~",api_call, data)
            # response = requests.post(api_call,headers={'everstox-shop-api-token': self.shop_api_key,'Content-Type': 'application/json', 'Accept': 'application/json',}, data=data)
        except Exception as err:
            _logger.info("Create Product API fail~~~~~~~~%r~~~~~~~~~!!!!!!!!!!!!!", err)
        if response.status_code in [400]:
            _logger.info("!!!!!! Create Product Error Response~~~~~~     %r   %r",response.reason, response.json())

        _logger.info("!!!!!! Product Created ~~~~~~     %r   ",response.json())
        if response:
            if response.status_code in [200, 201]:
                response = response.json()
                
                if response["status"] == "skipped":
                    if not product.item_id and response["response"]["product"]:
                        product.item_id = response["response"]["product"]["id"]
                        product.api_mapping_status = "mapped"
                    _logger.info("!!!!!!=Skipped Product Response~~~~~~   everstox product id -  %r   product_id - %r  ",response["response"]["product"]["id"], product.sku)
                    # We can run update heres also
                
                else:
                    try:
                        self.manage_product_creation_response(response, product)
                        _logger.info("!!!!!! Product Created ~~~~~~     %r   ",response)
                    except Exception as e:
                        _logger.info("!!!!!!=Error Response~~~~~~     %r   ",e)
        pass


    # Update Product
    ################
    def _api_update_everstox_product(self, product_data, product):

        api_call = self.shop_url + "api/v1/shops/" + self.shop_id + "/products/"+ product.item_id
        data = json.dumps(product_data)
        response = ""

        _logger.info(".......... Update Product Call   %r   \n........ data    %r   .......",api_call, data)
        try:
            response = requests.put(api_call,headers={'everstox-shop-api-token': self.shop_api_key,'Content-Type': 'application/json', 'Accept': 'application/json',}, data=data)
        except Exception as err:
            _logger.info("Update Product API fail~~~~~~~~%r~~~~~~~~~!!!!!!!!!!!!!", err)
        if response.status_code in [400]:
            _logger.info("!!!!!! Update Product Error Response~~~~~~     %r   ",response.reason)
        _logger.info("Update Product ~~~~~~%r~~~~~~~~%r~",response.reason, response.status_code)
        if response:
            if response.status_code in [200, 201]:
                response = response.json()
                
                if response["status"] == "skipped":
                    if not product.item_id and response["response"]["product"]:
                        product.item_id = response["response"]["product"]["id"]
                    _logger.info("!!!!!!=Skipped Product Response~~~~~~   everstox product id -  %r   product_id - %r  ",response["response"]["product"]["id"], product.sku)
                    # We can run update heres also
                
                else:
                    try:
                        self.manage_product_creation_response(response, product)
                        _logger.info("!!!!!! Product Updated ~~~~~~     %r   ",response)
                    except Exception as e:
                        _logger.info("!!!!!!=Error Response~~~~~~     %r   ",e)
        pass


    # Delete Product
    ################
    def _api_delete_everstox_product(self, product):

        api_call = self.shop_url + "api/v1/shops/" + self.shop_id + "/products/"+ product.item_id
        response = ""

        _logger.info("!!!!!~~~~~delete_product~~call~~~~%r~~~~~~",api_call)
        try:
            response = requests.delete(api_call,headers={'everstox-shop-api-token': self.shop_api_key,'Content-Type': 'application/json', 'Accept': 'application/json',})
        except Exception as err:
            _logger.info("Delete Product API fail~~~~~~~~%r~~~~~~~~~!!!!!!!!!!!!!", err)
        if response.status_code in [400]:
            _logger.info("!!!!!! Delete Product Error Response~~~~~~     %r   %r",response.reason, response.json())

        if response:
            if response.status_code in [204]:
                _logger.info("!!!!!! Product Updated ~~~~~~     %r   ",response)
                product.item_id = ""
                product.api_mapping_status = "unmapped"
        pass

    
    # Products Create And Update
    ############################
    def _api_product_create_or_update_by_csv(self, product_data):

        api_call = self.shop_url + "api/v1/shops/" + self.shop_id + "/products/csv_bulk_import"
        response = ""
        data = json.dumps({"csv_b64": str(product_data)})

        try:
            _logger.info("Bulk product update call ~~~~%r~~~ data ~~~~ %r ~~~~~",api_call, data)
            # response = requests.post(api_call,headers={'everstox-shop-api-token': self.shop_api_key,'Content-Type': 'application/json', 'Accept': 'application/json',}, data=data)
        except Exception as err:
            _logger.info("Create Product API fail~~~~~~~~%r~~~~~~~~~!!!!!!!!!!!!!", err)
        if response.status_code in [400]:
            _logger.info("!!!!!! Bulk Create Product Error Response~~~~~~     %r   %r",response.reason, response.json())
        _logger.info("Products Added ~~~~~~     %r   ",response.json())

        if response:
            if response.status_code in [200]:
                _logger.info("Products Added ~~~~~~     %r   ",response.json())

            pass



    ##################
    # Order Management
    ##################


    # Get Orders
    ############
    def get_warehouse_orders(self, call):

        response = ""
        try:
            _logger.info("!!!!!~~~~~get_warehouse_orders~~~~~~%r~~~~~~~~~~",call)
            response = requests.get(call,headers={'everstox-shop-api-token': self.shop_api_key,'Content-Type': 'application/json'})
        except Exception as err:
            _logger.info("~~~Get Orders API fail~~~~~~~~%r~~~~~~~~~", err)

        if response:
            if response.status_code == 200:
                response = response.json()
                _logger.info("%r", response)
                return self.process_recieved_orders(response)

        return False

    
    # Create Order
    ##############
    def send_order_data_to_everstox(self, order, data):
        
        call = self.shop_url + "api/v1/shops/" + self.shop_id + "/orders"
        data = json.dumps(data)
        response = ""
        
        try:
            _logger.info("!!!!!~~~~~create_orders~~~~~~%r~~~~%r~~~~~~",call, data)
            # response = requests.post(call,headers={'everstox-shop-api-token': self.shop_api_key,'Content-Type': 'application/json'}, data = data)
        except Exception as err:
            _logger.info("~~~Create Orders API fail~~~~~~~~%r~~~~~~~~~", err)

        if response:
            if response.status_code == 400:
                res = response.json()
                _logger.info("~~~Order Creation error~~~~~~~~%r~~~~~~~~~", res.get('detail'))
            if response.status_code == 201:
                res = response.json()
                _logger.info("~~~Create Orders response~~~~~~~~%r~~~~~~~~~", res)
                return self.update_recieved_order(order, res)
            if response.status_code == 202:
                res = response.json()
                try:
                    order_number = res.get("errors").get('order_number').split('"')[1]
                    if order_number == order.order_number:
                        order.everstox_mapped_state = "mapped"
                    _logger.info("......... Order already exists   %r ...........", order_number)
                except:
                    _logger.info("......... Order Creation Error  %r ........!!!!!!!!", res.get("errors"))


        return True

    # Cancel Order
    ##############
    def cancel_order_on_everstox(self, call):
        response = ""
        data = {
            "set_hours_late_zero": True
        }
        try:
            _logger.info(".......... Cancel_order call    %r  ..........",call)
            response = requests.put(call,headers={'everstox-shop-api-token': self.shop_api_key,'Content-Type': 'application/json'}, data= json.dumps(data) )
        except Exception as err:
            _logger.info("........... Cancel Orders API fail~~~~~~~~%r~~~~~~~~~", err)
        _logger.info("............ Order Canceled Response   %r  ..........", response.text)

        if response:
            if response.status_code == 200:
                _logger.info("~~~ Order Canceled Sucessfully ~~~")



    # Delete Order 
    ##############
    def delete_order_on_everstox(self,call):
        response = ""
        try:
            _logger.info("!!!!!~~~~~delete_orders call~~~~~~%r~~~~~%r~~~~~",call, self.shop_api_key)
            response = requests.delete(call,headers={'everstox-shop-api-token': self.shop_api_key,'Content-Type': 'application/json'})
        except Exception as err:
            _logger.info("~~~Delete Orders API fail~~~~~~~~%r~~~~~~~~~", err)
        _logger.info("~~~ Order Deleted Sucessfully ~~~%r", response.text)

        if response:
            if response.status_code == 200:
                _logger.info("~~~ Order Deleted Sucessfully ~~~")

        pass


    # Bulk Order Upload
    ###################
    def update_bulk_orders(self, data):
        response = ""
        data = {
            "csv_b64": data,
            "encoding": "utf-8",
            "csv_delimiter": ";",
            "shop_instance_id": self.shop_instance_id
            }

        call = self.shop_url + "api/v1/shops/" + self.shop_id + "/orders/csv-bulk-import"
        try:
            _logger.info("!!!!!~~~~~upload bulk_orders~~~~~~%r~~~~~~~~~%r~",call, data)
            # response = requests.post(call,headers={'everstox-shop-api-token': self.shop_api_key,'Content-Type': 'application/json'},data=data)
        except Exception as err:
            _logger.info("~~~ Order Bulk Upload API fail~~~~~~~~%r~~~~~~~~~", err)

        if response:
            if response.status_code == 200:
                response = response.json()
                # self.process_recieved_orders(response)

        pass


    #####################
    # Transfer Management
    #####################

    # Get All Transfer 
    def get_all_transfers(self):
        call = self.shop_url + "api/v1/shops/" + self.shop_id +"/transfers"
        try:
            _logger.info("............. Get all transfer   %r  ..........",call)
            response = requests.get(call,headers={'everstox-shop-api-token': self.shop_api_key,'Content-Type': 'application/json'})
        except Exception as err:
            _logger.info("......... Get Transfers API fail  %r ......!!!!!!!!!", err)

        if response:
            if response.status_code == 200:
                _logger.info("~~~ Order Deleted Sucessfully ~~~%r", response.json())
                try:
                    self.create_transfer_count = 0
                    self.update_transfer_count = 0
                    self.process_received_transfers(response.json())
                except Exception as e:
                    _logger.info("......... Transfer Processing break - %r ...........", e)
        return self.transfer_wizards()

    #######################
    # Transfer wizards message
    #######################
    def transfer_wizards(self):

        message = ""
        name = "Transfer Report"
        message = ("Transfer Created  -  "+str(self.create_transfer_count )+"<br/>")
        message += ("Transfer Updated - "+str(self.update_transfer_count)+"<br/>")
        if message:
            return self.env['everstox.shop.wizard'].show_wizard_message(message, name)


    # Create Transfers
    ##################
    def create_transfer(self, data):
        call = self.shop_url + "api/v1/shops/" + self.shop_id +"/transfers"
        response = False
        try:
            _logger.info("............. Create transfer   %r  ......%r....",call, data)
            # response = requests.post(call,headers={'everstox-shop-api-token': self.shop_api_key,'Content-Type': 'application/json'}, data = json.dumps(data))
        except Exception as err:
            _logger.info("......... Create Transfers API fail  %r ......!!!!!!!!!", err)
        if response:
            _logger.info("~Create Transfer.......... %r......%r....", response.status_code, response.reason)
            if response.status_code == 201:
                return response.json()
        return False

    
    # Get Transfer Updates
    ######################
    def get_transfer_update(self, call):
        try:
            _logger.info("............. Get transfer update   %r  ..........",call)
            response = requests.get(call,headers={'everstox-shop-api-token': self.shop_api_key,'Content-Type': 'application/json'})
        except Exception as err:
            _logger.info("......... Get Transfers update API fail  %r ......!!!!!!!!!", err)

        if response:
            if response.status_code == 200:
                _logger.info("....... Updating Transfer ..... %r ......", response.json())
                try:
                    self.process_received_transfers(response.json())
                except Exception as e:
                    _logger.info("......... Transfer Update Processing Failed - %r .......!!!!!!!", e)


    # Add Transfer Updates
    ######################
    def add_transfer_updates(self, call, data):
        response = False
        try:
            _logger.info(".............  transfer complete   %r  ..........",call)
            response = requests.put(call,headers={'everstox-shop-api-token': self.shop_api_key,'Content-Type': 'application/json'}, data= json.dumps(data))
        except Exception as err:
            _logger.info(".........  Transfers complete API fail  %r ......!!!!!!!!!", err)

        if response:
            if response.status_code == 200:
                _logger.info("....... Complete Transfer Response..... %r ......", response.json())
                # try:
                #     self.process_received_transfers(response.json())
                # except Exception as e:
                #     _logger.info("......... Transfer Complete Processing Failed - %r .......!!!!!!!", e)
        pass


    # Complete Transfer
    ###################
    def complete_transfer(self,call):
        response = False
        try:
            _logger.info(".............  Transfer complete   %r  ..........",call)
            # response = requests.post(call,headers={'everstox-shop-api-token': self.shop_api_key,'Content-Type': 'application/json'})
        except Exception as err:
            _logger.info(".........  Transfers complete API fail  %r ......!!!!!!!!!", err)
        _logger.info("....... Complete Transfer Response..... %r ..%r....", response.status_code, response.text)

        if response:
            if response.status_code == 200:
                _logger.info("....... Completed Transfer  ..... %r ......", response.json())
                # self.process_received_transfers(response.json())

            else:
                _logger.info("....... Complete Transfer Response..... %r ......", response.json())


    # Cancel Transfers
    ##################
    def cancel_transfers(self, call):
        response = False
        try:
            _logger.info(".............  transfer cancel   %r  ..........",call)
            response = requests.put(call,headers={'everstox-shop-api-token': self.shop_api_key,'Content-Type': 'application/json'})
        except Exception as err:
            _logger.info(".........  Transfers cancel API failed  %r ......!!!!!!!!!", err)

        if response:
            if response.status_code == 200:
                _logger.info("..........  Successfully canceled transfer  .........")
            else:
                _logger.info("..........  Cancel transfer failed response .........", response.status_code)


    # Delete Transfers
    ##################
    def delete_transfer(self, call):
        response = False
        try:
            _logger.info(".............  transfer delete   %r  ..........",call)
            response = requests.delete(call,headers={'everstox-shop-api-token': self.shop_api_key,'Content-Type': 'application/json'})
        except Exception as err:
            _logger.info(".........  Transfers delete API failed  %r ......!!!!!!!!!", err)

        if response:
            if response.status_code == 201:
                _logger.info("..........  Successfully deleted transfer  .........")
            else:
                _logger.info("..........  Delete transfer failed response .........", response.status_code)



    #################
    # Process Methods
    #################

    def process_get_warehouse_stock_updates_response(self, data):
        if data:
            _logger.info(".............. Total Stock Updates Recieved   %r   ..............", data.get("count"))
            for item in data.get("items"):

                # Stock ID
                stock_obj = self.env['everstox.warehouse.stock']
                existing_stock_update = self.env['everstox.warehouse.stock.updates'].search([('stock_update_id','=', item.get("id"))])
                if not existing_stock_update:
                    stock_id = stock_obj.search([('stock_id', '=', item.get("stock").get('product').get("id"))])

                    stock_update_id = self.env['everstox.warehouse.stock.updates'].create({
                        "action_type": item.get("action_type"),
                        "stock_update_id": item.get("id"),
                        "new_quantity": item.get("new_quantity"),
                        "quantity_correction": item.get("quantity_correction"),
                        "update_datetime": item.get("update_datetime"),
                        "update_reason": item.get("update_reason"),
                        "update_reason_code": item.get("update_reason_code"),
                        "stock_id": stock_id.id if stock_id else stock_obj,
                        "everstox_shop_id": self.id
                    })
                    if stock_update_id:
                        stock_id.total_stock = stock_update_id.new_quantity
                        for item in stock_id.stock_item_ids:
                            item.quantity = stock_id.total_stock
                    self.warehouse_stock_update_create_count +=1
                    _logger.info(".............. Stock Update Created %r  ..........", stock_update_id)
                else:
                    existing_stock_update.process_stock_update(existing_stock_update, item)
                    self.warehouse_stock_update_updated_count +=1
                    _logger.info(".............. Stock Update Updated %r  ..........", existing_stock_update)


    def process_stock_updates(self, data):
        if data:
            stock_obj = self.env["everstox.warehouse.stock"]
            _logger.info("........Total Stock Items Recieved   %r .........", data.get("count"))
            for item in data.get("items"):
                existing_stock = stock_obj.search([('sku', '=', item.get("sku"))]) or stock_obj.search([('stock_id', '=', item.get("id"))])
                if not existing_stock:
                    stock_items = self.process_stock_items(item.get("stocks"))
                    stock_id = stock_obj.create({
                        "batch_product": item.get("batch_product"),
                        "bundle_product": item.get("bundle_product"),
                        "stock_id": item.get("id"),
                        "ignore_during_import": item.get("ignore_during_import"),
                        "ignore_during_shipment": item.get("ignore_during_shipment"),
                        "last_stock_update": item.get("last_stock_update"),
                        "name": item.get("name"),
                        "sku": item.get("sku"),
                        "status": item.get("status"),
                        "total_stock": item.get("total_stock"),
                        "stock_item_ids": stock_items,
                        "everstox_shop_id": self.id,
                    })
                    self.stock_created_count +=1 
                    _logger.info("........... Stock Created   %r  ...........", stock_id.sku)
                else:
                    # Updating Stock 
                    existing_stock.total_stock = item.get("total_stock")
                    existing_stock.status = item.get("status")
                    existing_stock.last_stock_update = item.get("last_stock_update")
                    existing_stock.everstox_shop_id = self.id
                    
                    
                    # Update Stock Items 
                    for stock_item in item.get("stocks"):

                        existing_stock_item = existing_stock.stock_item_ids.search([('stock_item_id', '=', stock_item.get("id"))])
                        
                        if existing_stock_item:
                            
                            existing_stock_item.stock_runway = stock_item.get("stock_runway")
                            existing_stock_item.quantity = stock_item.get("quantity")
                            existing_stock_item.updated_date = stock_item.get("updated_date")
                            
                            for quantity in stock_item.get("stock_quantities"):

                                existing_quantity_type = existing_stock_item.stock_quantities_ids.search([('stock_type','=',quantity.get("stock_type")),('stock_item_id','in',[existing_stock_item.id])])

                                if existing_quantity_type:
                                    existing_quantity_type.stock_quantity = quantity.get("quantity")
                                else:
                                    _logger.info("Already Items added %r   ", existing_stock_item.stock_quantities_ids)
                                    new_qty = self.env["everstox.stock.quantities"].create({
                                        "stock_quantity": quantity.get("quantity"),
                                        "stock_type": quantity.get("stock_type"),
                                        "stock_item_id": existing_stock_item.id,
                                    })
                        else:
                            
                            existing_stock.stock_item_ids.create({
                                "stock_item_id": stock_item.get("id"),
                                "quantity": stock_item.get("quantity"),
                                "stock_runway": stock_item.get("stock_runway"),
                                "stock_warehouse_id": stock_item.get("warehouse").get("id"),
                                "stock_warehouse_name": stock_item.get("warehouse").get("name"),
                                "updated_date": stock_item.get("updated_date"),
                                "batch": stock_item.get("batch"),
                                "stock_quantities_ids": self.process_stock_item_quantities(stock_item),
                            })
                    self.stock_updated_count += 1
                    _logger.info("............ Stock Updated   %r ...........", existing_stock.sku)
            self.is_stock_synced = True


    def process_stock_items(self,  stocks):
        stock_items = stock_item_obj = self.env["everstox.warehouse.stock.item"]
        for stock in stocks:
            stock_quantities = self.process_stock_item_quantities(stock)
            stock_items += stock_item_obj.create({
                "stock_item_id": stock.get("id"),
                "quantity": stock.get("quantity"),
                "stock_runway": stock.get("stock_runway"),
                "stock_warehouse_id": stock.get("warehouse").get("id"),
                "stock_warehouse_name": stock.get("warehouse").get("name"),
                "updated_date": stock.get("updated_date"),
                "batch": stock.get("batch"),
                "stock_quantities_ids": stock_quantities,
            })
        return stock_items
                

    def process_stock_item_quantities(self, stock):
        stock_quantities = stock_quantities_obj = self.env["everstox.stock.quantities"]
        for qty in stock.get("stock_quantities"):
            stock_quantities += stock_quantities_obj.create( {
                "stock_quantity": qty.get("quantity"),
                "stock_type": qty.get("stock_type")
            })
        return stock_quantities


    def process_everstox_carriers(self, data):
        shipment_option_obj = self.env['shipment.options']
        for item in data.get("items"):
            already_exist = shipment_option_obj.search([('carrier_id','=', item.get("id"))])
            if not already_exist:
                data = self.process_shipment_aliases(item.get("shipment_option_aliases"))
                shipment_option_id = shipment_option_obj.create({
                    "creation_date": item.get("creation_date"),
                    "external_identifiers": item.get("external_identifier"),
                    "carrier_id": item.get("id"),
                    "ignored": item.get("ignored"),
                    "name": item.get("name"),
                    "everstox_shop_id": self.id,
                    "status": item.get("status"),
                    "updated_date": item.get("update_date"),
                    "shipment_option_aliases_ids": data
                })
            else:
                _logger.info("~~Shipment Already Exists~~~~~~~~`%r~~~~~~~~", already_exist.id)


    def process_shipment_aliases(self, shipment_aliases):
        data = []
        for aliase in shipment_aliases:
            prepared_data = (0,0,{
                "name": aliase.get("name"),
                "aliase_id": aliase.get("id"),
            })
            data.append(prepared_data)

        return data


    def process_order_update(self, data):
       
        order_id = self.env["everstox.shop.order"].search([('order_id','=', data.get("order_details").get("id"))])
        _logger.info("Order data   %r   !!!!!!!!!",order_id)
        
        # Once All changes made into system send response to API 
        # {
        #     "shipments_forwarded_to_shop": [
        #         {
        #             "shipment_id": "bf786497-8cc0-4fb0-9edc-01e33c194f3e"
        #         },
        #         {
        #             "shipment_id": "c5666bb9-e1cf-40c8-99b8-3bb8f04e7a66"
        #         }
        #     ]
        # }
        if order_id:
            self.update_recieved_order(order_id, data.get("order_details"))


    def process_stock_update(self, data):
        product_id = self.env['everstox.shop.product'].search([('sku', 'in',[data.get('sku')]),("everstox_shop_id", "in", [self.id])], limit=1)
        if product_id:
            product_id.total_stock = data.get('total_stock')
            product_id.status = data.get('status')
            
            _logger.info("Product Updated    %r ~~~~~~~~~~~",product_id.sku)
        else:
            _logger.info("Product not found for the given data   %r   !!!!!!!!!",data)
        pass


    def manage_product_creation_response(self, response, product):
        product.creation_date = response["creation_date"]
        product.item_id = response["id"]
        product.updated_date = response["updated_date"]
        product.total_stock = response["total_stock"]
        product.status = response["status"]
        product.api_mapping_status = "mapped"
        self.env.cr.commit()



    def process_recieved_products(self, response_data):
        if response_data.get('count') > 0:

            product_obj = self.env["everstox.shop.product"]
            product_unit_obj = self.env["everstox.product.unit"]
            odoo_product_obj = self.env["product.product"]
            for item in response_data.get("items"):
                existing_product = product_obj.search([('sku', 'in', [item.get("sku")]),('everstox_shop_id', '=', self.id)])
                if not existing_product:
                    odoo_product_id = odoo_product_obj.search([('default_code', '=', item.get("sku"))])
                    existing_product = product_obj.create({
                        "everstox_shop_id": self.id,
                        "name": item.get("name"),
                        "item_id": item.get("id"),
                        "sku": item.get("sku"),
                        "status": item.get("status"),
                        "shop_id": item.get("shop_id"),
                        "total_stock": item.get("total_stock"),
                        "creation_date": item.get("creation_date"),
                        "updated_date": item.get("updated_date"),
                        "batch_product": item.get("batch_product"),
                        "bundle_product": item.get("bundle_product"),
                        "bundles": item.get("bundles"),
                        "color": item.get("color"),
                        "country_of_origin": item.get("country_of_origin"),
                        "creation_date": item.get("creation_date"),
                        "customs_code": item.get("customs_code"),
                        "customs_description": item.get("customs_description"),
                        "ignore_during_import": item.get("ignore_during_import"),
                        "ignore_during_shipment": item.get("ignore_during_shipment"),
                        "color": item.get("color"),
                        "product_id": odoo_product_id.id if odoo_product_id else False,
                        "api_mapping_status": "mapped",
                    })
                    if odoo_product_id:
                        odoo_product_id.everstox_product_id = existing_product.id
                        odoo_product_id.everstox_shop_ids = self.id,
                        odoo_product_id.everstox_mapped_state = "mapped"
                        _logger.info("............ Product Created ..........   %r .......", odoo_product_id.name)

                    for unit in item.get("units"):
                        existing_unit = product_unit_obj.search([('unit_id', '=', unit.get("id"))])
                        if not existing_unit:
                            product_unit_obj.create({
                                "everstox_shop_id": self.id,
                                "everstox_product_id": existing_product.id,
                                "base_unit_id": unit.get("base_unit_id"),
                                "base_unit_name":unit.get("base_unit_name"),
                                "default_unit": unit.get("default_unit"),
                                "gtin": unit.get("gtin"),
                                "unit_id": unit.get("id"),
                                "name": unit.get("name"),
                                "quantity_of_base_unit": unit.get("quantity_of_base_unit"),
                                "weight_gross_in_kg":unit.get("weight_gross_in_kg"),
                                "weight_net_in_kg":unit.get("weight_net_in_kg"),
                                "height_in_cm":unit.get("height_in_cm"),
                                "width_in_cm":unit.get("width_in_cm"),
                                "length_in_cm":unit.get("length_in_cm"),
                            })
                    self.product_created_count += 1
                else:
                    if not existing_product.item_id:
                        existing_product.item_id = item.get("id")
                    if existing_product.api_mapping_status == "unmapped":
                        existing_product.api_mapping_status = "mapped"
                    if item.get("total_stock") != existing_product.total_stock:
                        existing_product.total_stock = item.get("total_stock")
                    _logger.info("............ Product Updated ..........   %r .......", existing_product.name)
                    self.product_updated_count += 1

                    # Other Product Feilds To Update


        return True


        

    def process_recieved_orders(self, response):
        _logger.info("Received Order Count ->    %r   ", response.get("count"))
        shop_order_obj = self.env["everstox.shop.order"]
        for item in response.get("items"):
            existing_order = shop_order_obj.search([('order_id','in', [item.get("id")])], limit=1) or shop_order_obj.search([('order_number','in', [item.get("order_number")])], limit=1)
            # If Create Order else Update Order 
            if len(existing_order) < 1:
                order_lines = self.prepare_order_item_data(item.get("order_items"))
                fulfillments = self.prepare_fulfillments_data(item.get("fulfillments"), False)
                returns = self.prepare_return_data(item.get("returns"))

                new_order_id = shop_order_obj.create({
                    "billing_vat_number": item.get("billing_address").get("VAT_number"),
                    "billing_address_1": item.get("billing_address").get("address_1"),
                    "billing_address_2": item.get("billing_address").get("address_2"),
                    "billing_address_type": item.get("billing_address").get("address_type"),
                    "billing_city": item.get("billing_address").get("city"),
                    "billing_company": item.get("billing_address").get("company"),
                    "billing_contact_person": item.get("billing_address").get("contact_person"),
                    "billing_country": item.get("billing_address").get("country"),
                    "billing_country_code": item.get("billing_address").get("country_code"),
                    "billing_first_name": item.get("billing_address").get("first_name"),
                    "billing_last_name": item.get("billing_address").get("last_name"),
                    "billing_latitude": item.get("billing_address").get("latitude"),
                    "billing_longitude": item.get("billing_address").get("longitude"),
                    "billing_phone": item.get("billing_address").get("phone"),
                    "billing_province": item.get("billing_address").get("province"),
                    "billing_province_code": item.get("billing_address").get("province_code"),
                    "billing_department": item.get("billing_address").get("department"),
                    "billing_sub_department": item.get("billing_address").get("sub_department"),
                    "billing_title": item.get("billing_address").get("title"),
                    "billing_zip": item.get("billing_address").get("zip"),

                    "shipping_address_1": item.get("shipping_address").get("address_1"),
                    "shipping_address_2": item.get("shipping_address").get("address_2"),
                    "shipping_address_type": item.get("shipping_address").get("address_type"),
                    "shipping_city": item.get("shipping_address").get("city"),
                    "shipping_company": item.get("shipping_address").get("company"),
                    "shipping_contact_person": item.get("shipping_address").get("contact_person"),
                    "shipping_country": item.get("shipping_address").get("country"),
                    "shipping_country_code": item.get("shipping_address").get("country_code"),
                    "shipping_first_name": item.get("shipping_address").get("first_name"),
                    "shipping_last_name": item.get("shipping_address").get("last_name"),
                    "shipping_latitude": item.get("shipping_address").get("latitude"),
                    "shipping_longitude": item.get("shipping_address").get("longitude"),
                    "shipping_phone": item.get("shipping_address").get("phone"),
                    "shipping_province": item.get("shipping_address").get("province"),
                    "shipping_province_code": item.get("shipping_address").get("province_code"),
                    "shipping_department": item.get("shipping_address").get("department"),
                    "shipping_sub_department": item.get("shipping_address").get("sub_department"),
                    "shipping_title": item.get("shipping_address").get("title"),
                    "shipping_zip": item.get("shipping_address").get("zip"),

                    "shipping_price_currency" : item.get("shipping_price").get("currency"),
                    "shipping_price_discount" : item.get("shipping_price").get("discount"),
                    "shipping_price_discount_gross" : item.get("shipping_price").get("discount_gross"),
                    "shipping_price_discount_net" : item.get("shipping_price").get("discount_net"),
                    "shipping_price" : item.get("shipping_price").get("price"),
                    "shipping_price_gross" : item.get("shipping_price").get("price_gross"),
                    "shipping_price_net_after_discount" : item.get("shipping_price").get("price_net_after_discount"),
                    "shipping_price_net_before_discount" : item.get("shipping_price").get("price_net_before_discount"),
                    "shipping_price_tax" : item.get("shipping_price").get("tax"),
                    "shipping_price_tax_amount" : item.get("shipping_price").get("tax_amount"),
                    "shipping_price_tax_rate" : item.get("shipping_price").get("tax_rate"),

                    "creation_date" : item.get("creation_date"),
                    "custom_email" : item.get("custom_email"),
                    "financial_status" : item.get("financial_status"),
                    "hours_late" : item.get("hours_late"),
                    "order_id" : item.get("id"),
                    "order_date" : item.get("order_date"),
                    "order_number" : item.get("order_number"),
                    "order_priority" : item.get("order_priority"),
                    "out_of_stock_hours" : item.get("out_of_stock_hours"),
                    "payment_methods" : item.get("payment_methods"),
                    "requested_delivery_date" : item.get("requested_delivery_date"),
                    "requested_warehouse_id" : item.get("requested_warehouse_id"),
                    "order_shop_id" : item.get("shop_id"),
                    "shop_instance_id" : item.get("shop_instance").get("id"),
                    "shop_instance_name" : item.get("shop_instance").get("name"),
                    "state" : item.get("state"),
                    "udpated_date" : item.get("udpated_date"),
                    "order_errors" : item.get("errors"),
                    "order_returns" : item.get("returns"),
                    "order_attachments" : item.get("attachments"),
                    "order_custom_attributes" : item.get("custom_attributes"),

                    "shop_order_line_ids": order_lines,
                    "shop_order_fulfillment_ids": fulfillments,
                    "shop_order_return_ids": returns,
                    "everstox_shop_id": self.id,
                    "everstox_mapped_state": "mapped",
                })
                self.order_created_count += 1
                _logger.info(".......... Order Created .........  %r ........", new_order_id)
            else:

                # Order Detials Update 
                existing_order.order_id = item.get("id")
                existing_order.state = item.get("state")
                existing_order.udpated_date = item.get("udpated_date")
                existing_order.everstox_mapped_state = "mapped"
                _logger.info("............ Order Udpated ......... %r .......", existing_order.order_id)
                self.order_updated_count += 1

                # Order Line Details Update 
                for line_item in item.get("order_items"):
                    existing_order_line = existing_order.shop_order_line_ids.search([('shop_order_id', '=', existing_order.id),('order_line_product_sku' , '=', line_item.get('product').get('sku'))])
                    if len(existing_order_line) > 0:
                        existing_order_line.order_line_id = line_item.get("id")
                        _logger.info("......... Order line Udpated  %r  ..........", existing_order_line.order_line_id)

                # Order Fulfillment Details Update
                if len(item.get("fulfillments")) > len(existing_order.shop_order_fulfillment_ids):
                    fulfillments = self.prepare_fulfillments_data(item.get("fulfillments"), existing_order)
                    if fulfillments:    
                        existing_order.write({
                            "shop_order_fulfillment_ids": fulfillments,
                        })
                        _logger.info("........... Order fulfillment Udpated  %r   ..........", existing_order.shop_order_fulfillment_ids)
        return True


    def update_recieved_order(self, order, response):
        if order:
            if len(response.get("fulfillments")) >= 1: 
                fulfillments = self.prepare_fulfillments_data(response.get("fulfillments"), order)
            order.write({
                "order_id": response.get("id"),
                "state": response.get("state"),
                "udpated_date": response.get("udpated_date"),
                "shop_order_fulfillment_ids": fulfillments,
                "everstox_mapped_state": "mapped"
            })
            self.update_order_lines( order, response.get('order_items'))
            return True
    

    def update_order_lines(self, order, order_items):
        for order_line in order.shop_order_line_ids:
                if not order_line.order_line_id:
                    for item in order_items:
                        if item.get('product').get('sku') == order_line.order_line_product_name:
                            order_line.write({
                                'order_line_id': item.get('id')
                            })
                            break

        pass


    def prepare_fulfillments_data(self, fulfillments, order):
        fulfillments_data = self.env["everstox.shop.order.fulfillment"]
        for fulfillment in fulfillments:

            shipment_data = False
            if len(fulfillment.get("shipments")) >= 1:
                shipment_data = self.get_shipment_data(fulfillment)

            fulfillments_data += self.env["everstox.shop.order.fulfillment"].create({
                    "fulfillment_cancellations": fulfillment.get("cancellations"),
                    "fulfillment_errors": fulfillment.get("errors"),
                    "fulfillment_hours_late": fulfillment.get("hours_late"),
                    "fulfillment_id": fulfillment.get("id"),
                    "fulfillment_state": fulfillment.get("state"),
                    "fulfillment_warehouse_id": fulfillment.get("warehouse").get("id"),
                    "fulfillment_warehouse_name": fulfillment.get("warehouse").get("name"),
                    
                    "fulfillment_item_id": fulfillment.get("fulfillment_items")[0].get("id"),
                    "fulfillment_order_item_id": fulfillment.get("fulfillment_items")[0].get("order_item_id"),
                    "fulfillment_product_name": fulfillment.get("fulfillment_items")[0].get("product").get("name"),
                    "fulfillment_product_id": fulfillment.get("fulfillment_items")[0].get("product").get("id"),
                    "fulfillment_product_sku": fulfillment.get("fulfillment_items")[0].get("product").get("sku"),
                    "fulfillment_state": fulfillment.get("fulfillment_items")[0].get("state"),
                    "fulfillment_quantity": fulfillment.get("fulfillment_items")[0].get("quantity"),
                    "shipment_ids": shipment_data,
                }
            )
        
        return fulfillments_data
    

    def get_shipment_data(self, fulfillment):
        shipment_data = self.env["everstox.order.shipment"]
        for shipment in fulfillment.get("shipments"):
            shipment_items = self.prepare_shipment_data(shipment)
            processing_shift = None
            IST = pytz.timezone('Asia/Kolkata')
            time_now = datetime.datetime.strftime(datetime.datetime.now(IST), "%Y-%m-%d %H:%M:%S")
            if int(time_now.split(' ')[1][:2]) <= 19:
                processing_shift = 'first'
            else:
                processing_shift = 'second'
            shipment_id= self.env["everstox.order.shipment"].create({
                "carrier_id": shipment.get("carrier").get("id"),
                "carrier_name": shipment.get("carrier").get("name"),
                "forwarded_to_shop": shipment.get("forwarded_to_shop"),
                "shipment_id": shipment.get("id"),
                "shipment_date": shipment.get("shipment_date"),
                "tracking_codes": shipment.get("tracking_codes"),
                "tracking_urls": shipment.get("tracking_urls"),
                "shipment_items": shipment_items,
                "everstox_shop_id": self.id,
                "processing_time": processing_shift,
            })
            shipment_data += shipment_id

        return shipment_data


    def prepare_shipment_data(self, shipment):
        shipment_items_data = []
        for shipment_item in shipment.get("shipment_items"):
            shipped_batches = self.env["everstox.order.shipped.batches"]
            if shipment_item.get("shipped_batches"):
                shipped_batches = self.get_shipment_batches_data(shipment_item)
            shipment_items_data.append((0,0,{
                "fulfillment_item_id": shipment_item.get("fulfillment_item_id"),
                "shipment_item_id": shipment_item.get("shipment_item_id"),
                "quantity": shipment_item.get("quantity"),
                "shipment_batch_ids": shipped_batches,
            }))
        return shipment_items_data


    def get_shipment_batches_data(self, shipment_item):
        shipped_batch_data = []
        for batch in shipment_item.get("shipped_batches"):
            shipped_batch_data.append((0,0,{
                "batch" : batch.get("batch"),
                "expiration_date": batch.get("expiration_date"),
                "batch_id": batch.get("id"),
                "quantity": batch.get("quantity"),
                "sku": batch.get("sku"),
            }))
        return shipped_batch_data
            

    def prepare_order_item_data(self, order_line_items):
        order_lines = []
        for order_line in order_line_items:

            # Setting Carrier
            carrier = False
            if order_line.get("shipment_options")[0].get("id"):
                carrier = self.env["shipment.options"].search([("carrier_id", "=", order_line.get("shipment_options")[0].get("id"))])

            order_lines.append(
                (0,0, {
                    
                    "order_line_custom_attributes" : order_line.get("custom_attributes"),
                    "order_line_errors" : order_line.get("errors"),
                    "order_line_id" : order_line.get("id"),
                    "order_line_product_name" : order_line.get("product").get("name"),
                    "order_line_product_sku" : order_line.get("product").get("sku"),
                    "order_line_quantity" : order_line.get("quantity"),
                    "order_line_requested_batch" : order_line.get("requested_batch"),
                    "order_line_requested_batch_expiration_date" : order_line.get("requested_batch_expiration_date"),
                    "order_line_state" : order_line.get("state"),
                    "order_line_shipment_options_id" : carrier.carrier_id if carrier else None,
                    "order_line_shipment_options_name" : carrier.name if carrier else None,
                    "order_line_currency" : order_line.get("price_set")[0].get("currency"),
                    "order_line_discount" : order_line.get("price_set")[0].get("discount"),
                    "order_line_discount_gross" : order_line.get("price_set")[0].get("discount_gross"),
                    "order_line_discount_net" : order_line.get("price_set")[0].get("discount_net"),
                    "order_line_price" : order_line.get("price_set")[0].get("price"),
                    "order_line_price_gross" : order_line.get("price_set")[0].get("price_gross"),
                    "order_line_price_net_after_discount" : order_line.get("price_set")[0].get("price_net_after_discount"),
                    "order_line_price_net_before_discount" : order_line.get("price_set")[0].get("price_net_before_discount"),
                    "order_line_price_set_quantity" : order_line.get("price_set")[0].get("quantity"),
                    "order_line_tax" : order_line.get("price_set")[0].get("tax"),
                    "order_line_tax_amount" : order_line.get("price_set")[0].get("tax_amount"),
                    "order_line_tax_rate" : order_line.get("price_set")[0].get("tax_rate"),
                })
            )
        return order_lines


    def prepare_return_data(self, returns):
        return_ids = return_obj = self.env["everstox.order.return"]
        for return_id in returns:

            return_items = self.get_return_item_data(return_id.get("return_items"))

            return_ids += return_obj.create({
                "return_id": return_id.get("id"),
                "order_number": return_id.get("order_number"),
                "return_reference": return_id.get("return_reference"),
                "state": return_id.get("state"),
                "return_date": return_id.get("return_date"),
                "updated_date": return_id.get("updated_date"),
                "return_warehouse_id": return_id.get("warehouse").get("id"),
                "return_warehouse_name": return_id.get("warehouse").get("name"),

                "return_item_ids": return_items,
                "everstox_shop_id": self.id,
            })
        return return_ids


    def get_return_item_data(self, return_items):
        item_ids = item_obj = self.env["everstox.order.return.item"]
        for item in return_items:
            item_ids += item_obj.create(
                {
                    "customer_service_state": item.get("customer_service_state"),
                    "return_item_id": item.get("return_item_id"),
                    "return_product_id": item.get("product").get("id"),
                    "return_product_name": item.get("product").get("name"),
                    "return_product_sku": item.get("product").get("sku"),
                    "quantity": item.get("quantity"),
                    "return_reason": item.get("return_reason"),
                    "return_reason_code": item.get("return_reason_code"),
                    "stock_state": item.get("stock_state"),
                }
            ) 
        return item_ids


    def map_odoo_products_to_everstox(self):
        self.ensure_one()
        to_map_products = []
        warehouse_id = self.env['marketplace.warehouse'].search([('warehouse_id', '=', self.warehouse_id.id)])
        last_product = self.env['warehouse.inventory'].search([('warehouse_id', 'in', [warehouse_id.id])], order='create_date desc', limit=1)
        products = self.env['warehouse.inventory'].search([('warehouse_id', 'in', [warehouse_id.id]),('create_date', '=', last_product.create_date)])
        for product in products:
            odoo_product_id = self.env['product.product'].search([('default_code', '=', product.product_id)], limit=1)
            if odoo_product_id:
                to_map_products += [odoo_product_id.id]
                if odoo_product_id.everstox_mapped_state not in ["mapped", "unmapped"]:
                    odoo_product_id.everstox_mapped_state = "unmapped"
                if not odoo_product_id.everstox_shop_ids:
                    odoo_product_id.everstox_shop_ids = self.id

        return {
            'type': 'ir.actions.act_window',
            'name': _("%s's Mapped Products", self.name),
            'view_mode': 'list',
            'res_model': 'product.product',
            'search_view_id': [self.env.ref('odoo_everstox_integration.product_everstox_search_view').id],
            'view_id': self.env.ref('odoo_everstox_integration.everstox_product_view_tree').id,
            'context': {
                "search_default_everstox_mapped_state": 1,
            },
            'domain': [('id', 'in', to_map_products)],
        }


    def map_odoo_orders_to_everstox(self):
        self.ensure_one()
        warehouse_id = self.env['marketplace.warehouse'].search([('warehouse_id', '=', self.warehouse_id.id)])
        processed_order_ids = self.env['processed.order'].search([('warehouse', 'in', [warehouse_id.warehouse_code])])
        for order_id in processed_order_ids:
            if order_id.everstox_mapped_state not in ["mapped", "unmapped"]:
                order_id.everstox_mapped_state = "unmapped"
            if not order_id.everstox_shop_ids:
                order_id.everstox_shop_ids = self.id

        return {
            'type': 'ir.actions.act_window',
            'name': _("%s's Mapped Orders", self.name),
            'view_mode': 'list,form',
            'res_model': 'processed.order',
            'search_view_id': [self.env.ref('odoo_everstox_integration.view_everstox_processed_order_filters').id],
            'context': {
                "search_default_everstox_mapped_state": 1, "search_default_date": 1, "search_default_processing_time": 1,
            },
            'domain': [('id', 'in', processed_order_ids.ids)],
        }


    def get_odoo_date_format(self, everstox_date_format):
        if everstox_date_format:
            date_time_string = everstox_date_format.replace("T", " ")[0:everstox_date_format.find(":")+6] if everstox_date_format else False
        else:
            date_time_string = False
        return date_time_string


    def process_received_transfers(self, data):
        transfer_obj = self.env["everstox.transfers"]
        try:
            for transfer in data.get("items"):
                existing_transfer_id = transfer_obj.search([('transfer_id','=', transfer.get("id"))])
                if not existing_transfer_id:

                    # Create Transfer 
                    transfer_items = transfer_shipments = []
                    if transfer.get("transfer_items"):
                        transfer_items = self.process_transfer_item(transfer.get("transfer_items"))
                    if transfer.get("transfer_shipments"):
                        transfer_shipments = self.process_transfer_shipments(transfer.get("transfer_shipments"))
                    transfer_id = transfer_obj.create({
                        "eta": self.get_odoo_date_format(transfer.get("ETA")),
                        "custom_attributes": transfer.get("custom_attributes"),
                        "source": transfer.get("source"),
                        "transfer_number": transfer.get("transfer_number"),
                        "transfer_packing_type": transfer.get("transfer_packing_type"),
                        "destination": transfer.get("destination"),
                        "transfer_id": transfer.get("id"),
                        "shop_id": transfer.get("shop_id"),
                        "creation_date": self.get_odoo_date_format(transfer.get("creation_date")),
                        "updated_date": self.get_odoo_date_format(transfer.get("updated_date")),
                        "transfer_item_ids": transfer_items,
                        "transfer_shipment_ids": transfer_shipments,
                        "everstox_shop_id": self.id,
                    })
                    self.create_transfer_count += 1
                    _logger.info(".......... Existing Created %r ............", transfer_id)

                else:
                    
                    # Update Transfer 
                    existing_transfer_id.transfer_id = transfer.get("id")
                    existing_transfer_id.state = transfer.get("state")
                    existing_transfer_id.shop_id = transfer.get("shop_id")
                    existing_transfer_id.updated_date = self.get_odoo_date_format(transfer.get("updated_date"))
                    existing_transfer_id.creation_date = self.get_odoo_date_format(transfer.get("creation_date"))

                    # Update Transfer Items 
                    for item in transfer.get("transfer_items"):
                        transfer_item_id = existing_transfer_id.transfer_item_ids.search([('sku', '=', item.get("sku")), ('transfer_id', '=', existing_transfer_id.id)])
                        if len(transfer_item_id) == 1:
                            transfer_item_id.state = item.get("state")
                            transfer_item_id.quantity_received = item.get("quantity_received")
                            transfer_item_id.quantity_stocked = item.get("quantity_stocked")
                            transfer_item_id.product_id = item.get("id")

                    self.update_transfer_count += 1
                    _logger.info(".......... Existing Transfer Updated  %r............", existing_transfer_id)

        except:
            transfer = data
            existing_transfer_id = transfer_obj.search([('transfer_id','=', transfer.get("id"))])
            # Update Transfer 
            existing_transfer_id.transfer_id = transfer.get("id")
            existing_transfer_id.state = transfer.get("state")
            existing_transfer_id.shop_id = transfer.get("shop_id")
            existing_transfer_id.updated_date = self.get_odoo_date_format(transfer.get("updated_date"))
            existing_transfer_id.creation_date = self.get_odoo_date_format(transfer.get("creation_date"))

            # Update Transfer Items 
            for item in transfer.get("transfer_items"):
                transfer_item_id = existing_transfer_id.transfer_item_ids.search([('sku', '=', item.get("sku")), ('transfer_id', '=', existing_transfer_id.id)])
                if len(transfer_item_id) == 1:
                    transfer_item_id.state = item.get("state")
                    transfer_item_id.quantity_received = item.get("quantity_received")
                    transfer_item_id.quantity_stocked = item.get("quantity_stocked")
                    transfer_item_id.product_id = item.get("id")

            if transfer.get("transfer_shipments"):
                shipment_ids = self.process_transfer_shipments(transfer.get('transfer_shipments'))
                existing_transfer_id.transfer_shipment_ids = shipment_ids
            self.update_transfer_count += 1
            _logger.info(".......... Existing Transfer Updated  %r............", existing_transfer_id)
    

    def process_transfer_item(self, transfers):
        transfer_ids = transfer_item_obj = self.env["everstox.transfer.item"]
        for transfer in transfers:
            transfer_ids += transfer_item_obj.create({
                "custom_attributes": transfer.get("custom_attributes"),
                "product_id": transfer.get("product_id"),
                "quantity_announced": transfer.get("quantity_announced"),
                "sku": transfer.get("sku"),
                "everstox_shop_id": self.id,
            })
        return transfer_ids


    def process_transfer_shipments(self, shipments):
        shipment_ids = shipment_obj = self.env["everstox.transfer.shipment"]
        for shipment in shipments:
            existing_shipment = shipment_obj.search([("transfer_shipment_id", "=", shipment.get("id"))])
            transfer_shipment_items = self.env["everstox.transfer.shipment.item"]
            if not existing_shipment:
                if shipment.get("transfer_shipment_items"):
                    transfer_shipment_items = self.process_transfer_shipment_items(shipment.get("transfer_shipment_items"))

                shipment_ids += shipment_obj.create({
                    "forwarded_to_shop": shipment.get("forwarded_to_shop"),
                    "transfer_shipment_id": shipment.get("id"),
                    "shipment_received_date": self.get_odoo_date_format(shipment.get("shipment_received_date")),
                    "transfer_shipment_item_ids": transfer_shipment_items,
                    "everstox_shop_id": self.id,
                })
                _logger.info("~...............%r.............", shipment_ids)

            else:
                existing_shipment.forwarded_to_shop = shipment.get("forwarded_to_shop")
                if shipment.get("transfer_shipment_items"):
                    transfer_shipment_items = self.process_transfer_shipment_items(shipment.get("transfer_shipment_items"))
                    existing_shipment.transfer_shipment_item_ids = transfer_shipment_items
                _logger.info("~...............%r.............", existing_shipment)
        return shipment_ids


    def process_transfer_shipment_items(self, shipment_items):
        shipment_item_ids = shipment_item_obj = self.env["everstox.transfer.shipment.item"]
        for shipment_item in shipment_items:

            existing_shipment_item = shipment_item_obj.search([("transfer_shipment_item_id", "=", shipment_item.get("id"))])
            if not existing_shipment_item:

                transfer_shipment_batches = self.env["everstox.transfer.shipment.batches"]

                if shipment_item.get("shipped_batches"):
                    transfer_shipment_batches = self.process_transfer_shipment_batches(shipment_item.get("shipped_batches"))

                shipment_item_ids = shipment_item_obj.create({
                    "transfer_shipment_item_id": shipment_item.get("id"),
                    "product_id": shipment_item.get("product").get("id"),
                    "product_name": shipment_item.get("product").get("name"),
                    "product_sku": shipment_item.get("product").get("sku"),
                    "quantity_received": shipment_item.get("quantity_received"),
                    "quantity_stocked": shipment_item.get("quantity_stocked"),
                    "transfer_shipment_batch_ids": transfer_shipment_batches,
                    "transfer_item_id": shipment_item.get("transfer_item_id"),
                    "everstox_shop_id": self.id,
                })
            else:
                existing_shipment_item.quantity_received = shipment_item.get("quantity_received")
                existing_shipment_item.quantity_stocked = shipment_item.get("quantity_stocked")
                if shipment_item.get("shipped_batches"):
                    transfer_shipment_batches = self.process_transfer_shipment_batches(shipment_item.get("shipped_batches"))
                    existing_shipment_item.transfer_shipment_batch_ids = transfer_shipment_batches
                _logger.info("~~~~~~shipment_item_ids ....... %r ...", existing_shipment_item)
                
        _logger.info("~~~~~~shipment_item_ids ....... %r ...", shipment_item_ids)
        return shipment_item_ids


    def process_transfer_shipment_batches(self, batches):
        shipment_batch_ids = shipment_batch_obj = self.env["everstox.transfer.shipment.batches"]
        for batch in batches:
            shipment_batch_ids = shipment_batch_obj.create({
                "batch": batch.get("batch"),
                "expiration_date": self.get_odoo_date_format(batch.get("expiration_date")),
                "batch_id": batch.get("id"),
                "quantity_received": batch.get("quantity_received"),
                "quantity_stocked": batch.get("quantity_stocked"),
                "everstox_shop_id": self.id,
            })

        _logger.info("~~~~~~shipment_batch_ids ....... %r ...", shipment_batch_ids)
        return shipment_batch_ids


    #######
    # CRONS
    ####### 

    # Get Stock Updates 
    def get_everstox_stock_updates_cron(self):
        shops = self.search([])
        for shop in shops:
            try:
                _logger.info("............. Stock Update Cron For Shop - %r ...........", shop.name)
                shop.get_warehouse_stock_updates()
                shop.last_stock_update_time = datetime.datetime.now()
            except Exception as e:
                _logger.info("Error while getting stock updates. !!!!!!!")

    # Get Order Updates 
    def get_everstox_order_updates_cron(self):
        pass
