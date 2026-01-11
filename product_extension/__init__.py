# -*- coding: utf-8 -*-
from . import models


def post_init_hook(env):
    """Called after module installation/upgrade"""
    from .models.product_category_migration import post_init_hook as migrate
    migrate(env)

