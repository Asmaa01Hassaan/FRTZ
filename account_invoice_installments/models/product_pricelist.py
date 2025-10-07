# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval
import math
from math import ceil, floor, fabs, sqrt, log, log10, exp


def _adv_formula_namespace():
    # Keep this whitelist tight
    return {
        "min": min,
        "max": max,
        "round": round,
        "abs": abs,
        "math": math,
    }

class ProductPricelist(models.Model):
    _inherit = "product.pricelist"

    def _compute_price_rule(self, products, *args, **kwargs):
        """
        v17/18-compatible override:
        - Accept any upstream args/kwargs (quantity, partner, date, uom_id, compute_price, etc.)
        - Call super() unchanged
        - Post-process lines whose pricelist item has compute_price == 'adv_formula'
        """
        # 1) Let core compute first (keeps all native behaviors)
        res = super()._compute_price_rule(products, *args, **kwargs)
        # res: {product_id: (price, rule_id)}

        if not res:
            return res

        PricelistItem = self.env["product.pricelist.item"]
        Product = self.env["product.product"]

        # 2) Build map of rule_id -> item
        rule_ids = {rule_id for (_, (_, rule_id)) in res.items() if rule_id}
        items_map = {i.id: i for i in PricelistItem.browse(list(rule_ids)).exists()}

        # 3) Extract qty/partner/date/uom from either kwargs, args, or list-of-tuples
        #    Default fallbacks:
        quantity_kw = kwargs.get("quantity")
        partner_kw = kwargs.get("partner")
        date_kw = kwargs.get("date")
        uom_id_kw = kwargs.get("uom_id")

        # If positional args were used (typical order: quantity, partner, date, uom_id, ...):
        if len(args) >= 1 and quantity_kw is None:
            quantity_kw = args[0]
        if len(args) >= 2 and partner_kw is None:
            partner_kw = args[1]
        if len(args) >= 3 and date_kw is None:
            date_kw = args[2]
        if len(args) >= 4 and uom_id_kw is None:
            uom_id_kw = args[3]

        # If 'products' is a list of tuples [(product, qty, partner), ...], keep it for per-product lookup
        products_list = []
        if isinstance(products, (list, tuple)) and products:
            # Odoo classic calling style
            if isinstance(products[0], tuple):
                products_list = products
            else:
                # List of records -> normalize
                products_list = [(p, quantity_kw or 0.0, partner_kw) for p in products]
        else:
            # Single recordset -> normalize
            products_list = [(p, quantity_kw or 0.0, partner_kw) for p in (products if getattr(products, "_ids", False) else [products])]

        uom = self.env["uom.uom"].browse(uom_id_kw) if uom_id_kw else False
        the_date = date_kw or fields.Date.context_today(self)

        # 4) Post-process items marked as adv_formula
        for prod_id, (base_price, rule_id) in list(res.items()):
            item = items_map.get(rule_id)
            if not item or item.compute_price != "adv_formula":
                continue

            product_rec = Product.browse(prod_id)

            # Find qty/partner for this specific product
            qty, partner = 0.0, False
            for p, q, prt in products_list:
                if p.id == prod_id:
                    qty = float(q or 0.0)
                    partner = prt
                    break

            safe_locals = {
                "price": float(base_price),                 # upstream computed price as base
                "list_price": float(product_rec.list_price),
                "cost": float(product_rec.standard_price),
                "qty": qty,
                "uom": uom or product_rec.uom_id,          # record
                "date": the_date,                          # date
                "partner": partner,                        # record or False
                "product": product_rec,                    # record
                "category": product_rec.categ_id,          # record
                "currency_rate": 1.0,                      # plug real conversion if needed
            }

            try:
                new_price = safe_eval(item.adv_formula or "price", _adv_formula_namespace(), safe_locals)
            except Exception as e:
                raise UserError(f"Adv-formule error in pricelist item #{item.id}:\n{e}")

            try:
                new_price = float(new_price)
            except Exception:
                raise UserError(
                    f"Adv-formule in pricelist item #{item.id} didn't return a numeric value."
                )

            if new_price < 0:
                new_price = 0.0

            res[prod_id] = (new_price, rule_id)

        return res
