# -*- coding: utf-8 -*-
{
    'name': 'Shop Data Cleaner',
    'version': '1.0.0',
    'category': 'Sales/Sales',
    'sequence': 5,
    'summary': 'Shop Data Cleaner',
    'description': """Shop Data Cleaner""",
    'website': '',
    'depends': ["odoo_mirakl_integration"],
    'data': [
        'security/ir.model.access.csv',
        'views/actions.xml',
        'views/menus.xml',
        'views/data_cleaner.xml',
        'views/cron.xml'
    ],
    'application': True,
    'installable': True,
    'license': 'LGPL-3',
}
