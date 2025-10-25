from odoo import api, fields, models, _


class FrtzCustomer(models.Model):
    _inherit = 'res.partner'

    # Removed sale_order_customer_id field as it's no longer needed
    # The relationship is now handled through Many2many in sale.order
    # Using standard 'ref' field instead of custom customer_number

    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
        store=True
    )

    status = fields.Selection([
        ('active', 'Active'),
        ('suspended', 'Suspended'),
    ], string='Status', default='active')
    
    # Installment Information - Moved to invoice_installment_extension module

    @api.depends('name', 'ref')
    def _compute_display_name(self):
        for partner in self:
            name = partner.name or ''
            if partner.ref:
                name = f"{partner.ref} {name}"
            partner.display_name = name

    def name_get(self):
        result = []
        for partner in self:
            result.append((partner.id, partner.display_name or partner.name))
        return result

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        """
        Override name_search to include ref
        """
        args = args or []
        domain = []
        if name:
            domain = ['|', ('name', 'ilike', name), ('ref', 'ilike', name)]
        records = self.search(domain + args, limit=limit)
        return records.name_get()

