# -*- coding: utf-8 -*-
{
    "name": "Advance Product Installment Buying",
    "author": "Botspot Infoware Pvt. Ltd.",
    "category": "Sales",
    "summary": """This module adds a new feature to invoice installment, In configuration by enabling the feature advance installment common installment invoices will be merged.""",
    "website": "https://www.botspotinfoware.com",
    "description": """This module adds a new feature to invoice installment, In configuration by enabling the feature advance installment common installment invoices will be merged.""",
    "version": "18.1",
    "depends": ["base", "sale_management", "bsi_product_installment_buying"],
    "data": [
        "reports/adv_product_installment_buying_report.xml",
        "reports/report_adv_product_installment_buying_document.xml",
        "wizard/sale_advance_payment_inv.xml",
        "views/sale_view.xml",
    ],
    "images": ["static/description/Banner.gif"],
    "license": "OPL-1",
    "price": 21.00,
    "currency": "USD",
    "installable": True,
    "application": True,
    "auto_install": False,
}
