# -*- coding: utf-8 -*-
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.tools import float_is_zero, float_compare
from datetime import date
from datetime import timedelta
import calendar
from odoo.fields import Command
from datetime import datetime, timedelta
from itertools import groupby
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools import float_is_zero


class SaleOrder(models.Model):
    _inherit = "sale.order"

    bsi_account_move = fields.One2many(
        "account.move", "bsi_sale_order_id", readonly=True, string="Installment Details"
    )
    overall_installments = fields.Integer(
        compute="compute_overall_installments",
        string="Overall Installments",
        readonly=True,
    )
    current_installment = fields.Integer(
        compute="compute_current_installment",
        string="Current Installment",
        readonly=True,
    )
    total_installment_amount = fields.Monetary(
        compute="compute_total_installment_amount",
        string="Total Installment Amount",
        readonly=True,
    )
    total_installment_due = fields.Monetary(
        compute="compute_total_installment_due",
        string="Total Installment Due",
        readonly=True,
    )
    # Override BASE: to consider and neglate Installment Invoices

    def compute_overall_installments(self):
        count = 0
        for record in self.bsi_account_move:
            if record.total_installments:
                count += 1
        self.overall_installments = count

    def compute_current_installment(self):
        temp_current_installment = 0
        current_installment_date = date.today()
        current_installment_month = current_installment_date.month
        for record in self.bsi_account_move:
            if current_installment_date.month == record.invoice_date.month:
                if record.installment_number:
                    temp_current_installment = record.installment_number
        self.current_installment = temp_current_installment

    def compute_total_installment_amount(self):
        temp_total = 0
        for record in self.bsi_account_move:
            if record.amount_total:
                temp_total = temp_total + record.amount_total_signed
        self.total_installment_amount = temp_total

    def compute_total_installment_due(self):
        sub_total = 0
        for record in self.bsi_account_move:
            if record.amount_residual_signed:
                sub_total = sub_total + record.amount_residual_signed
        self.total_installment_due = sub_total

    def _create_invoices(self, grouped=False, final=False, date=None):
        """
        Create the invoice associated to the SO.
        :param grouped: if True, invoices are grouped by SO id. If False, invoices are grouped by
                        (partner_invoice_id, currency)
        :param final: if True, refunds will be generated if necessary
        :returns: list of created invoices
        """
        if not self.env["account.move"].check_access_rights("create", False):
            try:
                self.check_access_rights("write")
                self.check_access_rule("write")
            except AccessError:
                return self.env["account.move"]

        # 1) Create invoices.
        invoice_vals_list = []
        # Incremental sequencing to keep the lines order on the invoice.
        invoice_item_sequence = 0
        for order in self:
            order = order.with_company(order.company_id)
            invoice_vals = order._prepare_invoice()
            invoiceable_lines = order._get_invoiceable_lines(final)

            if not any(not line.display_type for line in invoiceable_lines):
                continue

            invoice_line_vals = []
            down_payment_section_added = False
            for line in invoiceable_lines:
                if not down_payment_section_added and line.is_downpayment:
                    # Create a dedicated section for the down payments
                    # (put at the end of the invoiceable_lines)
                    invoice_line_vals.append(
                        Command.create(
                            order._prepare_down_payment_section_line(
                                sequence=invoice_item_sequence
                            )
                        ),
                    )
                    down_payment_section_added = True
                    invoice_item_sequence += 1
                invoice_line_vals.append(
                    Command.create(
                        line._prepare_invoice_line(sequence=invoice_item_sequence)
                    ),
                )
                invoice_item_sequence += 1

            invoice_vals["invoice_line_ids"] += invoice_line_vals
            invoice_vals_list.append(invoice_vals)

        # EDIT: Add, Create Installment Invoices
        installable_order_lines = []
        for temp_order in self:
            for o_line in temp_order.order_line:
                if o_line.is_installment_invoice and o_line.installment_id:
                    installable_order_lines.append(o_line)

        if installable_order_lines:
            for install_order_line in installable_order_lines:
                installment_invoice_vals_list = []
                total_months = install_order_line.installment_id.months
                installment_amount = install_order_line.installment_amt
                invoice_date = fields.Date.today()

                installment_number = 0
                for months in range(0, total_months):
                    days_in_month1 = calendar.monthrange(
                        invoice_date.year, invoice_date.month
                    )[1]
                    installment_number += 1

                    installable_inv_value = [
                        (
                            0,
                            0,
                            {
                                "product_id": install_order_line.product_id.id,
                                "name": install_order_line.name,
                                "quantity": 1.0,
                                "price_unit": installment_amount,
                                "sale_line_ids": [(6, 0, [install_order_line.id])],
                            },
                        )
                    ]
                    installment_invoice_vals = {
                        "partner_id": self.partner_id.id,
                        "move_type": "out_invoice",
                        "invoice_date": invoice_date,
                        "total_installments": install_order_line.installment_id.months,
                        "installment_number": installment_number,
                        "is_installment_invoice": install_order_line.is_installment_invoice,
                        "invoice_line_ids": installable_inv_value,
                        "bsi_sale_order_id": self.id,
                    }
                    new_inv = self.env["account.move"].create(installment_invoice_vals)
                    # Edit: Removed extra created 0.0 value lines from new invoices
                    if new_inv and new_inv.invoice_line_ids:
                        for new_inv_line in new_inv.invoice_line_ids:
                            if (
                                not new_inv_line.product_id
                                and new_inv_line.price_unit == 0.0
                            ):
                                new_inv_line.unlink()

                    # installment date increment
                    invoice_date = invoice_date + timedelta(days=days_in_month1)

        # EDIT: Added 'not installable_order_lines' for only Installable invoice process
        if not invoice_vals_list and not installable_order_lines:
            raise self._nothing_to_invoice_error()

        # if not invoice_vals_list and self._context.get('raise_if_nothing_to_invoice', True):
        #     raise UserError(self._nothing_to_invoice_error_message())

        # 2) Manage 'grouped' parameter: group by (partner_id, currency_id).
        if not grouped:
            new_invoice_vals_list = []
            invoice_grouping_keys = self._get_invoice_grouping_keys()
            invoice_vals_list = sorted(
                invoice_vals_list,
                key=lambda x: [
                    x.get(grouping_key) for grouping_key in invoice_grouping_keys
                ],
            )
            for _grouping_keys, invoices in groupby(
                invoice_vals_list,
                key=lambda x: [
                    x.get(grouping_key) for grouping_key in invoice_grouping_keys
                ],
            ):
                origins = set()
                payment_refs = set()
                refs = set()
                ref_invoice_vals = None
                for invoice_vals in invoices:
                    if not ref_invoice_vals:
                        ref_invoice_vals = invoice_vals
                    else:
                        ref_invoice_vals["invoice_line_ids"] += invoice_vals[
                            "invoice_line_ids"
                        ]
                    origins.add(invoice_vals["invoice_origin"])
                    payment_refs.add(invoice_vals["payment_reference"])
                    refs.add(invoice_vals["ref"])
                ref_invoice_vals.update(
                    {
                        "ref": ", ".join(refs)[:2000],
                        "invoice_origin": ", ".join(origins),
                        "payment_reference": len(payment_refs) == 1
                        and payment_refs.pop()
                        or False,
                    }
                )
                new_invoice_vals_list.append(ref_invoice_vals)
            invoice_vals_list = new_invoice_vals_list

        # 3) Create invoices.

        # As part of the invoice creation, we make sure the sequence of multiple SO do not interfere
        # in a single invoice. Example:
        # SO 1:
        # - Section A (sequence: 10)
        # - Product A (sequence: 11)
        # SO 2:
        # - Section B (sequence: 10)
        # - Product B (sequence: 11)
        #
        # If SO 1 & 2 are grouped in the same invoice, the result will be:
        # - Section A (sequence: 10)
        # - Section B (sequence: 10)
        # - Product A (sequence: 11)
        # - Product B (sequence: 11)
        #
        # Resequencing should be safe, however we resequence only if there are less invoices than
        # orders, meaning a grouping might have been done. This could also mean that only a part
        # of the selected SO are invoiceable, but resequencing in this case shouldn't be an issue.
        if len(invoice_vals_list) < len(self):
            SaleOrderLine = self.env["sale.order.line"]
            for invoice in invoice_vals_list:
                sequence = 1
                for line in invoice["invoice_line_ids"]:
                    line[2]["sequence"] = SaleOrderLine._get_invoice_line_sequence(
                        new=sequence, old=line[2]["sequence"]
                    )
                    sequence += 1

        # Manage the creation of invoices in sudo because a salesperson must be able to generate an invoice from a
        # sale order without "billing" access rights. However, he should not be able to create an invoice from scratch.
        moves = (
            self.env["account.move"]
            .sudo()
            .with_context(default_move_type="out_invoice")
            .create(invoice_vals_list)
        )

        # 4) Some moves might actually be refunds: convert them if the total amount is negative
        # We do this after the moves have been created since we need taxes, etc. to know if the total
        # is actually negative or not
        if final:
            moves.sudo().filtered(lambda m: m.amount_total < 0).action_switch_move_type()
        for move in moves:
            if final:
                # Downpayment might have been determined by a fixed amount set by the user.
                # This amount is tax included. This can lead to rounding issues.
                # E.g. a user wants a 100€ DP on a product with 21% tax.
                # 100 / 1.21 = 82.64, 82.64 * 1,21 = 99.99
                # This is already corrected by adding/removing the missing cents on the DP invoice,
                # but must also be accounted for on the final invoice.

                delta_amount = 0
                for order_line in self.order_line:
                    if not order_line.is_downpayment:
                        continue
                    inv_amt = order_amt = 0
                    for invoice_line in order_line.invoice_lines:
                        if invoice_line.move_id == move:
                            inv_amt += invoice_line.price_total
                        elif invoice_line.move_id.state != 'cancel':  # filter out canceled dp lines
                            order_amt += invoice_line.price_total
                    if inv_amt and order_amt:
                        # if not inv_amt, this order line is not related to current move
                        # if no order_amt, dp order line was not invoiced
                        delta_amount += (inv_amt * (1 if move.is_inbound() else -1)) + order_amt

                if not move.currency_id.is_zero(delta_amount):
                    receivable_line = move.line_ids.filtered(
                        lambda aml: aml.account_id.account_type == 'asset_receivable')[:1]
                    product_lines = move.line_ids.filtered(
                        lambda aml: aml.display_type == 'product' and aml.is_downpayment)
                    tax_lines = move.line_ids.filtered(
                        lambda aml: aml.tax_line_id.amount_type not in (False, 'fixed'))
                    if tax_lines and product_lines and receivable_line:
                        line_commands = [Command.update(receivable_line.id, {
                            'amount_currency': receivable_line.amount_currency + delta_amount,
                        })]
                        delta_sign = 1 if delta_amount > 0 else -1
                        for lines, attr, sign in (
                            (product_lines, 'price_total', -1 if move.is_inbound() else 1),
                            (tax_lines, 'amount_currency', 1),
                        ):
                            remaining = delta_amount
                            lines_len = len(lines)
                            for line in lines:
                                if move.currency_id.compare_amounts(remaining, 0) != delta_sign:
                                    break
                                amt = delta_sign * max(
                                    move.currency_id.rounding,
                                    abs(move.currency_id.round(remaining / lines_len)),
                                )
                                remaining -= amt
                                line_commands.append(Command.update(line.id, {attr: line[attr] + amt * sign}))
                        move.line_ids = line_commands

            move.message_post_with_source(
                'mail.message_origin_link',
                render_values={'self': move, 'origin': move.line_ids.sale_line_ids.order_id},
                subtype_xmlid='mail.mt_note',
            )
        return moves

    def _get_invoiceable_lines(self, final=False):
        """Return the invoiceable lines for order `self`."""
        down_payment_line_ids = []
        invoiceable_line_ids = []
        pending_section = None
        precision = self.env["decimal.precision"].precision_get(
            "Product Unit of Measure"
        )

        for line in self.order_line:
            # EDIT: Neglate installment product line for the regular inv creation
            if line.is_installment_invoice and line.installment_id:
                pass
            else:
                if line.display_type == "line_section":
                    # Only invoice the section if one of its lines is invoiceable
                    pending_section = line
                    continue
                if line.display_type != "line_note" and float_is_zero(
                    line.qty_to_invoice, precision_digits=precision
                ):
                    continue
                if (
                    line.qty_to_invoice > 0
                    or (line.qty_to_invoice < 0 and final)
                    or line.display_type == "line_note"
                ):
                    if line.is_downpayment:
                        # Keep down payment lines separately, to put them together
                        # at the end of the invoice, in a specific dedicated section.
                        down_payment_line_ids.append(line.id)
                        continue
                    if pending_section:
                        invoiceable_line_ids.append(pending_section.id)
                        pending_section = None
                    invoiceable_line_ids.append(line.id)

        return self.env["sale.order.line"].browse(
            invoiceable_line_ids + down_payment_line_ids
        )


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    is_installment_invoice = fields.Boolean(
        string="Is Installment Invoice", default=False
    )
    installment_id = fields.Many2one("installment.config", string="Installment")
    installment_amt = fields.Float(
        string="Installment Amount", compute="compute_installment_amt"
    )
    installment_ok = fields.Boolean(
        string="Related Field", related="product_id.product_tmpl_id.installment_ok"
    )

    @api.onchange("is_installment_invoice")
    def onchange_is_installment_invoice(self):
        if self.is_installment_invoice is True:
            self.installment_id = False
            self.installment_amt = False
        if self.product_id and self.is_installment_invoice is False:
            self.price_subtotal = self.product_uom_qty * self.price_unit
        elif self.is_installment_invoice is True:
            class_obj = self.env["product.template"].search(
                [("id", "=", self.product_id.product_tmpl_id.id)]
            )
            inst_list = []
            for record in class_obj:
                if self.product_id:
                    for inst_id in record.installment_ids:
                        inst_list.append(inst_id.id)
            res = {}
            res["domain"] = {"installment_id": [("id", "in", inst_list)]}
            return res

    @api.depends(
        "is_installment_invoice", "installment_id", "product_uom_qty", "price_unit"
    )
    def compute_installment_amt(self):
        """
        A function that compute the installment amount based on the
         selected installment
        """
        for record in self:
            if record.installment_id:
                installment_ids = self.env["installment.config"].search(
                    [("id", "=", record.installment_id.id)]
                )

                total_amt = 0
                installment_amt = 0

                for i in installment_ids:
                    if record.is_installment_invoice is True:
                        if i.id == record.installment_id.id:
                            total_amt = record.product_uom_qty * record.price_unit + (
                                record.product_uom_qty * record.price_unit * i.emi / 100
                            )
                            installment_amt = total_amt / i.months
                        record.installment_amt = installment_amt
                    else:
                        record.installment_amt = 0
            else:
                record.installment_amt = 0


class AccountMove(models.Model):
    _inherit = "account.move"
    """
    inherited the account.move to add installment amount in
    generated invoice
    """
    bsi_sale_order_id = fields.Many2one("sale.order", string="Sale Order Id")
    total_installments = fields.Integer(string="Total Installments", readonly=True)
    installment_number = fields.Integer(string="Installment Number", readonly=True)
    is_installment_invoice = fields.Boolean(
        string="Is Installment Invoice", default=False
    )


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"
    """
    inherited the account.move.line to add installment amount in
    generated invoice
    """
    installment_id = fields.Many2one("installment.config", string="Installment")
    installment_amt = fields.Float(string="Installment Amount")

    @api.onchange("installment_id")
    def onchange_product_id(self):
        if self.installment_id:
            if self.product_id.quantity:
                self.installment_amt = self.installment_id.installment_amt
