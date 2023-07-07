{
    'name': 'Wayfair SKU',
    'version': '1.0.0',
    'sequence':-100,
    'summary': 'Wayfair SKU',
    # 'description': """""",
    'depends': [],
    'data': [
                "security/ir.model.access.csv",
                "views/wayfair_sku_view.xml",
                "views/amazon_sku_view.xml"
            ],              
    'demo': [],
    'installable': True,
    'application':True,
    'auto_install': False,
    'license': 'LGPL-3',
}
