# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    invoice_ids_with_pending_installments = fields.One2many(
        'account.move',
        compute='_compute_invoice_ids_with_pending_installments',
        string='Invoices with Pending Installments',
        help='Invoices for the selected customer that have pending installments',
        readonly=True,
    )
    
    selected_installment_invoice_ids = fields.Many2many(
        'account.move',
        'payment_installment_invoice_rel',
        'payment_id',
        'invoice_id',
        string='Selected Invoices',
        help='Selected invoices with pending installments',
        domain="[('id', 'in', invoice_ids_with_pending_installments)]",
    )
    
    total_selected_nearest_due_amount = fields.Monetary(
        string='Total Nearest Due Amount',
        currency_field='currency_id',
        compute='_compute_total_selected_nearest_due_amount',
        help='Sum of nearest due installment amounts from selected invoices',
    )
    
    payment_amount_after_nearest_due = fields.Monetary(
        string='Payment Amount After Nearest Due',
        currency_field='currency_id',
        compute='_compute_total_selected_nearest_due_amount',
        help='Payment amount minus sum of selected invoices nearest due installment amounts',
    )

    @api.depends('partner_id')
    def _compute_invoice_ids_with_pending_installments(self):
        """Compute invoices with pending installments for the selected partner"""
        for payment in self:
            if payment.partner_id and payment.partner_type == 'customer':
                # Get all customer invoices with pending installments
                invoices = self.env['account.move'].search([
                    ('partner_id', '=', payment.partner_id.id),
                    ('move_type', '=', 'out_invoice'),
                    ('state', '=', 'posted'),
                    ('pending_installment_count', '>', 0),
                ])
                payment.invoice_ids_with_pending_installments = invoices
            else:
                payment.invoice_ids_with_pending_installments = False

    def write(self, vals):
        """Override write to update memo when invoices are selected"""
        result = super().write(vals)
        
        # Update memo when selected invoices change
        if 'selected_installment_invoice_ids' in vals:
            for payment in self:
                if payment.selected_installment_invoice_ids:
                    invoice_names = ', '.join(payment.selected_installment_invoice_ids.mapped('name'))
                    payment.memo = invoice_names
                elif not payment.selected_installment_invoice_ids:
                    # Clear memo if no invoices selected (optional - you can remove this line if you want to keep memo)
                    pass
        
        return result

    @api.depends('selected_installment_invoice_ids', 'selected_installment_invoice_ids.nearest_due_installment_amount', 'amount')
    def _compute_total_selected_nearest_due_amount(self):
        """Compute sum of nearest due amounts from selected invoices"""
        for payment in self:
            if payment.selected_installment_invoice_ids:
                # Sum of nearest_due_installment_amount from selected invoices
                total_nearest_due = sum(payment.selected_installment_invoice_ids.mapped('nearest_due_installment_amount'))
                payment.total_selected_nearest_due_amount = total_nearest_due
                
                # Payment amount minus sum of nearest due amounts
                payment.payment_amount_after_nearest_due = payment.amount - total_nearest_due if payment.amount else 0.0
            else:
                payment.total_selected_nearest_due_amount = 0.0
                payment.payment_amount_after_nearest_due = payment.amount or 0.0

    @api.onchange('selected_installment_invoice_ids')
    def _onchange_selected_installment_invoice_ids(self):
        """Update memo field with selected invoice names"""
        if self.selected_installment_invoice_ids:
            invoice_names = ', '.join(self.selected_installment_invoice_ids.mapped('name'))
            # Set memo with selected invoice names
            self.memo = invoice_names

