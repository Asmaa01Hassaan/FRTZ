# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ControlPayment(models.Model):
    """Control Payment model to manage invoice payments"""
    _name = 'control.payment'
    _description = 'Control Payment'
    _rec_name = 'display_name'
    _order = 'invoice_date desc, id desc'

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
        index=True
    )
    
    # Related fields from invoice
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
    
    due_amount = fields.Monetary(
        string='Due Amount',
        currency_field='currency_id',
        compute='_compute_due_amount',
        readonly=True,
        help='Due amount on the invoice (computed from invoice)'
    )
    
    @api.depends('invoice_id', 'invoice_id.due_amount', 'due_date')
    def _compute_due_amount(self):
        """Compute due_amount from invoice, updating invoice's due_date_filter if needed"""
        for record in self:
            if not record.invoice_id:
                record.due_amount = 0.0
                continue
            
            # If due_date is set, update invoice's due_date_filter to trigger recomputation
            if record.due_date and record.invoice_id.due_date_filter != record.due_date:
                record.invoice_id.due_date_filter = record.due_date
                record.invoice_id._compute_due_amount()
            
            record.due_amount = record.invoice_id.due_amount or 0.0
    
    @api.onchange('due_date', 'invoice_id')
    def _onchange_due_date(self):
        """Update invoice due_date_filter when due_date changes"""
        if self.invoice_id and self.due_date:
            self.invoice_id.due_date_filter = self.due_date
            self.invoice_id._compute_due_amount()
            self._compute_due_amount()
    
    @api.onchange('to_pay')
    def _onchange_to_pay(self):
        """Trigger recomputation of total_control_to_pay on payment"""
        if self.payment_id:
            self.payment_id._compute_total_control_to_pay()
    
    # Date filter field
    due_date = fields.Date(
        string='Due Date',
        help='Date filter for calculating due amount on invoice'
    )
    
    # Non-related field
    to_pay = fields.Monetary(
        string='To Pay',
        currency_field='currency_id',
        default=0.0,
        help='Amount to pay for this invoice'
    )
    
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        related='payment_id.currency_id',
        store=True,
        readonly=True
    )
    
    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
        store=True
    )
    
    @api.depends('invoice_id.name', 'payment_id.name', 'to_pay')
    def _compute_display_name(self):
        for record in self:
            if record.invoice_id and record.payment_id:
                record.display_name = f"{record.payment_id.name} - {record.invoice_id.name} - {record.to_pay}"
            else:
                record.display_name = _('New')
    
    def write(self, vals):
        """Override write to trigger recomputation of total_control_to_pay"""
        result = super().write(vals)
        if 'to_pay' in vals:
            for record in self:
                if record.payment_id:
                    record.payment_id._compute_total_control_to_pay()
        return result
    
    _sql_constraints = [
        ('unique_payment_invoice', 'unique(payment_id, invoice_id)', 
         'Each invoice can only have one control payment record per payment!'),
    ]

