{
    'name': 'Manual Tracking Update',
    'version': '1.0',
    'summary': 'Provide User a option to send tracking even if delivery is done in odoo',
    'category': 'Sales',
    'license': '',
    'depends': [
        'odoo_mirakl_integration',
    ],
    'data': [
        'views/stock_picking.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
