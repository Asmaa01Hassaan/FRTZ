# -*- coding: utf-8 -*-
from odoo import fields, models, _
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

class ProductPricelistItem(models.Model):
    _inherit = "product.pricelist.item"

    compute_price = fields.Selection(
        selection_add=[('expression', 'Expression')],
        ondelete={'expression': 'set default'},
    )

    price_expression = fields.Char(
        string="Expression",
        help="Python expression that returns the final unit price. Available variables: price, cost, qty, installment_num, first_payment, round()",
    )

    def _compute_price(self, *args, **kwargs):
        """Compute price using expression if configured"""
        base_price = super()._compute_price(*args, **kwargs)

        product = args[0] if len(args) >= 1 else kwargs.get("product")
        quantity = args[1] if len(args) >= 2 else kwargs.get("quantity", 1.0)

        if self.compute_price == "expression" and self.price_expression:
            try:
                env = {
                    "price": float(base_price or 0.0),
                    "cost": float(getattr(product, "standard_price", 0.0) or 0.0),
                    "qty": float(quantity or 0.0),
                    "installment_num": float(self.env.context.get("installment_num", 0.0) or 0.0),
                    "first_payment": float(self.env.context.get("first_payment", 0.0) or 0.0),
                    "round": round,
                }
                
                new_price = float(safe_eval(self.price_expression, env, nocopy=True))
                _logger.debug(f"Expression pricing: {self.price_expression} -> {new_price}")
                return new_price
                
            except Exception as e:
                _logger.error(f"Error evaluating price expression '{self.price_expression}': {e}")
                # Return base price as fallback
                return base_price

        return base_price
