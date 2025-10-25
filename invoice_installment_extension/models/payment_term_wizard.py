# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class PaymentTermGenerationWizard(models.TransientModel):
    _name = 'payment.term.generation.wizard'
    _description = 'Payment Term Generation Wizard'

    invoice_id = fields.Many2one(
        'account.move',
        string="Invoice",
        required=True,
        readonly=True
    )
    installment_num = fields.Float(
        string="Number of Installments",
        required=True,
        help="Total number of installments"
    )
    first_payment_type = fields.Selection([
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount')
    ], string="First Payment Type", default='percentage', required=True)
    
    first_payment_percentage = fields.Float(
        string="First Payment Percentage",
        default=0.0,
        help="Percentage of total amount for first payment"
    )
    first_payment_amount = fields.Monetary(
        string="First Payment Amount",
        default=0.0,
        help="Fixed amount for first payment"
    )
    currency_id = fields.Many2one(
        'res.currency',
        string="Currency",
        related='invoice_id.currency_id',
        readonly=True
    )
    total_amount = fields.Monetary(
        string="Total Amount",
        related='invoice_id.amount_total',
        readonly=True
    )
    payment_interval = fields.Integer(
        string="Payment Interval (Days)",
        default=30,
        help="Days between payments"
    )
    
    @api.model
    def default_get(self, fields_list):
        """Set default values from invoice"""
        res = super().default_get(fields_list)
        if 'invoice_id' in self.env.context:
            invoice = self.env['account.move'].browse(self.env.context['invoice_id'])
            res.update({
                'invoice_id': invoice.id,
                'installment_num': invoice.installment_num or 0,
                'first_payment_amount': invoice.first_payment or 0,
                'first_payment_percentage': (invoice.first_payment / invoice.amount_total * 100) if invoice.amount_total > 0 else 0,
            })
        return res

    @api.onchange('first_payment_type', 'first_payment_percentage', 'first_payment_amount', 'total_amount')
    def _onchange_payment_calculation(self):
        """Calculate percentage/amount based on type"""
        if self.first_payment_type == 'percentage' and self.total_amount > 0:
            self.first_payment_amount = (self.first_payment_percentage / 100) * self.total_amount
        elif self.first_payment_type == 'fixed' and self.total_amount > 0:
            self.first_payment_percentage = (self.first_payment_amount / self.total_amount) * 100

    def action_generate_payment_term(self):
        """Generate payment term based on wizard settings"""
        self.ensure_one()
        
        if self.installment_num <= 0:
            raise UserError(_("Number of installments must be greater than 0"))
        
        if self.first_payment_type == 'percentage' and (self.first_payment_percentage < 0 or self.first_payment_percentage > 100):
            raise UserError(_("First payment percentage must be between 0 and 100"))
        
        if self.first_payment_type == 'fixed' and self.first_payment_amount < 0:
            raise UserError(_("First payment amount cannot be negative"))
        
        try:
            # Create payment term
            payment_term = self.env['account.payment.term'].create_installment_term(
                installment_num=self.installment_num,
                first_payment=self.first_payment_amount,
                total_amount=self.total_amount,
                payment_interval=self.payment_interval
            )
            
            if payment_term:
                # Assign to invoice
                self.invoice_id.invoice_payment_term_id = payment_term.id
                
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Success'),
                        'message': _('Payment term "%s" has been generated and assigned to the invoice.') % payment_term.name,
                        'type': 'success',
                        'sticky': False,
                    }
                }
            else:
                raise UserError(_("Failed to generate payment term"))
                
        except Exception as e:
            _logger.error(f"Error generating payment term: {e}")
            raise UserError(_("Error generating payment term: %s") % str(e))

