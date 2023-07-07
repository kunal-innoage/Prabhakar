# -*- coding: utf-8 -*-

from odoo import http, _
from odoo.http import request
import json
from odoo.exceptions import ValidationError

import logging
_logger = logging.getLogger(__name__)


class EverstroxWebhooks(http.Controller):

    def authenticate_api_key(self, headers):

        api_token = headers.get("Api-Token")
        if api_token:
            shop_id = request.env["everstox.shop"].search([('shop_api_key', 'in', [api_token])], limit=1)
            if len(shop_id) >= 1: 
                return shop_id
        return False

    @http.route(route='/everstox/stock/update',type="json", auth="none", methods=['POST'])
    def everstox_stock_update(self, **kwargs):
        # import pdb ; pdb.set_trace()
        _logger.info("~stock update~~~data~~1~~~%r~~~~~~~~~", request.httprequest.data)

        shop_id = self.authenticate_api_key(request.httprequest.headers)
        if shop_id:
            data = json.loads(request.httprequest.data)
            _logger.info("~stock update~~~data~~~~~%r~~~~~~~~~", data)
            try:
                shop_id.process_stock_update(data)
            except Exception as e:
                _logger.info("Error while handling stock update data  %r  %r  !!!!!!!", data, e)
        else:
            _logger.info("Given API token %r   is not valid  !!!!!!!", request.httprequest.headers.get("Api-Token"))
            return ("Given API token "+ request.httprequest.headers.get("Api-Token") +"is not valid")

    @http.route(route='/everstox/order/update',type="json", auth="none", methods=['POST'])
    def everstox_order_update(self, **kwargs):
        shop_id = self.authenticate_api_key(request.httprequest.headers)
        if shop_id:
            data = json.loads(request.httprequest.data)
            try:

                shop_id.process_order_update(data)
                # Once All changes made into system send response to API 

            except Exception as e:
                _logger.info("Error while handling order update data  %r  %r  !!!!!!!", data, e)
        else:
            _logger.info("Given API token %r   is not valid  !!!!!!!", request.httprequest.headers.get("Api-Token"))
            return ("Given API token "+ request.httprequest.headers.get("Api-Token") +"is not valid")
    
    
    @http.route(route='/everstox/daily/stock/update',type="json", auth="none", csrf=False)
    def everstox_daily_stock_update(self, **kwargs):

        shop_id = self.authenticate_api_key(request.httprequest.headers)
        if shop_id:
            data = json.loads(request.httprequest.data)
            _logger.info("~daily~~~data~~~~~%r~~~~~~~~~", data)
            try:
                shop_id.process_stock_update(data)
            except Exception as e:
                _logger.info("Error while handling daily stock update data  %r  %r  !!!!!!!", data, e)
        else:
            _logger.info("Given API token %r   is not valid  !!!!!!!", request.httprequest.headers.get("Api-Token"))
            return ("Given API token "+ request.httprequest.headers.get("Api-Token") +"is not valid")

