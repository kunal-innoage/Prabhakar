# -*- coding: utf-8 -*-
{
    'name': 'Purchase Stock Analysis',
    'version': '1.0.0',
    'sequence': -101,
    'summary': 'Odoo Purchase Stock Analysis',
    'description': """Odoo Purchase Stock Analysis""",
    'website': '',
    'depends': ["odoo_mirakl_integration",],
    'data': [
                "security/ir.model.access.csv",
                "views/etl.xml",

            ],
    'application': True,
    'installable': True,
    'license': 'LGPL-3',
}