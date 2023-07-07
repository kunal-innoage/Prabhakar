{
    "name" : "ManoMano Connector",
    "depends": ['sale','account','odoo_mirakl_integration','amazon_connector'],
    "data": [
        "security/ir.model.access.csv",
        "views/res_partner_views.xml",
        "views/sale_order_views.xml",
        "views/seller_views.xml",
        "views/manomano_orders_views.xml",
        "views/manomano_offers_views.xml",
        "views/shop_carriers.xml",
        "wizard/notification_wizard.xml",
    ],
    'application': True,
    "installable": True,
    'license': 'LGPL-3',
    

}
