from odoo import models, fields, api

class SaleOrder(models.Model):
    _inherit = "sale.order"

    invoice_per_line = fields.Boolean(
        string="Invoice Per Line",
        help="If enabled, 'Create Invoice' will generate a separate invoice for each invoiceable order line.",
        default=False,
        tracking=True,
    )

    def _create_invoices(self, grouped=False, final=False):
        """
        If invoice_per_line is True on an order, generate ONE invoice per invoiceable order line.
        Otherwise, fallback to the standard behavior for that order.
        MUST return an account.move recordset (not an action).
        """
        AccountMove = self.env["account.move"]
        AccountMoveLine = self.env["account.move.line"]

        all_invoices = AccountMove.browse()

        for order in self:
            # لو الاختيار مش مفعّل على الأمر ده → سلوك Odoo الافتراضي للأمر المعني فقط
            if not order.invoice_per_line:
                # نستخدم super على الـ record الفردي (مش على self كله)
                invoices_std = super(SaleOrder, order)._create_invoices(grouped=grouped, final=final)
                all_invoices |= invoices_std
                continue

            # السطور القابلة للفوترة فقط
            lines_to_invoice = order.order_line.filtered(
                lambda l: not l.display_type and l.qty_to_invoice > 0
            )
            if not lines_to_invoice:
                # مفيش سطور تتفوّر — نضيف ولا حاجة ونكمل
                continue

            for so_line in lines_to_invoice:
                # 1) رأس الفاتورة (يحترم partner/currency/company/fpos ...)
                inv_vals = order._prepare_invoice()
                invoice = AccountMove.create(inv_vals)

                # 2) سطر الفاتورة من سطر البيع
                line_vals = so_line._prepare_invoice_line()
                line_vals.update({
                    "move_id": invoice.id,
                    "sale_line_ids": [(6, 0, [so_line.id])],  # للـ traceability
                })
                AccountMoveLine.create(line_vals)

                # 3) إعادة حساب مرنة (تناسب اختلافات الإصدارات/الفوركات)
                recomputed = False
                for m in ('_recompute_dynamic_lines',):
                    if hasattr(invoice, m):
                        getattr(invoice, m)(recompute_all_taxes=True)
                        recomputed = True
                        break
                if not recomputed:
                    if hasattr(invoice, '_recompute_payment_terms_lines'):
                        invoice._recompute_payment_terms_lines()
                    if hasattr(invoice, '_recompute_tax_lines'):
                        invoice._recompute_tax_lines()
                    if hasattr(invoice, '_compute_amount'):
                        invoice._compute_amount()

                all_invoices |= invoice

        # IMPORTANT: لازم نرجّع recordset من account.move
        return all_invoices
