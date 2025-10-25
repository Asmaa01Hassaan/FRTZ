# -*- coding: utf-8 -*-
{
    'name': 'Enhanced Installment Management System',
    'version': '18.0.1.0.0',
    'category': 'Sales/Installments',
    'summary': 'Advanced installment management with payment tracking, reminders, and analytics',
    'description': """
        Enhanced Installment Management System
        =====================================
        
        This module provides a comprehensive installment management solution with:
        
        * **Smart Payment Term Generation**: Visual wizard with payment schedule preview
        * **Individual Installment Tracking**: Each payment as separate record
        * **Payment Status Management**: Track paid, pending, overdue installments
        * **Automated Reminders**: Email/SMS notifications for due payments
        * **Payment Adjustments**: Modify future installments
        * **Payment Analytics**: Reports and dashboards
        * **Payment Plan Templates**: Reusable payment configurations
        * **Multi-Currency Support**: Handle different currencies
        * **Customer Preferences**: Remember customer payment preferences
        
        Features:
        ---------
        * Visual payment schedule with drag-and-drop adjustments
        * Flexible first payment options (percentage, fixed, custom)
        * Multiple payment frequencies (monthly, quarterly, custom)
        * Payment method integration
        * Late payment penalties and interest
        * Early payment discounts
        * Payment history and audit trail
        * Customer payment preferences
        * Payment analytics and reporting
    """,
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'depends': [
        'base',
        'account',
        'sale',
        'account_invoice_installments',
        'pricelist_expression',
        'sale_invoice_per_line',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/installment_data.xml',
        'views/installment_views.xml',
        'views/installment_wizard_views.xml',
        'views/payment_adjustment_wizard_views.xml',
        'views/account_move_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
    'license': 'LGPL-3',
}
