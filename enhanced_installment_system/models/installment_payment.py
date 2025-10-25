# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)


class InstallmentPayment(models.Model):
    _name = 'installment.payment'
    _description = 'Individual Installment Payment'
    _order = 'due_date, sequence'
    _rec_name = 'display_name'

    # Basic Information
    name = fields.Char(string='Payment Reference', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    sequence = fields.Integer(string='Sequence', default=1, help="Payment sequence number")
    installment_schedule_id = fields.Many2one('installment.schedule', string='Payment Schedule', required=True, ondelete='cascade')
    
    # Payment Details
    amount = fields.Monetary(string='Amount', currency_field='currency_id', required=True)
    currency_id = fields.Many2one('res.currency', string='Currency', compute='_compute_currency_id', store=True, readonly=True)
    
    @api.depends('installment_schedule_id.currency_id')
    def _compute_currency_id(self):
        for payment in self:
            payment.currency_id = payment.installment_schedule_id.currency_id if payment.installment_schedule_id else False
    
    due_date = fields.Date(string='Due Date', required=True)
    paid_date = fields.Date(string='Paid Date', readonly=True)
    
    # Status and Tracking
    state = fields.Selection([
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
        ('adjusted', 'Adjusted')
    ], string='Status', default='pending', tracking=True)
    
    # Payment Information
    payment_method_id = fields.Many2one('account.payment.method', string='Payment Method')
    payment_reference = fields.Char(string='Payment Reference')
    notes = fields.Text(string='Notes')
    
    # Late Payment Management
    is_late = fields.Boolean(string='Is Late Payment', compute='_compute_is_late', store=True)
    days_overdue = fields.Integer(string='Days Overdue', compute='_compute_days_overdue')
    late_fee = fields.Monetary(string='Late Fee', currency_field='currency_id', default=0.0)
    interest_rate = fields.Float(string='Interest Rate (%)', default=0.0, help="Annual interest rate for late payments")
    interest_amount = fields.Monetary(string='Interest Amount', currency_field='currency_id', compute='_compute_interest_amount', store=True)
    
    # Computed Fields
    display_name = fields.Char(string='Display Name', compute='_compute_display_name', store=True)
    total_amount = fields.Monetary(string='Total Amount', currency_field='currency_id', compute='_compute_total_amount', store=True)
    
    # Related Information
    partner_id = fields.Many2one('res.partner', string='Customer', related='installment_schedule_id.partner_id', store=True)
    invoice_id = fields.Many2one('account.move', string='Invoice', related='installment_schedule_id.invoice_id', store=True)
    
    @api.depends('amount', 'late_fee', 'interest_amount')
    def _compute_total_amount(self):
        for payment in self:
            payment.total_amount = payment.amount + payment.late_fee + payment.interest_amount
    
    @api.depends('due_date', 'state')
    def _compute_is_late(self):
        today = fields.Date.today()
        for payment in self:
            payment.is_late = (payment.state == 'pending' and 
                             payment.due_date and 
                             payment.due_date < today)
    
    @api.depends('due_date', 'state')
    def _compute_days_overdue(self):
        today = fields.Date.today()
        for payment in self:
            if (payment.state == 'pending' and 
                payment.due_date and 
                payment.due_date < today):
                payment.days_overdue = (today - payment.due_date).days
            else:
                payment.days_overdue = 0
    
    @api.depends('amount', 'interest_rate', 'days_overdue')
    def _compute_interest_amount(self):
        for payment in self:
            if payment.interest_rate > 0 and payment.days_overdue > 0:
                # Calculate daily interest rate
                daily_rate = payment.interest_rate / 365 / 100
                payment.interest_amount = payment.amount * daily_rate * payment.days_overdue
            else:
                payment.interest_amount = 0.0
    
    @api.depends('sequence', 'amount', 'due_date')
    def _compute_display_name(self):
        for payment in self:
            payment.display_name = f"Payment {payment.sequence} - {payment.amount:,.2f} - {payment.due_date}"
    
    @api.model
    def create(self, vals):
        # Ensure currency_id is set during creation
        if 'installment_schedule_id' in vals and not vals.get('currency_id'):
            schedule = self.env['installment.schedule'].browse(vals['installment_schedule_id'])
            if schedule.currency_id:
                vals['currency_id'] = schedule.currency_id.id
        
        # Set sequence name
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('installment.payment') or _('New')
        return super().create(vals)
    
    def action_mark_paid(self):
        """Mark payment as paid"""
        self.ensure_one()
        if self.state != 'pending':
            raise UserError(_("Only pending payments can be marked as paid"))
        
        self.write({
            'state': 'paid',
            'paid_date': fields.Date.today(),
        })
        
        # Check if all payments are paid
        if all(p.state == 'paid' for p in self.installment_schedule_id.installment_payment_ids):
            self.installment_schedule_id.state = 'completed'
    
    def action_mark_overdue(self):
        """Mark payment as overdue"""
        self.ensure_one()
        if self.state != 'pending':
            raise UserError(_("Only pending payments can be marked as overdue"))
        
        self.state = 'overdue'
    
    def action_cancel(self):
        """Cancel payment"""
        self.ensure_one()
        if self.state == 'paid':
            raise UserError(_("Paid payments cannot be cancelled"))
        
        self.state = 'cancelled'
    
    def action_adjust(self):
        """Open adjustment wizard"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Adjust Payment'),
            'res_model': 'installment.payment.adjustment.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_installment_payment_id': self.id,
                'default_original_amount': self.amount,
                'default_original_due_date': self.due_date,
            }
        }
    
    @api.model
    def _cron_check_overdue_payments(self):
        """Cron job to check for overdue payments"""
        today = fields.Date.today()
        overdue_payments = self.search([
            ('state', '=', 'pending'),
            ('due_date', '<', today)
        ])
        
        for payment in overdue_payments:
            payment.action_mark_overdue()
            _logger.info(f"Payment {payment.name} marked as overdue")
    
    @api.model
    def _cron_send_payment_reminders(self):
        """Cron job to send payment reminders"""
        # Send reminders 7 days before due date
        reminder_date = fields.Date.today() + timedelta(days=7)
        payments_to_remind = self.search([
            ('state', '=', 'pending'),
            ('due_date', '=', reminder_date)
        ])
        
        for payment in payments_to_remind:
            # Send reminder email
            payment._send_payment_reminder()
    
    def _send_payment_reminder(self):
        """Send payment reminder email"""
        self.ensure_one()
        if not self.partner_id.email:
            return
        
        # Email template will be implemented in future version
        _logger.info(f"Payment reminder would be sent for {self.name} to {self.partner_id.email}")

