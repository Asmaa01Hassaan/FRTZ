from odoo import fields, models, api


class ResPartner(models.Model):
    _inherit = "res.partner"

    uid = fields.Char(string="UID")
    first_name = fields.Char(string="First Name")
    father_name = fields.Char(string="Father Name")
    gfather_name = fields.Char(string="GFather Name")
    sur_name = fields.Char(string="Sur Name")
    birth_date = fields.Date(string="Birth Date")
    hiring_date = fields.Date(string="Hiring Date")
    name_from_parts = fields.Boolean(compute="_compute_name_from_parts", store=False)
    status = fields.Selection([
        ('active', 'Active'),
        ('suspended', 'Suspended'),
    ], string='Status', default='active')
    divisions = fields.Char(string='Divisions')
    contact_address_ids = fields.One2many('contact.addresses', 'partner_id', string='Contact Addresses')
    max_salary_deduction = fields.Monetary(string='Max Salary Deduction', currency_field='currency_id')
    max_installments_amount = fields.Monetary(string='Max Installments Amount', currency_field='currency_id')
    max_grantees_amount = fields.Monetary(string='Max Grantees Amount', currency_field='currency_id')

    @api.depends('first_name', 'father_name', 'gfather_name', 'sur_name')
    def _compute_name_from_parts(self):
        """Compute if name should be readonly based on name parts"""
        for record in self:
            record.name_from_parts = bool(record.first_name or record.father_name or 
                                         record.gfather_name or record.sur_name)

    @api.onchange('first_name', 'father_name', 'gfather_name', 'sur_name')
    def _onchange_name_parts(self):
        """Automatically update name field when name parts are entered"""
        name_parts = []
        if self.first_name:
            name_parts.append(self.first_name)
        if self.father_name:
            name_parts.append(self.father_name)
        if self.gfather_name:
            name_parts.append(self.gfather_name)
        if self.sur_name:
            name_parts.append(self.sur_name)
        
        if name_parts:
            self.name = ' '.join(name_parts)

