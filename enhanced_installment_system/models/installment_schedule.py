# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class InstallmentSchedule(models.Model):
    _name = 'installment.schedule'
    _description = 'Installment Payment Schedule'
    _order = 'create_date desc'
    _rec_name = 'name'

    # Basic Information
    name = fields.Char(string='Schedule Name', required=True)
    sequence = fields.Integer(string='Sequence', default=1, help="Sequence for ordering")
    invoice_id = fields.Many2one('account.move', string='Invoice', required=True, ondelete='cascade')
    partner_id = fields.Many2one('res.partner', string='Customer', related='invoice_id.partner_id', store=True)
    
    # Schedule Details
    total_amount = fields.Monetary(string='Total Amount', currency_field='currency_id', required=True)
    currency_id = fields.Many2one('res.currency', string='Currency', compute='_compute_currency_id', store=True, readonly=True)
    
    @api.depends('invoice_id.currency_id')
    def _compute_currency_id(self):
        for schedule in self:
            schedule.currency_id = schedule.invoice_id.currency_id if schedule.invoice_id else False
    
    @api.model
    def create(self, vals):
        # Ensure currency_id is set during creation
        if 'invoice_id' in vals and not vals.get('currency_id'):
            invoice = self.env['account.move'].browse(vals['invoice_id'])
            vals['currency_id'] = invoice.currency_id.id
        return super().create(vals)
    installment_count = fields.Integer(string='Number of Installments', required=True)
    payment_frequency = fields.Selection([
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('custom', 'Custom Interval')
    ], string='Payment Frequency', default='monthly', required=True)
    
    # Status and Tracking
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True)
    
    # Payment Information
    installment_payment_ids = fields.One2many('installment.payment', 'installment_schedule_id', string='Installment Payments')
    paid_amount = fields.Monetary(string='Paid Amount', currency_field='currency_id', compute='_compute_paid_amount', store=True)
    remaining_amount = fields.Monetary(string='Remaining Amount', currency_field='currency_id', compute='_compute_remaining_amount', store=True)
    
    # Computed Fields
    paid_count = fields.Integer(string='Paid Payments', compute='_compute_payment_counts', store=True)
    pending_count = fields.Integer(string='Pending Payments', compute='_compute_payment_counts', store=True)
    overdue_count = fields.Integer(string='Overdue Payments', compute='_compute_payment_counts', store=True)
    
    @api.depends('installment_payment_ids.state', 'installment_payment_ids.amount')
    def _compute_paid_amount(self):
        for schedule in self:
            paid_payments = schedule.installment_payment_ids.filtered(lambda p: p.state == 'paid')
            schedule.paid_amount = sum(paid_payments.mapped('amount'))
    
    @api.depends('total_amount', 'paid_amount')
    def _compute_remaining_amount(self):
        for schedule in self:
            schedule.remaining_amount = schedule.total_amount - schedule.paid_amount
    
    @api.depends('installment_payment_ids.state')
    def _compute_payment_counts(self):
        for schedule in self:
            schedule.paid_count = len(schedule.installment_payment_ids.filtered(lambda p: p.state == 'paid'))
            schedule.pending_count = len(schedule.installment_payment_ids.filtered(lambda p: p.state == 'pending'))
            schedule.overdue_count = len(schedule.installment_payment_ids.filtered(lambda p: p.state == 'overdue'))
    
    def action_activate(self):
        """Activate the payment schedule"""
        self.ensure_one()
        if not self.installment_payment_ids:
            raise UserError(_("No installment payments found. Please generate payments first."))
        
        self.state = 'active'
    
    def action_complete(self):
        """Mark schedule as completed"""
        self.ensure_one()
        if self.remaining_amount > 0:
            raise UserError(_("Cannot complete schedule with remaining payments"))
        
        self.state = 'completed'
    
    def action_cancel(self):
        """Cancel the payment schedule"""
        self.ensure_one()
        if self.state == 'completed':
            raise UserError(_("Cannot cancel completed schedule"))
        
        self.state = 'cancelled'
        self.installment_payment_ids.filtered(lambda p: p.state == 'pending').action_cancel()
    
    def action_generate_payments(self):
        """Generate individual payment records"""
        self.ensure_one()
        if self.installment_payment_ids:
            raise UserError(_("Payments already generated"))
        
        # This will be implemented in the wizard
        pass
