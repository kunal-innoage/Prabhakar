{
    'name': 'Product Image Types',
    'version': '15.0.2.0',
    'summary': 'This module manges product images and videos',
    'license': 'LGPL-3',
    'depends': ['web','product'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_images.xml',
        'views/product_views.xml'
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
