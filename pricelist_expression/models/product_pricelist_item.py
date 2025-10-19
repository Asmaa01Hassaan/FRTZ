# -*- coding: utf-8 -*-
from odoo import fields, models, _
from odoo.tools.safe_eval import safe_eval

DEBUG_PLEXPR = True
def _dbg(msg):
    if DEBUG_PLEXPR:
        print(f"[PLEXPR] {msg}", flush=True)

class ProductPricelistItem(models.Model):
    _inherit = "product.pricelist.item"

    compute_price = fields.Selection(
        selection_add=[('expression', 'Expression')],
        ondelete={'expression': 'set default'},
    )

    price_expression = fields.Char(
        string="Expression",
        help="Python expression that returns the final unit price. Vars: price, cost, qty, installment_num, first_payment, round()",
    )

    def _compute_price(self, *args, **kwargs):
        base_price = super()._compute_price(*args, **kwargs)

        product = args[0] if len(args) >= 1 else kwargs.get("product")
        quantity = args[1] if len(args) >= 2 else kwargs.get("quantity", 1.0)

        _dbg(f"item._compute_price: item={self.id}, type={self.compute_price}, "
             f"product={getattr(product,'display_name',product)}({getattr(product,'id','?')}), "
             f"qty={quantity}, base_price={base_price}")

        if self.compute_price == "expression" and self.price_expression:
            env = {
                "price": float(base_price or 0.0),
                "cost": float(getattr(product, "standard_price", 0.0) or 0.0),
                "qty": float(quantity or 0.0),
                "installment_num": float(self.env.context.get("installment_num", 0.0) or 0.0),
                "first_payment":   float(self.env.context.get("first_payment",   0.0) or 0.0),  # ✅ جديد
                "round": round,
            }
            _dbg("   expr='%s', env={price:%s, cost:%s, qty:%s, installment_num:%s, first_payment:%s}" %
                 (self.price_expression, env["price"], env["cost"], env["qty"], env["installment_num"], env["first_payment"]))
            try:
                new_price = float(safe_eval(self.price_expression, env, nocopy=True))
                _dbg(f"   -> new_price={new_price}")
                return new_price
            except Exception as e:
                _dbg(f"   ERROR evaluating expression: {e}")
                return base_price

        return base_price
