# -*- coding: utf-8 -*-
{
    "name": "Product Installment Buying",
    "author": "Botspot Infoware Pvt. Ltd.",
    "category": "Sales/Sales",
    "summary": """Sell products with installments and generate seperate
                  invoices with installment amount based on installment
                  months""",
    "website": "https://www.botspotinfoware.com",
    "description": """This Module adds a new feature to the products and allows
                      them to have an installment option. Also, includes a
                      'Create Invoice' button that creates separate invoices
                      for orders with instalment options and orders without
                      instalment options. In addition, for products with an
                      installment option, different invoices are generated
                      based on the months of installment, with each invoice
                      containing the installment amount and subtotal as per
                      the requirement.""",
    "version": "17.3",
    "depends": ["base", "sale_management"],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/installment_config.xml",
        "views/product_template_view.xml",
        "views/sale_view.xml",
    ],
    "images": ["static/description/Banner.gif"],
    "license": "OPL-1",
    "price": 29.00,
    "currency": "USD",
    "installable": True,
    "application": True,
    "auto_install": False,
}
