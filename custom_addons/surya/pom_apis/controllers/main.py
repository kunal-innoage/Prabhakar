from odoo import http
from odoo.http import request
import json
import collections
import datetime
from asyncio.log import logger


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
            vendor_ids = [vendor.name.id for vendor in product.product_id.seller_ids]
            vals = {
                'sku': product.sku or "",
                'design': product.design or "",
                'master_design': product.material_design or "",
                'create_date': str(product.create_date) or "",
                'vendor_ref': product.vendor_ref_number or "",
                'pattern': product.pattern or "",
                'rug_shape': product.rug_shape or "",
                'product_link': product.product_link if product.product_link else "",
                'hs_code': product.hs_code or "",
                'construction': product.construction or "",
                'colors': product.colors or "",
                'upc': product.upc or "",
                'length_cm': product.length_cm or "",
                'width_cm': product.width_cm or "",
                'total_area': product.total_area or "",
                'product_weight_kg': product.product_weight_kg or "",
                'ship_weight_kg': product.ship_weight_kg or "",
                'ship_length_cm': product.ship_length_cm or "", 
                'ship_width_cm': product.ship_width_cm or "",
                'ship_height_cm': product.ship_height_cm or "",
                'volume_per_pcs': product.volume_per_pcs or "",
                'material_composition': product.material_composition or "",
                'in_out_door': product.in_out_door or "",
                'machine_washable': product.machine_washable or "",
                'machine_washable': product.machine_washable or "",
                'vendor': product.vendor or "",
                'country': product.country or "",
                'fob_psm': product.fob_psm or "",
                'fob_cost_per_pc': product.fob_cost_per_pc or "",
                'landed_cost_psm': product.landed_cost_psm or "",
                'landed_cost_per_pc_usd': product.landed_cost_per_pc_usd or "",
                'landed_cost_per_pc_eur': product.landed_cost_per_pc_eur or "",
                'points': product.points or "",
                'reed': product.reed or "",
                'shots': product.shots or "",
                'dtex': product.dtex or "",
                'colors_in_creel': product.colors_in_creel or "",
                'pile_weight': product.pile_weight or "",
                'backing_weight_gr': product.backing_weight_gr or "",
                'weight_sqm_gr': product.weight_sqm_gr or "",
                'backing_material': product.backing_material or "",
                'fringe': product.fringe or "",
                'length_of_finge_cm': product.length_of_finge_cm or "",
                'lance': product.lance or "",
                'pile_height_mm': product.pile_height_mm or "",
                'overall_thickness_backing': product.overall_thickness_backing or "",
                'pile_type': product.pile_type or "",
                'loom_size_cm': product.loom_size_cm or "",
                'size': product.size or "",
                'container_capacity_in_pile': product.container_capacity_in_pile or "",
                'container_capacity_out_pile': product.container_capacity_out_pile or "",
                'quality_degree': product.quality_degree or "",
                'etl_wh': product.etl_wh or "",
                'wayfair_wh': product.waryfair_wh or "",
                'iful_wh': product.iful_wh or "",
                'cdisc_wh': product.cdisc_wh or "",
                "odoo_vendor_ids": vendor_ids if len(vendor_ids) else "",
                "last_modified_date": str(product.write_date),
            }
            image_product = request.env['product.image.type'].sudo().search([('sku','=',product.sku)],limit=1)
            if image_product:
                images = {}
                images['flat_image'] = image_product.flat_image or ""
                images['corner'] = image_product.corner or ""
                images['swatch'] = image_product.swatch or ""
                images['roomscene2'] = image_product.roomscene2 or ""
                images['fold_image'] = image_product.fold_image or ""
                images['front'] = image_product.front or ""
                images['pile'] = image_product.pile or ""
                images['roomscene1'] = image_product.roomscene1 or ""
                images['styleshot'] = image_product.styleshot or ""
                images['video'] = image_product.video or ""
                images['roomscene3'] = image_product.roomscene3 or ""
                images['texture'] = image_product.texture or ""
                images['roomscene4'] = image_product.roomscene4 or ""
                images['bat_set_one'] = image_product.bat_set_one or ""
                images['bat_set_two'] = image_product.bat_set_two or ""
                vals['images'] = images or ""
            data.append(vals)
        return data

    #Api Endpoint for Get products
    @http.route(['/get_product_data'], type="http", auth='public',methods=['GET'])
    def get_product_data(self, **post):
        headers = request.httprequest.headers
        key_match = request.env['pom.api.control'].sudo().search([('api_key','=',headers.get('key'))])
        if key_match: 
            domain = self.get_domain(dict(request.params))
            products = request.env['marketplace.product'].sudo().search(domain)
            data = self.prepare_product_data(products,False)
            response_data = {'records_count': len(products), 'products': data}

            return http.Response(json.dumps(response_data), mimetype="application/json")
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
                'sku': line.product_id.name or "",
                'ean': line.product_id.barcode or "",
                'product_qty': line.product_qty or "",
                'uom': line.product_uom.name or "",
                'price_unit': line.price_unit or "",
                # 'taxes': lines. #TODO
                'price_subtotal': line.price_subtotal or ""
            }
            lines.append(vals)
        return lines
    
    def prepare_purchase_order_data(self,orders):
        data = []
        for order in orders:
            if len(order.order_line) > 1:
                vals = {
                    'name': order.name if order.name else "",
                    'supplier_name': order.partner_id.name if order.partner_id and order.partner_id.name else "",
                    'supplier_ref': order.partner_ref if order.partner_ref else "",
                    'order_deadline': str(order.date_order) if order.date_order else "",
                    'receipt_date': str(order.date_planned) if order.date_planned else "",
                    'deliver_to': order.picking_type_id.warehouse_id.name + ': Receipt' if order.picking_type_id and  order.picking_type_id.warehouse_id else "",
                    'odoo_vendor_id': order.partner_id.id or "",
                    'order_lines': self.get_purchase_order_lines(order),
                }
                data.append(vals)
            else:
                logger.info("Order skipped as it does not have multiple order lines")
        return data

    def get_domain(self,params):
        domain = []
        if len(params):
            for param,value in params.items():
                domain.append((param,'ilike',value))
        return domain

    @http.route(['/get_purchase_orders'], type="http", auth='public',methods=['GET'])
    def get_purchase_orders(self, **post):
        headers = request.httprequest.headers
        key_match = request.env['pom.api.control'].sudo().search([('api_key','=',headers.get('key'))])
        if key_match: 
            domain = self.get_domain(dict(request.params))
            orders = request.env['purchase.order'].sudo().search(domain)
            data = self.prepare_purchase_order_data(orders)
            response_data = {'records_count': len(data), 'purchase_orders': data}
            return http.Response(json.dumps(response_data), mimetype="application/json")
        else:
            return http.Response("You are not authorized. Please check your credentials",status="401",mimetype="application/json")

    def prepare_vendors_data(self,vendors):
        data = []
        for vendor in vendors:
            vals = {
                'name': vendor.name if vendor.name else "",
                'street': vendor.street if vendor.street else "",
                'zip': vendor.zip if vendor.zip else "",
                'city': vendor.city if vendor.city else "",
                'state': vendor.state if vendor.state else "",
                'country': vendor.country if vendor.country else "",
                'short_name': vendor.short_name if vendor.short_name else "",
                'is_company': vendor.is_a_company if vendor.is_a_company else "",
                'related_company': vendor.reated_company if vendor.reated_company else "",
                'address_type': vendor.address_type if vendor.address_type else "",
                'email': vendor.partner_id.email if vendor.partner_id and vendor.partner_id.email else "",
                'odoo_vendor_id': vendor.partner_id.id if vendor.partner_id else "",
            }
            data.append(vals)
        return data


    @http.route(['/get_vendors_data'], type="http", auth='public',methods=['GET'])
    def get_vendors_data(self, **post):
        headers = request.httprequest.headers
        params = dict(request.params)
        key_match = request.env['pom.api.control'].sudo().search([('api_key','=',headers.get('key'))])
        if key_match: 
            domain = self.get_domain(dict(request.params))
            vendors = request.env['marketplace.vendor'].sudo().search(domain)
            data = self.prepare_vendors_data(vendors)
            response_data = {'record_counts': len(data), 'vendors': data}
            return http.Response(json.dumps(response_data), mimetype="application/json")
        else:
            return http.Response("You are not authorized. Please check your credentials",status="401",mimetype="application/json")
