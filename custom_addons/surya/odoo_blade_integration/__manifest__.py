{
    'name': 'Odoo Blade Integration',
    'version': '15.0.1.0.0',
    'depends': [
        'odoo_everstox_integration',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/shop_views.xml',
        'views/warehouse_processed_orders.xml',
        'views/warehouse_product.xml',
        'views/warehouse_sale_order.xml',
        "views/sale_order_views.xml"
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
