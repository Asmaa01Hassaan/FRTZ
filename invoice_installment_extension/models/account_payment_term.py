# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class AccountPaymentTerm(models.Model):
    _inherit = 'account.payment.term'

    is_installment_term = fields.Boolean(
        string="Is Installment Payment Term",
        default=False,
        help="Indicates if this payment term is for installments"
    )
    installment_count = fields.Integer(
        string="Number of Installments",
        default=0,
        help="Number of installments for this payment term"
    )
    first_payment_percentage = fields.Float(
        string="First Payment Percentage",
        default=0.0,
        help="Percentage of first payment"
    )

    @api.model
    def create_installment_term(self, installment_num, first_payment=0, total_amount=0):
        """Create a payment term for installments"""
        try:
            payment_term_lines = []

            # First payment (if specified)
            if first_payment > 0 and total_amount > 0:
                first_payment_percentage = (first_payment / total_amount) * 100
                payment_term_lines.append({
                    'value': 'percent',
                    'value_amount': first_payment_percentage,
                    'days': 0,
                    'option': 'day_after_invoice_date',
                })

            # Regular installments
            remaining_amount = total_amount - first_payment
            remaining_installments = installment_num - (1 if first_payment > 0 else 0)

            if remaining_installments > 0:
                installment_amount = remaining_amount / remaining_installments
                installment_percentage = (installment_amount / total_amount) * 100

                for i in range(int(remaining_installments)):
                    payment_term_lines.append({
                        'value': 'percent',
                        'value_amount': installment_percentage,
                        'days': (i + 1) * 30,  # 30 days between installments
                        'option': 'day_after_invoice_date',
                    })

            # Create payment term
            payment_term = self.create({
                'name': f'Installment Terms ({installment_num} installments)',
                'is_installment_term': True,
                'installment_count': int(installment_num),
                'first_payment_percentage': (first_payment / total_amount) * 100 if total_amount > 0 else 0,
                'line_ids': [(0, 0, line) for line in payment_term_lines]
            })

            _logger.info(f"Created installment payment term with {len(payment_term_lines)} lines")
            return payment_term

        except Exception as e:
            _logger.error(f"Error creating installment payment term: {e}")
            return False

    def _compute_installment_info(self):
        """Compute installment information from payment term lines"""
        for term in self:
            if term.is_installment_term:
                term.installment_count = len(term.line_ids)
                if term.line_ids:
                    first_line = term.line_ids[0]
                    if first_line.days == 0:
                        term.first_payment_percentage = first_line.value_amount
                    else:
                        term.first_payment_percentage = 0
                else:
                    term.first_payment_percentage = 0
