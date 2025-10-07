# -*- coding: utf-8 -*-
from odoo import models

DEBUG_PLEXPR = True
def _dbg(msg):
    if DEBUG_PLEXPR:
        print(f"[PLEXPR] {msg}", flush=True)

class ProductPricelist(models.Model):
    _inherit = "product.pricelist"

    def _compute_price_rule(self, products_qty_partner, date=False, uom_id=False, **kwargs):
        _dbg(f"_compute_price_rule called, kwargs={kwargs}")
        res = super()._compute_price_rule(products_qty_partner, date=date, uom_id=uom_id, **kwargs)

        # ده نداء لاختيار القاعدة بس (مش لحساب السعر)
        if kwargs.get("compute_price") is False:
            _dbg("compute_price=False -> returning super() result as-is")
            return res

        _dbg(f"context.installment_num={float(self._context.get('installment_num', 0.0) or 0.0)}")

        # طباعة سريعة للنتيجة من غير تعديل عشان التتبع
        for product, qty, partner in products_qty_partner:
            if product.id in res:
                val = res[product.id]
                shape = "new(price,item)" if (len(val) >= 2 and getattr(val[1], "_name", False)) else "old(rule_id,price)"
                _dbg(f"-> product={product.display_name}({product.id}), qty={qty}, result_shape={shape}, val={val}")
        return res
