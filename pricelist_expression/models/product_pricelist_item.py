# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.tools.safe_eval import safe_eval
import math

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
        help="Python expression that returns the final unit price. Vars: price, cost, qty, installment_num, round(), math",
    )

    # ✅ توقيع مرن: ناخد أي args/kwargs، ونمررها كما هي للسوبر
    def _compute_price(self, *args, **kwargs):
        # 1) نادِ السوبر بالضبط بنفس التوقيع اللي جالك (بدون إضافة partner/currency بالاسم)
        base_price = super()._compute_price(*args, **kwargs)

        # 2) استخرج product و quantity بأمان من args/kwargs (أول اتنين positional عادة)
        product = None
        quantity = None
        if len(args) >= 1:
            product = args[0]
        if len(args) >= 2:
            quantity = args[1]
        if product is None:
            product = kwargs.get("product")
        if quantity is None:
            quantity = kwargs.get("quantity", 1.0)

        _dbg(f"item._compute_price: item={self.id}, type={self.compute_price}, "
             f"product={getattr(product,'display_name',product)}({getattr(product,'id','?')}), "
             f"qty={quantity}, base_price={base_price}")

        # 3) لو النوع Expression، طبّق المعادلة
        if self.compute_price == "expression" and self.price_expression:
            env = {
                "price": float(base_price or 0.0),
                "cost": float(getattr(product, "standard_price", 0.0) or 0.0),
                "qty": float(quantity or 0.0),
                "installment_num": float(self.env.context.get("installment_num", 0.0) or 0.0),
                "round": round,
            }

            _dbg(f"   expr='{self.price_expression}', env={{price:{env['price']}, cost:{env['cost']}, qty:{env['qty']}, installment_num:{env['installment_num']}}}")
            try:
                new_price = float(safe_eval(self.price_expression, env, nocopy=True))
                _dbg(f"   -> new_price={new_price}")
                return new_price
            except Exception as e:
                _dbg(f"   ERROR evaluating expression: {e}")
                return base_price

        return base_price

