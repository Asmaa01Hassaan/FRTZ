# -*- coding: utf-8 -*-
import math
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = "account.move"

    # تشغيل التقسيط على الفاتورة
    apply_installment = fields.Boolean(string="Apply Installment")

    # عدد الأقساط المقترح/المطلوب (fallback لو مش محدد مبلغ القسط)
    number_of_installments = fields.Integer(string="Number of Installments", default=1)

    # تاريخ أول/أقرب قسط
    next_due_date = fields.Date(string="Next Due Date")



    # قيمة القسط الواحد (لو اتحددت، هنولّد الأقساط بناءً عليها)
    installment_amount = fields.Monetary(
        string="Installment Amount",
        help="If set, installments will be generated using this fixed amount; "
             "the last installment adjusts rounding differences."
    )

    # المتبقي الواجب سداده (مرجعي/حسابي)
    installment_payable = fields.Monetary(
        string="Installment Payable",
        compute="_compute_installment_payable",
        help="For posted invoices, this shows the residual. "
             "For draft, it shows total minus paid installments."
    )

    # الأقساط المرتبطة بالفاتورة
    installment_ids = fields.One2many(
        "account.move.installment", "move_id", string="Installments"
    )

    # عداد للأقساط (اختياري للعرض)
    installment_count = fields.Integer(compute="_compute_installment_count")

    # -----------------------------
    #        COMPUTES / HELPERS
    # -----------------------------
    def _compute_installment_count(self):
        for rec in self:
            rec.installment_count = len(rec.installment_ids)

    def _compute_installment_payable(self):
        """لو الفاتورة posted نعرض residual الحقيقي؛ وإلا نحسب إجمالي-مدفوع."""
        for rec in self:
            currency = rec.currency_id or self.env.company.currency_id
            if rec.state == 'posted':
                # المتبقي في أودو مظبوط أصلاً
                val = abs(rec.amount_residual)
            else:
                total = abs(rec.amount_total)
                paid = sum(abs(i.amount) for i in rec.installment_ids.filtered(lambda r: r.state == 'paid'))
                val = max(total - paid, 0.0)
            rec.installment_payable = currency.round(val)

    def _installment_base_amount(self):
        """أساس القسمة: المتبقي لو Posted، وإلا الإجمالي. دائماً موجب."""
        self.ensure_one()
        if self.state == 'posted':
            return abs(self.amount_residual)
        return abs(self.amount_total)

    def _compute_amount_splits_from_installment_amount(self):
        """
        يبني قائمة مبالغ الأقساط من قيمة قسط ثابتة (installment_amount)،
        آخر قسط يتظبط لأي فروق Rounding. دائماً ترجع مبالغ موجبة.
        """
        self.ensure_one()
        currency = self.currency_id
        remaining = self._installment_base_amount()

        if not self.installment_amount or self.installment_amount <= 0:
            raise UserError(_("Please set a positive 'Installment Amount'."))

        # عدد الأقساط = سقف(المتبقي / قيمة القسط)
        n = max(1, int(math.ceil(remaining / self.installment_amount)))

        splits = []
        # أقساط متساوية (مقربة لعملة الفاتورة)
        for _ in range(n - 1):
            splits.append(currency.round(self.installment_amount))

        # آخر قسط = المتبقي - مجموع السابق
        last = currency.round(remaining - sum(splits))
        if last <= 0 and splits:
            # حالات نادرة جداً مع التقريب
            splits[-1] = currency.round(splits[-1] + last)
        else:
            splits.append(last)

        # تسوية نهائية لأي فرق rounding بايتات
        diff = currency.round(remaining - sum(splits))
        if diff != 0 and splits:
            splits[-1] = currency.round(splits[-1] + diff)

        # نرجع مبالغ موجبة فقط — نوع الحركة (invoice/refund) يتحدد لاحقاً في register payment
        splits = [abs(currency.round(x)) for x in splits]
        return splits

    @api.onchange('installment_amount')
    def _onchange_installment_amount_set_n(self):
        """
        بمجرد تغيير قيمة القسط، نقترح عدد الأقساط تلقائيًا من المتبقي/الإجمالي.
        """
        for inv in self:
            if inv.installment_amount and inv.installment_amount > 0:
                base = inv._installment_base_amount()
                inv.number_of_installments = max(
                    1, int(math.ceil(base / inv.installment_amount))
                )

    # -----------------------------
    #             ACTIONS
    # -----------------------------
    def action_generate_installments(self):
        """
        يولّد الأقساط:
          - لو installment_amount موجودة وموجبة → نستخدمها لتوليد Splits.
          - وإلا → نقسم بالتساوي على number_of_installments (مع تسوية آخر قسط).
        التواريخ: افتراضي شهري متتابع من next_due_date.
        """
        for inv in self:
            # صلاحية
            if inv.move_type not in ('out_invoice', 'out_refund'):
                raise UserError(_("Installments are supported only for Customer Invoices/Credit Notes."))
            if inv.state != 'posted':
                raise UserError(_("Please post the invoice before generating installments."))
            if not inv.apply_installment:
                raise UserError(_("Enable 'Apply Installment' first."))
            if not inv.next_due_date:
                raise UserError(_("Please set the Next Due Date."))

            # امسح أي أقساط قديمة لتجنّب التكرار
            inv.installment_ids.unlink()

            currency = inv.currency_id
            base_amount = inv._installment_base_amount()  # موجب

            if base_amount == 0.0:
                raise UserError(_("Nothing to schedule: the invoice residual is zero."))

            # 1) بالحجم الثابت لو متوفر
            if inv.installment_amount and inv.installment_amount > 0:
                amounts = inv._compute_amount_splits_from_installment_amount()
                n = len(amounts)
            else:
                # 2) بالعدد
                if not inv.number_of_installments or inv.number_of_installments < 1:
                    raise UserError(_("Number of installments must be at least 1."))
                n = inv.number_of_installments
                per = currency.round(base_amount / n)
                amounts = [per for _ in range(n)]
                # سوّي آخر قسط لأي فرق
                diff = currency.round(base_amount - sum(amounts))
                amounts[-1] = currency.round(amounts[-1] + diff)
                amounts = [abs(currency.round(x)) for x in amounts]

            # إنشاء السطور + تواريخ شهرية
            date = inv.next_due_date
            lines = []
            for idx, amt in enumerate(amounts, start=1):
                lines.append((0, 0, {
                    "name": _("Installment %s/%s", idx, n),
                    "payment_date": date,
                    "amount": amt,  # دائماً موجب
                    "currency_id": inv.currency_id.id,
                    "state": "draft",
                }))
                date = date + relativedelta(months=1)

            inv.write({"installment_ids": lines})
