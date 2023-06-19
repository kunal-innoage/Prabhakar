{
    'name': 'ASI Page Extension',
    'version': '1.0',
    'summary': 'Extension module to add ASI page in product.product',
    'description': 'This module adds a new page named ASI in the product.product model',
    'depends': ["odoo_mirakl_integration",],
    'data': [
        'views/asi_page_extension_views.xml',
    ],
    'installable': True,    
    'application': True,
    'license': 'LGPL-3',
    
}
