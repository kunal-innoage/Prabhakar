{
    "name" : "Wayfair Connector",
    "depends": ['sale','account','odoo_mirakl_integration','amazon_connector',],
    'version': '15.0.0.1',
    "data": [
        "security/ir.model.access.csv",
        "views/res_partner_views.xml",
        "views/sale_order_views.xml",
        "views/seller_views.xml",
        "views/wayfair_orders_views.xml",
        "views/wayfair_labels_views.xml",
        "wizard/bulk_inventory_update.xml",
        "views/marketplace_warehouse.xml",
        "views/product_views.xml"

    ],
    'external_dependencies': {

        # 'python' : ['pdfreader'],

    },
    "application": True,
    "installable": True,
    'license': 'LGPL-3',

    

}
