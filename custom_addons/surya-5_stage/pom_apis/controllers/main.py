from odoo import http
from odoo.http import request
import json
import datetime


class Controller(http.Controller):

    def prepare_product_data(self,products,today):
        data = []
        for product in products:
            if today:
                if product.product_id:
                    if product.product_id.create_date.strftime('%Y-%m-%d') != datetime.datetime.now().date().strftime('%Y-%m-%d'):
                        print("Skipping Product as it's not created today")
                        continue
                else:
                    print("Product not found")
                    continue
            vals = {
                'sku': product.sku,
                'design': product.design,
                'master_design': product.material_design,
                'create_date': str(product.create_date),
                'vendor_ref': product.vendor_ref_number,
                'pattern': product.pattern,
                'rug_shape': product.rug_shape,
                'product_link': product.product_link,
                'hs_code': product.hs_code,
                'construction': product.construction,
                'colors': product.colors,
                'upc': product.upc,
                'length_cm': product.length_cm,
                'width_cm': product.width_cm,
                'total_area': product.total_area,
                'product_weight_kg': product.product_weight_kg,
                'ship_weight_kg': product.ship_weight_kg,
                'ship_length_cm': product.ship_length_cm,
                'ship_width_cm': product.ship_width_cm,
                'ship_height_cm': product.ship_height_cm,
                'volume_per_pcs': product.volume_per_pcs,
                'material_composition': product.material_composition,
                'in_out_door': product.in_out_door,
                'machine_washable': product.machine_washable,
                'machine_washable': product.machine_washable,
                'vendor': product.vendor,
                'country': product.country,
                'fob_psm': product.fob_psm,
                'fob_cost_per_pc': product.fob_cost_per_pc,
                'landed_cost_psm': product.landed_cost_psm,
                'landed_cost_per_pc_usd': product.landed_cost_per_pc_usd,
                'landed_cost_per_pc_eur': product.landed_cost_per_pc_eur,
                'points': product.points,
                'reed': product.reed,
                'shots': product.shots,
                'dtex': product.dtex,
                'colors_in_creel': product.colors_in_creel,
                'pile_weight': product.pile_weight,
                'backing_weight_gr': product.backing_weight_gr,
                'weight_sqm_gr': product.weight_sqm_gr,
                'backing_material': product.backing_material,
                'fringe': product.fringe,
                'length_of_finge_cm': product.length_of_finge_cm,
                'lance': product.lance,
                'pile_height_mm': product.pile_height_mm,
                'overall_thickness_backing': product.overall_thickness_backing,
                'pile_type': product.pile_type,
                'loom_size_cm': product.loom_size_cm,
                'size': product.size,
                'container_capacity_in_pile': product.container_capacity_in_pile,
                'container_capacity_out_pile': product.container_capacity_out_pile,
                'quality_degree': product.quality_degree,
                'etl_wh': product.etl_wh,
                'wayfair_wh': product.waryfair_wh,
                'iful_wh': product.iful_wh,
                'cdisc_wh': product.cdisc_wh,
            }
            data.append(vals)
        return data

    #Api Endpoint for Get products
    @http.route(['/get_product_data'], type="http", auth='public',methods=['GET'])
    def get_product_data(self, **post):
        headers = request.httprequest.headers
        key_match = request.env['pom.api.control'].sudo().search([('api_key','=',headers.get('key'))])
        if key_match: 
            products = request.env['marketplace.product'].sudo().search([])
            data = self.prepare_product_data(products,False)
            # response_data = {'count': len(products), 'products': data}

            return http.Response(json.dumps(data), mimetype="application/json")
        else:
            return http.Response(status="401", mimetype="application/json")

    @http.route(['/get_today_products'], type="http", auth='public',methods=['GET'])
    def get_today_products(self, **post):
        headers = request.httprequest.headers
        key_match = request.env['pom.api.control'].sudo().search([('api_key','=',headers.get('key'))])
        if key_match: 
            products = request.env['marketplace.product'].sudo().search([])
            data = self.prepare_product_data(products,True)
            # response_data = {'count': len(products), 'products': data}

            return http.Response(json.dumps(data), mimetype="application/json")
        else:
            return http.Response(status="401", mimetype="application/json")

    def get_purchase_order_lines(self,order):
        lines = []
        for line in order.order_line:
            vals = {
                'sku': line.product_id.name,
                'ean': line.product_id.barcode,
                'product_qty': line.product_qty,
                'uom': line.product_uom.name,
                'price_unit': line.price_unit,
                # 'taxes': lines. #TODO
                'price_subtotal': line.price_subtotal
            }
            lines.append(vals)
        return lines
    
    def prepare_purchase_order_data(self,orders):
        data = []
        for order in orders:
            vals = {
                'name': order.name,
                'supplier_name': order.partner_id.name,
                'supplier_ref': order.partner_ref,
                'order_deadline': str(order.date_order),
                'receipt_date': str(order.date_planned),
                'deliver_to': order.picking_type_id.warehouse_id.name + ': Receipt',
                'order_lines': self.get_purchase_order_lines(order),
            }
            data.append(vals)
        return data

    
    @http.route(['/get_purchase_orders'], type="http", auth='public',methods=['GET'])
    def get_purchase_orders(self, **post):
        headers = request.httprequest.headers
        key_match = request.env['pom.api.control'].sudo().search([('api_key','=',headers.get('key'))])
        if key_match: 
            orders = request.env['purchase.order'].sudo().search([])
            data = self.prepare_purchase_order_data(orders)
            # response_data = {'count': len(orders), 'purchase_orders': data}
            return http.Response(json.dumps(data), mimetype="application/json")
        else:
            return http.Response("You are not authorized. Please check your credentials",status="401",mimetype="application/json")
