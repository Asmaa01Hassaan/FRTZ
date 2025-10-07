# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class ProductPricelistItem(models.Model):
    _inherit = "product.pricelist.item"

    compute_price = fields.Selection(
        selection_add=[("adv_formula", "Adv-formule")],
        ondelete={"adv_formula": "set default"},
    )

    adv_formula = fields.Text(
        string="Advanced Formula",
        help=(
            "Write a Python-like expression to compute the unit price.\n"
            "Available variables: price, list_price, cost, qty, uom, date, "
            "partner, product, category, currency_rate.\n"
            "Example: price * (0.9 if qty >= 10 else 1.0)"
        ),
    )
    currency_id = fields.Many2one(
        "res.currency",
        related="pricelist_id.currency_id",
        readonly=True,
        store=False,
    )
    test_product_id = fields.Many2one("product.product", string="Preview Product")
    test_qty = fields.Float(string="Preview Qty", default=1.0)

    adv_preview_price = fields.Monetary(
        string="Preview Price",
        currency_field="currency_id",
        compute="_compute_adv_preview_price",
        help="Computed using the current formula for the selected Preview Product/Qty.",
    )

    @api.depends("compute_price", "adv_formula", "test_product_id", "test_qty")
    def _compute_adv_preview_price(self):
        for rec in self:
            price = 0.0
            if rec.compute_price == "adv_formula" and rec.test_product_id:
                # Let the pricelist engine compute (your override will kick in)
                res = rec.pricelist_id._compute_price_rule(
                    rec.test_product_id, rec.test_qty or 1.0, False
                )
                price = res.get(rec.test_product_id.id, (0.0, False))[0]
            rec.adv_preview_price = price


    @api.constrains("compute_price", "adv_formula")
    def _check_adv_formula(self):
        """Quick static validation: must have some text if adv_formula selected."""
        for rec in self:
            if rec.compute_price == "adv_formula":
                if not (rec.adv_formula or "").strip():
                    raise ValidationError(_("Please enter a formula for Adv-formule."))

    @api.onchange("compute_price")
    def _onchange_compute_price_clear_adv(self):
        if self.compute_price != "adv_formula":
            self.adv_formula = False
