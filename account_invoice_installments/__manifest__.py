{
    "name": "Invoice Installments",
    "version": "18.0.1.0.0",
    "summary": "Enhanced sale orders with payment plans and order types",
    "description": """
        This module enhances sale orders with:
        - Payment plan types (immediate, regular, irregular installments)
        - Order type classification (standard, custom, wholesale, subscription)
        - Automatic sequence generation based on order type
        - Improved order management and tracking
    """,
    "author": "Your Company",
    "depends": ['sale', 'product'],
    "data": [
        "data/ir_sequence.xml",
        "views/menu_views.xml",
        "views/sales_orders_view.xml",
    ],
    "i18n": [
        "i18n/ar.po",
        "i18n/account_invoice_installments.pot",
    ],
    "license": "LGPL-3",
    "application": False,
    "installable": True,
    "auto_install": False,
}
