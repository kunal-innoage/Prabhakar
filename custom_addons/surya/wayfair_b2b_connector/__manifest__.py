{
    "name" : "Wayfair B2B Connector",
    'version': '1.1.0',
    'category': 'Sales/Sales',
    'sequence': 5,
    'summary': 'Wayfair B2B Connector',
    'description': """Wayfair B2B Connector""",
    'website': '',
    "depends": ['sale','account','odoo_mirakl_integration'],
    "data": [
        "security/ir.model.access.csv",
        "views/wayfair_b2b_order.xml",
        "views/wayfair_replenishment.xml",
        "views/shop.xml",
        "views/action.xml",
        "views/menu.xml",
        "views/sale_order_views.xml",
    ],
    "application": True,
    "installable": True,
    'license': 'LGPL-3',
}