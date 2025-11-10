from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging


class AccountMove(models.Model):
    _inherit = "account.move"

    sale_order_line_id = fields.Many2one('sale.order.line', string=_("Sale Order Line"))

    installment_num = fields.Float(
        string=_("Installments"), default=0.0, readonly=True
    )
    first_payment = fields.Float(
        string=_("First Payment"), default=0.0, readonly=True
    )


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    # installment_num = fields.Float(string="Installments", readonly=True)
    # first_payment = fields.Float(string="First Payment", readonly=True)
