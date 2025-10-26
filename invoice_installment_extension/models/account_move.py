# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


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
                
        return result

    def _auto_generate_payment_terms(self):
        """Automatically generate payment terms based on installment data"""
        for move in self:
            if move.installment_num <= 0:
                continue
                
            try:
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

    def action_post(self):
        """Override action_post to automatically generate installments after confirmation"""
        result = super().action_post()
        
        # Auto-generate installments after invoice confirmation
        for move in self:
            if move.installment_num > 0 and not move.installment_list_ids:
                move._auto_generate_installments()
                
        return result

    def _auto_generate_installments(self):
        """Automatically generate installment list from payment terms after invoice confirmation"""
        for move in self:
            if move.installment_num <= 0:
                continue
                
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
        
        for line in move.invoice_payment_term_id.line_ids:
            if line.value == 'percent':
                amount = move.amount_total * line.value_amount / 100
            elif line.value == 'fixed':
                amount = line.value_amount
            else:
                continue
            
            # Calculate due date
            due_date = fields.Date.today()
            if line.nb_days > 0:
                from datetime import timedelta
                due_date = due_date + timedelta(days=line.nb_days)
            
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
