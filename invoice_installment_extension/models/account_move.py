# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


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
