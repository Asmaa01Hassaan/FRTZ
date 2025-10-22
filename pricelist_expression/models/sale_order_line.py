# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
import logging

_logger = logging.getLogger(__name__)

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    installment_num = fields.Float(
        string="Installments", 
        default=0.0,
        help="Number of installments for this line"
    )
    first_payment = fields.Float(
        string="First Payment", 
        default=0.0,
        help="First payment amount for installment calculations"
    )

    def _get_pricelist_context(self):
        """Build pricing context with installment information"""
        ctx = dict(self.env.context or {})
        try:
            if self.order_id and hasattr(self.order_id, "_get_pricelist_context"):
                ctx.update(self.order_id._get_pricelist_context())
        except Exception as e:
            _logger.warning(f"Error getting pricelist context from order: {e}")
        
        ctx["installment_num"] = float(self.installment_num or 0.0)
        ctx["first_payment"] = float(self.first_payment or 0.0)
        
        _logger.debug(f"Pricelist context: line_id={self.id or 'new'}, "
                     f"installment_num={ctx['installment_num']}, "
                     f"first_payment={ctx['first_payment']}")
        return ctx

    def _recompute_price_from_installments(self):
        """Recompute price based on installment information"""
        for line in self:
            if not line.product_id or not line.order_id or not line.order_id.pricelist_id:
                _logger.debug("Skipping price recompute: missing product/pricelist/order")
                continue
            
            try:
                ctx = line._get_pricelist_context()
                price = super(SaleOrderLine, line.with_context(ctx))._get_pricelist_price()
                line.price_unit = price
                _logger.debug(f"Price recomputed: {price} "
                            f"(installment_num={ctx.get('installment_num')}, "
                            f"first_payment={ctx.get('first_payment')})")
            except Exception as e:
                _logger.error(f"Error recomputing price for line {line.id}: {e}")

    @api.onchange('installment_num')
    @api.onchange('first_payment')
    def _onchange_installment_related(self):
        """Recompute price when installment fields change"""
        _logger.debug("Onchange installment_num/first_payment -> recompute price")
        self._recompute_price_from_installments()

    @api.onchange('product_id', 'product_uom', 'product_uom_qty')
    def _onchange_product_or_qty(self):
        """Recompute price when product, UOM, or quantity changes"""
        _logger.debug("Onchange product/uom/qty -> recompute price")
        self._recompute_price_from_installments()

    @api.model
    def create(self, vals):
        """Create line and recompute price if needed"""
        line = super().create(vals)
        if any(k in vals for k in ('installment_num', 'first_payment', 'product_id', 'product_uom', 'product_uom_qty')):
            line._recompute_price_from_installments()
        return line

    def write(self, vals):
        """Update line and recompute price if needed"""
        res = super().write(vals)
        if any(k in vals for k in ('installment_num', 'first_payment', 'product_id', 'product_uom', 'product_uom_qty', 'order_id')):
            self._recompute_price_from_installments()
        return res

    def _get_pricelist_price(self):
        """Get pricelist price with installment context"""
        if not self.product_id or not self.order_id or not self.order_id.pricelist_id:
            _logger.debug(f"Missing product/pricelist for line {self.id} -> keeping price_unit={self.price_unit}")
            return self.price_unit or 0.0

        ctx = self._get_pricelist_context()
        line_ctx = self.with_context(ctx)

        _logger.debug(f"Pricelist item: id={getattr(self.pricelist_item_id, 'id', None)}, "
                     f"type={getattr(self.pricelist_item_id, 'compute_price', None)}, "
                     f"installment_num={ctx.get('installment_num')}, "
                     f"first_payment={ctx.get('first_payment')}")

        price = super(SaleOrderLine, line_ctx)._get_pricelist_price()
        _logger.debug(f"Final price: {price} for product {self.product_id.id}, "
                     f"qty={self.product_uom_qty}, item_id={getattr(self.pricelist_item_id, 'id', False)}")
        return price
