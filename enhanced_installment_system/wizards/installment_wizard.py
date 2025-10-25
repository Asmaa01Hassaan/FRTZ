# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)


class InstallmentGenerationWizard(models.TransientModel):
    _name = 'installment.generation.wizard'
    _description = 'Installment Generation Wizard'

    # Invoice Information
    invoice_id = fields.Many2one('account.move', string='Invoice', required=True, readonly=True)
    partner_id = fields.Many2one('res.partner', string='Customer', related='invoice_id.partner_id', readonly=True)
    total_amount = fields.Monetary(string='Total Amount', currency_field='currency_id', related='invoice_id.amount_total', readonly=True)
    currency_id = fields.Many2one('res.currency', string='Currency', related='invoice_id.currency_id', readonly=True)
    
    # Installment Configuration
    installment_count = fields.Integer(string='Number of Installments', required=True, default=3)
    first_payment_type = fields.Selection([
        ('percentage', 'Percentage of Total'),
        ('fixed', 'Fixed Amount'),
        ('custom', 'Custom Amount')
    ], string='First Payment Type', default='percentage', required=True)
    
    first_payment_percentage = fields.Float(string='First Payment Percentage', default=20.0, help="Percentage of total amount")
    first_payment_amount = fields.Monetary(string='First Payment Amount', currency_field='currency_id', default=0.0)
    custom_first_payment = fields.Monetary(string='Custom First Payment', currency_field='currency_id', default=0.0)
    
    # Payment Schedule
    payment_frequency = fields.Selection([
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('custom', 'Custom Interval')
    ], string='Payment Frequency', default='monthly', required=True)
    
    custom_interval_days = fields.Integer(string='Custom Interval (Days)', default=30, help="Days between payments")
    start_date = fields.Date(string='Start Date', default=fields.Date.today, required=True)
    
    # Advanced Options
    late_fee_percentage = fields.Float(string='Late Fee Percentage', default=0.0, help="Percentage of payment amount")
    interest_rate = fields.Float(string='Interest Rate (%)', default=0.0, help="Annual interest rate for late payments")
    early_payment_discount = fields.Float(string='Early Payment Discount (%)', default=0.0, help="Discount for early payments")
    
    # Payment Schedule Preview
    payment_schedule_ids = fields.One2many('installment.schedule.preview', 'wizard_id', string='Payment Schedule Preview')
    
    @api.onchange('first_payment_type', 'first_payment_percentage', 'first_payment_amount', 'custom_first_payment', 'total_amount')
    def _onchange_first_payment(self):
        """Calculate first payment amount based on type"""
        if self.total_amount <= 0:
            return
        
        if self.first_payment_type == 'percentage':
            self.first_payment_amount = (self.first_payment_percentage / 100) * self.total_amount
        elif self.first_payment_type == 'fixed':
            self.first_payment_percentage = (self.first_payment_amount / self.total_amount) * 100
        elif self.first_payment_type == 'custom':
            self.first_payment_amount = self.custom_first_payment
            self.first_payment_percentage = (self.custom_first_payment / self.total_amount) * 100
    
    @api.onchange('installment_count', 'first_payment_amount', 'total_amount', 'payment_frequency', 'custom_interval_days', 'start_date')
    def _onchange_generate_preview(self):
        """Generate payment schedule preview"""
        if not self.installment_count or not self.total_amount:
            self.payment_schedule_ids = [(5, 0, 0)]
            return
        
        # Clear existing preview
        self.payment_schedule_ids = [(5, 0, 0)]
        
        # Calculate remaining amount after first payment
        remaining_amount = self.total_amount - self.first_payment_amount
        remaining_installments = self.installment_count - 1
        
        if remaining_installments <= 0:
            return
        
        # Calculate installment amount
        installment_amount = remaining_amount / remaining_installments
        
        # Calculate payment dates
        payment_dates = self._calculate_payment_dates()
        
        # Create preview records
        preview_lines = []
        
        # First payment
        preview_lines.append((0, 0, {
            'sequence': 1,
            'due_date': self.start_date,
            'amount': self.first_payment_amount,
            'payment_type': 'First Payment',
            'status': 'pending'
        }))
        
        # Regular installments
        for i in range(remaining_installments):
            preview_lines.append((0, 0, {
                'sequence': i + 2,
                'due_date': payment_dates[i] if i < len(payment_dates) else self.start_date,
                'amount': installment_amount,
                'payment_type': 'Installment',
                'status': 'pending'
            }))
        
        self.payment_schedule_ids = preview_lines
    
    def _calculate_payment_dates(self):
        """Calculate payment dates based on frequency"""
        dates = []
        current_date = self.start_date
        
        if self.payment_frequency == 'monthly':
            for i in range(self.installment_count - 1):
                # Add months (approximate)
                if current_date.month == 12:
                    current_date = current_date.replace(year=current_date.year + 1, month=1)
                else:
                    current_date = current_date.replace(month=current_date.month + 1)
                dates.append(current_date)
        elif self.payment_frequency == 'quarterly':
            for i in range(self.installment_count - 1):
                # Add 3 months
                if current_date.month >= 10:
                    current_date = current_date.replace(year=current_date.year + 1, month=current_date.month - 9)
                else:
                    current_date = current_date.replace(month=current_date.month + 3)
                dates.append(current_date)
        else:  # custom
            for i in range(self.installment_count - 1):
                current_date = current_date + timedelta(days=self.custom_interval_days)
                dates.append(current_date)
        
        return dates
    
    def action_generate_installments(self):
        """Generate installment schedule and payments"""
        self.ensure_one()
        
        if not self.payment_schedule_ids:
            raise UserError(_("Please generate payment schedule preview first"))
        
        # Validate inputs
        if self.installment_count <= 0:
            raise UserError(_("Number of installments must be greater than 0"))
        
        if self.first_payment_amount < 0:
            raise UserError(_("First payment amount cannot be negative"))
        
        if self.first_payment_amount > self.total_amount:
            raise UserError(_("First payment amount cannot exceed total amount"))
        
        try:
            # Create installment schedule
            schedule = self.env['installment.schedule'].create({
                'name': f"Installment Schedule - {self.invoice_id.name}",
                'invoice_id': self.invoice_id.id,
                'total_amount': self.total_amount,
                'installment_count': self.installment_count,
                'payment_frequency': self.payment_frequency,
                'state': 'draft'
            })
            
            # Create individual payment records
            for preview in self.payment_schedule_ids:
                self.env['installment.payment'].create({
                    'name': f"Payment {preview.sequence}",
                    'sequence': preview.sequence,
                    'installment_schedule_id': schedule.id,
                    'amount': preview.amount,
                    'due_date': preview.due_date,
                    'state': 'pending'
                })
            
            # Create payment term for the invoice
            payment_term = self._create_payment_term(schedule)
            if payment_term:
                self.invoice_id.invoice_payment_term_id = payment_term.id
            
            # Activate schedule
            schedule.action_activate()
            
            return {
                'type': 'ir.actions.act_window',
                'name': _('Installment Schedule'),
                'res_model': 'installment.schedule',
                'res_id': schedule.id,
                'view_mode': 'form',
                'target': 'current',
            }
            
        except Exception as e:
            _logger.error(f"Error generating installments: {e}")
            raise UserError(_("Error generating installments: %s") % str(e))
    
    def _create_payment_term(self, schedule):
        """Create payment term for the invoice"""
        try:
            payment_term_lines = []
            
            for payment in schedule.installment_payment_ids:
                # Calculate days from invoice date
                days_difference = (payment.due_date - self.invoice_id.invoice_date).days
                days_difference = max(0, days_difference)  # Ensure non-negative
                
                payment_term_lines.append({
                    'value': 'percent',
                    'value_amount': (payment.amount / self.total_amount) * 100,
                    'nb_days': days_difference,
                    'delay_type': 'days_after',
                })
            
            payment_term = self.env['account.payment.term'].create({
                'name': f"Installment Terms - {schedule.name}",
                'line_ids': [(0, 0, line) for line in payment_term_lines]
            })
            
            return payment_term
            
        except Exception as e:
            _logger.error(f"Error creating payment term: {e}")
            return False


class InstallmentSchedulePreview(models.TransientModel):
    _name = 'installment.schedule.preview'
    _description = 'Installment Schedule Preview'

    wizard_id = fields.Many2one('installment.generation.wizard', string='Wizard', required=True, ondelete='cascade')
    sequence = fields.Integer(string='Sequence', required=True)
    due_date = fields.Date(string='Due Date', required=True)
    amount = fields.Monetary(string='Amount', currency_field='currency_id', required=True)
    currency_id = fields.Many2one('res.currency', string='Currency', related='wizard_id.currency_id')
    payment_type = fields.Char(string='Payment Type', required=True)
    status = fields.Selection([
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue')
    ], string='Status', default='pending')
