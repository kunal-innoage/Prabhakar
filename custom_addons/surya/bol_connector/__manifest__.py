{
    "name" : "Bol Connector",
    "depends": ['sale','account','odoo_mirakl_integration','amazon_connector'],
    "data": [  
        "security/ir.model.access.csv" 
        "views/bol_seller_view.xml",    
    ],
    'application': True,
    "installable": True,
    'license': 'LGPL-3',
    

}
