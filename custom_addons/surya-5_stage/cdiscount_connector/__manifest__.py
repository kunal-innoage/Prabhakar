{
    "name" : "CDiscount Connector",
    "depends": ['sale','account','odoo_mirakl_integration','amazon_connector'],
    'sequence': 6,
    'version': '1.0.1',
    "data": [
        "security/ir.model.access.csv",
        "wizard/notification_wizard.xml",
        "views/res_partner_views.xml",
        "views/cdiscount_stock.xml",
        "views/sale_order_views.xml",
        "views/seller_views.xml",
        "views/cdiscount_orders_views.xml",
        "views/token_cron.xml",
        "views/stock_picking.xml",
        "views/market_place_order_tracking.xml",
        "views/shop_offers.xml",
        'views/carrier_views.xml'

    ],
    'images': ['static/images/cdisc.png'],
    "application": True,
    "installable": True,
    'license': 'LGPL-3',
    

}
