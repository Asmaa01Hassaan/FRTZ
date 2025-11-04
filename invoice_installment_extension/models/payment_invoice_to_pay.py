# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class PaymentInvoiceToPay(models.Model):
    """Intermediate model to store to_pay_amount per invoice per payment"""
    _name = 'payment.invoice.to.pay'
    _description = 'Payment Invoice To Pay'
    _rec_name = 'display_name'
    
    payment_id = fields.Many2one(
        'account.payment',
        string='Payment',
        required=True,
        ondelete='cascade',
        index=True
    )
    
    invoice_id = fields.Many2one(
        'account.move',
        string='Invoice',
        required=True,
        ondelete='cascade',
        index=True,
        domain="[('move_type', '=', 'out_invoice'), ('state', '=', 'posted'), ('payment_state', '!=', 'paid')]"
    )
    
    # Invoice fields to display
    invoice_name = fields.Char(
        string='Transion',
        related='invoice_id.name',
        readonly=True,
        store=True
    )
    
    invoice_date = fields.Date(
        string='Transion Date',
        related='invoice_id.invoice_date',
        readonly=True,
        store=True
    )
    
    amount_total = fields.Monetary(
        string='Total Amount',
        currency_field='currency_id',
        related='invoice_id.amount_total',
        readonly=True,
        store=True
    )
    
    total_remaining_amount = fields.Monetary(
        string='Remaining Amount',
        currency_field='currency_id',
        related='invoice_id.total_remaining_amount',
        readonly=True,
        store=True
    )
    
    to_pay_amount = fields.Monetary(
        string='To Pay Amount',
        currency_field='currency_id',
        default=0.0,
        help='Amount to pay for this invoice from the payment amount'
    )
    
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        related='payment_id.currency_id',
        store=True,
        readonly=True
    )
    
    due_date_filter = fields.Date(
        string='Date for Pay',
        help='Date filter for calculating due amount on invoice'
    )
    
    due_amount = fields.Monetary(
        string='Due Amount',
        currency_field='currency_id',
        compute='_compute_due_amount',
        readonly=True,
        help='Due amount on the invoice based on date filter'
    )
    
    has_partial_payment = fields.Boolean(
        string='Has Partial Payment',
        compute='_compute_has_partial_payment',
        store=True,
        help='Indicates if this invoice has partial payment (to_pay_amount > 0 but < total_remaining_amount)'
    )
    
    @api.depends('to_pay_amount', 'total_remaining_amount')
    def _compute_has_partial_payment(self):
        """Compute if invoice has partial payment"""
        for record in self:
            record.has_partial_payment = (
                record.to_pay_amount > 0 and 
                record.total_remaining_amount > 0 and
                record.to_pay_amount < record.total_remaining_amount
            )
    
    @api.onchange('due_date_filter', 'invoice_id')
    def _onchange_due_date_filter(self):
        """Update invoice due_date_filter and recompute due_amount"""
        if not self.invoice_id:
            return
        if self.due_date_filter:
            # Update invoice's due_date_filter to trigger recomputation
            self.invoice_id.due_date_filter = self.due_date_filter
            self.invoice_id._compute_due_amount()
            self._compute_due_amount()
    
    @api.onchange('to_pay_amount')
    def _onchange_to_pay_amount(self):
        """Trigger recomputation when to_pay_amount changes"""
        if self.payment_id:
            # Trigger recomputation on the payment
            self.payment_id._compute_total_invoice_to_pay()
    
    @api.onchange('invoice_id')
    def _onchange_invoice_id(self):
        """Update related fields when invoice is selected"""
        if self.invoice_id:
            # Sync due_date_filter from payment if available
            if self.payment_id and self.payment_id.payment_due_date_filter:
                self.due_date_filter = self.payment_id.payment_due_date_filter
            elif self.invoice_id.due_date_filter:
                self.due_date_filter = self.invoice_id.due_date_filter
            # Trigger recomputation
            self._compute_due_amount()
    
    @api.depends('invoice_id', 'due_date_filter', 'invoice_id.due_amount')
    def _compute_due_amount(self):
        """Compute due_amount based on invoice and date filter"""
        for record in self:
            if not record.invoice_id:
                record.due_amount = 0.0
                continue
            if record.due_date_filter:
                # Update invoice's due_date_filter first if different
                if record.invoice_id.due_date_filter != record.due_date_filter:
                    record.invoice_id.due_date_filter = record.due_date_filter
                    record.invoice_id._compute_due_amount()
                record.due_amount = record.invoice_id.due_amount
            else:
                record.due_amount = 0.0
    
    @api.model
    def create(self, vals):
        """Override create to ensure invoice_id is set"""
        if not vals.get('invoice_id'):
            raise UserError(_("Invoice is required. Please select an invoice."))
        return super().create(vals)
    
    def write(self, vals):
        """Override write to trigger recomputation on payment when to_pay_amount changes"""
        # Validate invoice_id if being cleared
        if 'invoice_id' in vals and not vals.get('invoice_id'):
            raise UserError(_("Invoice is required. Cannot remove invoice from payment line."))
        
        result = super().write(vals)
        if 'to_pay_amount' in vals:
            # Trigger recomputation of total on all related payments
            for record in self:
                if record.payment_id:
                    record.payment_id._compute_total_invoice_to_pay()
        return result
    
    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
        store=True
    )
    
    @api.depends('invoice_id.name', 'payment_id.name', 'to_pay_amount')
    def _compute_display_name(self):
        for record in self:
            if record.invoice_id and record.payment_id:
                record.display_name = f"{record.payment_id.name} - {record.invoice_id.name} - {record.to_pay_amount}"
            else:
                record.display_name = _('New')
    
    _sql_constraints = [
        ('unique_payment_invoice', 'unique(payment_id, invoice_id)', 
         'Each invoice can only have one to_pay_amount record per payment!'),
    ]

