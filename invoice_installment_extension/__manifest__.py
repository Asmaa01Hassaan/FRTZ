# -*- coding: utf-8 -*-
{
    'name': 'Invoice Installment Extension',
    'summary': 'Enhanced invoice management with installment support and auto payment terms',
    'description': """
        This module extends invoice functionality with:
        - Installment fields (installment_num, first_payment) in invoices
        - Auto-generation of payment terms based on installment_num
        - Integration with sale order installment data
        - Enhanced invoice management for installment-based sales
        - Automatic payment term creation for regular installments
    """,
    'version': '18.0.1.0.0',
    'category': 'Accounting/Invoicing',
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'depends': [
        'base',
        'account',
        'sale',
        'account_invoice_installments',
        'pricelist_expression',
        'sale_invoice_per_line'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/account_move_views.xml',
        # 'views/account_payment_term_views.xml',
    ],
    'i18n': [
        'i18n/ar.po',
        'i18n/invoice_installment_extension.pot',
    ],
    'demo': [],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
