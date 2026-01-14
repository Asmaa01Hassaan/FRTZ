{
    "name": "Frtz Customer",
    "version": "18.0.1.0.0",
    "summary": "Enhanced customer management with guarantees functionality",
    "author": "Your Company",
    # Add 'account' so partner actions like open_customer_statement are available
    "depends": ['base','sale','account'],
    "data": [
        "security/ir.model.access.csv",
        "views/customer_view.xml",
        "views/customer_guarantees_view.xml",
        "views/sale_order_view.xml",
    ],
    "i18n": [
        "i18n/ar.po",
        "i18n/frtz_customer.pot",
    ],
    "license": "LGPL-3",
    "application": False,
}
