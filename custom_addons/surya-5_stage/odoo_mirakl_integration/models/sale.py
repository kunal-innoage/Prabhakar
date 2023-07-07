# -*- coding: utf-8 -*-
from operator import add
import json
from odoo import fields, models, _, api
from odoo.exceptions import ValidationError, UserError, MissingError
import datetime
from datetime import timedelta

import requests
from odoo.tools import float_compare

import logging
_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit="sale.order"

    @api.depends('state', 'order_line.invoice_status')
    def _get_invoice_status(self):
        for so in self:
            if so.invoice_status == "invoiced":
                so.mirakl_order_state = "closed"


    acceptance_descission_date = fields.Datetime("Acceptance Descission Date")
    can_cancel = fields.Boolean("Can Cancel")
    can_shop_ship = fields.Boolean("Can Shop Ship")
    processed = fields.Boolean("Processed")
    channel = fields.Char("Channel")
    commercial_id = fields.Char("Commercial Id")
    mirakl_created_date = fields.Datetime("Mirakl Created Date")
    currency_iso_code = fields.Char("Currency ISO Code")

    mirakl_carrier_name = fields.Char("Mirakl Carrier Name")
    customer_directly_pays_seller = fields.Boolean("Customer Directly Pays Seller")
    customer_debited_date = fields.Datetime("Customer Debited Date")
    customer_notification_email = fields.Char("Customer Notification Email")
    mirakl_earliest_delivery_date = fields.Char("Mirakl Earliest Delivery Date")
    mirakl_latest_delivery_date = fields.Char("Mirakl Latest Delivery Date")

    has_customer_message = fields.Boolean("Has Customer Message")
    has_incident = fields.Boolean("Has Incident")
    has_invoice = fields.Boolean("Had invoice")
    mirakl_last_updated_date = fields.Datetime("Mirakl Last Updated Date")
    leadtime_to_ship = fields.Char("Lead time to ship")
    mirakl_comment = fields.Char("Comment")
    mirakl_order_id = fields.Char("Mirakl Order Id")

    mirakl_order_state = fields.Selection([('staging','STAGING'), ('waiting_acceptance','WAITING ACCEPTANCE'), ('waiting_debit','WAITING DEBIT'), ('waiting_debit_payment','WAITING DEBIT PAYMENT'), ('shipping','SHIPPING'), ('shipped','SHIPPED'), ('to_collect','TO_COLLECT'), ('received','RECEIVED'),  ('closed','CLOSED'), ('refused','REFUSED'), ('canceled','CANCELED')],"Order State")
    order_state_reason_code = fields.Char("Order State Reason Code")
    order_state_reason_label = fields.Char("Order State Reason Label")
    order_tax_mode = fields.Selection([('tax_included','TAX_INCLUDED'), ('tax_excluded', 'TAX_EXCLUDED')], "Order Tax Mode")
    paymentType = fields.Char("Payment Type")
    payment_type = fields.Char("Mirakl Payment Type")
    payment_workflows = fields.Selection([('pay_on_acceptance','PAY_ON_ACCEPTANCE'),('pay_on_delivery', 'PAY_ON_DELIVERY'),('pay_on_due_date', 'PAY_ON_DUE_DATE'), ('pay_on_shipment', 'PAY_ON_SHIPMENT'), ('no_customer_payment_confirmation', 'NO_CUSTOMER_PAYMENT_CONFIRMATION')],"Payment Workflow")
    mirakl_price = fields.Float("Mirakl Order Price")

    quote_id = fields.Char("Quote Id")

    shipping_carrier_code = fields.Char("Shipping Carrier Code")
    shipping_company = fields.Char("Shipping Company")
    shipping_deadline = fields.Datetime("Shipping Deadline")
    shipping_price = fields.Float("Mirakl Shipping Price")
    shipping_pudo_id = fields.Char("Shipping Pudo Id")
    shipping_tracking = fields.Char("Shipping Tracking")
    shipping_tracking_url = fields.Char("Shipping Tracking URL")
    shipping_type_code = fields.Char("Shipping Type Code")
    shipping_type_label = fields.Char("Shipping Type Label")
    total_commission = fields.Float('Total Commission')
    total_price = fields.Float("Total Price")
    transaction_date = fields.Datetime("Transaction Date")
    transaction_number = fields.Char("Transaction Number")
    mirakl_shop_id = fields.Many2one("shop.integrator", "Shop")

    market_place_shop = fields.Char("Shop Name")

    #All delivered

    all_delivered = fields.Boolean(string='All Delivered')
    

    # Switch Warehouse
    #~~~~~~~~~~~~~~~~~

    def switch_warehouse(self):
        res = self.env['order.changes'].create({
            "sale_order_id": self.id,
            "current_warehouse_id": self.warehouse_id.id,
        })
        return {'name': 'Switch Warehouse', 'res_id': res.id, 'res_model': 'order.changes', 'type': 'ir.actions.act_window', 'view_mode': 'form', 'view_id': self.env.ref('odoo_mirakl_integration.warehouse_switch_form').id, 'target': 'new', 'nodestroy': True}

    def multi_order_switch_warehouse(self):
        res = self.env['order.changes'].create({
            "current_warehouse_id": self[0].warehouse_id.id,
        })
        sale_ids = [order.id for order in self]
        return {'name': 'Switch Warehouse', 'res_id': res.id,'context': {'sale_order_ids': sale_ids}, 'res_model': 'order.changes', 'type': 'ir.actions.act_window', 'view_mode': 'form', 'view_id': self.env.ref('odoo_mirakl_integration.multi_order_warehouse_switch_form').id, 'target': 'new', 'nodestroy': True}




    # Data Prep Functions
    # ~~~~~~~~~~~~~~~~~~~

    def get_odoo_date_format(self, mirakl_date_format):
        if mirakl_date_format:
            date_time_string = mirakl_date_format.replace("T", " ")[0:mirakl_date_format.find(":")+6] if mirakl_date_format else False
        else:
            date_time_string = False
        return date_time_string

    def update_stock_changes_marketplace(self, except_shop, line):

        # Search Product for other marketplaces and send updates
        shops_to_update_on = self.env['mirakl.stock'].search([('odoo_product_id','in',[line.product_id.id])])

        # Send API calls on shops
        for shop in shops_to_update_on:
            if shop.quantity > 0 and shop.quantity >= line.product_uom_qty:
                shop.quantity -= line.product_uom_qty
                if shop.quantity < 0:
                    shop.quantity = 0
                shop.last_updated_date = datetime.datetime.now()
            # CAll
            if except_shop != shop.shop_id:
                self.send_api_calls(shop, line.product_uom_qty)

    def sale_order_instock(self, so):
        for line in so.order_line:
            stock_count = 0
            stocks = self.env['stock.quant'].search([('product_id','=',line.product_id.id),('location_id.warehouse_id', '=', so.warehouse_id)])
            for stock in stocks:
                if stock.location_id.warehouse_id == so.warehouse_id:
                    stock_count += stock.quantity
            if stock_count >= line.product_uom_qty and so.mirakl_shop_id:
                continue
            else:
                return False
        return True

    def update_stock_on_mirakl(self, so):
        for line in so.order_line:
            self.update_stock_changes_marketplace(so.mirakl_shop_id, line)

    def per_shop_order_update(self, shop_order_dict):

        # Change this to per shop product qty update in single cycle 
        for shop in shop_order_dict.keys():
            for order in shop_order_dict[shop]:
                self.update_stock_on_mirakl(order)

    def divide_orders_per_shop(self):
        shop_wise_orders = {}
        for so in self:
            if so.mirakl_order_id:
                if so.mirakl_shop_id not in shop_wise_orders.keys():
                    shop_wise_orders[so.mirakl_shop_id] = [so]
                else:
                    shop_wise_orders[so.mirakl_shop_id].append(so)
        return shop_wise_orders
    


    # Sale Order Funtions
    # ~~~~~~~~~~~~~~~~~~~

    def _create_customer(self, order):
        customer_data = order.get('customer')
        if customer_data:
            customer_env = self.env['res.partner']
            customer = customer_env.search([('mirakl_customer_id', '=', customer_data.get("customer_id"))], limit=1)
            if not customer:
                customer = customer_env.create({
                    'company_type': 'person',
                    'name': customer_data.get('firstname') + ' ' + customer_data.get('lastname'),
                    'phone': customer_data.get('billing_address').get("phone") if customer_data.get('billing_address') else False,
                    'email': order.get('customer_notification_email'),
                    'mirakl_customer_id': customer_data.get("customer_id"),
                    'mirakl_locale': customer_data.get("locale"),
                })
            return customer.id
        return False

    def _create_billing_customer(self, billing_address, customer_id):
        billing_customer = self.env['res.partner'].search([('type', '=', 'invoice'), ('parent_id', '=', customer_id)], limit=1)
        if not billing_customer:
            country = state = full_name = False
            if billing_address['country'] == "Espagne":
                country = self.env['res.country'].search([('name', '=', 'Spain')])
            else:
                country = self.env['res.country'].search([('name', '=', billing_address['country'])])
            if len(country) <= 0:
                country = self.env['res.country'].search([('code', '=', billing_address['country_iso_code'])])
                if country.name == "Australia":
                    country = self.env['res.country'].search([('name', '=', "Austria")])
            if billing_address['state'] != "None":
                state = self.env['res.country.state'].search([('name', '=', billing_address['state']), ('country_id', '=', country.id)])
            if billing_address.get('firstname'):
                full_name = billing_address.get('firstname')
                if billing_address.get('lastname'):
                    full_name += " "+ billing_address.get('lastname')
            else:
                if billing_address.get('lastname'):
                    full_name = billing_address.get('lastname')
            billing_customer = self.env['res.partner'].create({
                'company_type': 'person',
                'type': 'invoice',
                'name': full_name,
                'parent_id': customer_id,
                'street': billing_address['street_1'],
                'street2': billing_address['street_2'],
                'phone': billing_address.get("phone") if billing_address.get("phone") != "None" else False,
                'city': billing_address.get("city") if billing_address.get("city") != "None" else False,
                'state_id': state.id if state else False,
                'country_id': country.id if country else False,
                'country_code': country.code if country else False,
                'zip': billing_address.get("zip_code") if billing_address.get("zip_code") != "None" else False,
            })
        return billing_customer.id

    def _create_shipping_customer(self, shipping_address, customer_id):
        shipping_customer = self.env['res.partner'].search([('type', '=', 'delivery'), ('parent_id', '=', customer_id)], limit=1)
        if not shipping_customer:
            country = state = full_name = False
            if shipping_address['country'] == "Espagne":
                country = self.env['res.country'].search([('name', '=', 'Spain')])
            else:
                country = self.env['res.country'].search([('name', '=', shipping_address['country'])])
            if len(country) <= 0:
                country = self.env['res.country'].search([('code', '=', shipping_address['country_iso_code'])])
                if country.name == "Australia":
                    country = self.env['res.country'].search([('name', '=', "Austria")])
                                
            if shipping_address['state'] != "None":
                state = self.env['res.country.state'].search([('name', '=', shipping_address['state']), ('country_id', '=', country.id)])
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
                'street': shipping_address['street_1'],
                'street2': shipping_address['street_2'],
                'phone': shipping_address.get("phone"),
                'city': shipping_address['city'],
                'state_id': state.id if state else False,
                'country_id': country.id if country else False,
                'country_code': country.code if country else False,
                'zip': shipping_address['zip_code'],
            })
        return shipping_customer.id

    def add_dummy_address(self, customer_id, order):
        customer = self.env['res.partner'].search([('parent_id', '=', customer_id)], limit=1)
        locale = customer.mirakl_locale
        country_code = {'it_IT': 'ITA', 'fr_FR': 'FRA' , 'es_ES': 'ESP'}
        if locale in country_code.keys():
            customer.country_id = self.env['res.country'].search([('code', '=', country_code.get(locale))])
        billing_customer = self.env['res.partner'].search([('type', '=', 'invoice'), ('parent_id', '=', customer_id)], limit=1)
        if len(billing_customer) == 0:
            billing_customer = self.env['res.partner'].create({
                'company_type': 'person',
                'type': 'invoice',
                'name': customer.name,
                'parent_id': customer_id,
                'country_id': customer.country_id.id if len(customer.country_id) > 0 else False,
                'country_code': customer.country_id.code if len(customer.country_id) > 0 else False,
            })
        shipping_customer = self.env['res.partner'].search([('type', '=', 'delivery'), ('parent_id', '=', customer_id)], limit=1)
        if len(shipping_customer) == 0:
            shipping_customer = self.env['res.partner'].create({
                'company_type': 'person',
                'type': 'delivery',
                'name': customer.name,
                'parent_id': customer_id,
                'country_id': customer.country_id.id if len(customer.country_id) > 0 else False,
                'country_code': customer.country_id.code if len(customer.country_id) > 0 else False,
            })
        return [billing_customer.id, shipping_customer.id]

    def _create_product(self, line):
        product_env = self.env['product.product']
        prod = product_env.search(['|', ('name', '=', line.get('title')), ('name', '=', line.get('offer_sku'))], limit=1)
        if len(prod) <= 0:
            prod = product_env.search([('barcode', '=', line.get('offer_sku').lstrip("0"))])
        return prod

    def _get_warehouse(self, shop_id):
        shop_obj = self.env['shop.integrator'].search([('id', 'in', [shop_id])])
        warehouse = shop_obj.warehouse_id
        if not warehouse:
            raise MissingError(_('Please assign a Warehouse to this shop first - (Shop: %s)', shop_obj.name))
        else:
            return warehouse.id

    def get_sale_order_lines(self, order_lines, shop_id, shipping_id):
        sale_order_lines = []
        added_line = False
        for line in order_lines:
            try:
                product_id = self._create_product(line)
                if len(product_id) > 0:
                    added_line = (0, 0, {
                        'product_id': product_id.id,
                        'can_refund': line.get('can_refund') if line.get('can_refund') else False,
                        'commission_fee': line.get('commission_fee') if line.get('commission_fee') else False,
                        'commission_rate_vat': line.get('commission_rate_vat') if line.get('commission_rate_vat') else False,
                        'commission_vat': line.get('commission_vat') if line.get('commission_vat') else False,
                        'mirakl_created_date': self.get_odoo_date_format(line.get('created_date')) if self.get_odoo_date_format(line.get('created_date')) else False,
                        'debited_date':  self.get_odoo_date_format(line.get('debited_date')) if self.get_odoo_date_format(line.get('debited_date')) else False,
                        'description': line.get('description') if line.get('description') else False,
                        'mirakl_offer_id': line.get('offer_id') if line.get('offer_id') else False,
                        'offer_sku': line.get('offer_sku') if line.get('offer_sku') else False,
                        'offer_state_code': line.get('offer_state_code') if line.get('offer_state_code') else False,
                        'mirakl_order_line_id': line.get('order_line_id') if line.get('order_line_id') else False,
                        'order_line_index': line.get('order_line_index') if line.get('order_line_index') else False,
                        'order_line_states': line.get('order_line_state').lower() if line.get('order_line_state').lower() else False,
                        'order_line_state_reason_code': line.get('order_line_state_reason_code') if line.get('order_line_state_reason_code') else False,
                        'order_line_state_reason_label': line.get('order_line_state_reason_label') if line.get('order_line_state_reason_label') else False,
                        'order_line_index': line.get('order_line_index') if line.get('order_line_index') else False,
                        'mirakl_line_price': line.get('price') if line.get('price') else False,
                        'price_additional_info': line.get('price_additional_info') if line.get('price_additional_info') else False,
                        'mirakl_price_unit': line.get('price_unit') if line.get('price_unit') else False,
                        'price_unit': line.get('price_unit') if line.get('price_unit') else False,
                        'product_uom_qty': line.get('quantity') if line.get('quantity') else False,
                        'shipped_date': self.get_odoo_date_format(line.get('shipped_date')) if self.get_odoo_date_format(line.get('shipped_date')) else False,
                        'shipping_price': line.get('shipping_price') if line.get('shipping_price') else False,
                        'shipping_price_additional_unit': line.get('shipping_price_additional_unit') if line.get('shipping_price_additional_unit') else False,
                        'shipping_price_unit': line.get('shipping_price_unit') if line.get('shipping_price_unit') else False,
                        'total_commission': line.get('total_commission') if line.get('total_commission') else False,
                        'mirakl_total_price': line.get('total_price') if line.get('total_price') else False,
                    })
            except Exception as err:
                _logger.info("Sale Order Line Creation Error~~~~~~~~~~~%r~~~~~~~~~~",err)
            sale_order_lines.append(added_line)
        return sale_order_lines

    def sale_order_workflow(self, order):
        if order.mirakl_order_state in ['canceled']:
            order.action_cancel()
        if order.mirakl_order_state in ['waiting_debit_payment', 'waiting_debit', "shipping", "shipped" ,"closed", "received"]:
            if order.order_state_reason_code == "REFUNDED":
                order.action_cancel()
            else:
                order.action_confirm()
        pass

    def check_for_delivery_validation(self, sale_order):
        if sale_order.mirakl_order_state in ["shipped" ,"closed", "received"]:
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
                        delivery.shipping_tracking = sale_order.shipping_tracking if sale_order.shipping_tracking else False
                        delivery.shipping_tracking_url = sale_order.shipping_tracking_url if sale_order.shipping_tracking_url else False
                        delivery.mirakl_carrier_name = sale_order.shipping_carrier_code
                        delivery.with_context(skip_immediate=True, skip_sms=True).button_validate()
                        sale_order.invoice_status = 'to invoice'
            
    def update_sale_order_filter(self, shop_obj, sale_order):
        if sale_order.mirakl_created_date:
            shop_obj.date_created_start = sale_order.mirakl_created_date
        else:
            _logger.info("~~~~~~~~~~last date not found~~~~~~~~~~~")
            pass

    def check_for_customer_updates(self, order, sale_order):
        # Customer Data
        customer_data = order.get('customer')
        billing_data = customer_data.get('billing_address') or False
        shipping_data = customer_data.get('shipping_address') or False
        
        billing_address = sale_order.partner_invoice_id
        shipping_address = sale_order.partner_shipping_id
        customer_address=  sale_order.partner_id
        if customer_address:
            if customer_address.country_id.name == "Australia":
                customer_address.country_id = self.env['res.country'].search([('name', '=', "Austria")])
        
        if billing_data and shipping_data:
            
            if order.get("order_state").lower() != 'waiting_acceptance':
                # Update Billing Address 
                if len(billing_address) > 0:
                    biller_name = billing_data.get('firstname') + ' ' + billing_data.get('lastname') if billing_data.get('firstname') else billing_data.get('lastname') if billing_data.get('lastname') else sale_order.partner_id.name
                    if billing_address.name != biller_name:
                        billing_address.name = biller_name
                    
                    if billing_address.street != billing_data.get('street_1'):
                        billing_address.street = billing_data.get('street_1')
                    if billing_address.street2 != billing_data.get('street_2'):
                        billing_address.street2 = billing_data.get('street_2')
                    if billing_address.zip != billing_data.get('zip_code'):
                        billing_address.zip = billing_data.get('zip_code')
                    if len(billing_address.country_id) > 0:
                        if billing_address.country_id.code != billing_data.get('country_iso_code'):
                            billing_address.country_id = self.env['res.country'].search([('code', '=', billing_data.get('country_iso_code'))]) or self.env['res.country'].search([('name', '=', billing_data['country'])])
                            if billing_address.country_id.name == "Australia":
                                billing_address.country_id = self.env['res.country'].search([('name', '=', "Austria")])
                            elif billing_address.country_id.name == "espagne":
                                billing_address.country_id = self.env['res.country'].search([('name', '=', "Spain")])
                            elif billing_address.country_id.name == "italie":
                                billing_address.country_id = self.env['res.country'].search([('name', '=', "Italy")]) 
                    else:
                        billing_address.country_id = self.env['res.country'].search([('code', '=', billing_data.get('country_iso_code'))]) or self.env['res.country'].search([('name', '=', billing_data['country'])]) or False
                    if billing_data['state'] != None:
                        if billing_address.state_id.name != billing_data.get('state').lower():
                            if len(billing_address.country_id)> 0:
                                billing_address.state_id = self.env['res.country.state'].search([('name', '=', billing_data['state']), ('country_id', '=', billing_address.country_id.id)])
                            else:
                                billing_address.state_id = self.env['res.country.state'].search([('name', '=', billing_data['state'])], limit=1)
                    if billing_address.phone != shipping_data.get('phone'):
                        if shipping_data.get("phone"):
                            billing_address.phone = shipping_data.get("phone")
                            sale_order.partner_id.phone = shipping_data.get("phone") or False
                        else:
                            billing_address.phone = shipping_data.get("phone_secondary") or False
                            sale_order.partner_id.phone = shipping_data.get("phone_secondary") or False
                    if billing_address.city != billing_data.get('city'):
                        billing_address.city = billing_data.get("city") if billing_data.get("city") != "None" else False

            # Update Shipping Address 
            if order.get("order_state").lower() != 'waiting_acceptance':
                if len(shipping_address) > 0:
                    full_name = shipping_data.get('firstname') + ' ' + shipping_data.get('lastname') if shipping_data.get('firstname') else shipping_data.get('lastname') if shipping_data.get('lastname') else sale_order.partner_id.name
                    if shipping_address.name != full_name:
                        shipping_address.name = full_name
                    if shipping_address.street != shipping_data.get('street_1'):
                        shipping_address.street = shipping_data.get('street_1')
                    if shipping_address.street2 != shipping_data.get('street_2'):
                        shipping_address.street2 = shipping_data.get('street_2')
                    if shipping_address.zip != shipping_data.get('zip_code'):
                        shipping_address.zip = shipping_data.get('zip_code')
                    if len(shipping_address.country_id) > 0:
                        if shipping_address.country_id.code != shipping_data.get('country_iso_code'):
                            shipping_address.country_id = self.env['res.country'].search([('code', '=', shipping_data.get('country_iso_code'))]) or self.env['res.country'].search([('name', '=', shipping_data['country'])])
                            if shipping_address.country_id.name == "Australia":
                                shipping_address.country_id = self.env['res.country'].search([('name', '=', "Austria")])
                            elif shipping_address.country_id.name == "espagne":
                                shipping_address.country_id = self.env['res.country'].search([('name', '=', "Spain")])
                            elif shipping_address.country_id.name == "italie":
                                shipping_address.country_id = self.env['res.country'].search([('name', '=', "Italy")])
                    else:
                        shipping_address.country_id = self.env['res.country'].search([('code', '=', shipping_data.get('country_iso_code'))]) or self.env['res.country'].search([('name', '=', shipping_data['country'])]) or False
                        if not shipping_address.country_id:
                            shipping_address.country_id = sale_order.partner_id.country_id
                    if shipping_data['state'] != None:
                        if shipping_address.state_id.name != shipping_data.get('state').lower():
                            if len(shipping_address.country_id)> 0:
                                shipping_address.state_id = self.env['res.country.state'].search([('name', '=', shipping_data['state']), ('country_id', '=', shipping_address.country_id.id)])
                            else:
                                shipping_address.state_id = self.env['res.country.state'].search([('name', '=', shipping_data['state'])], limit=1)
                    if shipping_address.phone != shipping_data.get('phone'):
                        if shipping_data.get("phone"):
                            shipping_address.phone = shipping_data.get("phone")
                        else:
                            shipping_address.phone = shipping_data.get("phone_secondary") or False
                    if shipping_address.city != shipping_data.get('city'):
                        shipping_address.city = shipping_data.get("city") if shipping_data.get("city") != "None" else False

            if len(sale_order.partner_id.country_id) == 0:
                if len(billing_address.country_id) > 0:
                    sale_order.partner_id.country_id = billing_address.country_id
                if len(shipping_address.country_id) > 0:
                    sale_order.partner_id.country_id = shipping_address.country_id
                if len(sale_order.partner_id.country_id) == 0:
                    try:
                        sale_order.partner_id.country_id = self.env['res.country'].search(['|',('name', '=',  order.get('channel').get('label').lower()), ('code', '=', order.get('channel').get('code'))])
                        if len(shipping_address.country_id) == 0:
                            shipping_address.country_id = sale_order.partner_id.country_id
                    except:
                        _logger.info("!!!!!!!!! Country not found, leaving empty  order id - %r ;;;;;;", sale_order.id)
                _logger.info("Country Updated__%r____for the mirakl order______%r__", sale_order.partner_id.country_id,order.get('order_id'))

    def check_for_order_line_updates(self, order_lines, sale_order):
        line_obj = self.env["sale.order.line"]
        for line in order_lines:
            try:
                product_id = self._create_product(line)
                if len(product_id) > 0:
                    skip=False
                    for ol in sale_order.order_line:
                        if product_id == ol.product_id:
                            skip = True
                    if not skip:
                        line_id = line_obj.create({
                            'product_id': product_id.id,
                            'can_refund': line.get('can_refund') if line.get('can_refund') else False,
                            'commission_fee': line.get('commission_fee') if line.get('commission_fee') else False,
                            'commission_rate_vat': line.get('commission_rate_vat') if line.get('commission_rate_vat') else False,
                            'commission_vat': line.get('commission_vat') if line.get('commission_vat') else False,
                            'mirakl_created_date': self.get_odoo_date_format(line.get('created_date')) if self.get_odoo_date_format(line.get('created_date')) else False,
                            'debited_date':  self.get_odoo_date_format(line.get('debited_date')) if self.get_odoo_date_format(line.get('debited_date')) else False,
                            'description': line.get('description') if line.get('description') else False,
                            'mirakl_offer_id': line.get('offer_id') if line.get('offer_id') else False,
                            'offer_sku': line.get('offer_sku') if line.get('offer_sku') else False,
                            'offer_state_code': line.get('offer_state_code') if line.get('offer_state_code') else False,
                            'mirakl_order_line_id': line.get('order_line_id') if line.get('order_line_id') else False,
                            'order_line_index': line.get('order_line_index') if line.get('order_line_index') else False,
                            'order_line_states': line.get('order_line_state').lower() if line.get('order_line_state').lower() else False,
                            'order_line_state_reason_code': line.get('order_line_state_reason_code') if line.get('order_line_state_reason_code') else False,
                            'order_line_state_reason_label': line.get('order_line_state_reason_label') if line.get('order_line_state_reason_label') else False,
                            'order_line_index': line.get('order_line_index') if line.get('order_line_index') else False,
                            'mirakl_line_price': line.get('price_unit') if line.get('price_unit') else False,
                            'price_unit': line.get('price_unit') if line.get('price_unit') else False,
                            'product_uom_qty': line.get('quantity') if line.get('quantity') else False,
                            'shipped_date': self.get_odoo_date_format(line.get('shipped_date')) if self.get_odoo_date_format(line.get('shipped_date')) else False,
                            'shipping_price': line.get('shipping_price') if line.get('shipping_price') else False,
                            'shipping_price_additional_unit': line.get('shipping_price_additional_unit') if line.get('shipping_price_additional_unit') else False,
                            'shipping_price_unit': line.get('shipping_price_unit') if line.get('shipping_price_unit') else False,
                            'total_commission': line.get('total_commission') if line.get('total_commission') else False,
                            'mirakl_total_price': line.get('total_price') if line.get('total_price') else False,
                            'order_id': sale_order.id,
                        })
                        _logger.info("...Sale Order Line Updated.......  %r .........", line_id)
            except Exception as err:
                _logger.info("Sale Order Line Updation Error~~~~~~~~~~~%r~~~~~~~~~~",err)

    # Get Shipment Details for Multi Delivery Orders 
    def get_shipment_details(self, sale_order):
        if sale_order.mirakl_shop_id and sale_order.mirakl_order_id:
            picking_info = sale_order.mirakl_shop_id.get_shipment_tracking_info(sale_order.mirakl_order_id)
            if len(sale_order.picking_ids) > 0:
                for picking in sale_order.picking_ids:
                    if picking_info:
                        for shipment in picking_info:
                            if len(picking.move_line_ids_without_package) == 1:
                                if shipment.get('shipment_lines')[0].get('offer_sku') == picking.move_line_ids_without_package.product_id.default_code:
                                    if picking.shipping_tracking_url != shipment.get('tracking').get('shipping_tracking_url'):
                                        picking.shipping_tracking = shipment.get('tracking').get('tracking_number')
                                        picking.shipping_tracking_url = shipment.get('tracking').get('tracking_url')
                                        picking.mirakl_carrier_code = shipment.get('tracking').get('carrier_code')
                                        picking.mirakl_carrier_name = shipment.get('tracking').get('carrier_name')
                                        picking.is_tracking_updated = True
                                        picking_info.remove(shipment)
                                        break

    def check_for_order_data_changes(self, order, sale_order):
        
        # State Change Check
        if sale_order.mirakl_order_state != order.get('order_state').lower():
            sale_order.mirakl_order_state = order.get('order_state').lower()
        if sale_order.order_state_reason_code != order.get('order_state_reason_code'):
            sale_order.order_state_reason_code = order.get('order_state_reason_code')

        
        # Date Updates
        if sale_order.customer_debited_date != self.get_odoo_date_format(order.get('customer_debited_date')):
            sale_order.customer_debited_date = self.get_odoo_date_format(order.get('customer_debited_date'))
        if sale_order.mirakl_latest_delivery_date != self.get_odoo_date_format(order.get('latest_delivery_date')):
            sale_order.mirakl_latest_delivery_date = self.get_odoo_date_format(order.get('latest_delivery_date'))
        if sale_order.mirakl_last_updated_date != self.get_odoo_date_format(order.get('last_updated_date')):
            sale_order.mirakl_last_updated_date = self.get_odoo_date_format(order.get('last_updated_date'))
        if sale_order.shipping_deadline != self.get_odoo_date_format(order.get('shipping_deadline')):
            sale_order.shipping_deadline = self.get_odoo_date_format(order.get('shipping_deadline'))
        if sale_order.transaction_date != self.get_odoo_date_format(order.get('transaction_date')):
            sale_order.transaction_date = self.get_odoo_date_format(order.get('transaction_date'))
            
        
        # Boolean Updates
        if sale_order.can_cancel != order.get('can_cancel'):
            sale_order.can_cancel = order.get('can_cancel')
        if sale_order.can_shop_ship != order.get('can_shop_ship'):
            sale_order.can_shop_ship = order.get('can_shop_ship')
        if sale_order.has_customer_message != order.get('has_customer_message'):
            sale_order.has_customer_message = order.get('has_customer_message')
        if sale_order.has_incident != order.get('has_incident'):
            sale_order.has_incident = order.get('has_incident')
        if sale_order.has_invoice != order.get('has_invoice'):
            sale_order.has_invoice = order.get('has_invoice')
        if sale_order.customer_directly_pays_seller != order.get('customer_directly_pays_seller'):
            sale_order.customer_directly_pays_seller = order.get('customer_directly_pays_seller')
        
        # Shipping Details Update 
        if order.get("order_state").lower() not in ['waiting_acceptance', 'waiting_debit']:
            if order.get("customer").get("shipping_address"):
                if sale_order.mirakl_comment != order.get("customer").get("shipping_address").get("additional_info"):
                    sale_order.mirakl_comment = order.get("customer").get("shipping_address").get("additional_info")
        if sale_order.shipping_carrier_code != order.get('shipping_carrier_code'):
            sale_order.shipping_carrier_code = order.get('shipping_carrier_code')
        if sale_order.shipping_company != order.get('shipping_company'):
            sale_order.shipping_company = order.get('shipping_company')
        if sale_order.shipping_price != order.get('shipping_price'):
            sale_order.shipping_price = order.get('shipping_price')
        if sale_order.shipping_pudo_id != order.get('shipping_pudo_id'):
            sale_order.shipping_pudo_id = order.get('shipping_pudo_id')
        if sale_order.shipping_tracking != order.get('shipping_tracking'):
            sale_order.shipping_tracking = order.get('shipping_tracking')
        if sale_order.shipping_tracking_url != order.get('shipping_tracking_url'):
            sale_order.shipping_tracking_url = order.get('shipping_tracking_url')
        if sale_order.shipping_type_code != order.get('shipping_type_code'):
            sale_order.shipping_type_code = order.get('shipping_type_code')

        # Update Order Lines 

        self.check_for_order_line_updates(order.get('order_lines'), sale_order)

        
        ######################
        # Update Delivery
        ######################
        
        if sale_order.mirakl_order_state in ["shipped", "received", "closed"]:
            for delivery in sale_order.picking_ids:
                if len(sale_order.picking_ids) > 1:
                    self.get_shipment_details(sale_order)
                else:
                    if not delivery.shipping_tracking or not delivery.shipping_tracking_url or not delivery.mirakl_carrier_name:
                        delivery.shipping_tracking = order.get('shipping_tracking')
                        delivery.shipping_tracking_url = order.get('shipping_tracking_url')
                        delivery.mirakl_carrier_code = order.get('shipping_carrier_code')
                        delivery.mirakl_carrier_name = order.get('shipping_company')
                        delivery.is_tracking_updated = True
                        _logger.info("Updated Old tracking info inside delivery;;;;;")


        if sale_order.shipping_type_label != order.get('shipping_type_label'):
            sale_order.shipping_type_label = order.get('shipping_type_label')
        if sale_order.transaction_number != order.get('transaction_number'):
            sale_order.transaction_number = order.get('transaction_number')
        if sale_order.total_commission != order.get('total_commission'):
            sale_order.total_commission = order.get('total_commission')
        if sale_order.total_price != order.get('total_price'):
            sale_order.total_price = order.get('total_price')
        
    def create_sale_order(self, order, shop_id, update_filter=False, recalled_first=False):
        
        shop_obj = self.env['shop.integrator'].search([('id', 'in', [shop_id])])
        sale_order = self.env['sale.order'].search([('mirakl_order_id', '=', order.get('order_id'))], limit=1) or False
        warehouse_id = False
        if not sale_order:
            # Create Sale Order
            sale_order = False
            
            # Create Customer Details and Addresses
            try:
                customer_id = self._create_customer(order)
            except:
                _logger.info("Customer creation error~~~~~~~%r ;;;;;",order.get('customer'))
                customer_id = False
            if customer_id:
                if order.get('customer').get("billing_address") !=None and order.get('customer').get("shipping_address") != None:
                    try:
                        billing_id = self._create_billing_customer(order.get('customer').get("billing_address"), customer_id)
                    except:
                        _logger.info("Billing creation error~~~~~~~%r ;;;;;",order.get('customer').get("billing_address"))
                        billing_id = False
                    try:
                        shipping_id = self._create_shipping_customer(order.get('customer').get("shipping_address"), customer_id)
                    except:
                        _logger.info("Shipping creation error~~~~~~~%r ;;;;;", order.get('customer').get("shipping_address"))
                        shipping_id = False
                else:
                    if order.get('order_state').lower() in ['waiting_acceptance', 'waiting_debit_payment', 'waiting_debit']:
                        billing_id, shipping_id = self.add_dummy_address(customer_id, order)
                    else:
                        billing_id, shipping_id = False, False
            
            # Assign Warehouse
            try:
                warehouse_id = self._get_warehouse(shop_id)
            except:
                _logger.info("Warehouse not assigned error in the shop ;;;;;")
                warehouse_id = False
            
            # Create Order Lines
            try:
                order_line = self.get_sale_order_lines(order.get('order_lines'), shop_id, shipping_id)
            except:
                _logger.info("Order Line creation error ;;;;;")
                order_line = False

            # Create Order
            if customer_id and billing_id and shipping_id and warehouse_id and order_line:
                try:
                    sale_order = self.env['sale.order'].create({
                        'partner_id': customer_id,
                        'partner_invoice_id': billing_id,
                        'partner_shipping_id': shipping_id,
                        'mirakl_shop_id': shop_obj.id,
                        'market_place_shop': shop_obj.name,
                        'acceptance_descission_date': self.get_odoo_date_format(order.get('acceptance_descission_date')) if order.get('acceptance_descission_date') else False,
                        'customer_debited_date':self.get_odoo_date_format(order.get('customer_debited_date')) if order.get('customer_debited_date') else False,
                        'mirakl_earliest_delivery_date': self.get_odoo_date_format(order.get('delivery_date').get('earliest')) if order.get('delivery_date') else False,
                        'mirakl_latest_delivery_date': self.get_odoo_date_format(order.get('delivery_date').get('latest')) if  order.get('') else False,
                        'mirakl_created_date': self.get_odoo_date_format(order.get('created_date')) if order.get('created_date') else False,
                        'mirakl_last_updated_date': self.get_odoo_date_format(order.get('last_updated_date')) if order.get('last_updated_date') else False,
                        'shipping_deadline': self.get_odoo_date_format(order.get('shipping_deadline')) if order.get('shipping_deadline') else False,
                        'transaction_date': self.get_odoo_date_format(order.get('transaction_date')) if order.get('transaction_date') else False,
                        
                        'can_cancel': order.get("can_cancel") if order.get("can_cancel") else False,
                        'can_shop_ship': order.get("can_shop_ship") if order.get("can_shop_ship") else False,
                        'channel': order.get("channel") if order.get("channel") else False,
                        'commercial_id': order.get("commercial_id") if order.get("commercial_id") else False,
                        'currency_iso_code' : order.get("currency_iso_code") if order.get("currency_iso_code") else False,
                        'customer_directly_pays_seller': order.get("customer_directly_pays_seller") if order.get("customer_directly_pays_seller") else False,
                        'customer_notification_email': order.get("customer_notification_email") if order.get("customer_notification_email") else False,

                        'has_customer_message': order.get("has_customer_message") if order.get("has_customer_message") else False,
                        'has_incident': order.get("has_incident") if order.get("has_incident") else False,
                        'has_invoice': order.get("has_invoice") if order.get("has_invoice") else False,
                        'leadtime_to_ship': order.get("leadtime_to_ship") if order.get("leadtime_to_ship") else False,
                        'mirakl_order_id': order.get("order_id") if order.get("order_id") else False,
                        
                        'mirakl_comment': order.get("customer").get("shipping_address").get("additional_info") if order.get("customer").get("shipping_address") and order.get("customer").get("shipping_address").get("additional_info") else False,
                        
                        'mirakl_order_state': order.get("order_state").lower() if order.get("order_state").lower() else False,
                        'order_state_reason_code': order.get("order_state_reason_code") if order.get("order_state_reason_code") else False,
                        'order_state_reason_label': order.get("order_state_reason_label") if order.get("order_state_reason_label") else False,
                        'order_tax_mode': order.get("order_tax_mode").lower() if order.get("order_tax_mode").lower() else False,
                        'paymentType': order.get("paymentType") if order.get("paymentType") else False,
                        'payment_type': order.get("payment_type") if order.get("payment_type") else False,
                        'payment_workflows': order.get("payment_workflow").lower() if order.get("payment_workflow").lower() else False,
                        'mirakl_price': order.get("price") if order.get("price") else False,

                        'quote_id': order.get("quote_id") if order.get("quote_id") else False,
                        'shipping_carrier_code': order.get("shipping_carrier_code") if order.get("shipping_carrier_code") else False,
                        'shipping_company': order.get("shipping_company") if order.get("shipping_company") else False,
                        'shipping_price': order.get("shipping_price") if order.get("shipping_price") else False,
                        'shipping_pudo_id': order.get("shipping_pudo_id") if order.get("shipping_pudo_id") else False,
                        'shipping_tracking': order.get("shipping_tracking") if order.get("shipping_tracking") else False,
                        'shipping_tracking_url': order.get("shipping_tracking_url") if order.get("shipping_tracking_url") else False,
                        'shipping_type_code': order.get("shipping_type_code") if order.get("shipping_type_code") else False,
                        'shipping_type_label': order.get("shipping_type_label") if order.get("shipping_type_label") else False,
                        'transaction_number': order.get("transaction_number") if order.get("transaction_number") else False,
                        
                        'total_commission': order.get('total_commission') if order.get('total_commission') else False,
                        'total_price': order.get('total_price') if order.get('total_price') else False,
                        'amount_total': order.get('total_price') if order.get('total_price') else False,
                        'warehouse_id': warehouse_id,
                        'order_line': order_line,
                    })
                    _logger.info("Sale Order Created~~~~~~%r ;;;;;", sale_order)
                except Exception as err:
                    _logger.info("Sale Order Creation Error~~~~~~~%r ;;;;;",err)
                    shop_obj.order_error_count += 1
            else:
                shop_obj.order_error_count += 1
                _logger.info("Error order id ~~~~~~~  %r ;;;;;",order.get("order_id"))

            # If order created successfuly
            if sale_order:
                
                # Update Created Product Count 
                shop_obj.created_orders_count +=1

                # If recall is required update filters
                if update_filter or shop_obj.is_order_recall:
                    self.update_sale_order_filter(shop_obj, sale_order)

                # Sale Order Automation
                self.sale_order_workflow(sale_order)

                sale_order.date_order = sale_order.mirakl_created_date

                # Dellivery Automation
                self.check_for_delivery_validation(sale_order)
        else:

            # If recall is required update filters
            if update_filter or shop_obj.is_order_recall:
                self.update_sale_order_filter(shop_obj, sale_order)
            if not recalled_first:
                shop_obj.existing_orders_count += 1

            # Update Order details
            self.check_for_customer_updates(order, sale_order)
            self.check_for_order_data_changes(order, sale_order)
            self.sale_order_workflow(sale_order)
            self.check_for_delivery_validation(sale_order)
            _logger.info("Sale Order already exists~~~~~~%r ;;;;;",sale_order.id)

    def run_sale_orders(self, response, shop_id, recall=False):
        # Order count limit
        last = len(response.get("orders"))
        count = 0
        # Create Sale Orders
        for order in response.get("orders"):
            count+=1
            try:
                # When filter is updated
                if recall:
                    if count == last:
                        self.create_sale_order(order, shop_id, recall, False)
                    elif count == 1:
                        self.create_sale_order(order, shop_id, False, True)
                    else:
                        self.create_sale_order(order, shop_id, False, False)
                else:
                    self.create_sale_order(order, shop_id, False, False)

            except Exception as error:
                _logger.info("~~~Order creation error~~~~~~~~%r~~~~~~~~",error)
                pass
        shop_obj = self.env['shop.integrator'].search([('id', 'in', [shop_id])])
        if shop_obj.created_orders_count == shop_obj.total_order_count:
            shop_obj.existing_orders_count = 0


    # Mirakl Actions
    # ~~~~~~~~~~~~~~

    def update_date(self):
        for order in self:
            if order.mirakl_order_id:
                order.date_order = order.mirakl_created_date

    def action_confirm(self):
        res = False 

        for so in self:
            if so.mirakl_order_id:
                if so.mirakl_order_state in ["waiting_acceptance", "shipping"] :
                    self.update_warehouse_info(so)

        to_update_stock = to_update_so = to_confirm_so = non_mirakl_orders = self.env["sale.order"]
        for so in self:
            #Change state of the mirakl sale order
            if so.mirakl_order_id:
                if len(so.order_line) > 0:

                    if so.mirakl_order_state == "waiting_acceptance":
                        if self.sale_order_instock(so):
                            response = so.mirakl_shop_id.accept_marketplace_orders(so)
                            to_update_stock += so
                            so.mirakl_order_state = "waiting_debit_payment"
                            to_confirm_so += so
                    elif so.mirakl_order_state in ["shipping", "shipped" ,"closed", "received"]:
                        to_confirm_so += so

                else:
                    to_update_so += so
            else:
                non_mirakl_orders += so

        if to_update_so:
            to_update_so.marketplace_action_update()
        if to_confirm_so:
            res = super(SaleOrder, to_confirm_so).action_confirm()
            orders_per_shop = to_update_stock.divide_orders_per_shop()
            self.per_shop_order_update(orders_per_shop)

        if non_mirakl_orders:
            res = super(SaleOrder, non_mirakl_orders).action_confirm()
        return res

    def update_warehouse_info(self, sale_order):
        check_for_cdisc = []
        check_for_etl = []
        warehouse_cdisc = self.env['marketplace.warehouse'].search([('warehouse_code', '=', 'CDISC')])
        warehouse_etl = self.env['marketplace.warehouse'].search([('warehouse_code', '=', 'ETL')])
        for line in sale_order.order_line:

            # Check if available in C-discount 
            cdisc_stock_count = 0
            etl_stock_count = 0
            stocks = self.env['stock.quant'].search([('product_id','=',line.product_id.id)])
            for stock in stocks:
                if stock.location_id.warehouse_id.code == "CDISC":
                    cdisc_stock_count += stock.quantity
                if stock.location_id.warehouse_id.code == "ETL":
                    etl_stock_count += stock.quantity
            if etl_stock_count >= line.product_uom_qty:
                check_for_etl.append(True)
            else:
                check_for_etl.append(False)
            if cdisc_stock_count >= line.product_uom_qty and sale_order.warehouse_id.code != "CDISC":
                check_for_cdisc.append(True)
            else:
                check_for_cdisc.append(False)
        # Warehouse changed to CDISCOUNT
        if sale_order.mirakl_shop_id.is_cdiscount_priority:
            # If cdiscount stock is available
            if len(check_for_cdisc) == check_for_cdisc.count(True):
                #Checking for country priority
                if sale_order.partner_shipping_id.country_id:
                    if sale_order.partner_shipping_id.country_id.code == "DE" and len(check_for_etl) == check_for_etl.count(True):
                        sale_order.warehouse_id = warehouse_etl.warehouse_id
                    else:
                        sale_order.warehouse_id = warehouse_cdisc.warehouse_id
                else:
                    sale_order.warehouse_id = warehouse_cdisc.warehouse_id

    def marketplace_action_update(self):
        multi_shop_orders = {}
        for order in self:
            if order.mirakl_order_id:
                if  order.mirakl_shop_id.id not in multi_shop_orders.keys():
                    multi_shop_orders[order.mirakl_shop_id.id] = [order]
                else:
                    multi_shop_orders[order.mirakl_shop_id.id].append(order)
        for single_shop in multi_shop_orders.keys():
            shop_obj = self.env['shop.integrator'].search([('id', '=', single_shop)])
            shop_obj.get_order_by_ids(shop_obj, multi_shop_orders[single_shop])
    
    def get_invoice_btn(self):
        for order in self:
            if order.state == "sale":
                all_done = True
                for picking in order.picking_ids:
                    if picking.state != "done":
                        all_done  = False
                if all_done:
                    order.invoice_status = 'to invoice'

    def update_shop_sale_orders(self, order_data):
        for order_data in order_data.get("orders"):
            order_id = self.search([('mirakl_order_id', '=', order_data.get('order_id'))], limit=1)
            if order_id:
                self.check_for_customer_updates(order_data, order_id)
                self.check_for_order_data_changes(order_data, order_id)
                self.sale_order_workflow(order_id)
                order_id.date_order = order_id.mirakl_created_date
                self.check_for_delivery_validation(order_id)

    def export_warehouse_orders(self):
        shipping_sale_orders = []
        for order in self:
            if order.mirakl_order_state == "shipping" and order.mirakl_order_id:
                shipping_sale_orders.append(order)
        if len(shipping_sale_orders) > 0:
            _logger.info("_________%r Order Processed to Warehouse Processing Management~~~~~~~~",len(shipping_sale_orders))
            self.env['shop.integrator'].separate_warehouse_orders(shipping_sale_orders)

    def marketplace_order_close(self):
        for order in self:
            if order.mirakl_order_id and order.mirakl_order_state == "shipped":
                order.mirakl_order_state = "closed"
                try:
                    pass
                    # call stoped before testing
                    # self.env['shop.integrator'].search([('self', 'in', [order.mirakl_shop_id])]).refuse_orders(order)
                except:
                    pass

    def marketplace_action_refuse(self):
        for order in self:
            if order.mirakl_order_id and order.mirakl_order_state == 'waiting_acceptance':
                order.mirakl_order_state = "refused"
                try:
                    pass
                    # call stoped before testing
                    # self.env['shop.integrator'].search([('self', 'in', [order.mirakl_shop_id])]).refuse_orders(order)
                except:
                    pass

    def marketplace_action_cancel(self):
        for order in self:
            if order.mirakl_order_id and order.mirakl_order_state == 'waiting_acceptance':
                order.mirakl_order_state = "canceled"
                try:
                    pass
                    # call stoped before testing
                    # self.env['shop.integrator'].search([('self', 'in', [order.mirakl_shop_id])]).cancel_orders(order)
                except:
                    pass
    


    # Send Stock Update
    # ~~~~~~~~~~~~~~~~~

    def send_api_calls(self, shop, ded_qty):
        offer_id = self.env['mirakl.offers'].search([('shop_id','=', shop.shop_id.id), ('product_id','=',shop.odoo_product_id.id)])
        if offer_id:
            call = shop.shop_id.shop_url+"/api/offers/" + offer_id.offer_id
            try:
                response_data = requests.get(call,headers={'Authorization': shop.shop_id.api_key,'Content-Type': 'application/json'}).json()
            except:
                return False
            if len(response_data):
                quantity = int(response_data.get('quantity') if response_data.get('quantity') else 0) - ded_qty
                if quantity < 0:
                    _logger.info(_("Offer %s has 0 available quantity in %s already! Cannot reduce more", offer_id, shop.shop_id.name))
                    quantity = 0
                # response_data = response
                discount = response_data.get('discount')
                if response_data.get('all_prices'):
                        for price in response_data.get('all_prices'):
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
                            "end_date": discount['end_date'] if discount else None,
                            "price": discount['discount_price'] if discount else None,
                            "ranges": discount['ranges'] if discount else None,
                            "start_date": discount['start_date'] if discount else None
                        },
                        "internal_description": response_data.get('description'),
                        "leadtime_to_ship": response_data.get('leadtime_to_ship'),
                        "logistic_class": response_data['logistic_class']['code'] if response_data.get('logistic_class') else None,
                        # "max_order_quantity": 3,
                        # "min_order_quantity": 1,
                        "min_quantity_alert": response_data.get('min_quantity_alert'),
                        "offer_additional_fields": response_data.get('offer_additional_fields'),
                        # "package_quantity": "2",
                        "product_id": response_data.get('product_references')[0].get('reference') if response_data.get('product_references') else None,
                        "product_id_type": response_data.get('product_references')[0].get('reference_type') if response_data.get('product_references') else None,
                        "price": discount.get('origin_price') if discount else response_data.get('price'),
                        "price_additional_info": response_data.get('price_additional_info'),
                        "all_prices": response_data.get('all_prices'),
                        "quantity": quantity ,
                        "shop_sku": response_data.get('shop_sku'),
                        "state_code": response_data.get('state_code'),
                        "update_delete": "update"
                    }
                ]
                }
                if response_data.get('min_order_quantity'):
                    data['offers'][0].update({'min_order_quantity': response_data.get('min_order_quantity')})
                if response_data.get('max_order_quantity'):
                    data['offers'][0].update({'min_order_quantity': response_data.get('max_order_quantity')})

                response = False
                post_call = shop.shop_id.shop_url+'/api/offers/'
                if shop.shop_id.shop_id:
                    post_call += "?shop_id=" + shop.shop_id.shop_id
                _logger.info("URL = " + call + "key = " +  shop.shop_id.api_key)
                try:
                    _logger.info("Stock Updation Api Called with for offer "+ offer_id.offer_id)
                    # response = requests.post(post_call,headers={'Authorization': shop.shop_id.api_key,'Content-Type': 'application/json'}, data=json.dumps(data)).json()

                    if response and response.get('import_id'):
                        offer_record = self.env['mirakl.offers'].search([('offer_id','=',offer_id.offer_id)])
                        offer_record.write({'last_updated_import_id': response['import_id']})
                        # print("Offer Updated with "+ response.get('import_id')+ " Import Id")
                        _logger.info("Offer Updated with " + str(response.get('import_id')))
                except Exception as err:
                    _logger.info("Stock Updation Error~~~~~~~~~~~%r ;;;;;",err)
                if response:
                    _logger.info("Stock Update Response~~~~~~~~~~%r ;;;;;",response)

    def mark_orders_as_shipped(self):
        for order in self:
            if order.state != 'cancel':
                order.state = "sale"
                order.action_confirm()
                order.mirakl_order_state = 'shipped'
                self.change_order_delivery_state(order)
    
    def change_order_delivery_state(self,sale_order):
        if sale_order.mirakl_order_state in ["shipped" ,"closed", "received"]:
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
                        delivery.shipping_tracking = sale_order.shipping_tracking if sale_order.shipping_tracking else False
                        delivery.shipping_tracking_url = sale_order.shipping_tracking_url if sale_order.shipping_tracking_url else False
                        delivery.mirakl_carrier_name = sale_order.shipping_carrier_code
                        delivery.with_context(skip_immediate=True, skip_sms=True).button_validate()
                        sale_order.invoice_status = 'to invoice'

class SaleOrderLine(models.Model):
    _inherit= "sale.order.line"

    can_refund = fields.Boolean("Can Refund")
    commission_fee = fields.Float("Commission Fee")
    commission_rate_vat = fields.Float("Commission Rate VAT")
    commission_vat = fields.Float("Commission VAT")
    mirakl_created_date = fields.Datetime("Mirakl Created Date")
    description = fields.Char("Shop Description")
    last_updated_date = fields.Datetime("Last Updated Date")
    debited_date = fields.Datetime("Debited Date")
    mirakl_offer_id = fields.Char("Offer Id")
    offer_sku = fields.Char("Offer SKU")
    offer_state_code = fields.Char("Offer State Code")
    mirakl_order_line_id = fields.Char("Mirakl Order Line")
    order_line_index = fields.Char("Order Line Index")
    order_line_states = fields.Selection([('staging','STAGING'), ('waiting_acceptance','WAITING_ACCEPTANCE'), ('waiting_debit','WAITING_DEBIT'), ('waiting_debit_payment','WAITING_DEBIT_PAYMENT'), ('shipping','SHIPPING'), ('shipped','SHIPPED'), ('to_collect','TO_COLLECT'), ('received','RECEIVED'),  ('closed','CLOSED'), ('refused','REFUSED'), ('canceled','CANCELED'), ('incident_open','INCIDENT_OPEN'), ('refunded','REFUNDED')],"Order Line State")
    order_line_state_reason_code = fields.Char("Order Line State Reason Code")
    order_line_state_reason_label = fields.Char("Order Line State Reason Label")
    order_line_index = fields.Char("Order Line Index")
    mirakl_line_price = fields.Float("Mirakl Price")
    price_additional_info = fields.Char("Price Additional Info")
    mirakl_price_unit = fields.Float("Mirakl Price Unit")
    
    mirakl_quantity = fields.Float("Mirakl Product Quantity")
    received_date = fields.Datetime("Received Date")
    shipped_date = fields.Datetime("Shipped Date")
    shipping_price = fields.Float("Shipping Price")
    shipping_price_additional_unit = fields.Float("Shipping Price Additional Unit")
    shipping_price_unit = fields.Float("Shipping Price Unit")
    total_commission = fields.Float("Total Commission")
    mirakl_total_price = fields.Float("Total Price")


    def _action_launch_stock_rule(self, previous_product_uom_qty=False):
        if self.order_id.amazon_b2b_order_id:
            values = super(SaleOrderLine, self)._action_launch_stock_rule(previous_product_uom_qty)
            return values
        else:
            precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            for line in self:

                procurements = []
                line = line.with_company(line.company_id)
                if line.state != 'sale' or not line.product_id.type in ('consu','product'):
                    continue
                qty = line._get_qty_procurement(previous_product_uom_qty)
                if float_compare(qty, line.product_uom_qty, precision_digits=precision) == 0:
                    continue
                for each_qty in range(0,int(line.product_uom_qty)):
                    
                    group_id = self.env['procurement.group'].create(line._prepare_procurement_group_vals())
                    line.order_id.procurement_group_id = group_id
                    values = line._prepare_procurement_values(group_id=group_id)
                    product_qty = 1

                    line_uom = line.product_uom
                    quant_uom = line.product_id.uom_id
                    product_qty, procurement_uom = line_uom._adjust_uom_quantities(product_qty, quant_uom)
                    procurements.append(self.env['procurement.group'].Procurement(
                        line.product_id, product_qty, procurement_uom,
                        line.order_id.partner_shipping_id.property_stock_customer,
                        line.name, line.order_id.name, line.order_id.company_id, values))
                if procurements:
                    self.env['procurement.group'].run(procurements)

            # This next block is currently needed only because the scheduler trigger is done by picking confirmation rather than stock.move confirmation
            orders = self.mapped('order_id')
            for order in orders:
                pickings_to_confirm = order.picking_ids.filtered(lambda p: p.state not in ['cancel', 'done'])
                if pickings_to_confirm:
                    # Trigger the Scheduler for Pickings
                    pickings_to_confirm.action_confirm()
        return True
