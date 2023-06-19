# -*- coding: utf-8 -*-

from odoo import fields, models, _, api
import datetime
import requests
import pytz


import logging
_logger = logging.getLogger(__name__)


class OrderTracking(models.Model):
    _name = "order.tracking"
    _description = "Order Tracking"
