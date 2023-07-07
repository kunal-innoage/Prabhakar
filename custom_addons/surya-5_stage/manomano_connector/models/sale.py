from odoo import fields,api,models
import json
import requests
import logging
_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    manomano_order_id = fields.Char("ManoMano Order ID")
    first_name = fields.Char("First Name")
    last_name = fields.Char("Last Name")
    order_status = fields.Char('Order Status')
    shipping_method = fields.Char("Ship Method")
    shipping_address = fields.Char("Ship To Address Line 1")
    shipping_zip = fields.Char("Ship To ZIP Code")
    delivery_city = fields.Char("Ship To City")
    delivery_country = fields.Char("Ship To Country or Region")
    product_id = fields.Many2one("product.product","Product")
    full_name = fields.Char("Ship To Name")
    quantity = fields.Char("Item Quantity")
    total_price = fields.Char("Item Cost")
    delivery_cost = fields.Char("Amount Delivery costs (€ incl. VAT)")
    phone = fields.Char('Phone Number')
    line_id = fields.Char('Line ID')
    billing_zip = fields.Char("Billing postcode")
    billing_city = fields.Char("Billing city")
    billing_country = fields.Char("Billing country")
    order_id = fields.Many2one('sale.order',"Sale Order")
    sku = fields.Char('SKU')
    manomano_warehouse_id = fields.Char('Manomano Warehouse')
    manomano_shop_id = fields.Many2one("manomano.seller", "Manomano Shop")

    #sale manomano fields
    status = fields.Selection([
        ('PENDING','Pending'),
        ('WAITING_PAYMENT','Waiting Period'),
        ('REFUSED','Refused'),
        ('PREPARATION','Preparation'),
        ('SHIPPED','Shipped'),
        ('REFUNDED','Refunded'),
        ('REFUNDING','Refunding'),
        ('REMORSE_PERIOD','Remorse Period'),
    ], "Manomano Status")
   
    
    total_price_amount = fields.Float(" Price Amount")
    total_price_currency = fields.Char("Total Price Currency")
    total_price_vat_amount= fields.Float("Vat Amount")
    total_price_vat_currency=  fields.Char(" Vat Currency")
    shipping_price_vat_rate = fields.Float("Shipping Price")

    products_price_amount = fields.Float("Product Price")
    products_price_currency = fields.Char("Product Price Currency")
    products_price_excluding_vat_amount =fields.Float("Product Amount")
    products_price_excluding_vat_currency = fields.Char("Product Currency")

    products_price_vat_amount = fields.Float("Product  vat amount")
    products_price_vat_currency = fields.Char("Product vat currency")
    manomano_discount_amount = fields.Float("Discount amount")
    manomano_discount_currency = fields.Char("Discount Currency")

    seller_discount_currency = fields.Char()
    seller_contract_id = fields.Char("Seller Id")
    order_reference = fields.Char("Order Refrence")
    shipping_discount_amount = fields.Float("Shipping Discount Amount")
    shipping_discount_currency = fields.Char("Shipping Discount Currency")
    
    created_at = fields.Datetime("Created at")
    status_updated_at = fields.Datetime("Status Updated at")
    total_discount = fields.Float("Total Discount")
    customer_firstname = fields.Char("First name")
    customer_lastname = fields.Char("Last name")
    is_mmf = fields.Char("IS MMF")
    is_professional = fields.Char("IS Professional")
    billing_fiscal_number = fields.Char("Billig Fiscal Number")
 
    #new fields
    order_date = fields.Char("Order Place Date")
    req_ship_date = fields.Char("Required Ship Date")
    ship_method_code = fields.Char("Ship Method Code")
    shipping_address2 = fields.Char("Ship To Address Line 2")
    shipping_address3 = fields.Char("Ship To Address Line 3")
    shipping_state = fields.Char("Ship To State")
    is_gift = fields.Char("Is it Gift?")
    asin = fields.Char("ASIN")
    carrier = fields.Char("carrier")
    gift_meesage = fields.Char("Gift Message")
    tracking_id = fields.Char("Tracking ID")
    ship_date = fields.Char("Shipped Date")
    payment_ref = fields.Char("Payment Ref")
    email = fields.Char("email")

    
    # Check if stock is available
    def sale_order_instock_manomano(self, so):
        for line in so.order_line:
            stock_count = 0
            stocks = self.env['stock.quant'].search([('product_id','=',line.product_id.id),('location_id.warehouse_id', '=', so.warehouse_id)])
            for stock in stocks:
                if stock.location_id.warehouse_id == so.warehouse_id:
                    stock_count += stock.quantity
            if stock_count >= line.product_uom_qty and so.manomano_shop_id:
                continue
            else:
                return False
        return True

    # Order Confirm
    def action_confirm(self):
        res = False 

        to_accept_so = non_manomano_orders = self.env["sale.order"]
        for order in self:
            if order.manomano_order_id:

                if order.status in ["PENDING"]:    
                    if self.sale_order_instock_manomano(order):
                        to_accept_so += order
                if order.status in ["PREPARATION", "SHIPPED"]:
                    if order.status == "PREAPARATION":
                        order.mirakl_order_state = "shipping"
                    if order.status == "SHIPPED":
                        order.mirakl_order_state = "shipped"
                    non_manomano_orders += order
            else:
                non_manomano_orders += order

        if to_accept_so:
            response = to_accept_so.accept_order_maomano()
            if response:
                res = super(SaleOrder, to_accept_so).action_confirm()

        if non_manomano_orders:
            res = super(SaleOrder, non_manomano_orders).action_confirm()
        return res


    ##################
    # Order Acceptance
    ##################

    def accept_order_maomano(self):
        items = []
        shop_id = False
        for accept_order in self:
            to_add = {
                "order_reference": accept_order.order_reference,
                "seller_contract_id":  accept_order.manomano_shop_id.seller_contract_id   
            }
            shop_id = accept_order.manomano_shop_id
            items.append(to_add)
        
        data = items
        result = self.accept_order_api(data, shop_id)
        if result:
            for accept_order in self:
                accept_order.status = "PREPARATION"
                accept_order.mirakl_order_state = "shipping"
            return True
        else:
            return False

    def accept_order_api(self, data, shop_id):
        call = "https://partnersapi.manomano.com/orders/v1/accept-orders"
        data = json.dumps(data)

        _logger.info("!!!!!~~~~~Accept Order~~~~~~%r~~~~%r~~~~~~",call, data)
        response = False
        try:
            # response = requests.post(call,headers={'x-api-key': shop_id.api_key,'Content-Type': 'application/json'}, data = data)
            pass
        except Exception as err:
            _logger.info("~~~Accept Order API failed~~~~~~~~%r~~~~~~~~~", err)
            response = False
        if response:
            _logger.info("!!!!!~~~~~Accept Order~~~~~~%r~~~~~~~~~~",response.text)
            if response.status_code == 204 or response.status_code == 500:
                return True
            else:
                return False
        else:
            return False

    
    ##############
    # Order Update
    ##############

    def marketplace_action_update(self):
        multi_shop_orders = {}
        to_update_orders = self.env["sale.order"]
        for order in self:
            if order.manomano_order_id:
                # Set State
                if order.status:
                    order.order_status = order.status.lower()
                else:
                    if order.order_status:
                        if order.order_status == "pending":
                            order.status = "PENDING"
                        if order.order_status == "preparation":
                            order.status = "PREPARATION"
                        if order.order_status == "shipped":
                            order.status = "SHIPPED"
                        if order.order_status == "refunded" or order.order_status == "Refunded":
                            order.status = "REFUNDED"
                        
                if order.manomano_shop_id:
                    if  order.manomano_shop_id.id not in multi_shop_orders.keys():
                        multi_shop_orders[order.manomano_shop_id.id] = [order]
                    else:
                        multi_shop_orders[order.manomano_shop_id.id].append(order)
                else:
                    manomano_shop_id = self.env["manomano.seller"].search([("name", "=", "Manomano FR")])
                    if manomano_shop_id:
                        order.manomano_shop_id = manomano_shop_id.id
                        if  order.manomano_shop_id.id not in multi_shop_orders.keys():
                            multi_shop_orders[order.manomano_shop_id.id] = [order]
                        else:
                            multi_shop_orders[order.manomano_shop_id.id].append(order)
        for single_shop in multi_shop_orders.keys():
            shop_obj = self.env['manomano.seller'].search([('id', '=', single_shop)])
            shop_obj.order_update_per_shop(shop_obj, multi_shop_orders[single_shop])

        return super(SaleOrder,self).marketplace_action_update()


    ################
    # Process Orders
    ################

    def export_warehouse_orders(self):

        shipping_sale_orders = []
        for order in self:
            if order.status == "PREPARATION" and order.mirakl_order_state == "shipping" and order.manomano_order_id:
                shipping_sale_orders.append(order)
        if len(shipping_sale_orders) > 0:
            self.env['shop.integrator'].separate_warehouse_orders(shipping_sale_orders)
        return super(SaleOrder, self).export_warehouse_orders()


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    line_id = fields.Char("Line Id")
