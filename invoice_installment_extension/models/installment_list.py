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
    paid_amount = fields.Monetary(string='Paid Amount', currency_field='currency_id', default=0.0, help='Amount that has been paid for this installment')
    remaining_amount = fields.Monetary(string='Remaining Amount', currency_field='currency_id', compute='_compute_remaining_amount', store=True, help='Remaining amount to be paid')
    
    # Status and Tracking
    state = fields.Selection([
        ('pending', 'Pending'),
        ('partial_paid', 'Partial Paid'),
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
            installment.is_late = (installment.state in ('pending', 'partial_paid') and 
                                 installment.due_date and 
                                 installment.due_date < today)
    
    @api.depends('due_date', 'state')
    def _compute_days_overdue(self):
        today = fields.Date.today()
        for installment in self:
            if (installment.state in ('pending', 'partial_paid') and 
                installment.due_date and 
                installment.due_date < today):
                installment.days_overdue = (today - installment.due_date).days
            else:
                installment.days_overdue = 0
    
    @api.depends('amount', 'paid_amount')
    def _compute_remaining_amount(self):
        """Compute remaining amount to be paid"""
        for installment in self:
            installment.remaining_amount = installment.amount - installment.paid_amount
    
    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('installment.list') or _('New')
        return super().create(vals)

    def action_mark_paid(self):
        """Mark installment as fully paid"""
        self.ensure_one()
        if self.state not in ('pending', 'partial_paid'):
            raise UserError(_("Only pending or partial paid installments can be marked as fully paid"))
        
        previous_state = self.state
        self.write({
            'state': 'paid',
            'paid_amount': self.amount,  # Set paid amount to full amount
            'paid_date': fields.Date.today(),
        })
        
        # Create payment record
        self.env['payment.records'].create_payment_record(
            installment=self,
            payment=None,
            paid_amount=self.amount - (self.paid_amount or 0.0),
            previous_state=previous_state,
            new_state='paid',
            action_type='action_mark_paid'
        )
    
    def action_mark_partial_paid(self, partial_amount=0.0):
        """Mark installment as partially paid or update partial payment"""
        self.ensure_one()
        if self.state == 'paid':
            raise UserError(_("Fully paid installments cannot be updated"))
        if self.state == 'cancelled':
            raise UserError(_("Cancelled installments cannot be paid"))
        
        # Validate partial amount
        if partial_amount <= 0:
            raise UserError(_("Partial payment amount must be greater than 0"))
        
        new_paid_amount = (self.paid_amount or 0.0) + partial_amount
        previous_state = self.state
        
        if new_paid_amount >= self.amount:
            # If partial payment makes it fully paid, mark as paid
            self.write({
                'state': 'paid',
                'paid_amount': self.amount,
                'paid_date': fields.Date.today(),
            })
            new_state = 'paid'
        else:
            # Update partial payment
            self.write({
                'state': 'partial_paid',
                'paid_amount': new_paid_amount,
                'paid_date': fields.Date.today() if not self.paid_date else self.paid_date,
            })
            new_state = 'partial_paid'
        
        # Create payment record
        self.env['payment.records'].create_payment_record(
            installment=self,
            payment=None,
            paid_amount=partial_amount,
            previous_state=previous_state,
            new_state=new_state,
            action_type='action_mark_partial_paid'
        )
    
    def action_mark_overdue(self):
        """Mark installment as overdue"""
        self.ensure_one()
        if self.state not in ('pending', 'partial_paid'):
            raise UserError(_("Only pending or partial paid installments can be marked as overdue"))
        
        self.state = 'overdue'
    
    def action_cancel(self):
        """Cancel installment"""
        self.ensure_one()
        if self.state == 'paid':
            raise UserError(_("Paid installments cannot be cancelled"))
        
        self.state = 'cancelled'
    
    @api.constrains('paid_amount', 'amount')
    def _check_paid_amount(self):
        """Validate that paid amount does not exceed installment amount"""
        for installment in self:
            if installment.paid_amount and installment.paid_amount > installment.amount:
                raise UserError(_("Paid amount cannot exceed the installment amount"))
    
    @api.onchange('paid_amount')
    def _onchange_paid_amount(self):
        """Automatically update state based on paid amount"""
        for installment in self:
            if not installment.paid_amount or installment.paid_amount == 0.0:
                if installment.state == 'partial_paid':
                    installment.state = 'pending'
            elif installment.paid_amount >= installment.amount:
                installment.state = 'paid'
                if not installment.paid_date:
                    installment.paid_date = fields.Date.today()
            else:
                if installment.state == 'pending':
                    installment.state = 'partial_paid'
    
    @api.model
    def _cron_check_overdue_installments(self):
        """Cron job to check for overdue installments"""
        today = fields.Date.today()
        overdue_installments = self.search([
            ('state', 'in', ('pending', 'partial_paid')),
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
    partial_paid_installment_count = fields.Integer(string='Partial Paid Installments', compute='_compute_installment_count', store=True)
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
    
    # Due date filter and due amount calculation
    due_date_filter = fields.Date(
        string='Date for Pay',
        help='Select a date to calculate due amount for installments due on or before this date'
    )
    
    due_amount = fields.Monetary(
        string='Due Amount',
        currency_field='currency_id',
        compute='_compute_due_amount',
        help='Total remaining amount of installments due on or before the selected date'
    )
    
    to_pay_amount = fields.Monetary(
        string='To Pay',
        currency_field='currency_id',
        help='Amount to be distributed among installments due on or before the selected date'
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
            move.partial_paid_installment_count = len(move.installment_list_ids.filtered(lambda i: i.state == 'partial_paid'))
            move.pending_installment_count = len(move.installment_list_ids.filtered(lambda i: i.state == 'pending'))
            move.overdue_installment_count = len(move.installment_list_ids.filtered(lambda i: i.state == 'overdue'))
    
    @api.depends('installment_list_ids.state', 'installment_list_ids.amount', 'installment_list_ids.paid_amount', 'amount_total')
    def _compute_installment_totals(self):
        for move in self:
            # Calculate total paid amount from fully paid installments (using full amount)
            paid_installments = move.installment_list_ids.filtered(lambda i: i.state == 'paid')
            paid_amount = sum(paid_installments.mapped('amount'))
            
            # Add paid_amount from partially paid installments
            partial_paid_installments = move.installment_list_ids.filtered(lambda i: i.state == 'partial_paid')
            partial_paid_amount = sum(partial_paid_installments.mapped('paid_amount') or [0.0])
            
            move.total_paid_amount = paid_amount + partial_paid_amount
            
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
            
            # Get all pending/partial_paid/overdue installments (not fully paid, not cancelled)
            # Access the records directly from installment_list_ids
            pending_installments = move.installment_list_ids.filtered(
                lambda i: i.state in ('pending', 'partial_paid', 'overdue')
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
                    # Use remaining_amount for partial_paid, amount for others
                    if nearest_installment.state == 'partial_paid':
                        move.nearest_due_installment_amount = nearest_installment.remaining_amount
                    else:
                        move.nearest_due_installment_amount = nearest_installment.amount
                    move.nearest_due_installment_date = nearest_installment.due_date
                    
                    _logger.debug(f"Invoice {move.name}: Nearest due installment - Amount: {nearest_installment.amount}, Date: {nearest_installment.due_date}")
            except Exception as e:
                _logger.error(f"Error computing nearest due installment for invoice {move.name}: {e}")
                import traceback
                _logger.error(traceback.format_exc())
    
    @api.depends('due_date_filter', 'installment_list_ids', 'installment_list_ids.state', 'installment_list_ids.due_date', 'installment_list_ids.remaining_amount', 'installment_list_ids.amount', 'installment_list_ids.paid_amount')
    def _compute_due_amount(self):
        """Compute total remaining amount of installments due on or before the selected date"""
        for move in self:
            if not move.due_date_filter:
                move.due_amount = 0.0
                continue
            
            if not move.installment_list_ids:
                move.due_amount = 0.0
                continue
            
            # Filter installments that are:
            # 1. Not fully paid and not cancelled (pending, partial_paid, or overdue)
            # 2. Due date <= selected date
            due_installments = move.installment_list_ids.filtered(
                lambda i: i.state in ('pending', 'partial_paid', 'overdue') and
                         i.due_date and
                         i.due_date <= move.due_date_filter
            )
            
            # Sum the remaining_amount from these installments
            # For partial_paid, use remaining_amount; for others, use amount (since remaining = amount for pending/overdue)
            total_due_amount = 0.0
            for installment in due_installments:
                if installment.state == 'partial_paid':
                    total_due_amount += installment.remaining_amount
                else:
                    # For pending/overdue, remaining_amount = amount (no payment made yet)
                    total_due_amount += installment.amount
            
            move.due_amount = total_due_amount
    
    @api.onchange('due_date_filter')
    def _onchange_due_date_filter(self):
        """Trigger recomputation of due_amount when date filter changes"""
        # The @api.depends decorator should handle this, but we explicitly trigger it here
        # to ensure immediate UI update
        self._compute_due_amount()
    
    def action_pay_installments(self):
        """Distribute the to_pay_amount among eligible installments"""
        self.ensure_one()
        
        if not self.to_pay_amount or self.to_pay_amount <= 0:
            raise UserError(_("Please enter a valid amount to pay"))
        
        if not self.due_date_filter:
            raise UserError(_("Please select a date for pay first"))
        
        # Get all eligible installments (due on or before the selected date, not fully paid, not cancelled)
        eligible_installments = self.installment_list_ids.filtered(
            lambda i: i.state in ('pending', 'partial_paid') and
                     i.due_date and
                     i.due_date <= self.due_date_filter
        )
        
        if not eligible_installments:
            raise UserError(_("No installments found due on or before the selected date"))
        
        # Sort installments: partial_paid first (to complete them), then by due_date (oldest first)
        partial_paid_installments = eligible_installments.filtered(lambda i: i.state == 'partial_paid')
        pending_installments = eligible_installments.filtered(lambda i: i.state == 'pending')
        
        # Sort partial paid by due_date
        sorted_partial = partial_paid_installments.sorted(key=lambda i: i.due_date)
        # Sort pending by due_date
        sorted_pending = pending_installments.sorted(key=lambda i: i.due_date)
        
        # Combine: partial_paid first, then pending
        sorted_installments = sorted_partial | sorted_pending
        
        remaining_to_pay = self.to_pay_amount
        
        # Distribute payments
        for installment in sorted_installments:
            if remaining_to_pay <= 0:
                break
            
            # Calculate remaining amount needed for this installment
            if installment.state == 'partial_paid':
                remaining_needed = installment.remaining_amount
            else:  # pending
                remaining_needed = installment.amount
            
            # Determine how much to pay for this installment
            previous_state = installment.state
            payment_amount = min(remaining_to_pay, remaining_needed)
            
            if remaining_to_pay >= remaining_needed:
                # Can fully pay this installment
                new_state = 'paid'
                installment.write({
                    'paid_amount': installment.amount,
                    'state': 'paid',
                    'paid_date': fields.Date.today() if not installment.paid_date else installment.paid_date,
                })
                remaining_to_pay -= remaining_needed
            else:
                # Partial payment
                new_state = 'partial_paid'
                new_paid_amount = (installment.paid_amount or 0.0) + remaining_to_pay
                installment.write({
                    'paid_amount': new_paid_amount,
                    'state': 'partial_paid',
                    'paid_date': fields.Date.today() if not installment.paid_date else installment.paid_date,
                })
                remaining_to_pay = 0.0
            
            # Create payment record for this installment
            # Check if called from a payment (via context)
            payment_id = self.env.context.get('payment_id')
            payment = self.env['account.payment'].browse(payment_id) if payment_id else None
            
            self.env['payment.records'].create_payment_record(
                installment=installment,
                payment=payment,
                paid_amount=payment_amount,
                previous_state=previous_state,
                new_state=new_state,
                action_type='action_pay_installments'
            )
        
        # Clear the to_pay_amount field and save the invoice
        self.write({'to_pay_amount': 0.0})
        
        # Recompute due amount after payments
        self._compute_due_amount()
        
        # Trigger recomputation of installment counts and totals on the invoice
        self._compute_installment_count()
        self._compute_installment_totals()
        
        # Prepare success message
        if remaining_to_pay > 0:
            message = _("Payment distributed. Remaining amount %.2f could not be applied to any installment.") % remaining_to_pay
            msg_type = 'warning'
            msg_title = _('Partial Payment Applied')
        else:
            message = _('Payment has been distributed to installments successfully.')
            msg_type = 'success'
            msg_title = _('Success')
        
        # Return action that reloads the form view to show updated installments
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
            'context': {'form_view_initial_mode': 'edit'},
        }
    
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
