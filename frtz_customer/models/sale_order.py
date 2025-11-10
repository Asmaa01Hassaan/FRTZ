from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    customer_guarantees_ids = fields.Many2many(
        'res.partner',
        'sale_order_customer_guarantees_rel',
        'sale_order_id',
        'partner_id',
        string='Customer Guarantees',
        help='Select customers who will act as guarantees for this sale order'
    )

    guarantees_count = fields.Integer(
        string='Guarantees Count',
        compute='_compute_guarantees_count'
    )
    
    # New relation to customer.guarantees model
    customer_guarantees_list_ids = fields.One2many(
        'customer.guarantees',
        'sale_order_id',
        string='Customer Guarantees List'
    )

    @api.depends('customer_guarantees_ids')
    def _compute_guarantees_count(self):
        for order in self:
            order.guarantees_count = len(order.customer_guarantees_ids)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            partner_id = vals.get('partner_id')
            if partner_id:
                partner = self.env['res.partner'].browse(partner_id)
                if partner.status == 'suspended':
                    raise UserError(_("This Customer Is Suspended"))
        return super(SaleOrder, self).create(vals_list)

    def write(self, vals):
        """Prevent saving (updating) Sale Orders if customer is suspended."""
        for order in self:
            # Check partner if changed or even if not changed
            partner = self.env['res.partner'].browse(
                vals.get('partner_id', order.partner_id.id)
            )
            if partner.status == 'suspended':
                raise UserError(_("This Customer Is Suspended"))
        return super(SaleOrder, self).write(vals)