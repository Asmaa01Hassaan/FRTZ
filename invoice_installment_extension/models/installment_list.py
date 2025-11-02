# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class InstallmentList(models.Model):
    _name = 'installment.list'
    _description = 'Installment Payment List'
    _order = 'sequence, due_date'
    _rec_name = 'display_name'

    # Basic Information
    name = fields.Char(string='Installment Reference', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    sequence = fields.Integer(string='Sequence', default=1, help="Installment sequence number")
    invoice_id = fields.Many2one('account.move', string='Invoice', required=True, ondelete='cascade')
    payment_term_id = fields.Many2one('account.payment.term', string='Payment Term', related='invoice_id.invoice_payment_term_id', store=True)
    
    # Payment Details
    amount = fields.Monetary(string='Amount', currency_field='currency_id', required=True)
    currency_id = fields.Many2one('res.currency', string='Currency', related='invoice_id.currency_id', store=True, readonly=True)
    due_date = fields.Date(string='Due Date', required=True)
    paid_date = fields.Date(string='Paid Date', readonly=True)
    
    # Status and Tracking
    state = fields.Selection([
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='pending', tracking=True)
    
    # Payment Information
    payment_method_id = fields.Many2one('account.payment.method', string='Payment Method')
    payment_reference = fields.Char(string='Payment Reference')
    notes = fields.Text(string='Notes')
    
    # Computed Fields
    display_name = fields.Char(string='Display Name', compute='_compute_display_name', store=True)
    is_late = fields.Boolean(string='Is Late Payment', compute='_compute_is_late', store=True)
    days_overdue = fields.Integer(string='Days Overdue', compute='_compute_days_overdue')
    
    # Related Information
    partner_id = fields.Many2one('res.partner', string='Customer', required=True)
    customer_name = fields.Char(string='Customer Name', related='partner_id.name', store=True)
    customer_number = fields.Char(string='Customer Number', related='partner_id.ref', store=True)
    customer_guarantees_names = fields.Char(string='Customer Guarantees', compute='_compute_customer_guarantees_names', store=True)
    
    @api.depends('invoice_id.customer_guarantees_ids.name')
    def _compute_customer_guarantees_names(self):
        for installment in self:
            if installment.invoice_id and installment.invoice_id.customer_guarantees_ids:
                names = installment.invoice_id.customer_guarantees_ids.mapped('name')
                installment.customer_guarantees_names = ', '.join(names)
            else:
                installment.customer_guarantees_names = ''
    
    @api.depends('sequence', 'amount', 'due_date')
    def _compute_display_name(self):
        for installment in self:
            installment.display_name = f"Installment {installment.sequence} - {installment.amount:,.2f} - {installment.due_date}"
    
    @api.depends('due_date', 'state')
    def _compute_is_late(self):
        today = fields.Date.today()
        for installment in self:
            installment.is_late = (installment.state == 'pending' and 
                                 installment.due_date and 
                                 installment.due_date < today)
    
    @api.depends('due_date', 'state')
    def _compute_days_overdue(self):
        today = fields.Date.today()
        for installment in self:
            if (installment.state == 'pending' and 
                installment.due_date and 
                installment.due_date < today):
                installment.days_overdue = (today - installment.due_date).days
            else:
                installment.days_overdue = 0
    
    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('installment.list') or _('New')
        return super().create(vals)

    def action_mark_paid(self):
        """Mark installment as paid"""
        self.ensure_one()
        if self.state != 'pending':
            raise UserError(_("Only pending installments can be marked as paid"))
        
        self.write({
            'state': 'paid',
            'paid_date': fields.Date.today(),
        })
    
    def action_mark_overdue(self):
        """Mark installment as overdue"""
        self.ensure_one()
        if self.state != 'pending':
            raise UserError(_("Only pending installments can be marked as overdue"))
        
        self.state = 'overdue'
    
    def action_cancel(self):
        """Cancel installment"""
        self.ensure_one()
        if self.state == 'paid':
            raise UserError(_("Paid installments cannot be cancelled"))
        
        self.state = 'cancelled'
    
    @api.model
    def _cron_check_overdue_installments(self):
        """Cron job to check for overdue installments"""
        today = fields.Date.today()
        overdue_installments = self.search([
            ('state', '=', 'pending'),
            ('due_date', '<', today)
        ])
        
        for installment in overdue_installments:
            installment.action_mark_overdue()
            _logger.info(f"Installment {installment.name} marked as overdue")


class AccountMove(models.Model):
    _inherit = 'account.move'

    # Add installment list relationship
    installment_list_ids = fields.One2many('installment.list', 'invoice_id', string='Installment List')
    has_installments = fields.Boolean(string='Has Installments', compute='_compute_has_installments', store=True)
    installment_count = fields.Integer(string='Installment Count', compute='_compute_installment_count', store=True)
    paid_installment_count = fields.Integer(string='Paid Installments', compute='_compute_installment_count', store=True)
    pending_installment_count = fields.Integer(string='Pending Installments', compute='_compute_installment_count', store=True)
    overdue_installment_count = fields.Integer(string='Overdue Installments', compute='_compute_installment_count', store=True)
    
    # Installment payment totals
    total_paid_amount = fields.Monetary(string='Total Paid', currency_field='currency_id', compute='_compute_installment_totals', store=True)
    total_remaining_amount = fields.Monetary(string='Remaining Amount', currency_field='currency_id', compute='_compute_installment_totals', store=True)
    
    # Nearest due installment
    nearest_due_installment_amount = fields.Monetary(
        string='Nearest Due Installment Amount',
        currency_field='currency_id',
        compute='_compute_nearest_due_installment',
        store=True,
        help='Amount of the installment with the nearest due date'
    )
    nearest_due_installment_date = fields.Date(
        string='Nearest Due Installment Date',
        compute='_compute_nearest_due_installment',
        store=True,
        help='Due date of the installment with the nearest due date'
    )
    
    @api.depends('installment_list_ids')
    def _compute_has_installments(self):
        for move in self:
            move.has_installments = len(move.installment_list_ids) > 0
    
    @api.depends('installment_list_ids.state')
    def _compute_installment_count(self):
        for move in self:
            move.installment_count = len(move.installment_list_ids)
            move.paid_installment_count = len(move.installment_list_ids.filtered(lambda i: i.state == 'paid'))
            move.pending_installment_count = len(move.installment_list_ids.filtered(lambda i: i.state == 'pending'))
            move.overdue_installment_count = len(move.installment_list_ids.filtered(lambda i: i.state == 'overdue'))
    
    @api.depends('installment_list_ids.state', 'installment_list_ids.amount', 'amount_total')
    def _compute_installment_totals(self):
        for move in self:
            # Calculate total paid amount from paid installments
            paid_installments = move.installment_list_ids.filtered(lambda i: i.state == 'paid')
            move.total_paid_amount = sum(paid_installments.mapped('amount'))
            
            # Calculate remaining amount
            move.total_remaining_amount = move.amount_total - move.total_paid_amount

    @api.depends('installment_list_ids', 'installment_list_ids.state', 'installment_list_ids.due_date', 'installment_list_ids.amount')
    def _compute_nearest_due_installment(self):
        """Compute the installment with nearest due date from installment_list_ids"""
        for move in self:
            # Initialize with default values
            move.nearest_due_installment_amount = 0.0
            move.nearest_due_installment_date = False
            
            # Check if installment_list_ids exists and has records
            if not move.installment_list_ids:
                continue
            
            # Get all pending/overdue installments (not paid, not cancelled)
            # Access the records directly from installment_list_ids
            pending_installments = move.installment_list_ids.filtered(
                lambda i: i.state in ('pending', 'overdue')
            )
            
            if not pending_installments:
                continue
            
            # Filter those with due_date (ensure due_date is not False/None)
            installments_with_due_date = pending_installments.filtered(
                lambda i: i.due_date and i.due_date != False
            )
            
            if not installments_with_due_date:
                continue
            
            # Sort by due_date (ascending - nearest first)
            try:
                # Sort installments by due_date
                sorted_installments = installments_with_due_date.sorted(key=lambda i: i.due_date)
                
                if sorted_installments:
                    nearest_installment = sorted_installments[0]
                    
                    # Get values directly from the installment record
                    move.nearest_due_installment_amount = nearest_installment.amount
                    move.nearest_due_installment_date = nearest_installment.due_date
                    
                    _logger.debug(f"Invoice {move.name}: Nearest due installment - Amount: {nearest_installment.amount}, Date: {nearest_installment.due_date}")
            except Exception as e:
                _logger.error(f"Error computing nearest due installment for invoice {move.name}: {e}")
                import traceback
                _logger.error(traceback.format_exc())
    
    def action_view_installment_list(self):
        """Open installment list view"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Installment List'),
            'res_model': 'installment.list',
            'view_mode': 'list,form',
            'domain': [('invoice_id', '=', self.id)],
            'context': {
                'default_invoice_id': self.id,
                'default_currency_id': self.currency_id.id,
            }
        }
    
    def action_generate_installment_list(self):
        """Generate installment list from payment terms"""
        self.ensure_one()
        
        if not self.invoice_payment_term_id:
            raise UserError(_("No payment term found for this invoice"))
        
        if self.installment_list_ids:
            raise UserError(_("Installment list already exists for this invoice"))
        
        # Use the automatic generation method
        self._auto_generate_installments()
        
        return self.action_view_installment_list()
