# Quick Fix for 'text' display_type Error

## Immediate Fix (SQL)

If you're getting the error right now, run this SQL command to fix existing records:

```sql
UPDATE product_attribute 
SET display_type = 'radio' 
WHERE display_type = 'text';
```

## Automatic Fix (Module Upgrade)

The module now includes a migration script that will automatically fix this when you upgrade the module:

1. **Upgrade the module:**
   - Go to Apps
   - Search for "Invoice Installments"
   - Click "Upgrade"

2. **The migration will automatically:**
   - Find all attributes with `display_type='text'`
   - Change them to `display_type='radio'`
   - Log the number of migrated records

## Manual Fix via Odoo Shell

You can also run this in Odoo shell:

```python
env = self.env
attributes = env['product.attribute'].search([('display_type', '=', 'text')])
if attributes:
    attributes.write({'display_type': 'radio'})
    print(f"Fixed {len(attributes)} attribute(s)")
```

## After Fixing

Once the data is fixed:
- The frontend error will disappear
- Attributes will work normally
- Use `is_custom=True` on attribute values for free text input (see FREE_TEXT_GUIDE.md)


