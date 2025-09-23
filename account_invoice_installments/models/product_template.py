# models/product_template.py
from odoo import models, fields, api

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    installments_allowed = fields.Boolean(
        string="Installments Allowed",
        help="If enabled, sales order lines for this product will show installment fields."
    )
    installment_number = fields.Integer(string="No. of Installments")
    first_payment = fields.Float(string="First Payment")
    installment_amount = fields.Float(string="Installment Amount")

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    # mirror the product’s flag to control visibility in the view
    installments_allowed = fields.Boolean(
        related='product_id.product_tmpl_id.installments_allowed',
        store=False
    )

    installment_number = fields.Integer(string="No. of Installments")
    first_payment = fields.Float(string="First Payment")
    installment_amount = fields.Float(string="Installment Amount")

