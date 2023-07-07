from odoo import fields,api, models,_
import requests
from odoo.http import request
import json, datetime
import csv, base64
from io import StringIO
        
import logging
_logger = logging.getLogger(__name__)

class EverstoxShopProduct(models.Model):
    _name = 'everstox.shop.product'
    _description = 'Everstox Shop Product'

    item_id = fields.Char("Item ID")
    sku =fields.Char("SKU")
    status = fields.Char("Status")
    total_stock = fields.Char("Total Stock")
    name = fields.Char("Name")
    shop_id = fields.Char("Shop ID")
    size = fields.Char("Size")
    creation_date = fields.Char("Creation Date")
    updated_date = fields.Char("Updated Date")

    batch_product = fields.Boolean("Batch Product")
    bundle_product = fields.Boolean("Bundle Product")
    bundles = fields.Char("Bundles")
    color = fields.Char("Color")
    country_of_origin = fields.Char("Country Of Origin")
    customs_code = fields.Char("Customs Code")
    customs_description = fields.Char("Customs Description")
    ignore_during_import = fields.Char("Ignore During Import")
    ignore_during_shipment = fields.Char("Ignore During Shipment")

    everstox_warehouse_id = fields.Many2one("everstox.shop.warehouse", string= "Warehouse", default=False)
    everstox_shop_id = fields.Many2one("everstox.shop", string= "Shop")
    everstox_batch_unit = fields.One2many("everstox.product.unit", "everstox_product_id", "Units")
    product_id = fields.Many2one("product.product", string= "Product")
    api_mapping_status = fields.Selection([('mapped', 'Mapped'), ('unmapped', 'Unmapped')], string="Everstox Mapping Status")

    def prepare_product_data(self, product, shop_id):
        color = product.color
        if product.color:
            if len(product.color) > 30:
                color = (product.color[:30].split(","))
                color.pop()
                color = ",".join(color)

        product_data = {
                "batch_product": False,
                "ignore_during_import": product.ignore_during_import,
                "name": product.name,
                "size": product.size,
                "sku": product.sku,
                "status": product.status,
                "color": color,
                "shop_id": product.everstox_shop_id.shop_id,
                "customs_code": product.customs_code,
                "customs_description": product.customs_description,
                "country_of_origin": product.country_of_origin,
            }

        units_data = []

        if product.everstox_batch_unit:
            for unit in product.everstox_batch_unit:
                units_data += [{
                    "default_unit": True if unit.default_unit else False,
                    "gtin": unit.gtin,
                    "length_in_cm": float(unit.length_in_cm),
                    "width_in_cm": float(unit.width_in_cm),
                    "height_in_cm": float(unit.height_in_cm),
                    "name": unit.name,
                    "quantity_of_base_unit": int(float(unit.quantity_of_base_unit)),
                    "weight_gross_in_kg": float(unit.weight_gross_in_kg),
                    "weight_net_in_kg": float(unit.weight_net_in_kg),
                }]

        product_data["units"] = units_data
        return product_data


    def map_product_with_everstox(self):

        shop_id = False
        product_data = {}
        to_update_products = []

        for product in self:

            if not shop_id:
                shop_id = product.everstox_shop_id
            if product.item_id:
                to_update_products += [product]
            else:
                try:
                    product_data = self.prepare_product_data(product, shop_id)
                    shop_id._api_create_everstox_product(product_data, product)
                except Exception as e:
                    _logger.info("Error while preparing data or on API Call%r     %r", product.sku, e)
        if to_update_products and shop_id:
            call = shop_id.shop_url + "api/v1/shops/" + shop_id.shop_id + "/products"
            for product in to_update_products:
                call += "/" + product.item_id
                try:
                    shop_id.get_warehouse_product_by_id(call, product)
                except Exception as e:
                    _logger.info("Error while getting product updates on API Call %r     %r", product.sku, e)

        #Product created logs    

    def update_product_on_everstox(self):
        
        shop_id = False
        product_data = {}
        
        for product in self:
            
            if not shop_id:
                shop_id = product.everstox_shop_id

            try:
                product_data = self.prepare_product_data(product, shop_id)
                shop_id._api_update_everstox_product(product_data, product)
                self.env.cr.commit()
            except Exception as e:
                _logger.info("Error while preparing data or on API Call %r     %r", product.sku, e)

        #Product created logs    

    def delete_product_on_everstox(self):
        
        shop_id = False
        
        for product in self:
            if not shop_id:
                shop_id = product.everstox_shop_id
            try:
                shop_id._api_delete_everstox_product(product)
                # self.env.cr.commit()
                self.env.cr.savepoint()
            except Exception as e:
                _logger.info("Error while Delete Product API Call for %r     %r", product.sku, e)

        #Product created logs

    def bulk_upload_products_on_everstox(self):
        
        shop_id = False
        
        for product in self:
            if not shop_id:
                shop_id = product.everstox_shop_id
                break
        try:
            product_data = self.prepare_bulk_product_csv_data(self)
            shop_id._api_product_create_or_update_by_csv(product_data)
        except Exception as e:
            _logger.info("Error while Bulk Product API Call for  %r  ", e)

        #Product created logs

    def prepare_bulk_product_csv_data(self, products):
        
        headerList = ['SKU', 'Name', 'Batch Product (yes/no)', 'Country of origin', 'Custom Code', 'Custom Description',
            'Unit 1', 'Number of pieces Unit 1', 'EAN/GTIN (unit 1)' 'Weight net (unit 1) in kg', 'Weight gross(unit 1) in kg', 'Length (unit 1) in cm',
            'Width (unit 1) in cm', 'Height (unit 1) in cm']
        
        with open("bulk_data.csv", 'w') as file:
            dw = csv.DictWriter(file, delimiter=',', fieldnames=headerList)
            dw.writeheader()
        
        with open('bulk_data.csv', 'w', newline='', encoding="utf-8") as file:
            writer = csv.writer(file)
            for product in products:
                product_data_list = [product.sku, product.name, product.batch_product, product.country_of_origin,
                product.customs_code, product.customs_description]
                for unit in product.everstox_batch_unit:
                    product_data_list += [ "piece", 1, unit.gtin, unit.weight_net_in_kg,  unit.weight_gross_in_kg, unit.length_in_cm, unit.width_in_cm, unit.height_in_cm]

                writer.writerow(product_data_list)
        file_data = ""
        with open("bulk_data.csv", encoding="utf-8") as f:
            file_data += f.read() + '\n'
        product_data = base64.b64encode(file_data.encode('utf-8'))
        return product_data


    def create_missing_product(self, purchase_line, shop_id):
        if purchase_line.product_id:
            product_details = self.env['marketplace.product'].search([('sku', '=',purchase_line.product_id.default_code)], limit=1)
            if product_details:
                product_data = {
                    "batch_product": True,
                    "everstox_shop_id": shop_id.id,
                    "ignore_during_import": False,
                    "name": purchase_line.product_id.default_code,
                    "size": product_details.size,
                    "sku": purchase_line.product_id.default_code,
                    "status": "active",
                    "color": product_details.colors,
                    "total_stock": 0,
                    "product_id": purchase_line.product_id.id,
                    "customs_code": product_details.hs_code,
                    "customs_description": "HS CODE",
                    "country_of_origin": product_details.country,
                    "ignore_during_import": False,
                    "everstox_warehouse_id": shop_id.everstox_warehouse_id.id,
                    "api_mapping_status": "unmapped",
                    "everstox_batch_unit": [(0,0,
                        {
                        "default_unit": True,
                        "gtin": purchase_line.product_id.barcode,
                        "length_in_cm": product_details.ship_length_cm,
                        "width_in_cm": product_details.ship_width_cm,
                        "height_in_cm": product_details.ship_height_cm,
                        "name": "Piece",
                        "quantity_of_base_unit": 1,
                        "weight_gross_in_kg": product_details.product_weight_kg,
                        "weight_net_in_kg": product_details.ship_weight_kg,
                        }
                    )]
                }
                new_product_id = self.create(product_data)
                _logger.info("~~~~~~~~~~%r~~~~~~~~~~~``", new_product_id)
                new_product_id.map_product_with_everstox()
        pass
