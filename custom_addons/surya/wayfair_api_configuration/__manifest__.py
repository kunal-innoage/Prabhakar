{
    'name': 'Wayfair Api Configuration',
    'version': '15.0.1.0.0',
    'depends': [
        'odoo_mirakl_integration','wayfiar_connector',
    ],
    
    'data': [
        'security/ir.model.access.csv',
        'views/wayfair_api_config.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
