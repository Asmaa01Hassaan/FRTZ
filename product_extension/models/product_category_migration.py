# -*- coding: utf-8 -*-
import logging

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    """Called after module installation/upgrade"""
    # Update existing product category allowed type records to have clean names
    type_mapping = {
        'consu': 'Goods',
        'service': 'Service',
        'combo': 'Combo',
    }
    
    # Force update all records based on code
    for code, clean_name in type_mapping.items():
        records = env['product.category.allowed.type'].search([('code', '=', code)])
        for record in records:
            # Always update to clean name regardless of current value
            old_name = record.name
            record.name = clean_name
            # Trigger display_name computation
            record._compute_display_name()
            if old_name != clean_name:
                _logger.info(f"Updated product type '{code}' name from '{old_name}' to '{clean_name}'")
    
    # Also clean any records that might have code prefix in the name
    all_records = env['product.category.allowed.type'].search([])
    for record in all_records:
        if record.code and record.name:
            clean_name = type_mapping.get(record.code)
            if clean_name:
                # Always set to clean name if mapping exists
                if record.name != clean_name:
                    record.name = clean_name
                    record.display_name = clean_name
                    _logger.info(f"Cleaned product type '{record.code}' name to '{clean_name}'")
            elif record.code in record.name.lower():
                # If name contains code but no mapping, try to extract clean name
                if ' ' in record.name:
                    parts = record.name.split(' ', 1)
                    if parts[0].lower() in ['consu', 'service', 'combo']:
                        clean_name = parts[1] if len(parts) > 1 else parts[0]
                        record.name = clean_name
                        record.display_name = clean_name
                        _logger.info(f"Extracted clean name '{clean_name}' from '{record.name}'")
    
    # Odoo handles commits automatically, no need to commit manually

