# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class InstallmentTemplate(models.Model):
    _name = 'installment.template'
    _description = 'Installment Payment Template'
    _order = 'name'

    name = fields.Char(string='Template Name', required=True)
    description = fields.Text(string='Description')
    
    # Template Configuration
    installment_count = fields.Integer(string='Number of Installments', required=True, default=3)
    first_payment_type = fields.Selection([
        ('percentage', 'Percentage of Total'),
        ('fixed', 'Fixed Amount'),
        ('custom', 'Custom Amount')
    ], string='First Payment Type', default='percentage', required=True)
    
    first_payment_percentage = fields.Float(string='First Payment Percentage', default=20.0)
    first_payment_amount = fields.Float(string='First Payment Amount', default=0.0)
    
    payment_frequency = fields.Selection([
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('custom', 'Custom Interval')
    ], string='Payment Frequency', default='monthly', required=True)
    
    custom_interval_days = fields.Integer(string='Custom Interval (Days)', default=30)
    
    # Advanced Options
    late_fee_percentage = fields.Float(string='Late Fee Percentage', default=0.0)
    interest_rate = fields.Float(string='Interest Rate (%)', default=0.0)
    early_payment_discount = fields.Float(string='Early Payment Discount (%)', default=0.0)
    
    # Template Status
    active = fields.Boolean(string='Active', default=True)
    
    def action_use_template(self):
        """Use this template for installment generation"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Use Template'),
            'res_model': 'installment.generation.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_installment_count': self.installment_count,
                'default_first_payment_type': self.first_payment_type,
                'default_first_payment_percentage': self.first_payment_percentage,
                'default_first_payment_amount': self.first_payment_amount,
                'default_payment_frequency': self.payment_frequency,
                'default_custom_interval_days': self.custom_interval_days,
                'default_late_fee_percentage': self.late_fee_percentage,
                'default_interest_rate': self.interest_rate,
                'default_early_payment_discount': self.early_payment_discount,
            }
        }
