# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import timedelta
import logging

_logger = logging.getLogger(__name__)


class InstallmentReminder(models.Model):
    _name = 'installment.reminder'
    _description = 'Installment Payment Reminder'
    _order = 'reminder_date desc'

    # Reminder Information
    name = fields.Char(string='Reminder Reference', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    installment_payment_id = fields.Many2one('installment.payment', string='Installment Payment', required=True, ondelete='cascade')
    reminder_date = fields.Date(string='Reminder Date', required=True, default=fields.Date.today)
    
    # Reminder Details
    reminder_type = fields.Selection([
        ('due_soon', 'Due Soon'),
        ('overdue', 'Overdue'),
        ('final_notice', 'Final Notice')
    ], string='Reminder Type', required=True, default='due_soon')
    
    # Communication
    email_sent = fields.Boolean(string='Email Sent', default=False)
    sms_sent = fields.Boolean(string='SMS Sent', default=False)
    email_content = fields.Html(string='Email Content')
    sms_content = fields.Text(string='SMS Content')
    
    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('failed', 'Failed')
    ], string='Status', default='draft', tracking=True)
    
    # Related Information
    partner_id = fields.Many2one('res.partner', string='Customer', related='installment_payment_id.partner_id', store=True)
    due_date = fields.Date(string='Due Date', related='installment_payment_id.due_date', store=True)
    amount = fields.Monetary(string='Amount', currency_field='currency_id', related='installment_payment_id.amount', store=True)
    currency_id = fields.Many2one('res.currency', string='Currency', related='installment_payment_id.currency_id', store=True)
    
    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('installment.reminder') or _('New')
        return super().create(vals)
    
    def action_send_reminder(self):
        """Send payment reminder"""
        self.ensure_one()
        
        if self.state != 'draft':
            raise UserError(_("Only draft reminders can be sent"))
        
        try:
            # Send email reminder
            if self.partner_id.email and not self.email_sent:
                self._send_email_reminder()
                self.email_sent = True
            
            # Send SMS reminder
            if self.partner_id.mobile and not self.sms_sent:
                self._send_sms_reminder()
                self.sms_sent = True
            
            self.state = 'sent'
            _logger.info(f"Reminder {self.name} sent successfully")
            
        except Exception as e:
            self.state = 'failed'
            _logger.error(f"Failed to send reminder {self.name}: {e}")
            raise UserError(_("Failed to send reminder: %s") % str(e))
    
    def _send_email_reminder(self):
        """Send email reminder"""
        self.ensure_one()
        
        # Email template will be implemented in future version
        _logger.info(f"Payment reminder would be sent for {self.name}")
    
    def _send_sms_reminder(self):
        """Send SMS reminder"""
        self.ensure_one()
        
        # SMS sending logic would be implemented here
        # This depends on your SMS provider integration
        _logger.info(f"SMS reminder sent to {self.partner_id.mobile}")
    
    @api.model
    def _cron_send_payment_reminders(self):
        """Cron job to send payment reminders"""
        # Send reminders 7 days before due date
        reminder_date = fields.Date.today() + timedelta(days=7)
        
        payments_to_remind = self.env['installment.payment'].search([
            ('state', '=', 'pending'),
            ('due_date', '=', reminder_date)
        ])
        
        for payment in payments_to_remind:
            # Create reminder record
            reminder = self.create({
                'installment_payment_id': payment.id,
                'reminder_type': 'due_soon',
                'reminder_date': fields.Date.today(),
            })
            
            # Send reminder
            reminder.action_send_reminder()
    
    @api.model
    def _cron_send_overdue_reminders(self):
        """Cron job to send overdue payment reminders"""
        overdue_payments = self.env['installment.payment'].search([
            ('state', '=', 'overdue'),
            ('due_date', '<', fields.Date.today())
        ])
        
        for payment in overdue_payments:
            # Create overdue reminder
            reminder = self.create({
                'installment_payment_id': payment.id,
                'reminder_type': 'overdue',
                'reminder_date': fields.Date.today(),
            })
            
            # Send reminder
            reminder.action_send_reminder()
