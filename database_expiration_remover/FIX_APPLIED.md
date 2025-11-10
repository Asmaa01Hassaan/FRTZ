# Fix Applied: Database Expiration Remover

## Issue
```
TypeError: post_init_hook() missing 1 required positional argument: 'registry'
```

## Root Cause
The `post_init_hook` function in `__init__.py` had an outdated signature for Odoo 18.

### Old (Odoo 15 and below):
```python
def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
```

### New (Odoo 16+/18):
```python
def post_init_hook(env):
    # env is already provided by Odoo
```

## Fix Applied
Changed line 6 of `__init__.py` from:
- `def post_init_hook(cr, registry):` 
- To: `def post_init_hook(env):`

## Next Steps

### 1. Copy the fixed module to your server

From your local machine, copy to server:
```bash
scp -r custom_frtz/FRTZ/database_expiration_remover root@72.61.155.137:/opt/odoo/custom-addons/FRTZ/
```

### 2. Restart Odoo container
```bash
docker restart odoo
```

### 3. Try installing the module again
Via Odoo UI:
1. Apps → Remove "Apps" filter
2. Search "Database Expiration Remover"
3. Click "Install"

Or via CLI:
```bash
docker exec odoo odoo -i database_expiration_remover -d Dev --db_host=db --db_user=odoo --db_password=odoo --stop-after-init
docker restart odoo
```

## Verification
Module should install without the TypeError error.


