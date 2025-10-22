from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    invoice_per_line = fields.Boolean(
        string="Invoice Per Line",
        help="If enabled, 'Create Invoice' will generate a separate invoice for each invoiceable order line.",
        default=False,
        tracking=True,
    )

    def _create_invoices(self, grouped=False, final=False):
        AccountMove = self.env["account.move"]
        AccountMoveLine = self.env["account.move.line"]
        all_invoices = AccountMove.browse()

        for order in self:
            if not order.invoice_per_line:
                # Use the default Odoo behavior
                invoices_std = super(SaleOrder, order)._create_invoices(grouped=grouped, final=final)
                all_invoices |= invoices_std
                continue

            lines_to_invoice = order.order_line.filtered(
                lambda l: not l.display_type and l.qty_to_invoice > 0
            )
            if not lines_to_invoice:
                _logger.info("Order %s: no invoiceable lines.", order.name)
                continue

            _logger.info("Order %s: creating %s invoices (per line).", order.name, len(lines_to_invoice))

            for so_line in lines_to_invoice:
                try:
                    # Prepare invoice base values
                    inv_vals = order._prepare_invoice()

                    # Get custom values from sale order line
                    installment_num_val = getattr(so_line, 'installment_num', 0.0) or 0.0
                    first_payment_val = getattr(so_line, 'first_payment', 0.0) or 0.0

                    # Add these values to the invoice header
                    inv_vals.update({
                        "installment_num": float(installment_num_val),
                        "first_payment": float(first_payment_val),
                        "installment_num": float(installment_num_val),
                        "first_payment": float(first_payment_val),
                    })

                    # Create invoice record
                    invoice = AccountMove.create(inv_vals)

                    # Prepare invoice line
                    line_vals = so_line._prepare_invoice_line()
                    line_vals.update({
                        "move_id": invoice.id,
                        "sale_line_ids": [(6, 0, [so_line.id])],
                        "installment_num": float(installment_num_val),
                        "first_payment": float(first_payment_val),
                    })

                    AccountMoveLine.create(line_vals)

                    # Recompute totals
                    self._recompute_invoice_amounts(invoice)
                    all_invoices |= invoice

                    _logger.info("Created invoice %s for order %s line %s", invoice.id, order.name, so_line.id)

                except Exception as e:
                    _logger.exception("Failed to create invoice for sale order %s line %s", order.name, so_line.id)
                    raise UserError(_("Error creating invoice for line %s: %s") % (so_line.name or so_line.id, str(e)))

        return all_invoices

    def _recompute_invoice_amounts(self, invoice):
        """Recompute invoice amounts with fallback methods."""
        try:
            if hasattr(invoice, '_recompute_dynamic_lines'):
                invoice._recompute_dynamic_lines(recompute_all_taxes=True)
                return
        except Exception as e:
            _logger.warning(f"Failed to use _recompute_dynamic_lines: {e}")

        try:
            if hasattr(invoice, '_recompute_payment_terms_lines'):
                invoice._recompute_payment_terms_lines()
            if hasattr(invoice, '_recompute_tax_lines'):
                invoice._recompute_tax_lines()
            if hasattr(invoice, '_compute_amount'):
                invoice._compute_amount()
        except Exception as e:
            _logger.warning(f"Failed to recompute invoice amounts: {e}")
            invoice.flush_recordset()
