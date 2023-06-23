{
    'name': 'SKU Expense Analysis',
    'version': '1.0',
    'summary': 'SKU Expense Analysis using Sale Order',
    'description': 'Here in this model we will need to Analyze per SKU Expense using the sale order data',
    'depends': ["odoo_mirakl_integration","manomano_connector"],
    'data': [
        'views/expense.xml',
        'views/expense_analysis_view.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,    
    'application': True,
    'license': 'LGPL-3',
    
}