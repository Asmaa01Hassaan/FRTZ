# models/sale_order.py
from odoo import models, fields, api, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'
    payment_type = fields.Selection(
        selection=[
            ("immediate", "Immediate Payment"),
            ("regular", "Regular installments"),
            ("iregular", "Iregular installments"),
        ],
        string="Payment Plan",
        # default="immediate",
        tracking=True,
        copy=False,
    )
    order_type = fields.Selection([
        ('standard', 'Standard Sale'),
        ('custom', 'Custom Sale'),
        ('wholesale', 'Wholesale Order'),
        ('subscription', 'Subscription Sale'),
    ], string='Order Type', default='standard', required=True, tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                # Determine sequence based on order type
                order_type = vals.get('order_type', 'standard')
                sequence_map = {
                    'standard': 'sale.order',
                    'custom': 'custom.sale.order',
                    'wholesale': 'wholesale.sale.order',
                    'subscription': 'subscription.sale.order',
                }
                seq_code = sequence_map.get(order_type, 'sale.order')

                seq_date = fields.Datetime.context_timestamp(
                    self, fields.Datetime.to_datetime(vals.get('date_order'))
                ) if vals.get('date_order') else None
                vals['name'] = self.env['ir.sequence'].next_by_code(seq_code, sequence_date=seq_date) or _('New')
        return super().create(vals_list)

    def action_create_standard(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_mode': 'form',
            'target': 'current',
            # 'context': {'default_order_type': 'standard'},
        }

    def action_create_custom(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_mode': 'form',
            'target': 'current',
            'context': {'default_order_type': 'custom'},
        }

    def action_create_wholesale(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_mode': 'form',
            'target': 'current',
            'context': {'default_order_type': 'wholesale'},
        }
    def action_create_subscription(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_mode': 'form',
            'target': 'current',
            'context': {'default_order_type': 'subscription'},
        }