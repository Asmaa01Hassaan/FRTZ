# models/sale_order.py
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = 'sale.order'
    vendor_name_id = fields.Many2one('res.partner', string='Vendor Name')
    payment_type = fields.Selection(
        selection=[
            ("immediate", "Immediate Payment"),
            ("regular", "Regular Installments"),
            ("irregular", "Irregular Installments"),
        ],
        string="Payment Plan",
        default="immediate",
        tracking=True,
        copy=False,
        help="Select the payment plan for this order"
    )
    # Order Type Classification
    order_type = fields.Selection([
        ('standard', 'Standard Sale Order'),
        ('custom', 'Warehouse Sale Order'),
        ('wholesale', 'External Sales Order'),
        ('subscription', 'Service Sales Order'),
    ], string='Order Type', default='standard', required=True, tracking=True,
       help="Select the type of sale order")

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to generate sequence based on order type"""
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

                try:
                    seq_date = fields.Datetime.context_timestamp(
                        self, fields.Datetime.to_datetime(vals.get('date_order'))
                    ) if vals.get('date_order') else None
                    vals['name'] = self.env['ir.sequence'].next_by_code(
                        seq_code, sequence_date=seq_date
                    ) or _('New')
                except Exception as e:
                    # Fallback to default sequence if custom sequence fails
                    vals['name'] = self.env['ir.sequence'].next_by_code('sale.order') or _('New')
        return super().create(vals_list)

    def action_create_standard(self):
        """Create a new standard sale order"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('New Standard Sale Order'),
            'res_model': 'sale.order',
            'view_mode': 'form',
            'target': 'current',
            'context': {'default_order_type': 'standard'},
        }

    def action_create_custom(self):
        """Create a new custom sale order"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('New Custom Sale Order'),
            'res_model': 'sale.order',
            'view_mode': 'form',
            'target': 'current',
            'context': {'default_order_type': 'custom'},
        }

    def action_create_wholesale(self):
        """Create a new wholesale order"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('New Wholesale Order'),
            'res_model': 'sale.order',
            'view_mode': 'form',
            'target': 'current',
            'context': {'default_order_type': 'wholesale'},
        }

    def action_create_subscription(self):
        """Create a new subscription order"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('New Subscription Order'),
            'res_model': 'sale.order',
            'view_mode': 'form',
            'target': 'current',
            'context': {'default_order_type': 'subscription'},
        }