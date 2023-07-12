{
    'name': 'GLS Api Configuration',
    'version': '15.0.1.0.0',
    'sequence': -105,
    'depends': ["odoo_mirakl_integration"
        
    ],
    
    'data': [
        'security/ir.model.access.csv',
        'views/gls_api_config.xml',
        "views/gls_api_mapping.xml",
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
