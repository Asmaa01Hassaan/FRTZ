# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # Installment Information
    installment_list_ids = fields.One2many('installment.list', 'partner_id', string='Installment List')
    has_installments = fields.Boolean(string='Has Installments', compute='_compute_installment_info', store=True)
    installment_count = fields.Integer(string='Total Installments', compute='_compute_installment_info', store=True)
    paid_installment_count = fields.Integer(string='Paid Installments', compute='_compute_installment_info', store=True)
    pending_installment_count = fields.Integer(string='Pending Installments', compute='_compute_installment_info', store=True)
    overdue_installment_count = fields.Integer(string='Overdue Installments', compute='_compute_installment_info', store=True)
    total_installment_amount = fields.Monetary(string='Total Installment Amount', currency_field='currency_id', compute='_compute_installment_info', store=True)
    total_paid_amount = fields.Monetary(string='Total Paid Amount', currency_field='currency_id', compute='_compute_installment_info', store=True)
    total_remaining_amount = fields.Monetary(string='Remaining Amount', currency_field='currency_id', compute='_compute_installment_info', store=True)
    
    @api.depends('installment_list_ids', 'installment_list_ids.state', 'installment_list_ids.amount')
    def _compute_installment_info(self):
        for partner in self:
            installments = partner.installment_list_ids
            partner.has_installments = len(installments) > 0
            partner.installment_count = len(installments)
            partner.paid_installment_count = len(installments.filtered(lambda i: i.state == 'paid'))
            partner.pending_installment_count = len(installments.filtered(lambda i: i.state == 'pending'))
            partner.overdue_installment_count = len(installments.filtered(lambda i: i.state == 'overdue'))
            
            # Calculate amounts
            partner.total_installment_amount = sum(installments.mapped('amount'))
            paid_installments = installments.filtered(lambda i: i.state == 'paid')
            partner.total_paid_amount = sum(paid_installments.mapped('amount'))
            partner.total_remaining_amount = partner.total_installment_amount - partner.total_paid_amount
    
    def action_view_installments(self):
        """Open installment list view for this customer"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Installments for %s') % self.name,
            'res_model': 'installment.list',
            'view_mode': 'list,form',
            'domain': [('partner_id', '=', self.id)],
            'context': {
                'default_partner_id': self.id,
                'default_customer_name': self.name,
                'default_customer_number': self.ref or '',
            }
        }
