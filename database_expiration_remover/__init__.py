# -*- coding: utf-8 -*-

from . import models
from odoo import api, SUPERUSER_ID
import datetime


def post_init_hook(cr, registry):
    """Post-installation hook to create cron jobs and set dynamic dates (Odoo 18 signature)."""
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    # Set dynamic dates and config parameters
    try:
        current_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        env['ir.config_parameter'].sudo().set_param('database.trial_start_date', current_date)
        
        expiration_date = (datetime.datetime.now() + datetime.timedelta(days=30)).strftime('%Y-%m-%d %H:%M:%S')
        env['ir.config_parameter'].sudo().set_param('database.expiration_date', expiration_date)
        
        env['ir.config_parameter'].sudo().set_param('database.trial_status', 'active')
        print("✅ Dynamic dates and config parameters set successfully")
        
    except Exception as e:
        print(f"❌ Error setting dynamic dates and config parameters: {e}")
    
    # Create cron jobs programmatically
    try:
        existing_cron = env['ir.cron'].search([('name', '=', 'Auto Extend Database Trial')])
        if not existing_cron:
            model_id = env['ir.model'].search([('model', '=', 'database.expiration.remover')])
            if model_id:
                env['ir.cron'].create({
                    'name': 'Auto Extend Database Trial',
                    'model_id': model_id.id,
                    'state': 'code',
                    'code': 'model._cron_auto_extend_trial()',
                    'interval_number': 1,
                    'interval_type': 'days',
                    'active': True,
                    'doall': False,
                })
                
                maintenance_model_id = env['ir.model'].search([('model', '=', 'database.maintenance')])
                if maintenance_model_id:
                    env['ir.cron'].create({
                        'name': 'Database Maintenance',
                        'model_id': maintenance_model_id.id,
                        'state': 'code',
                        'code': 'model._cron_database_maintenance()',
                        'interval_number': 1,
                        'interval_type': 'hours',
                        'active': True,
                        'doall': False,
                    })
                
                core_model_id = env['ir.model'].search([('model', '=', 'database.expiration.core')])
                if core_model_id:
                    env['ir.cron'].create({
                        'name': 'Core Expiration Prevention',
                        'model_id': core_model_id.id,
                        'state': 'code',
                        'code': 'model._cron_prevent_expiration()',
                        'interval_number': 1,
                        'interval_type': 'hours',
                        'active': True,
                        'doall': False,
                    })
                
                print("✅ Database expiration remover cron jobs created successfully")
            else:
                print("⚠️ Model 'database.expiration.remover' not found, skipping cron job creation")
        else:
            print("ℹ️ Cron jobs already exist, skipping creation")
            
    except Exception as e:
        print(f"❌ Error creating cron jobs: {e}")
