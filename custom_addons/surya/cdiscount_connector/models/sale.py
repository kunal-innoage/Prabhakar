from odoo import fields,api,models

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    cdiscount_order_id = fields.Char("Cdiscount Order ID")
    # date_order = fields.Char("Order Date")
    date_order_sent = fields.Datetime("Converted Date time")
    #new fields
    civillity = fields.Char("Civillity")
    date_modify = fields.Char("Date of Last Modification")
    fee = fields.Char("Fee (€ incl. VAT)")
    seller_remu = fields.Char("Seller remuneration (€ incl. VAT)")
    phone_free2 = fields.Char("Phone free 2")
    name_and_billing_address = fields.Char("Name and Billing Address")
    ean = fields.Char("EAN")
    order_status = fields.Char("Order Status")
    shipping_method = fields.Char("Shipping Method")
    cdiscount_shop_id = fields.Many2one("cdiscount.seller", "Shop ID")
    shipping_zip = fields.Char("Shipping Zip")
    delivery_city = fields.Char("Delivery City")
    is_cdisc_business_order = fields.Boolean("Buisiness Order")
    cdisc_purchased_at = fields.Char("purchasedAt")
    cdisc_updated_at = fields.Char("updatedAt")
    cdisc_shipped_at_max= fields.Char("shippedAtMax")
    cdiscount_tracking_addded = fields.Boolean("Cdiscount shipment added")

    # Add new state for fulfillment orders to be used in every marketplace
    mirakl_order_state = fields.Selection(selection_add=[('fulfill','Fulfillment')])


    def export_warehouse_orders(self):

        shipping_sale_orders = []
        for order in self:
            if order.mirakl_order_state and order.mirakl_order_state == "shipping" and order.cdiscount_order_id:
                shipping_sale_orders.append(order)
        if len(shipping_sale_orders) > 0:
            self.env['shop.integrator'].separate_warehouse_orders(shipping_sale_orders)
        return super(SaleOrder, self).export_warehouse_orders()

    def update_shop_order(self):
        if self.cdiscount_order_id:
            self.env['cdiscount.seller'].get_order_by_ids(self.cdiscount_shop_id,self)

    def marketplace_action_update(self):
        multi_shop_orders = {}
        for order in self:
            if order.cdiscount_shop_id.id and order.cdiscount_order_id:
                self.env['cdiscount.seller'].get_order_by_ids(order.cdiscount_shop_id, order)

        return super(SaleOrder,self).marketplace_action_update()
    
    def update_shop_name(self):
        for rec in self:
            if rec.cdiscount_order_id and rec.cdiscount_shop_id:
                rec.market_place_shop = rec.cdiscount_shop_id.name
        return super(SaleOrder,self).update_shop_name()


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    line_id = fields.Char("Line Id")
    supply_mode = fields.Char("Supply mode")
