# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval


class InstallmentPaymentWizard(models.TransientModel):
    _name = "installment.payment.wizard"
    _description = "Create payment for installment"

    installment_id = fields.Many2one("account.move.installment", required=True, ondelete="cascade")
    move_id = fields.Many2one(related="installment_id.move_id", store=False)
    partner_id = fields.Many2one(related="installment_id.partner_id", store=False)
    amount = fields.Monetary(string="Amount", related="installment_id.amount", readonly=True)
    currency_id = fields.Many2one(related="installment_id.currency_id", store=False)
    journal_id = fields.Many2one(
        "account.journal",
        string="Journal",
        required=True,
        domain="[('type','in',('bank','cash'))]"
    )
    memo = fields.Char(string="Memo")

    def _extract_payment_from_action(self, action):
        """حاول تطلع payment(s) من الـ action اللي رجعه register._create_payments()."""
        Payment = self.env["account.payment"]
        if not isinstance(action, dict):
            return Payment

        # 1) لو في res_id (حالة دفع واحد)
        res_id = action.get("res_id")
        if res_id:
            return Payment.browse(res_id)

        # 2) لو في domain زي [('id','in',[...])]
        domain = action.get("domain")
        if domain:
            try:
                dom = safe_eval(domain) if isinstance(domain, str) else domain
            except Exception:
                dom = []
            if isinstance(dom, (list, tuple)):
                for cond in dom:
                    if (isinstance(cond, (list, tuple))
                        and len(cond) >= 3
                        and cond[0] == "id"
                        and cond[1] == "in"
                        and isinstance(cond[2], (list, tuple))):
                        ids = list(cond[2])
                        if ids:
                            return Payment.browse(ids)
        return Payment.browse()

    def action_create_payment(self):
        self.ensure_one()
        installment = self.installment_id
        move = installment.move_id

        if move.state != 'posted':
            raise UserError(_("Invoice must be posted."))

        # استخدم Register Payment لضمان القيود والمطابقة الصحيحة
        register = self.env["account.payment.register"].with_context(
            active_model="account.move",
            active_ids=[move.id],
        ).create({
            "amount": self.amount,
            "payment_date": installment.payment_date or fields.Date.context_today(self),
            "communication": self.memo or installment.name,
            "journal_id": self.journal_id.id,
        })

        action = register._create_payments()  # ينشئ و(عادة) يرحّل و يعمل reconciliation

        # التقط الـ payment(s) من الـ action
        payments = self._extract_payment_from_action(action)

        # Fallback لو الـ action ما احتوى IDs لأي سبب
        if not payments:
            payments = self.env["account.payment"].search([
                ("partner_id", "=", move.partner_id.id),
                ("journal_id", "=", self.journal_id.id),
                ("amount", "=", self.amount),
            ], order="id desc", limit=1)

        # اربط القسط بأحدث دفع وعلّمه Paid
        if payments:
            payment = payments[0]
            installment.write({
                "payment_id": payment.id,
                "state": "paid",
            })

        # افتح شاشة الدفع (زي ما رجّع register)
        return action
