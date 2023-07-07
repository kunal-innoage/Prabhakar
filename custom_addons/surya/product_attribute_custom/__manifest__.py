{
    'name': 'Product Custom Attributes',
    'summary': 'Product Custom Attributes',
    'version': '15.0.0.0',
    'depends': ['website_sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_custom_attribute.xml',
        'views/product_template.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
    'license': 'LGPL-3',
}
