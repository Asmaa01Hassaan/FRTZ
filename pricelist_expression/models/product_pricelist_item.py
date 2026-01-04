# -*- coding: utf-8 -*-
from odoo import fields, models, _
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import ValidationError
import logging
import math
import re
_logger = logging.getLogger(__name__)

class ProductPricelistItem(models.Model):
    _inherit = "product.pricelist.item"

    compute_price = fields.Selection(
        selection_add=[('expression', 'Expression')],
        ondelete={'expression': 'set default'},
    )

    price_expression = fields.Char(
        string="Expression",
        help=(
            "Python expression that returns the final unit price.\n"
            "Available variables:\n"
            "price → base price\n"
            "cost → standard cost\n"
            "purchase_price → purchase price (same as cost)\n"
            "qty → quantity\n"
            "installment_num → number of installments\n"
            "first_payment → first payment amount\n"
            "ceil(x) → round up to next integer\n"
            "round(x, n) → normal rounding"
        ),
    )

    payment_type = fields.Selection(
        [
            ('immediate', _('Immediate Payment')),
            ('regular', _('Regular Installments')),
            ('irregular', _('Irregular Installments')),
        ],
        string=_("Payment plan"),
        default="immediate",
        help=_("Select the payment plan for this pricelist rule")
    )

    def _compute_price(self, *args, **kwargs):
        """Compute price using expression if configured"""
        base_price = super()._compute_price(*args, **kwargs)

        product = args[0] if len(args) >= 1 else kwargs.get("product")
        quantity = args[1] if len(args) >= 2 else kwargs.get("quantity", 1.0)

        if self.compute_price == "expression" and self.price_expression:
            try:
                # Get product cost and purchase price safely
                cost = 0.0
                purchase_price = 0.0
                if product:
                    cost = float(getattr(product, "standard_price", 0.0) or 0.0)
                    purchase_price = cost  # purchase_price is same as standard_price (cost)
                
                # Helper function for conditional expressions (SQL-style: if(condition, true_value, false_value))
                def iff(condition, true_value, false_value):
                    """Conditional expression: returns true_value if condition is True, else false_value"""
                    return float(true_value) if condition else float(false_value)
                
                # Preprocess expression: replace if( with iff( to avoid Python keyword conflict
                # This allows users to write if(condition, true, false) which gets converted to iff(condition, true, false)
                expression = str(self.price_expression).strip()
                # Replace if( with iff( using word boundary to avoid replacing "if " or other variations
                expression = re.sub(r'\bif\s*\(', 'iff(', expression)
                
                env = {
                    "price": float(base_price or 0.0),
                    "cost": cost,
                    "purchase_price": purchase_price,  # Purchase price (same as cost/standard_price)
                    "qty": float(quantity or 0.0),
                    "installment_num": float(self.env.context.get("installment_num", 0.0) or 0.0),
                    "first_payment": float(self.env.context.get("first_payment", 0.0) or 0.0),
                    "round": round,
                    "ceil": math.ceil,
                    "iff": iff,  # Conditional function: iff(condition, true_value, false_value)
                }
                
                new_price = float(safe_eval(expression, env, nocopy=True))
                _logger.debug(f"Expression pricing: {self.price_expression} -> {new_price} (processed: {expression})")
                return new_price
                
            except Exception as e:
                _logger.error(f"Error evaluating price expression '{self.price_expression}': {e}")
                # Return base price as fallback
                return base_price

        return base_price
