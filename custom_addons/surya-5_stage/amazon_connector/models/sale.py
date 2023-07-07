from odoo import fields,api,models

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    amazon_order_id = fields.Char("Amazon Order ID")
    amazon_order = fields.Many2one("amazon.orders","Amazon Order")
    first_name = fields.Char("First Name")
    last_name = fields.Char("Last Name")
    order_status = fields.Char('Order Status')
    shipping_method = fields.Char("Ship Method")
    # date_order = fields.Datetime("Order Date")
    shipping_address = fields.Char("Ship To Address Line 1")
    shipping_zip = fields.Char("Ship To ZIP Code")
    delivery_city = fields.Char("Ship To City")
    delivery_country = fields.Char("Ship To Country or Region")
    product_id = fields.Many2one("product.product","Product")
    full_name = fields.Char("Ship To Name")
    # product_status = fields.Char("Product Status")
    # product_ref = fields.Char("Vendor Reference")
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
    warehouse = fields.Char('Warehouse Code')
    market_place_shop = fields.Char("Shop Name")

    #new fields
    # order_date = fields.Char("Order Place Date")
    req_ship_date = fields.Char("Required Ship Date")
    ship_method_code = fields.Char("Ship Method Code")
    shipping_address2 = fields.Char("Ship To Address Line 2")
    shipping_address3 = fields.Char("Ship To Address Line 3")
    shipping_state = fields.Char("Ship To State")
    is_gift = fields.Char("Is it Gift?")
    asin = fields.Char("ASIN")
    gift_meesage = fields.Char("Gift Message")
    tracking_id = fields.Char("Tracking ID")
    ship_date = fields.Char("Shipped Date")

    amazon_shop_id = fields.Many2one("amazon.seller", "Amazon Shop")

    # @api.multi
    # def action_confirm(self):
    #     ret = super(SaleOrder,self).action_confirm()   
    #     for order in self:
    #         if order.state == 'sale':
    #             order.partner_id.write ({'date_order': str(fields.Datetime.now())})
    #     return ret
    # _sql_constraints = [
    #     ('date_order_conditional_required', "CHECK(1=1)", "A confirmed sales order requires a confirmation date."),
    # ]

    def export_warehouse_orders(self):

        shipping_sale_orders = []
        for order in self:
            if order.mirakl_order_state and order.mirakl_order_state == "shipping" and order.amazon_order_id:
                shipping_sale_orders.append(order)
        if len(shipping_sale_orders) > 0:
            # _logger.info("_________%r Order Processed to Warehouse Processing Management~~~~~~~~",len(shipping_sale_orders))
            self.env['shop.integrator'].separate_warehouse_orders(shipping_sale_orders)
        return super(SaleOrder, self).export_warehouse_orders()

    def update_shop_name(self):
        for rec in self:
            if rec.mirakl_shop_id:
                rec.market_place_shop = rec.mirakl_shop_id.name

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    line_id = fields.Char("Line Id")
