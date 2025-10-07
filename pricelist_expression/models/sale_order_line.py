from odoo import api, fields, models

DEBUG_PLEXPR = True
def _dbg(msg):
    if DEBUG_PLEXPR:
        print(f"[PLEXPR] {msg}", flush=True)

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    installment_num = fields.Float(string="Installments", default=0.0)

    # بدل super(): ابنِ الكونتكست يدويًا
    def _get_pricelist_context(self):
        ctx = dict(self.env.context or {})
        try:
            if self.order_id and hasattr(self.order_id, "_get_pricelist_context"):
                ctx.update(self.order_id._get_pricelist_context())
        except Exception:
            pass
        ctx["installment_num"] = float(self.installment_num or 0.0)
        _dbg(f"_get_pricelist_context: line_id={self.id or 'new'}, "
             f"order_id={self.order_id.id or 'new'}, installment_num={ctx['installment_num']}")
        return ctx

    # ✅ هيلبر مركزي لإعادة التسعير
    def _recompute_price_from_installments(self):
        for line in self:
            if not line.product_id or not line.order_id or not line.order_id.pricelist_id:
                _dbg("skip recompute: missing product/pricelist/order")
                continue
            ctx = line._get_pricelist_context()
            price = super(SaleOrderLine, line.with_context(ctx))._get_pricelist_price()
            _dbg(f"recompute -> price={price} (installment_num={ctx.get('installment_num')})")
            line.price_unit = price

    # 🔁 onchange على الأقساط
    @api.onchange('installment_num')
    def _onchange_installment_num(self):
        _dbg("onchange installment_num -> recompute price")
        self._recompute_price_from_installments()

    # 🔁 onchange على المنتج/الوحدة/الكمية علشان بعد اختيار المنتج نعيد التسعير بالـ context الجديد
    @api.onchange('product_id', 'product_uom', 'product_uom_qty')
    def _onchange_product_or_qty(self):
        _dbg("onchange product/uom/qty -> recompute price")
        self._recompute_price_from_installments()

    # 💾 عند الإنشاء والكتابة (الحفظ) أعد التسعير لو القيم المهمة اتغيّرت
    @api.model
    def create(self, vals):
        line = super().create(vals)
        if any(k in vals for k in ('installment_num','product_id','product_uom','product_uom_qty')):
            line._recompute_price_from_installments()
        return line

    def write(self, vals):
        res = super().write(vals)
        if any(k in vals for k in ('installment_num','product_id','product_uom','product_uom_qty','order_id')):
            self._recompute_price_from_installments()
        return res

    # (اختياري – للتشخيص) اطبع القاعدة المختارة والسعر النهائي
    def _get_pricelist_price(self):
        if not self.product_id or not self.order_id or not self.order_id.pricelist_id:
            print("[PLEXPR] sale.order.line._get_pricelist_price: missing product/pricelist "
                  f"(product_id={getattr(self.product_id,'id',None)}, "
                  f"pl={getattr(self.order_id.pricelist_id,'id',None)}) -> keep price_unit={self.price_unit}", flush=True)
            return self.price_unit or 0.0

        ctx = self._get_pricelist_context()
        line_ctx = self.with_context(ctx)

        print(f"[PLEXPR] picked item: id={getattr(self.pricelist_item_id,'id',None)}, "
              f"type={getattr(self.pricelist_item_id,'compute_price',None)}, "
              f"expr={getattr(self.pricelist_item_id,'price_expression',None)}, "
              f"installment_num(ctx)={ctx.get('installment_num')}", flush=True)

        price = super(SaleOrderLine, line_ctx)._get_pricelist_price()
        print(
            "[PLEXPR] sale.order.line._get_pricelist_price: "
            f"order_pl={getattr(self.order_id.pricelist_id,'id',None)}/{getattr(self.order_id.pricelist_id,'name',None)}, "
            f"product_id={getattr(self.product_id,'id',None)}, qty={self.product_uom_qty}, "
            f"item_id={getattr(self.pricelist_item_id,'id',False)}, final_price={price}",
            flush=True
        )
        return price