# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class PaymentRecords(models.Model):
    """Payment Records model to track installment state changes and payment information"""
    _name = 'payment.records'
    _description = 'Payment Records'
    _rec_name = 'display_name'
    _order = 'payment_date desc, create_date desc'

    # Basic Information
    name = fields.Char(string=_('Payment Record Reference'), required=True, copy=False, readonly=True, default=lambda self: _('New'))
    payment_id = fields.Many2one(
        'account.payment',
        string=_('Payment'),
        ondelete='set null',
        index=True,
        help=_('The payment that triggered this record')
    )
    payment_name = fields.Char(
        string=_('Payment Name'),
        related='payment_id.name',
        readonly=True,
        store=True
    )
    payment_date = fields.Date(
        string=_('Payment Date'),
        related='payment_id.date',
        readonly=True,
        store=True
    )
    
    # Invoice Information
    invoice_id = fields.Many2one(
        'account.move',
        string=_('Invoice'),
        required=True,
        ondelete='cascade',
        index=True,
        help=_('The invoice this payment record is related to')
    )
    invoice_name = fields.Char(
        string=_('Invoice Name'),
        related='invoice_id.name',
        readonly=True,
        store=True
    )
    
    # Installment Information
    installment_id = fields.Many2one(
        'installment.list',
        string=_('Installment'),
        required=True,
        ondelete='cascade',
        index=True,
        help=_('The installment this payment record is related to')
    )
    installment_name = fields.Char(
        string=_('Installment Reference'),
        related='installment_id.name',
        readonly=True,
        store=True
    )
    installment_amount = fields.Monetary(
        string=_('Installment Amount'),
        currency_field='currency_id',
        related='installment_id.amount',
        readonly=True,
        store=True
    )
    installment_due_date = fields.Date(
        string=_('Installment Due Date'),
        related='installment_id.due_date',
        readonly=True,
        store=True
    )
    
    # Payment Details
    paid_amount = fields.Monetary(
        string=_('Paid Amount'),
        currency_field='currency_id',
        required=True,
        help=_('Amount paid for this installment in this payment record')
    )
    previous_state = fields.Selection([
        ('pending', _('Pending')),
        ('partial_paid', _('Partial Paid')),
        ('paid', _('Paid')),
        ('overdue', _('Overdue')),
        ('cancelled', _('Cancelled'))
    ], string=_('Previous State'), readonly=True, help=_('Installment state before this payment'))
    
    new_state = fields.Selection([
        ('pending', _('Pending')),
        ('partial_paid', _('Partial Paid')),
        ('paid', _('Paid')),
        ('overdue', _('Overdue')),
        ('cancelled', _('Cancelled'))
    ], string=_('New State'), readonly=True, help=_('Installment state after this payment'))
    
    # Action Information
    action_type = fields.Char(
        string=_('Action Type'),
        readonly=True,
        help=_('Type of action that triggered this record (e.g., action_pay_installments, action_mark_paid)')
    )
    
    # Additional Information
    currency_id = fields.Many2one(
        'res.currency',
        string=_('Currency'),
        related='invoice_id.currency_id',
        store=True,
        readonly=True
    )
    
    notes = fields.Text(string=_('Notes'))
    
    # Computed Fields
    display_name = fields.Char(
        string=_('Display Name'),
        compute='_compute_display_name',
        store=True
    )
    
    @api.depends('payment_name', 'invoice_name', 'installment_name', 'paid_amount', 'create_date')
    def _compute_display_name(self):
        for record in self:
            parts = []
            if record.payment_name:
                parts.append(record.payment_name)
            if record.invoice_name:
                parts.append(record.invoice_name)
            if record.installment_name:
                parts.append(record.installment_name)
            if record.paid_amount:
                parts.append(f"{record.paid_amount:,.2f}")
            record.display_name = ' - '.join(parts) if parts else _('New Payment Record')
    
    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('payment.records') or _('New')
        return super().create(vals)
    
    @api.model
    def create_payment_record(self, installment, payment=None, paid_amount=0.0, previous_state=None, new_state=None, action_type=None):
        """Helper method to create a payment record"""
        if not installment:
            return False
        
        record_vals = {
            'installment_id': installment.id,
            'invoice_id': installment.invoice_id.id,
            'paid_amount': paid_amount,
            'previous_state': previous_state or installment.state,
            'new_state': new_state or installment.state,
            'action_type': action_type or 'manual',
        }
        
        if payment:
            record_vals['payment_id'] = payment.id
        
        return self.create(record_vals)


