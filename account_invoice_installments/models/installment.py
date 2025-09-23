# models/installment.py (مقتطف)
from odoo import fields, models, _

class AccountMoveInstallment(models.Model):
    _name = "account.move.installment"
    _description = "Invoice Installment"
    _order = "payment_date, id"

    name = fields.Char(required=True)
    move_id = fields.Many2one("account.move", required=True, ondelete="cascade")
    partner_id = fields.Many2one(related="move_id.partner_id", store=True)
    currency_id = fields.Many2one(related="move_id.currency_id", store=True)
    payment_date = fields.Date(required=True)
    amount = fields.Monetary(required=True)
    state = fields.Selection([
        ("draft", "Draft"),
        ("paid", "Paid"),
        ("cancel", "Cancelled"),
    ], default="draft")
    payment_id = fields.Many2one("account.payment", string="Payment", readonly=True)

    def action_open_payment_wizard(self):
        self.ensure_one()
        if self.state == 'paid' and self.payment_id:
            return {
                "type": "ir.actions.act_window",
                "res_model": "account.payment",
                "view_mode": "form",
                "res_id": self.payment_id.id,
                "target": "current",
            }
        return {
            "type": "ir.actions.act_window",
            "name": _("Create Payment"),
            "res_model": "installment.payment.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_installment_id": self.id,
                "default_amount": self.amount,
                "default_memo": self.name,
            }
        }
