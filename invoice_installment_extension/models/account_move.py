# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import logging

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'
    hide_buttons_setting = fields.Boolean(compute='_compute_hide_sale_buttons_setting', store=False)

    @api.depends_context('uid')
    def _compute_hide_sale_buttons_setting(self):
        param = self.env['ir.config_parameter'].sudo().get_param('sale.hide_send_preview_buttons', default=False)
        for rec in self:
            rec.hide_buttons_setting = param

    @api.model
    def create(self, vals):
        """Ensure hide_buttons_setting is computed on new records"""
        record = super().create(vals)
        record._compute_hide_sale_buttons_setting()
        return record

    @api.model
    def default_get(self, fields_list):
        """Set the hide flag on brand new (unsaved) records so buttons are hidden immediately."""
        res = super().default_get(fields_list)
        if 'hide_buttons_setting' in fields_list:
            param = self.env['ir.config_parameter'].sudo().get_param('sale.hide_send_preview_buttons', default=False)
            res['hide_buttons_setting'] = bool(param)
        return res

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        """Keep standard behavior; rely on field-based invisibility instead of context."""
        return super().fields_view_get(view_id, view_type, toolbar, submenu)

    def action_quotation_send(self):
        """Override to prevent sending quotations when hide setting is enabled."""
        hide_buttons = self.env['ir.config_parameter'].sudo().get_param('sale.hide_send_preview_buttons', default=False)
        if hide_buttons:
            raise ValidationError(_("Sending quotations is disabled by system configuration."))
        return super().action_quotation_send()

    def write(self, vals):
        """Block transitions to 'sent' if setting is enabled."""
        hide_buttons = self.env['ir.config_parameter'].sudo().get_param('sale.hide_send_preview_buttons', default=False)
        if 'state' in vals and vals['state'] == 'sent' and hide_buttons:
            raise ValidationError(_("Changing state to 'Quotation Sent' is disabled by system configuration."))
        return super().write(vals)

class AccountMove(models.Model):
    _inherit = 'account.move'

    installment_num = fields.Float(
        string="Number of Installments",
        default=0.0,
        help="Number of installments for this invoice"
    )
    first_payment = fields.Monetary(
        string="First Payment Amount",
        default=0.0,
        help="First payment amount for installment calculations"
    )
    view_generate = fields.Boolean(string='View generate', default=False, groups="base.group_allow_export" )
    hide_buttons_setting = fields.Boolean(compute='_compute_hide_buttons_setting')

    @api.depends()
    def _compute_hide_buttons_setting(self):
        param = self.env['ir.config_parameter'].sudo().get_param('account.hide_buttons', default=False)
        for rec in self:
            rec.hide_buttons_setting = param

    @api.model
    def create(self, vals):
        move = super().create(vals)
        
        # Auto-generate payment terms if installment data is present
        if move.installment_num > 0:
            move._auto_generate_payment_terms()
            
        return move

    def write(self, vals):
        result = super().write(vals)
        
        # Auto-generate payment terms if installment data is updated
        for move in self:
            if move.installment_num > 0 and not move.invoice_payment_term_id:
                move._auto_generate_payment_terms()
            
            # Auto-generate installments if installment_num != 0 and payment term is Regular Installment
            is_regular_installment = (
                move.invoice_payment_term_id and 
                move.invoice_payment_term_id.name == 'Regular Installment'
            )
            if move.installment_num != 0 and is_regular_installment:
                if 'installment_num' in vals or 'invoice_payment_term_id' in vals:
                    # Regenerate installments if installment_num or payment term changed
                    move._auto_generate_installments()
                
        return result

    def _get_or_create_regular_installment_term(self):
        """Get or create the 'Regular Installment' payment term if it doesn't exist"""
        payment_term = self.env['account.payment.term'].search([('name', '=', 'Regular Installment')], limit=1)
        
        if not payment_term:
            # Create Regular Installment payment term
            # Payment due exactly at the end of next month (100% of total amount)
            payment_term = self.env['account.payment.term'].create({
                'name': 'Regular Installment',
                'note': 'Payment due at the end of next month from invoice date (100% of total amount)',
                'line_ids': [(0, 0, {
                    'value': 'percent',
                    'value_amount': 100.0,
                    'delay_type': 'days_after_end_of_next_month',
                    'nb_days': 0,
                })],
            })
            _logger.info("Created 'Regular Installment' payment term with end of next month due date")
        
        return payment_term

    def _auto_generate_payment_terms(self):
        """Automatically generate payment terms based on installment data"""
        for move in self:
            if move.installment_num <= 0:
                continue
                
            try:
                # Ensure Regular Installment payment term exists if installment_num != 0
                move._get_or_create_regular_installment_term()
                
                # Check if Regular Installment term should be used
                # If installment_num == 1 and first_payment == 0, use Regular Installment
                if move.installment_num == 1 and move.first_payment == 0:
                    # Use Regular Installment payment term
                    payment_term = move._get_or_create_regular_installment_term()
                    if payment_term:
                        move.invoice_payment_term_id = payment_term.id
                        _logger.info(f"Assigned 'Regular Installment' payment term to invoice {move.name}")
                        # Auto-generate installments for Regular Installment
                        move._auto_generate_installments()
                    continue
                
                # Also check if payment term is already Regular Installment and installment_num != 0
                if move.invoice_payment_term_id and move.invoice_payment_term_id.name == 'Regular Installment':
                    if move.installment_num != 0:
                        # Auto-generate installments for Regular Installment
                        move._auto_generate_installments()
                    continue
                
                # Calculate total amount
                total_amount = move.amount_total
                if total_amount <= 0:
                    continue
                
                # Create installment payment term
                payment_term = self.env['account.payment.term'].create_installment_term(
                    installment_num=move.installment_num,
                    first_payment=move.first_payment,
                    total_amount=total_amount
                )
                
                if payment_term:
                    move.invoice_payment_term_id = payment_term.id
                    _logger.info(f"Auto-generated payment term {payment_term.name} for invoice {move.name}")
                    
            except Exception as e:
                _logger.error(f"Error auto-generating payment terms for invoice {move.name}: {e}")

    def action_generate_payment_term(self):
        """Open wizard to generate payment term manually"""
        self.ensure_one()
        
        if self.installment_num <= 0:
            raise UserError(_("Please set the number of installments first"))
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Generate Payment Term'),
            'res_model': 'payment.term.generation.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_invoice_id': self.id,
                'default_installment_num': self.installment_num,
                'default_first_payment_amount': self.first_payment,
            }
        }

    def action_create_regular_installment_term(self):
        """Create or get the 'Regular Installment' payment term and optionally assign it"""
        self.ensure_one()
        
        # Get or create Regular Installment payment term
        payment_term = self.env['account.payment.term'].search([('name', '=', 'Regular Installment')], limit=1)
        
        if not payment_term:
            # Create Regular Installment payment term
            payment_term = self.env['account.payment.term'].create({
                'name': 'Regular Installment',
                'note': 'Payment due at the end of next month from invoice date (100% of total amount)',
                'line_ids': [(0, 0, {
                    'value': 'percent',
                    'value_amount': 100.0,
                    'delay_type': 'days_after_end_of_next_month',
                    'nb_days': 0,
                })],
            })
            _logger.info("Created 'Regular Installment' payment term via invoice button")
        
        # Optionally assign it to the invoice if installment_num == 1 and first_payment == 0
        if self.installment_num == 1 and self.first_payment == 0:
            self.invoice_payment_term_id = payment_term.id
            # Auto-generate installments after assigning payment term
            if self.installment_num != 0:
                self._auto_generate_installments()
            message = _('Regular Installment payment term has been created and assigned. Installments generated.')
        else:
            message = _('Regular Installment payment term is available. Set Installments=1 and First Payment=0 to auto-assign it.')
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': message,
                'type': 'success',
                'sticky': False,
            }
        }

    def action_post(self):
        """Override action_post to automatically generate installments after confirmation"""
        result = super().action_post()
        
        # Auto-generate installments after invoice confirmation
        for move in self:
            if move.installment_num > 0 and not move.installment_list_ids:
                move._auto_generate_installments()
                
        return result

    def _check_and_mark_paid_from_installments(self):
        """Check if all installments are paid and mark invoice as paid if so"""
        self.ensure_one()
        
        # Only process invoices that are posted
        if self.state != 'posted':
            return
        
        # Check if invoice is already fully paid
        if self.payment_state in ('paid', 'in_payment'):
            return
        
        # Verify all installments are paid
        all_installments = self.installment_list_ids.filtered(lambda i: i.state != 'cancelled')
        if not all_installments:
            return
        
        paid_installments = all_installments.filtered(lambda i: i.state == 'paid')
        if len(paid_installments) != len(all_installments):
            return
        
        # All installments are paid, mark invoice as paid
        self._mark_invoice_paid_from_installments()

    def _mark_invoice_paid_from_installments(self):
        """Mark invoice as paid when all installments are paid"""
        self.ensure_one()
        
        # Only process customer invoices that are posted
        if self.move_type not in ('out_invoice', 'in_invoice') or self.state != 'posted':
            return
        
        # Check if invoice is already fully paid
        if self.payment_state in ('paid', 'in_payment'):
            return
        
        # Verify all installments are paid
        all_installments = self.installment_list_ids.filtered(lambda i: i.state != 'cancelled')
        if not all_installments:
            return
        
        paid_installments = all_installments.filtered(lambda i: i.state == 'paid')
        if len(paid_installments) != len(all_installments):
            return
        
        # All installments are paid, create a payment to reconcile the invoice
        try:
            # Calculate total paid amount
            total_paid = sum(paid_installments.mapped('amount'))
            
            if total_paid <= 0:
                return
            
            # Get journal for payments
            if self.move_type == 'out_invoice':
                # Customer invoice - use payment journal
                payment_journal = self.env['account.journal'].search([
                    ('type', '=', 'bank'),
                    ('company_id', '=', self.company_id.id)
                ], limit=1)
                if not payment_journal:
                    payment_journal = self.env['account.journal'].search([
                        ('type', 'in', ('bank', 'cash')),
                        ('company_id', '=', self.company_id.id)
                    ], limit=1)
            else:
                # Vendor bill - use bank journal
                payment_journal = self.env['account.journal'].search([
                    ('type', '=', 'bank'),
                    ('company_id', '=', self.company_id.id)
                ], limit=1)
            
            if not payment_journal:
                _logger.warning(f"No payment journal found for company {self.company_id.name}")
                return
            
            # Create payment
            payment_vals = {
                'payment_type': 'inbound' if self.move_type == 'out_invoice' else 'outbound',
                'partner_type': 'customer' if self.move_type == 'out_invoice' else 'supplier',
                'partner_id': self.partner_id.id,
                'amount': total_paid,
                'currency_id': self.currency_id.id,
                'journal_id': payment_journal.id,
                'date': fields.Date.today(),
                'ref': f"Installment payments for {self.name}",
                'invoice_ids': [(4, self.id)],
            }
            
            payment = self.env['account.payment'].create(payment_vals)
            payment.action_post()
            
            # Reconcile the payment with invoice
            (payment.move_id.line_ids + self.line_ids).filtered(
                lambda line: line.account_id == payment.destination_account_id
                and not line.reconciled
            ).reconcile()
            
            _logger.info(f"Invoice {self.name} marked as paid from installments. Payment {payment.name} created and reconciled.")
            
        except Exception as e:
            _logger.error(f"Error marking invoice {self.name} as paid from installments: {e}")
            # Don't raise error, just log it

    def _auto_generate_installments(self):
        """Automatically generate installment list from payment terms after invoice confirmation"""
        for move in self:
            if move.installment_num <= 0:
                continue
            
            # Check if payment term is "Regular Installment"
            is_regular_installment = (
                move.invoice_payment_term_id and 
                move.invoice_payment_term_id.name == 'Regular Installment'
            )
            
            # Generate installments if installment_num != 0 and payment term is Regular Installment
            if move.installment_num != 0 and is_regular_installment:
                try:
                    # Clear existing installment list if any
                    if move.installment_list_ids:
                        move.installment_list_ids.unlink()
                    
                    # Generate based on installment_num with payment term due date logic
                    installment_list = self._generate_from_installment_num_with_payment_term(move)
                    
                    # Create installment records
                    if installment_list:
                        self.env['installment.list'].create(installment_list)
                        _logger.info(f"Auto-generated {len(installment_list)} installments for invoice {move.name} using Regular Installment (based on installment_num={move.installment_num})")
                    else:
                        _logger.warning(f"No installments could be generated for invoice {move.name}")
                        
                except Exception as e:
                    _logger.error(f"Error auto-generating installments for invoice {move.name}: {e}")
            elif move.installment_num > 0:
                # For other payment terms or when payment term doesn't exist
                try:
                    # Clear existing installment list if any
                    if move.installment_list_ids:
                        move.installment_list_ids.unlink()
                    
                    installment_list = []
                    
                    # Method 1: Generate from payment terms if they exist
                    if move.invoice_payment_term_id and move.invoice_payment_term_id.line_ids:
                        installment_list = self._generate_from_payment_terms(move)
                    else:
                        # Method 2: Generate from installment_num field
                        installment_list = self._generate_from_installment_num(move)
                    
                    # Create installment records
                    if installment_list:
                        self.env['installment.list'].create(installment_list)
                        _logger.info(f"Auto-generated {len(installment_list)} installments for invoice {move.name}")
                    else:
                        _logger.warning(f"No installments could be generated for invoice {move.name}")
                        
                except Exception as e:
                    _logger.error(f"Error auto-generating installments for invoice {move.name}: {e}")

    def _generate_from_payment_terms(self, move):
        """Generate installments from payment term lines"""
        installment_list = []
        sequence = 1
        
        # Use invoice date or today's date as reference
        date_ref = move.invoice_date or move.date or fields.Date.today()
        
        for line in move.invoice_payment_term_id.line_ids:
            if line.value == 'percent':
                amount = move.amount_total * line.value_amount / 100
            elif line.value == 'fixed':
                amount = line.value_amount
            else:
                continue
            
            # Calculate due date using payment term line's method
            # This properly handles delay_type like 'days_after_end_of_next_month'
            due_date = line._get_due_date(date_ref)
            
            installment_list.append({
                'name': f"Installment {sequence}",
                'sequence': sequence,
                'invoice_id': move.id,
                'partner_id': move.partner_id.id,
                'amount': amount,
                'due_date': due_date,
                'state': 'pending',
            })
            sequence += 1
        
        return installment_list

    def _generate_from_installment_num_with_payment_term(self, move):
        """Generate installments based on installment_num but use payment term for due date calculation"""
        installment_list = []
        installment_count = int(move.installment_num)
        
        if installment_count <= 0:
            return installment_list
        
        # Use invoice date or today's date as reference
        date_ref = move.invoice_date or move.date or fields.Date.today()
        
        # Get payment term line for due date calculation
        payment_term_line = None
        if move.invoice_payment_term_id and move.invoice_payment_term_id.line_ids:
            payment_term_line = move.invoice_payment_term_id.line_ids[0]  # Use first line
        
        # Calculate amount per installment
        total_amount = move.amount_total
        if move.first_payment > 0:
            # First payment is specified
            remaining_amount = total_amount - move.first_payment
            remaining_installments = installment_count - 1
            if remaining_installments > 0:
                amount_per_installment = remaining_amount / remaining_installments
            else:
                amount_per_installment = 0
        else:
            # Equal installments
            amount_per_installment = total_amount / installment_count
        
        # Generate installments
        for i in range(installment_count):
            if i == 0 and move.first_payment > 0:
                amount = move.first_payment
            else:
                amount = amount_per_installment
            
            # Calculate due date based on payment term line
            if payment_term_line:
                # Use payment term line's due date calculation as base
                base_due_date = payment_term_line._get_due_date(date_ref)
                
                # For subsequent installments after the first, add months
                if i > 0:
                    from dateutil.relativedelta import relativedelta
                    due_date = base_due_date + relativedelta(months=i)
                else:
                    due_date = base_due_date
            else:
                # Fallback: 30 days between installments
                from datetime import timedelta
                due_date = date_ref + timedelta(days=30 * i)
            
            installment_list.append({
                'name': f"Installment {i + 1}",
                'sequence': i + 1,
                'invoice_id': move.id,
                'partner_id': move.partner_id.id,
                'amount': amount,
                'due_date': due_date,
                'state': 'pending',
            })
        
        return installment_list

    def _generate_from_installment_num(self, move):
        """Generate installments from installment_num field when payment terms don't exist"""
        installment_list = []
        installment_count = int(move.installment_num)
        
        if installment_count <= 0:
            return installment_list
        
        # Calculate amount per installment
        total_amount = move.amount_total
        if move.first_payment > 0:
            # First payment is specified
            remaining_amount = total_amount - move.first_payment
            remaining_installments = installment_count - 1
            if remaining_installments > 0:
                amount_per_installment = remaining_amount / remaining_installments
            else:
                amount_per_installment = 0
        else:
            # Equal installments
            amount_per_installment = total_amount / installment_count
        
        # Generate installments
        for i in range(installment_count):
            if i == 0 and move.first_payment > 0:
                amount = move.first_payment
            else:
                amount = amount_per_installment
            
            # Calculate due date (30 days between installments)
            from datetime import timedelta
            due_date = fields.Date.today() + timedelta(days=30 * i)
            
            installment_list.append({
                'name': f"Installment {i + 1}",
                'sequence': i + 1,
                'invoice_id': move.id,
                'partner_id': move.partner_id.id,
                'amount': amount,
                'due_date': due_date,
                'state': 'pending',
            })
        
        return installment_list


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    # Installment fields from sale order line
    installment_num = fields.Float(
        string="Number of Installments",
        default=0.0,
        help="Number of installments for this line"
    )
    first_payment = fields.Monetary(
        string="First Payment Amount",
        default=0.0,
        help="First payment amount for installment calculations"
    )

    @api.model
    def create(self, vals):
        """Override create to transfer installment data from sale order line"""
        line = super().create(vals)
        
        # Transfer installment data from sale order line if available
        if line.sale_line_ids and len(line.sale_line_ids) == 1:
            sale_line = line.sale_line_ids[0]
            if hasattr(sale_line, 'installment_num') and hasattr(sale_line, 'first_payment'):
                line.installment_num = sale_line.installment_num
                line.first_payment = sale_line.first_payment
                _logger.info(f"Transferred installment data from sale line {sale_line.id} to move line {line.id}")
        
        return line

    def write(self, vals):
        """Override write to handle installment data updates"""
        result = super().write(vals)
        
        # Update installment data if sale line is updated
        for line in self:
            if line.sale_line_ids and len(line.sale_line_ids) == 1:
                sale_line = line.sale_line_ids[0]
                if hasattr(sale_line, 'installment_num') and hasattr(sale_line, 'first_payment'):
                    if line.installment_num != sale_line.installment_num or line.first_payment != sale_line.first_payment:
                        line.installment_num = sale_line.installment_num
                        line.first_payment = sale_line.first_payment
                        _logger.info(f"Updated installment data for move line {line.id}")
        
        return result
