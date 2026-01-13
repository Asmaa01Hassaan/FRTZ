# -*- coding: utf-8 -*-
from . import models

def post_init_hook(cr, registry):
    """Migrate existing records with display_type='text' to 'pills'"""
    cr.execute("""
        UPDATE product_attribute
        SET display_type = 'pills',
            allow_free_text = true,
            create_variant = 'no_variant'
        WHERE display_type = 'text'
    """)

