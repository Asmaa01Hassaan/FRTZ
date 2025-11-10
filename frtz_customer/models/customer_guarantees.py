from odoo import models, fields, api, _


class CustomerGuarantees(models.Model):
    _name = 'customer.guarantees'
    _description = 'Customer Guarantees'
    _rec_name = 'customer_id'

    sale_order_id = fields.Many2one(
        'sale.order',
        string='Sale Order',
        required=True,
        ondelete='cascade'
    )
    
    customer_id = fields.Many2one(
        'res.partner',
        string='Customer Name',
        required=True,
        domain="[('customer_rank', '>', 0)]"
    )
    
    sale_order_customer_guarantees_status = fields.Selection([
        ('active', 'Active'),
        ('suspended', 'Suspended'),
    ], string='Status', default='active', required=True)
    
    # Additional useful fields
    notes = fields.Text(string='Notes')
    date = fields.Date(string='Date', default=fields.Date.today)

