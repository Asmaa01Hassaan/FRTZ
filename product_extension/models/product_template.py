# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = "product.template"

    code = fields.Char(
        string="Code",
        help="Product code identifier"
    )

    subscription_ok = fields.Boolean(
        string='Subscription',
        default=True,
        help="Can be used in subscription orders"
    )

    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
        store=True,
        index=True
    )
    internal_reference_new = fields.Char(
        string="Internal Reference"
    )
    cost_method = fields.Selection(
        related='categ_id.property_cost_method',
        readonly=True
    )

    def write(self, vals):
        """Override write to auto-generate reference when category changes to automatic"""
        # Check if category is being changed
        if 'categ_id' in vals and not vals.get('internal_reference_new'):
            category = self.env['product.category'].browse(vals['categ_id'])
            if category.reference_type == 'automatic':
                # Generate reference for records that don't have one
                for product in self:
                    if not product.internal_reference_new:
                        generated_ref = self._generate_automatic_reference(category)
                        if generated_ref:
                            product.internal_reference_new = generated_ref
        
        return super().write(vals)

    def _generate_automatic_reference(self, category):
        """Generate automatic reference based on category configuration"""
        # Get sequence from category or use default
        sequence = category.reference_sequence_id
        if not sequence:
            # Use default sequence
            sequence = self.env.ref(
                'product_extension.seq_product_reference_default',
                raise_if_not_found=False
            )
        
        if not sequence:
            return False
        
        # Generate reference using sequence
        generated_ref = sequence.next_by_id()
        if not generated_ref:
            return False
        
        # Apply validation rules if set (for formatting)
        if category.validation_mode == 'length' and category.reference_length:
            # Pad or truncate to required length
            if category.reference_char_type == 'number':
                # Ensure numeric and pad with zeros
                try:
                    num = int(''.join(filter(str.isdigit, generated_ref)) or '0')
                    generated_ref = str(num).zfill(category.reference_length)
                except:
                    generated_ref = generated_ref[:category.reference_length].zfill(category.reference_length)
            else:
                # Mixed: truncate or pad
                generated_ref = generated_ref[:category.reference_length].ljust(
                    category.reference_length, '0'
                )
        
        return generated_ref

    @api.model
    def create(self, vals_list):
        """Override create to auto-generate internal reference when category is set to automatic"""
        # Handle both single dict and list of dicts
        if isinstance(vals_list, dict):
            vals_list = [vals_list]
        
        for vals in vals_list:
            # Generate reference if category is set to automatic and reference is not provided
            if not vals.get('internal_reference_new'):
                categ_id = vals.get('categ_id')
                if categ_id:
                    category = self.env['product.category'].browse(categ_id)
                    if category.reference_type == 'automatic':
                        generated_ref = self._generate_automatic_reference(category)
                        if generated_ref:
                            vals['internal_reference_new'] = generated_ref
        
        return super().create(vals_list)

    @api.constrains('internal_reference_new', 'categ_id')
    def _check_internal_reference_new(self):
        """Enhanced validation for internal reference based on category rules"""
        for product in self:
            cat = product.categ_id
            ref = product.internal_reference_new or ''

            # Skip validation if no category or manual mode
            if not cat or cat.reference_type == 'manual':
                continue
            
            # Skip validation if automatic (system generates, should be valid)
            if cat.reference_type == 'automatic':
                # Just ensure it's not empty (should be generated)
                if not ref:
                    raise ValidationError(
                        _("Internal Reference should be automatically generated for category '%s'. "
                          "Please save the product again or check the sequence configuration.") % cat.name
                    )
                continue
            
            # Validation mode: enforce rules
            if cat.reference_type == 'validation':
                # Check if reference is provided (required when validation is enabled)
                if not ref:
                    raise ValidationError(
                        _("Internal Reference is required for category '%s'.") % cat.name
                    )
                
                # Length validation
                if cat.validation_mode == 'length':
                    if not cat.reference_length:
                        continue  # No length set, skip length validation
                    if len(ref) != cat.reference_length:  # Fixed: use != instead of >
                        raise ValidationError(
                            _("Internal Reference must be exactly %(length)d characters for category '%(category)s'. "
                              "Current length: %(current)d") % {
                                'length': cat.reference_length,
                                'category': cat.name,
                                'current': len(ref)
                            }
                        )
                
                # Type validation
                if cat.validation_mode == 'type':
                    if cat.reference_char_type == 'number':
                        if not ref.isdigit():
                            raise ValidationError(
                                _("Internal Reference must contain numbers only for category '%s'.") % cat.name
                            )
                    elif cat.reference_char_type == 'mix':
                        # Enhanced mix validation: must contain both letters and numbers
                        has_letter = any(c.isalpha() for c in ref)
                        has_digit = any(c.isdigit() for c in ref)
                        if not (has_letter and has_digit):
                            raise ValidationError(
                                _("Internal Reference must contain both letters and numbers for category '%s'.") % cat.name
                            )

    @api.depends('name', 'internal_reference_new')
    def _compute_display_name(self):
        """Compute display name as 'INTERNAL_REFERENCE NAME' format"""
        for product in self:
            name = product.name or ''
            if product.internal_reference_new:
                name = f"{product.internal_reference_new} {name}"
            product.display_name = name

    def name_get(self):
        """Override to return formatted display name"""
        result = []
        for product in self:
            result.append((product.id, product.display_name or product.name))
        return result

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        """
        Override name_search to include internal_reference_new in search
        Allows searching by both name and internal reference
        """
        args = args or []
        domain = []
        if name:
            domain = ['|', ('name', operator, name), ('internal_reference_new', operator, name)]
        records = self.search(domain + args, limit=limit)
        return records.name_get()


class ProductTemplateAttributeLine(models.Model):
    _inherit = 'product.template.attribute.line'

    @api.constrains('value_ids', 'attribute_id')
    def _check_valid_values(self):
        for line in self:
            if line.attribute_id.display_type == 'text':
                continue
            if not line.value_ids:
                raise ValidationError(_(
                    "The attribute %(attribute)s must have at least one value for the product %(product)s.",
                    attribute=line.attribute_id.name,
                    product=line.product_tmpl_id.name
                ))

