{
    'name': 'Product Details',
    'version': '1.0.0',
    'sequence':-100,
    'summary': 'Add Product Details',
    'description': """Adding product details to product.product""",
    'depends': ["sale"],
    'data': [
                "security/ir.model.access.csv",
                "views/product_details_views.xml"
            ],              
    'demo': [],
    'installable': True,
    'application':True,
    'auto_install': False,
    'license': 'LGPL-3',
}
