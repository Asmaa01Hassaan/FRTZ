from odoo import api, fields, models


class FrtzCustomer(models.Model):
    _inherit = 'res.partner'

    # Removed sale_order_customer_id field as it's no longer needed
    # The relationship is now handled through Many2many in sale.order
    customer_number = fields.Char(
        string='Customer Number',
        size = 5,
        copy=False,
        index=True
    )

    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
        store=True
    )

    @api.depends('name', 'customer_number')
    def _compute_display_name(self):
        for partner in self:
            name = partner.name or ''
            if partner.customer_number:
                name = f"{partner.customer_number} {name}"
            partner.display_name = name

    def name_get(self):
        result = []
        for partner in self:
            result.append((partner.id, partner.display_name or partner.name))
        return result

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        """
        Override name_search to include customer_number
        """
        args = args or []
        domain = []
        if name:
            domain = ['|', ('name', 'ilike', name), ('customer_number', 'ilike', name)]
        records = self.search(domain + args, limit=limit)
        return records.name_get()

