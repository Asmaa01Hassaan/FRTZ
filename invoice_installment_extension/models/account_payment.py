# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import timedelta
import logging

_logger = logging.getLogger(__name__)


class AccountPayment(models.Model):
    _inherit = 'account.payment'
    
    def action_post(self):
        """Override action_post to process control payments before posting"""
        # Process control payments if there are any with to_pay > 0
        if self.control_payment_ids and any(self.control_payment_ids.mapped('to_pay')):
            try:
                # Call action_process_control_payments with context to indicate it's from action_post
                self.with_context(from_action_post=True).action_process_control_payments()
            except Exception as e:
                # If processing fails, still allow payment to be posted
                # but log the error
                _logger.warning(f"Error processing control payments for payment {self.name}: {e}")
        
        return super().action_post()

    # Date filter for all selected invoices (defaults to payment date)
    payment_due_date_filter = fields.Date(
        string=_('Date for Pay'),
        help=_('Date filter for calculating due amount on all selected invoices')
    )
    
    # Many2many field for all unpaid invoices
    available_invoice_ids = fields.Many2many(
        'account.move',
        'payment_available_invoice_rel',
        'payment_id',
        'invoice_id',
        string=_('Available Invoices'),
        help=_('All unpaid invoices for the selected customer'),
        domain="[('partner_id', '=', partner_id), ('move_type', '=', 'out_invoice'), ('state', '=', 'posted'), ('payment_state', '!=', 'paid')]"
    )
    
    # Many2many field for selected invoices
    selected_invoice_ids = fields.Many2many(
        'account.move',
        'payment_selected_invoice_rel',
        'payment_id',
        'invoice_id',
        string=_('Selected Invoices'),
        help=_('Invoices selected for payment'),
        domain="[('id', 'in', available_invoice_ids)]"
    )
    
    # One2many field for invoice to pay records (only for selected invoices)
    payment_invoice_line_ids = fields.One2many(
        'payment.invoice.to.pay',
        'payment_id',
        string=_('Invoice Payment Lines'),
        help=_('Invoices selected for payment with amounts to pay'),
        domain="[('invoice_id', 'in', selected_invoice_ids)]"
    )
    
    # One2many field for control payment records
    control_payment_ids = fields.One2many(
        'control.payment',
        'payment_id',
        string=_('Control Payments'),
        help=_('Control payment records for invoices')
    )
    
    # Computed fields
    total_invoice_to_pay = fields.Monetary(
        string=_('Total Invoice To Pay'),
        currency_field='currency_id',
        compute='_compute_total_invoice_to_pay',
        help=_('Sum of all to_pay_amount for selected invoices')
    )
    
    payment_remaining_amount = fields.Monetary(
        string=_('Remaining Amount'),
        currency_field='currency_id',
        compute='_compute_total_invoice_to_pay',
        help=_('Payment amount minus total invoice to pay')
    )
    
    # Computed fields for control payments
    total_control_to_pay = fields.Monetary(
        string=_('Total Control To Pay'),
        currency_field='currency_id',
        compute='_compute_total_control_to_pay',
        help=_('Sum of all to_pay for control payment records')
    )
    
    control_payment_remaining_amount = fields.Monetary(
        string=_('Control Remaining Amount'),
        currency_field='currency_id',
        compute='_compute_total_control_to_pay',
        help=_('Payment amount minus total control to pay')
    )
    
    @api.depends('payment_invoice_line_ids.to_pay_amount', 'amount')
    def _compute_total_invoice_to_pay(self):
        """Compute total invoice to pay and remaining amount"""
        for payment in self:
            total = sum(payment.payment_invoice_line_ids.mapped('to_pay_amount'))
            payment.total_invoice_to_pay = total
            payment.payment_remaining_amount = (payment.amount or 0.0) - total
    
    @api.depends('control_payment_ids.to_pay', 'amount')
    def _compute_total_control_to_pay(self):
        """Compute total control to pay and remaining amount"""
        for payment in self:
            total = sum(payment.control_payment_ids.mapped('to_pay'))
            payment.total_control_to_pay = total
            payment.control_payment_remaining_amount = (payment.amount or 0.0) - total
    
    @api.model
    def default_get(self, fields_list):
        """Set default payment_due_date_filter from date"""
        res = super().default_get(fields_list)
        if 'payment_due_date_filter' in fields_list and 'date' in fields_list:
            # If date is provided, use it; otherwise use today
            if 'date' in res and res['date']:
                res['payment_due_date_filter'] = res['date']
            else:
                res['payment_due_date_filter'] = fields.Date.today()
        elif 'payment_due_date_filter' in fields_list:
            res['payment_due_date_filter'] = fields.Date.today()
        return res
    
    @api.onchange('partner_id', 'partner_type')
    def _onchange_partner_load_invoices(self):
        """Load unpaid invoices when partner is selected"""
        if self.partner_id and self.partner_type == 'customer':
            # Get all unpaid invoices for the customer with remaining amount > 0
            invoices = self.env['account.move'].search([
                ('partner_id', '=', self.partner_id.id),
                ('move_type', '=', 'out_invoice'),
                ('state', '=', 'posted'),
                ('payment_state', '!=', 'paid'),
                ('total_remaining_amount', '!=', 0),
            ])
            # Set available invoices and select all by default
            self.available_invoice_ids = [(6, 0, invoices.ids)]
            self.selected_invoice_ids = [(6, 0, invoices.ids)]  # Select all by default
            # Update payment_invoice_line_ids for selected invoices
            self._update_payment_invoice_lines()
            # Update control_payment_ids for all available invoices
            self._update_control_payment_lines()
        elif not self.partner_id or self.partner_type != 'customer':
            # Clear everything if partner is removed or not customer
            self.available_invoice_ids = [(5, 0, 0)]
            self.selected_invoice_ids = [(5, 0, 0)]
            self.payment_invoice_line_ids = [(5, 0, 0)]
            self.control_payment_ids = [(5, 0, 0)]
    
    def _update_payment_invoice_lines(self):
        """Update payment_invoice_line_ids based on selected_invoice_ids"""
        if not self.selected_invoice_ids:
            self.payment_invoice_line_ids = [(5, 0, 0)]
            return
        
        # Get existing invoice IDs in payment_invoice_line_ids
        existing_invoice_ids = self.payment_invoice_line_ids.mapped('invoice_id').ids
        
        # Create lines for newly selected invoices
        to_create = []
        for invoice in self.selected_invoice_ids:
            if invoice.id not in existing_invoice_ids:
                to_create.append((0, 0, {
                    'invoice_id': invoice.id,
                    'to_pay_amount': 0.0,
                    'due_date_filter': self.payment_due_date_filter or invoice.due_date_filter or False,
                }))
        
        # Remove lines for deselected invoices
        to_remove = self.payment_invoice_line_ids.filtered(
            lambda l: l.invoice_id.id not in self.selected_invoice_ids.ids
        )
        to_remove_ids = [(2, line.id) for line in to_remove]
        
        # Update lines
        if to_create or to_remove_ids:
            current_lines = self.payment_invoice_line_ids.filtered(
                lambda l: l.invoice_id.id in self.selected_invoice_ids.ids
            )
            # Keep existing lines and add new ones
            self.payment_invoice_line_ids = [(6, 0, current_lines.ids)] + to_create
    
    def _update_control_payment_lines(self):
        """Update control_payment_ids based on available_invoice_ids"""
        if not self.available_invoice_ids:
            self.control_payment_ids = [(5, 0, 0)]
            return
        
        # Get existing invoice IDs in control_payment_ids
        existing_invoice_ids = self.control_payment_ids.mapped('invoice_id').ids
        
        # Use payment_due_date_filter (which equals payment date) or today's date
        due_date_value = self.payment_due_date_filter or self.date or fields.Date.today()
        
        # Create lines for newly available invoices
        to_create = []
        for invoice in self.available_invoice_ids:
            if invoice.id not in existing_invoice_ids:
                # Set invoice's due_date_filter to payment_due_date_filter
                if due_date_value and invoice.due_date_filter != due_date_value:
                    invoice.due_date_filter = due_date_value
                    invoice._compute_due_amount()
                
                to_create.append((0, 0, {
                    'invoice_id': invoice.id,
                    'to_pay': 0.0,
                    'due_date': due_date_value,
                }))
        
        # Remove lines for invoices no longer available
        to_remove = self.control_payment_ids.filtered(
            lambda l: l.invoice_id.id not in self.available_invoice_ids.ids
        )
        to_remove_ids = [(2, line.id) for line in to_remove]
        
        # Update lines
        if to_create or to_remove_ids:
            current_lines = self.control_payment_ids.filtered(
                lambda l: l.invoice_id.id in self.available_invoice_ids.ids
            )
            # Keep existing lines and add new ones
            self.control_payment_ids = [(6, 0, current_lines.ids)] + to_create
            
            # Trigger recomputation of due_amount for all control payment records
            for line in self.control_payment_ids:
                line._compute_due_amount()
    
    @api.onchange('date')
    def _onchange_payment_date(self):
        """Update payment_due_date_filter when payment date changes"""
        if self.date:
            self.payment_due_date_filter = self.date
            # Also trigger the update of invoice lines
            self._onchange_payment_due_date_filter()
    
    @api.onchange('payment_due_date_filter')
    def _onchange_payment_due_date_filter(self):
        """Update due_date_filter for all invoice lines and control payment lines"""
        if self.payment_due_date_filter:
            # Update payment_invoice_line_ids
            for line in self.payment_invoice_line_ids:
                line.due_date_filter = self.payment_due_date_filter
                # Trigger recomputation of due_amount
                if line.invoice_id:
                    line.invoice_id.due_date_filter = self.payment_due_date_filter
                    line.invoice_id._compute_due_amount()
                    line._compute_due_amount()
            
            # Update control_payment_ids
            for line in self.control_payment_ids:
                line.due_date = self.payment_due_date_filter
                if line.invoice_id:
                    line.invoice_id.due_date_filter = self.payment_due_date_filter
                    line.invoice_id._compute_due_amount()
                    line._compute_due_amount()
    
    @api.onchange('selected_invoice_ids')
    def _onchange_selected_invoice_ids(self):
        """Update payment_invoice_line_ids when selected invoices change"""
        self._update_payment_invoice_lines()
    
    def write(self, vals):
        """Override write to sync selected_invoice_ids and due_date_filter"""
        # If date is updated, also update payment_due_date_filter
        if 'date' in vals and vals['date']:
            vals['payment_due_date_filter'] = vals['date']
        
        # Sync payment_due_date_filter to invoice lines and control payment lines if it's being updated
        if 'payment_due_date_filter' in vals:
            for payment in self:
                # Update payment_invoice_line_ids
                if payment.payment_invoice_line_ids:
                    for line in payment.payment_invoice_line_ids:
                        line.due_date_filter = vals['payment_due_date_filter']
                        if line.invoice_id:
                            line.invoice_id.due_date_filter = vals['payment_due_date_filter']
                            line.invoice_id._compute_due_amount()
                
                # Update control_payment_ids
                if payment.control_payment_ids:
                    for line in payment.control_payment_ids:
                        line.due_date = vals['payment_due_date_filter']
                        if line.invoice_id:
                            line.invoice_id.due_date_filter = vals['payment_due_date_filter']
                            line.invoice_id._compute_due_amount()
                            line._compute_due_amount()
        
        result = super().write(vals)
        
        # After write, update payment_invoice_line_ids if selected_invoice_ids changed
        if 'selected_invoice_ids' in vals:
            for payment in self:
                payment._update_payment_invoice_lines()
        
        # Trigger recomputation of control totals if control_payment_ids changed
        if 'control_payment_ids' in vals:
            for payment in self:
                payment._compute_total_control_to_pay()
        
        return result
    
    def action_process_installment_payments(self):
        """Process installment payments for all selected invoices"""
        self.ensure_one()
        
        if not self.payment_invoice_line_ids:
            raise UserError(_("Please select at least one invoice to pay"))
        
        if not self.payment_due_date_filter:
            raise UserError(_("Please select a date for pay"))
        
        # Validate total equals payment amount
        total_to_pay = sum(self.payment_invoice_line_ids.mapped('to_pay_amount'))
        if total_to_pay != self.amount:
            raise UserError(_(
                "Total invoice to pay amount (%s) must equal the payment amount (%s)."
            ) % (total_to_pay, self.amount))
        
        processed_count = 0
        errors = []
        
        for line in self.payment_invoice_line_ids.filtered(lambda l: l.to_pay_amount > 0):
            try:
                # Update invoice with payment values
                line.invoice_id.write({
                    'to_pay_amount': line.to_pay_amount,
                    'due_date_filter': self.payment_due_date_filter,
                })
                
                # Process the installment payment
                line.invoice_id.action_pay_installments()
                processed_count += 1
            except Exception as e:
                errors.append(f"{line.invoice_id.name}: {str(e)}")
        
        if errors:
            error_message = _("Errors occurred while processing payments:\n%s") % '\n'.join(errors)
            raise UserError(error_message)
        
        if processed_count > 0:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _('Payment processed for %d invoice(s) successfully.') % processed_count,
                    'type': 'success',
                    'sticky': False,
                }
            }
        
        return False
    
    def action_process_control_payments(self):
        """Process installment payments for all control payment records"""
        self.ensure_one()
        
        # Check if called from action_post
        from_action_post = self.env.context.get('from_action_post', False)
        
        # Skip if no control payments or no amounts to pay
        if not self.control_payment_ids:
            if from_action_post:
                return False
            raise UserError(_("Please select at least one invoice to pay"))
        
        # Filter to only process invoices where to_pay is not 0
        invoices_to_process = self.control_payment_ids.filtered(lambda l: l.to_pay != 0)
        if not invoices_to_process:
            if from_action_post:
                return False
            raise UserError(_("Please select at least one invoice to pay"))
        
        if not self.payment_due_date_filter:
            # Use payment date if due_date_filter is not set
            self.payment_due_date_filter = self.date or fields.Date.today()
        
        total_to_pay = sum(invoices_to_process.mapped('to_pay'))
        if total_to_pay != self.amount:
            if from_action_post:
                # When called from action_post, don't raise error, just log warning and skip
                _logger.warning(
                    f"Payment {self.name}: Total control to pay amount ({total_to_pay}) does not equal payment amount ({self.amount}). Skipping processing."
                )
                return False
            else:
                # When called directly, raise error as before
                raise UserError(_(
                    "Total control to pay amount (%s) must equal the payment amount (%s)."
                ) % (total_to_pay, self.amount))
        
        processed_count = 0
        errors = []
        
        # Process invoices where to_pay is not 0
        for line in self.control_payment_ids.filtered(lambda l: l.to_pay != 0):
            try:
                # Set invoice's due_date_filter to payment_due_date_filter
                # Set invoice's to_pay_amount to line's to_pay
                line.invoice_id.write({
                    'due_date_filter': self.payment_due_date_filter,
                    'to_pay_amount': line.to_pay,
                })
                
                # Store timestamp before processing to find records created after
                before_timestamp = fields.Datetime.now()
                
                # Call the invoice's action_pay_installments method with payment context
                line.invoice_id.with_context(payment_id=self.id).action_pay_installments()
                
                # Find payment records created during action_pay_installments
                # and update them with payment reference
                payment_records = self.env['payment.records'].search([
                    ('installment_id.invoice_id', '=', line.invoice_id.id),
                    ('action_type', '=', 'action_pay_installments'),
                    ('create_date', '>=', before_timestamp)
                ])
                
                # Get payment name (might be sequence-based, so use display_name or name)
                payment_name = self.name or self.display_name or _('Payment %s') % self.id
                
                # Update payment records and installment payment_reference
                for payment_record in payment_records:
                    # Link payment to payment record (in case it wasn't set via context)
                    if not payment_record.payment_id:
                        payment_record.write({'payment_id': self.id})
                    
                    # Add payment name to installment's payment_reference
                    installment = payment_record.installment_id
                    if installment and payment_name:
                        current_ref = installment.payment_reference or ''
                        if payment_name not in current_ref:
                            if current_ref:
                                installment.write({'payment_reference': f"{current_ref}, {payment_name}"})
                            else:
                                installment.write({'payment_reference': payment_name})
                
                processed_count += 1
            except Exception as e:
                errors.append(f"{line.invoice_id.name}: {str(e)}")
        
        if errors:
            error_message = _("Errors occurred while processing payments:\n%s") % '\n'.join(errors)
            raise UserError(error_message)
        
        # Mark invoices as paid if total_remaining_amount = 0
        if processed_count > 0:
            self._mark_invoices_paid_if_fully_paid()
        
        if processed_count > 0:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _('Payment processed for %d invoice(s) successfully.') % processed_count,
                    'type': 'success',
                    'sticky': False,
                }
            }
        
        return False
    
    def _mark_invoices_paid_if_fully_paid(self):
        """Mark invoices as paid if their total_remaining_amount = 0"""
        for line in self.control_payment_ids.filtered(lambda l: l.to_pay != 0):
            invoice = line.invoice_id
            if invoice and invoice.total_remaining_amount == 0:
                # Check if invoice is not already marked as paid
                if invoice.payment_state != 'paid':
                    invoice.write({'payment_state': 'paid'})
                    _logger.info(f"Marked invoice {invoice.name} as paid (total_remaining_amount = 0)")

