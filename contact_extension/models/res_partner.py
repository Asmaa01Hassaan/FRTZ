from odoo import fields, models, api


class ResPartner(models.Model):
    _inherit = "res.partner"

    uid = fields.Char(string="UID")
    use_name_parts = fields.Boolean(string="Use Name Details", default=False,
                                    help="Enable this to compose the name from individual name parts. "
                                         "When enabled, the name field becomes read-only and is automatically updated from the name parts.")
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

    @api.depends('use_name_parts', 'first_name', 'father_name', 'gfather_name', 'sur_name')
    def _compute_name_from_parts(self):
        """Compute if name should be readonly based on use_name_parts checkbox"""
        for record in self:
            record.name_from_parts = record.use_name_parts

    @api.onchange('use_name_parts')
    def _onchange_use_name_parts(self):
        """Handle checkbox change - clear name parts if unchecked"""
        if not self.use_name_parts:
            # Clear all name parts when checkbox is unchecked
            self.first_name = False
            self.father_name = False
            self.gfather_name = False
            self.sur_name = False
        elif self.use_name_parts:
            # If checked and name parts exist, update name
            self._onchange_name_parts()

    @api.onchange('first_name', 'father_name', 'gfather_name', 'sur_name')
    def _onchange_name_parts(self):
        """Automatically update name field when name parts are entered (only if use_name_parts is True)"""
        if not self.use_name_parts:
            return
        
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

    def write(self, vals):
        """Clear name parts when use_name_parts is unchecked and prevent manual name editing when checked"""
        # If use_name_parts is being set to False, clear all name parts
        if 'use_name_parts' in vals and not vals['use_name_parts']:
            vals['first_name'] = False
            vals['father_name'] = False
            vals['gfather_name'] = False
            vals['sur_name'] = False
        
        # Prevent manual name editing when use_name_parts is True
        # Only allow name changes if it's coming from name parts update
        for record in self:
            if record.use_name_parts and 'name' in vals:
                # Check if name parts are being updated (which will update name via onchange)
                if not any(key in vals for key in ['first_name', 'father_name', 'gfather_name', 'sur_name']):
                    # If name is being changed manually without name parts update, ignore it
                    # Recompute name from current name parts instead
                    name_parts = []
                    first_name = vals.get('first_name', record.first_name)
                    father_name = vals.get('father_name', record.father_name)
                    gfather_name = vals.get('gfather_name', record.gfather_name)
                    sur_name = vals.get('sur_name', record.sur_name)
                    
                    if first_name:
                        name_parts.append(first_name)
                    if father_name:
                        name_parts.append(father_name)
                    if gfather_name:
                        name_parts.append(gfather_name)
                    if sur_name:
                        name_parts.append(sur_name)
                    
                    if name_parts:
                        vals['name'] = ' '.join(name_parts)
                    else:
                        # If no name parts, keep existing name or remove the name change
                        del vals['name']
        
        result = super().write(vals)
        
        # Also clear name parts for records where use_name_parts is False
        for record in self:
            if not record.use_name_parts and (record.first_name or record.father_name or 
                                               record.gfather_name or record.sur_name):
                record.write({
                    'first_name': False,
                    'father_name': False,
                    'gfather_name': False,
                    'sur_name': False,
                })
        
        return result

