# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

    # Enhanced installment fields
    installment_schedule_id = fields.Many2one('installment.schedule', string='Installment Schedule', readonly=True)
    has_installments = fields.Boolean(string='Has Installments', compute='_compute_has_installments', store=True)
    
    @api.depends('installment_schedule_id')
    def _compute_has_installments(self):
        for move in self:
            move.has_installments = bool(move.installment_schedule_id)
    
    def action_generate_installment_schedule(self):
        """Open enhanced installment generation wizard"""
        self.ensure_one()
        
        if self.state != 'draft':
            raise UserError(_("Installment schedule can only be generated for draft invoices"))
        
        if self.installment_schedule_id:
            raise UserError(_("This invoice already has an installment schedule"))
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Generate Installment Schedule'),
            'res_model': 'installment.generation.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_invoice_id': self.id,
            }
        }
    
    def action_view_installment_schedule(self):
        """View the installment schedule"""
        self.ensure_one()
        
        if not self.installment_schedule_id:
            raise UserError(_("No installment schedule found for this invoice"))
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Installment Schedule'),
            'res_model': 'installment.schedule',
            'res_id': self.installment_schedule_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    def action_view_installment_payments(self):
        """View installment payments"""
        self.ensure_one()
        
        if not self.installment_schedule_id:
            raise UserError(_("No installment schedule found for this invoice"))
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Installment Payments'),
            'res_model': 'installment.payment',
            'view_mode': 'list,form',
            'domain': [('installment_schedule_id', '=', self.installment_schedule_id.id)],
            'target': 'current',
        }
