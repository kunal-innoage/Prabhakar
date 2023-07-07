{
    'name': 'Pom Apis',
    'version': '15.0.1.2.1',
    'depends': [
        'odoo_mirakl_integration',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/api_key_views.xml'
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
