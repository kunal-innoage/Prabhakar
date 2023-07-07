from odoo import api, fields, models,_
import requests
from asyncio.log import logger
import json

class BladeShop(models.Model):
    _name = 'blade.shop'
    _description = 'Blade Shop'

    name = fields.Char(string='Name',required=True)
    # shop_url = fields.Char("Shop URL",required=True)
    warehouse_id = fields.Many2one("stock.warehouse", "Warehouse")
    user_name = fields.Char("User Name")
    user_pwd = fields.Char("Password")
    sandbox_url = fields.Char(string='Sandbox URL')
    production_url = fields.Char("Production URL")
    is_prod = fields.Boolean("Production Envoirment?")
    auth_token = fields.Char("Token")
    token_expiry = fields.Char("Token Expiry")
    channel_added = fields.Boolean(string='Channel Added')
    channel_id = fields.Char(string='Channel ID')
    org_id = fields.Char(string='Organization ID')
    tax_id = fields.Char("Tax ID")
    tax_name = fields.Char(string='Tax')
    tax_code = fields.Char(string='Tax Code')
    tax_rate = fields.Char(string='Rate')
    org_name = fields.Char("organization name")
    


    def map_odoo_orders_to_blade(self):
        self.ensure_one()
        warehouse_id = self.env['marketplace.warehouse'].search([('warehouse_id', '=', self.warehouse_id.id)])
        processed_order_ids = self.env['processed.order'].search([('warehouse', 'in', [warehouse_id.warehouse_code])])
        for order_id in processed_order_ids:
            if order_id.blade_mapped_state not in ["mapped", "unmapped"]:
                order_id.blade_mapped_state = "unmapped"
            if not order_id.blade_shop_id:
                order_id.blade_shop_id = self.id

        return {
            'type': 'ir.actions.act_window',
            'name': _("%s's Mapped Orders", self.name),
            'view_mode': 'list,form',
            'res_model': 'processed.order',
            'search_view_id': [self.env.ref('odoo_blade_integration.view_blade_processed_order_filters').id],
            'context': {
                "search_default_blade_mapped_state": 1, "search_default_date": 1, 
            },
            'domain': [('warehouse','=', 'BOH')]
        }
    
    def view_mapped_blade_orders(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _("%s's Mapped Orders", self.name),
            'view_mode': 'list,form',
            'res_model': 'blade.shop.order',
            'context': {
                
                'search_default_today':1,'search_default_blade_mapped_state': 1,'search_default_label_sent': 1, 'search_default_label_status': 1
            },
        }
        
    def view_products(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _("%s's Mapped Products", self.name),
            'view_mode': 'list,form',
            'res_model': 'blade.product',
        }
    

    def get_warehouse_products(self,pageNo=1):
        page = pageNo
        url = self.production_url if self.is_prod else self.sandbox_url
        url += '/products/variations?page=' + str(page)
        
        toekn = self.get_token(self)

        payload={}
        headers = {
            'Access-Token': self.auth_token
        }
        response = False
        try:
            response = requests.request("GET", url, headers=headers, data=payload)
        except Exception as err:
            logger.info(err)
        if response:
            response = response.json()
            if response.get("data"):
                data = response.get("data")
                if len(data) > 0:
                    self.map_products(data)
                    self.get_warehouse_products(page+1)
                else:
                    logger.info("No more products found to get from api")
        else:
            logger.info("Error in API")

    
    def map_products(self, products):
        for product in products:
            product1 = product.get('product')
            product_channel = product1.get('channel')
            created_product= self.env['blade.product'].create({
                'name': product.get('sku') if product.get('sku') else False,
                'sku': product.get('sku') if product.get('sku') else False,
                'product_channel_id': product_channel.get('id') if product_channel.get('id') else False,
                'variation_id': product1.get('descriptions').get('product_variation_id') if product1.get('descriptions') else False
            })
            if created_product:
                logger.info("Product Created with %s", created_product.sku)



    
    def get_token(self,shop):
        url = shop.production_url if shop.is_prod else shop.sandbox_url
        if url:
            url += '/auth/login'
            payload = json.dumps({
                "username": shop.user_name,
                "password": shop.user_pwd
            })
            headers = {
                'Content-Type': 'application/json'
            }
            response = False
            try:
                response = requests.request("POST", url, headers=headers, data=payload)
            
            
            except Exception as err:
                print(err)
            if response:
                response = response.json()
                if response.get('data'):
                    data = response.get('data')
                    shop.write({'auth_token': data.get('session_token'), 'token_expiry': data.get('expiry')})
                    return shop.auth_token
            else:
                logger.info("Error in api")
        else:
            logger.info("Url not found in settings")
        

    def get_channel_data(self):
        url = self.production_url if self.is_prod else self.sandbox_url
        url += '/orders/channels?expand=*'
        toekn = self.get_token(self)
        payload={}
        headers = {
            'Access-Token': self.auth_token
        }
        response = False
        try:
            response = requests.request("GET", url, headers=headers, data=payload).json()
        except Exception as err:
            logger.info(err)
        if response:
            data = response.get('data')
            if len(data) > 0:
                self.map_channels(data)
                
            else:
                logger.info("No data found")
        else:
            logger.info("Error In API call")
        

    def map_channels(self,data):
        for channel in data:
            if len(channel):
                if channel.get('id'):
                    channel_search = self.search([('channel_id','=', channel.get('id'))],limit=1)
                    if not channel_search:
                        self.write({
                            'channel_id': channel.get('id'),
                            'org_id': channel.get('organisation_id') if channel.get('organisation_id') else False,
                            'org_name': channel.get('name') if channel.get('name') else False,
                        })
                        logger.info("channel added with ID %s", channel.get('id'))
                        if channel.get('tax'):
                            channel_tax = channel.get('tax')
                            tax_id = tax_name = channel_code = rate = False
                            if channel_tax.get('id'):
                                tax_id = channel_tax.get('id')
                            if channel_tax.get('name'):
                                tax_name = channel_tax.get('name')
                            if channel_tax.get('rate'):
                                rate = channel_tax.get('rate')
                            self.write({'tax_id':tax_id, 'tax_name': tax_name, 'tax_rate': rate, 'channel_added': True  })
                    else:
                        logger.info("Channel Already added")

    def view_channels(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _("%s's Channels", self.name),
            'view_mode': 'list,form',
            'res_model': 'blade.channel',
        }


    
