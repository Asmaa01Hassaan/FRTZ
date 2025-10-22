# -*- coding: utf-8 -*-
{
    'name': "Sale Invoice Per Line",
    'summary': "Generate separate invoices for each order line",
    'description': """
        This module enhances sale order invoicing with:
        - Per-line invoice generation option
        - Separate invoice for each order line
        - Flexible invoice creation workflow
        - Integration with installment and pricing modules
        - Enhanced error handling and logging
    """,
    'author': "Your Company",
    'website': "https://www.yourcompany.com",
    'category': 'Sales',
    'version': '18.0.1.0.0',
    'depends': ['base', 'sale', 'account', 'pricelist_expression', 'account_invoice_installments'],
    'data': [
        'views/sale_order_view_invoice_per_line.xml',
        'views/account_move.xml',
    ],
    'i18n': [
        'i18n/ar.po',
        'i18n/sale_invoice_per_line.pot',
    ],
    'demo': [
        'demo/demo.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}

