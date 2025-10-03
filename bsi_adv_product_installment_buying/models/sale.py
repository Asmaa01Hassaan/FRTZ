# -*- coding: utf-8 -*-
from odoo import fields, models
from dateutil.relativedelta import relativedelta


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def create_invoices_for_installment(self):
        num = []
        temp_num = []
        max_number = 0
        for temp_order in self:
            for o_line in temp_order.order_line:
                if o_line.installment_id.months:
                    num = o_line.installment_id.months
                    temp_num.append(num)

                    max_number = temp_num[0]
                    for number in temp_num:
                        if number > max_number:
                            max_number = number

        invoice_date = fields.Date.today()
        for installment in range(1, max_number + 1):
            invoice_date = invoice_date + relativedelta(months=+1)
            if installment == 1:
                invoice_date = fields.Date.today()

            lines_list = []
            for line in self.order_line:
                if line.installment_id.months >= installment:
                    installment_amount = line.installment_amt
                    installable_inv_value = (
                        0,
                        0,
                        {
                            "product_id": line.product_id.id,
                            "name": line.name,
                            "quantity": 1.0,
                            "price_unit": installment_amount,
                            "sale_line_ids": [(6, 0, [line.id])],
                        },
                    )
                    lines_list.append(installable_inv_value)
                if installment == 1 and not line.installment_id:
                    installment_amount = line.price_subtotal
                    installable_inv_value = (
                        0,
                        0,
                        {
                            "product_id": line.product_id.id,
                            "name": line.name,
                            "quantity": 1.0,
                            "price_unit": installment_amount,
                            "sale_line_ids": [(6, 0, [line.id])],
                        },
                    )
                    lines_list.append(installable_inv_value)

            installment_invoice_vals = {
                "partner_id": line.order_id.partner_id.id,
                "move_type": "out_invoice",
                "invoice_date": invoice_date,
                "total_installments": max_number,
                "installment_number": installment,
                "is_installment_invoice": line.is_installment_invoice,
                "is_installment_invoice": True,
                "invoice_line_ids": lines_list,
                "bsi_sale_order_id": line.order_id.id,
            }
            new_inv = self.env["account.move"].create(installment_invoice_vals)


class AccountMove(models.Model):
    _inherit = "account.move"
    """
    inherited the account.move to add installment amount in
    generated invoice
    """
    is_installment_invoice = fields.Boolean(
        string="Is Installment Invoice", default=False
    )
    total_installments = fields.Integer(string="Total Installments", readonly=True)
    installment_number = fields.Integer(string="Installment Number", readonly=True)
