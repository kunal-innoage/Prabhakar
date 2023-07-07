from odoo import models , fields , api
import logging
_logger = logging.getLogger(__name__)

class BolOrder(models.Model):
    _name = 'bol.order'
    _description = 'Bol Orders Management'
    
