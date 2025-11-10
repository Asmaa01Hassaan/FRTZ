# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # Installment Information
    installment_list_ids = fields.One2many('installment.list', 'partner_id', string=_('Installment List'))
    has_installments = fields.Boolean(string=_('Has Installments'), compute='_compute_installment_info', store=True)
    view_installments = fields.Boolean(string=_('View Installments'), default=False , store=True)
    installment_count = fields.Integer(string=_('Total Installments'), compute='_compute_installment_info', store=True)
    paid_installment_count = fields.Integer(string=_('Paid Installments'), compute='_compute_installment_info', store=True)
    partial_paid_installment_count = fields.Integer(string=_('Partial Paid Installments'), compute='_compute_installment_info', store=True)
    pending_installment_count = fields.Integer(string=_('Pending Installments'), compute='_compute_installment_info', store=True)
    overdue_installment_count = fields.Integer(string=_('Overdue Installments'), compute='_compute_installment_info', store=True)
    total_installment_amount = fields.Monetary(string=_('Total Installment Amount'), currency_field='currency_id', compute='_compute_installment_info', store=True)
    total_paid_amount = fields.Monetary(string=_('Total Paid Amount'), currency_field='currency_id', compute='_compute_installment_info', store=True)
    total_remaining_amount = fields.Monetary(string=_('Remaining Amount'), currency_field='currency_id', compute='_compute_installment_info', store=True)
    
    @api.depends('installment_list_ids', 'installment_list_ids.state', 'installment_list_ids.amount', 'installment_list_ids.paid_amount')
    def _compute_installment_info(self):
        for partner in self:
            installments = partner.installment_list_ids
            partner.has_installments = len(installments) > 0
            partner.installment_count = len(installments)
            partner.paid_installment_count = len(installments.filtered(lambda i: i.state == 'paid'))
            partner.partial_paid_installment_count = len(installments.filtered(lambda i: i.state == 'partial_paid'))
            partner.pending_installment_count = len(installments.filtered(lambda i: i.state == 'pending'))
            partner.overdue_installment_count = len(installments.filtered(lambda i: i.state == 'overdue'))
            
            # Calculate amounts
            partner.total_installment_amount = sum(installments.mapped('amount'))
            # Sum from fully paid installments (full amount)
            paid_installments = installments.filtered(lambda i: i.state == 'paid')
            paid_amount = sum(paid_installments.mapped('amount'))
            # Add paid_amount from partially paid installments
            partial_paid_installments = installments.filtered(lambda i: i.state == 'partial_paid')
            partial_paid_amount = sum(partial_paid_installments.mapped('paid_amount') or [0.0])
            partner.total_paid_amount = paid_amount + partial_paid_amount
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
