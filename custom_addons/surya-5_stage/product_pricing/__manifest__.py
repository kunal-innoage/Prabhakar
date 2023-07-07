# -*- coding: utf-8 -*-
{
    'name': 'Product Pricing',
    'version': '1.0.1',
    # 'category': 'Product/Pricing',
    'sequence': -100,
    'summary': 'Odoo Product Pricing Analysis',
    'description': """Odoo Product Pricing Analysis""",
    'website': '',
    'depends': ['sale', "odoo_mirakl_integration" , "cdiscount_connector"],
    'data': [
                "security/ir.model.access.csv",
                "views/product_pricing.xml",
                "views/wayfair_shop_view.xml",
                "views/amazon_sku_view.xml",
                "views/competitor_shop_view.xml",
                "views/wayfair_product_view.xml",
                "views/manomano_shops_view.xml",
                "views/manomano_view.xml",
                "views/check_view.xml",
                "views/check_product_view.xml",
                "views/amazon_shop_view.xml",
                "views/mirakl_shop_view.xml",
                "views/mirakl_product_view.xml",
                "views/cdiscount_product_view.xml",
                "views/cdiscount_shop_view.xml",
                "views/product_sales_view.xml",
                "views/standard_price_view.xml",
                "views/cron.xml"
            ],
    'application': True,
    'installable': True,
    'license': 'LGPL-3',
}