# models/product_template.py
from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    installments_allowed = fields.Boolean(
        string="Installments Allowed",
        help="If enabled, sales order lines for this product will show installment fields."
    )
    installment_number = fields.Integer(string="No. of Installments")
    first_payment = fields.Float(string="First Payment")
    installment_amount = fields.Float(string="Installment Amount")
