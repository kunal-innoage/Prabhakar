{
    'name': 'Report Hub',
    'version': '15.0.1.1',
    'summary': 'This module manges sales reporting',
    'category': 'Sales',
    'license': '',
    'depends': [
        'sale','stock','odoo_mirakl_integration','wayfiar_connector',
    ],
    'data': [
        'views/sale_report.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
