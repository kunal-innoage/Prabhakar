from odoo import models,fields
import logging
_logger = logging.getLogger(__name__)


class WarehouseProcessedOrders(models.Model):
    _inherit = 'processed.order'


    blade_mapped_state = fields.Selection([('mapped', 'Mapped'), ('unmapped', 'Unmapped')],default="unmapped")
    blade_shop_id = fields.Many2one("blade.shop", string = "Blade Shop", readonly=True)
    blade_order_id = fields.Many2one("blade.shop.order", string="Everstox Order")

    def unmap_orders(self):
        for order in self:
            order.blade_mapped_state = "unmapped"

    def create_mapping_order_line_data(self, order, sale_order,blade_order):
        order_item_obj = order_line_ids = self.env["blade.shop.order.line"]

        for order_line in sale_order.order_line:
            if order.product_id == order_line.product_id:
                order_line_ids += order_item_obj.create({
                    "order_line_custom_attributes" : [],
                    "order_line_errors" : [],
                    "order_line_product_name" : order_line.product_id.name,
                    "order_line_product_sku" : order_line.product_id.default_code,
                    "order_line_quantity" : int(order_line.product_uom_qty),
                    "order_line_price_set_quantity" : int(order_line.product_uom_qty),
                    "order_line_state" : "in_fulfillment",
                    "order_line_requested_batch" : "",
                    "order_line_requested_batch_expiration_date" : "",
                    "order_line_price" : "100.00",
                    "order_line_price_gross" : "0.0",
                    "order_line_currency" : "EUR",
                    "order_line_discount" : "0.0",
                    "order_line_discount_net" : "0.0",
                    "order_line_discount_gross" : "0.0",
                    "order_line_price_net_after_discount" : "0.0",
                    "order_line_price_net_before_discount" : "0.0",
                    "order_line_tax" : "0.0",
                    "order_line_tax_amount" : "0.0",
                    "order_line_tax_rate" : "0",
                    'shop_order_id': blade_order.id 
                    # "order_line_shipment_options_id" : carrier.carrier_id if carrier else None,
                    # "order_line_shipment_options_name" : carrier.name if carrier else None,
                })
        _logger.info("~~~~~~~Order Lines ~~~~~~~~`   %r   ", order_line_ids)
        return order_line_ids
    
    def map_order_with_everstox(self):
        blade_order_obj = self.env["blade.shop.order"]
        for order in self:
            if order.warehouse == 'BOH' and order.blade_mapped_state == "unmapped":
                if order.sale_order_id:
                    billing_address_id = order.sale_order_id.partner_invoice_id
                    shipping_address_id = order.sale_order_id.partner_shipping_id
                    if billing_address_id and shipping_address_id:

                        # Biller name 
                        first_name = last_name = ""
                        if billing_address_id.name:
                            name = billing_address_id.name.split(" ")
                            if len(name) > 1:
                                first_name = name[0]
                                last_name = "".join(name[1:])
                            else:
                                first_name = name[0]

                        # Shipping name 
                        s_first_name = s_last_name = ""
                        if billing_address_id.name:
                            name = billing_address_id.name.split(" ")
                            if len(name) > 1:
                                s_first_name = name[0]
                                s_last_name = "".join(name[1:])
                            else:
                                s_first_name = name[0]

                        # Order Date Format 
                        order_date = ""
                        if order.sale_order_id.date_order:
                            order_date = "T".join(str(order.sale_order_id.date_order).split(" "))+ "Z"

                        # Order Line
                        
                        new_order_id = blade_order_obj.create({
                            "billing_address_1": billing_address_id.street,
                            "billing_address_2": billing_address_id.street2,
                            "billing_city": billing_address_id.city,
                            "billing_contact_person": billing_address_id.name,
                            "billing_country": billing_address_id.country_id.name if billing_address_id.country_id else shipping_address_id.country_id.name if shipping_address_id.country_id else "",
                            "billing_country_code": billing_address_id.country_code if billing_address_id.country_id else shipping_address_id.country_code if shipping_address_id.country_id else "",
                            "billing_first_name": first_name,
                            "billing_last_name": last_name,
                            "billing_phone": billing_address_id.phone,
                            "billing_province": billing_address_id.state_id.name if len(billing_address_id.state_id) == 1 else False,
                            "billing_province_code": billing_address_id.state_id.code if len(billing_address_id.state_id) == 1 else False,
                            "billing_zip": billing_address_id.zip,

                            "shipping_address_1": shipping_address_id.street,
                            "shipping_address_2": shipping_address_id.street2,
                            "shipping_city": shipping_address_id.city,
                            "shipping_contact_person": shipping_address_id.name,
                            "shipping_country": shipping_address_id.country_id.name,
                            "shipping_country_code": shipping_address_id.country_code,
                            "shipping_first_name": s_first_name,
                            "shipping_last_name": s_last_name,
                            "shipping_phone": shipping_address_id.phone,
                            "shipping_province": shipping_address_id.state_id.name if len(shipping_address_id.state_id) == 1 else False,
                            "shipping_province_code": shipping_address_id.state_id.code if len(shipping_address_id.state_id) == 1 else False,
                            "shipping_zip": shipping_address_id.zip,
                            "picking_instructions": "Print label and attach it to the rug",
                            "shipping_price_currency" : "EUR",
                            "shipping_price_discount" : "0",
                            "shipping_price_discount_gross" : "0",
                            "shipping_price_discount_net" : "0",
                            "shipping_price" : "0",
                            "shipping_price_gross" : "0",
                            "shipping_price_net_after_discount" : "0",
                            "shipping_price_net_before_discount" : "0",
                            "shipping_price_tax" : "0",
                            "shipping_price_tax_amount" : "0",
                            "shipping_price_tax_rate" : "0",
                            "email": "customer@surya.com",
                            "creation_date" : order_date,
                            "financial_status" : "paid",
                            "order_date" : order_date,
                            "order_number" : order.order_id,
                            # "requested_warehouse_id" : order.blade_shop_id.everstox_warehouse_id.warehouse_id,
                            "state" : "in_fulfillment",
                            "order_errors" : [],
                            "order_returns" : [],
                            "order_attachments" : [],
                            "order_custom_attributes" : [],
                            "sale_order_id":order.sale_order_id.id

                            # "order_line_ids": order_line_ids,
                            # "blade_shop_id": order.blade_shop_id.id,
                            # "blade_mapped_state": "unmapped",
                        })
                        order_line_ids = self.create_mapping_order_line_data(order, order.sale_order_id,new_order_id)
                        
                        if new_order_id:
                            attachments = self.env['ir.attachment'].search([("res_model","=","sale.order"),('res_id','=',order.sale_order_id.id)])
                            for attachment in attachments:
                                blade_attach = self.env['ir.attachment'].create({'name': "Label",'res_model': 'blade.shop.order', 'res_id': new_order_id.id, 'datas': attachment.datas})
                                if blade_attach:
                                    _logger.info("Attachment mapped with blade sale order")
                            order.blade_mapped_state = "mapped"

        super(WarehouseProcessedOrders,self).map_order_with_everstox()

