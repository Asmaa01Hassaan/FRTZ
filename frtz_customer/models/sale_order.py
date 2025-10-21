from odoo import api, fields, models

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
    
    @api.depends('customer_guarantees_ids')
    def _compute_guarantees_count(self):
        for order in self:
            order.guarantees_count = len(order.customer_guarantees_ids)
