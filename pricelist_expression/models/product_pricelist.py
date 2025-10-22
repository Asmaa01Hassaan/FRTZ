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
        if installment_num > 0:
            _logger.debug(f"Computing prices with installment context: installment_num={installment_num}")

        return res
