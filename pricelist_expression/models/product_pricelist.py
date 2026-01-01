# -*- coding: utf-8 -*-
from odoo import models
import logging

_logger = logging.getLogger(__name__)

class ProductPricelist(models.Model):
    _inherit = "product.pricelist"

    def _compute_price_rule(self, products_qty_partner, date=False, uom_id=False, **kwargs):
        """Enhanced price rule computation with installment support"""
        res = super()._compute_price_rule(products_qty_partner, date=date, uom_id=uom_id, **kwargs)

        # Skip if only rule selection is requested (not price computation)
        if kwargs.get("compute_price") is False:
            return res

        # Log installment context for debugging
        installment_num = float(self._context.get('installment_num', 0.0) or 0.0)
        payment_type = self._context.get('payment_type')
        if installment_num > 0 or payment_type:
            _logger.debug(f"Computing prices with context: installment_num={installment_num}, payment_type={payment_type}")

        return res

    def _get_applicable_rules_domain(self, products, date, **kwargs):
        """Override to add payment_type filtering"""
        domain = super()._get_applicable_rules_domain(products=products, date=date, **kwargs)
        
        # Get payment_type from context
        payment_type = self._context.get('payment_type')
        
        if payment_type:
            # Filter: pricelist items with matching payment_type OR no payment_type (fallback)
            # Domain: ('payment_type', 'in', [False, payment_type])
            # This means: payment_type is False (empty) OR payment_type matches
            domain.append(('payment_type', 'in', [False, payment_type]))
            _logger.debug(f"Filtering pricelist items by payment_type: {payment_type}")
        # If no payment_type in context, don't filter - show all items (backward compatibility)
        
        return domain

    def _get_applicable_rules(self, products, date, **kwargs):
        """Override to filter by payment_type after getting rules"""
        rules = super()._get_applicable_rules(products=products, date=date, **kwargs)
        
        # Additional filtering as safety measure (domain should handle it, but this ensures correctness)
        payment_type = self._context.get('payment_type')
        if payment_type:
            # Filter rules: must have matching payment_type OR no payment_type (fallback)
            filtered_rules = rules.filtered(
                lambda r: not r.payment_type or r.payment_type == payment_type
            )
            if len(filtered_rules) != len(rules):
                _logger.debug(f"Filtered {len(rules)} rules to {len(filtered_rules)} by payment_type={payment_type}")
            return filtered_rules
        
        return rules
