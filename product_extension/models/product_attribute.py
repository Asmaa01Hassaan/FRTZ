# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ProductAttribute(models.Model):
    _inherit = 'product.attribute'
    
    allow_free_text = fields.Boolean(
        string="Allow Free Text",
        default=False,
        help="If enabled, users can enter custom text values for this attribute instead of selecting from predefined values. "
             "This automatically enables 'is_custom' on attribute values."
    )
    
    @api.model
    def create(self, vals):
        """Set create_variant to no_variant when free text is enabled"""
        record = super().create(vals)
        if record.allow_free_text:
            record.create_variant = 'no_variant'
            # Enable is_custom on all existing values
            record.value_ids.write({'is_custom': True})
        return record
    
    def write(self, vals):
        """Handle free text option changes"""
        if 'allow_free_text' in vals:
            if vals['allow_free_text']:
                # When enabling free text, set create_variant to no_variant
                vals['create_variant'] = 'no_variant'
                # Enable is_custom on all values
                self.value_ids.write({'is_custom': True})
            else:
                # When disabling free text, disable is_custom on all values
                self.value_ids.write({'is_custom': False})
        
        result = super().write(vals)
        
        # Also handle when new values are added to an attribute with free text enabled
        if 'value_ids' in vals and self.allow_free_text:
            self.value_ids.write({'is_custom': True})
        
        return result


class ProductAttributeValue(models.Model):
    _inherit = 'product.attribute.value'
    
    @api.model
    def create(self, vals):
        """Automatically set is_custom if the attribute allows free text"""
        record = super().create(vals)
        if record.attribute_id and record.attribute_id.allow_free_text:
            record.is_custom = True
        return record