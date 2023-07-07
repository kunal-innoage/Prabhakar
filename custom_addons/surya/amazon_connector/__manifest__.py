{
    "name" : "Amazon Connector",
    "depends": ['sale','account','odoo_mirakl_integration'],
    "data": [
        "security/ir.model.access.csv",
        "views/res_partner_views.xml",
        "views/sale_order_views.xml",
        "views/seller_views.xml",
        "views/amazon_orders_views.xml",
        "wizard/notification_wizard.xml",
        "views/amazon_labels.xml",

    ],
    "application": True,
    "installable": True,
    'license': 'LGPL-3',
    

}
