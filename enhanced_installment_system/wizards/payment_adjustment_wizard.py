# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class PaymentAdjustmentWizard(models.TransientModel):
    _name = 'installment.payment.adjustment.wizard'
    _description = 'Payment Adjustment Wizard'

    # Basic Information
    installment_payment_id = fields.Many2one('installment.payment', string='Payment', required=True, readonly=True)
    original_amount = fields.Monetary(string='Original Amount', currency_field='currency_id', readonly=True)
    original_due_date = fields.Date(string='Original Due Date', readonly=True)
    
    # Adjustment Details
    adjustment_type = fields.Selection([
        ('amount', 'Amount Adjustment'),
        ('date', 'Date Adjustment'),
        ('both', 'Amount and Date Adjustment')
    ], string='Adjustment Type', required=True, default='amount')
    
    new_amount = fields.Monetary(string='New Amount', currency_field='currency_id')
    new_due_date = fields.Date(string='New Due Date')
    adjustment_reason = fields.Text(string='Adjustment Reason', required=True)
    
    # Currency
    currency_id = fields.Many2one('res.currency', string='Currency', related='installment_payment_id.currency_id', readonly=True)
    
    @api.model
    def default_get(self, fields_list):
        """Set default values from context"""
        defaults = super().default_get(fields_list)
        
        if 'installment_payment_id' in self.env.context:
            payment_id = self.env.context['installment_payment_id']
            payment = self.env['installment.payment'].browse(payment_id)
            
            defaults.update({
                'installment_payment_id': payment_id,
                'original_amount': payment.amount,
                'original_due_date': payment.due_date,
                'new_amount': payment.amount,
                'new_due_date': payment.due_date,
            })
        
        return defaults
    
    @api.onchange('adjustment_type')
    def _onchange_adjustment_type(self):
        """Update fields based on adjustment type"""
        if self.adjustment_type == 'amount':
            self.new_due_date = False
        elif self.adjustment_type == 'date':
            self.new_amount = False
        # For 'both', both fields remain editable
    
    def action_apply_adjustment(self):
        """Apply the payment adjustment"""
        self.ensure_one()
        
        if not self.adjustment_reason:
            raise ValidationError(_("Please provide a reason for the adjustment"))
        
        payment = self.installment_payment_id
        
        # Validate adjustment type and values
        if self.adjustment_type in ['amount', 'both']:
            if not self.new_amount or self.new_amount <= 0:
                raise ValidationError(_("New amount must be greater than 0"))
        
        if self.adjustment_type in ['date', 'both']:
            if not self.new_due_date:
                raise ValidationError(_("New due date is required"))
        
        # Apply adjustments
        update_vals = {}
        
        if self.adjustment_type in ['amount', 'both']:
            update_vals['amount'] = self.new_amount
        
        if self.adjustment_type in ['date', 'both']:
            update_vals['due_date'] = self.new_due_date
        
        # Add adjustment note
        current_notes = payment.notes or ""
        adjustment_note = f"\n\n[ADJUSTMENT] {fields.Datetime.now().strftime('%Y-%m-%d %H:%M')} - {self.adjustment_reason}"
        if self.adjustment_type in ['amount', 'both']:
            adjustment_note += f" | Amount: {self.original_amount} → {self.new_amount}"
        if self.adjustment_type in ['date', 'both']:
            adjustment_note += f" | Date: {self.original_due_date} → {self.new_due_date}"
        
        update_vals['notes'] = current_notes + adjustment_note
        update_vals['state'] = 'adjusted'
        
        # Apply the changes
        payment.write(update_vals)
        
        # Log the adjustment
        _logger.info(f"Payment {payment.name} adjusted: {self.adjustment_reason}")
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Payment adjustment applied successfully'),
                'type': 'success',
                'sticky': False,
            }
        }
    
    def action_cancel(self):
        """Cancel the adjustment"""
        return {'type': 'ir.actions.act_window_close'}
