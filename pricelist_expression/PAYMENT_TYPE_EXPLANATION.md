# How `payment_type` Field Works in Pricelist Items

## Current Implementation

### 1. **Field Definition**
The `payment_type` field has been added to `product.pricelist.item` model with three options:
- `immediate`: Immediate Payment
- `regular`: Regular Installments  
- `irregular`: Irregular Installments

**Location:** `models/product_pricelist_item.py`
```python
payment_type = fields.Selection(
    [
        ('immediate', _('Immediate Payment')),
        ('regular', _('Regular Installments')),
        ('irregular', _('Irregular Installments')),
    ],
    string=_("Payment plan"),
    default="immediate",
    help=_("Select the payment plan for this pricelist rule")
)
```

### 2. **View Display**
The field appears in the pricelist item form view after the "Validity Period" field.

**Location:** `views/pricelist_item_views.xml`
```xml
<xpath expr="//field[@name='date_start']" position="after">
    <field name="payment_type" string="Payment plan"/>
</xpath>
```

## How It Currently Works

### Current State: **Storage Only**
Right now, the `payment_type` field is:
- ✅ Stored in the database
- ✅ Visible in the form view
- ❌ **NOT used** in pricelist item selection
- ❌ **NOT used** in price computation

### Price Computation Flow (Current)

```
Sale Order (with payment_type='regular')
    ↓
Sale Order Line
    ↓
_get_pricelist_price()
    ↓
_get_pricelist_context() → adds installment_num, first_payment to context
    ↓
Odoo's _compute_price_rule()
    ↓
_get_applicable_rules() → selects pricelist items based on:
    - Product match
    - Date range
    - Min quantity
    - Applied on (category/product/variant)
    ❌ NOT based on payment_type
    ↓
_compute_price() → calculates price using:
    - Fixed price
    - Percentage
    - Formula
    - Expression (custom)
    ↓
Final Price
```

## How to Make It Functional

To make `payment_type` actually filter pricelist items, you need to override the rule selection method.

### Option 1: Filter in `_get_applicable_rules()` (Recommended)

**Add to:** `models/product_pricelist.py` or create new method in `product_pricelist_item.py`

```python
from odoo import models, api

class ProductPricelist(models.Model):
    _inherit = "product.pricelist"

    def _get_applicable_rules(self, products, date=None, **kwargs):
        """Override to filter by payment_type from context"""
        # Get payment_type from context (set by sale order)
        payment_type = self._context.get('payment_type')
        
        # Get base rules
        rules = super()._get_applicable_rules(products, date=date, **kwargs)
        
        # Filter by payment_type if specified
        if payment_type:
            rules = rules.filtered(
                lambda r: not r.payment_type or r.payment_type == payment_type
            )
        
        return rules
```

### Option 2: Filter in Sale Order Line Context

**Modify:** `models/sale_order_line.py` - `_get_pricelist_context()`

```python
def _get_pricelist_context(self):
    """Build pricing context with installment and payment_type information"""
    ctx = dict(self.env.context or {})
    
    # Add payment_type from order
    if self.order_id and hasattr(self.order_id, 'payment_type'):
        ctx['payment_type'] = self.order_id.payment_type
    
    # Existing installment context
    ctx["installment_num"] = float(self.installment_num or 0.0)
    ctx["first_payment"] = float(self.first_payment or 0.0)
    
    return ctx
```

### Option 3: Use in Expression Pricing

**Modify:** `models/product_pricelist_item.py` - `_compute_price()`

```python
def _compute_price(self, *args, **kwargs):
    """Compute price using expression if configured"""
    base_price = super()._compute_price(*args, **kwargs)
    
    # Get payment_type from context
    payment_type = self.env.context.get('payment_type', 'immediate')
    
    # Only apply expression if payment_type matches
    if self.compute_price == "expression" and self.price_expression:
        # Check if payment_type matches (or if pricelist item has no payment_type restriction)
        if not self.payment_type or self.payment_type == payment_type:
            # ... existing expression evaluation code ...
            pass
    
    return base_price
```

## Complete Functional Flow (After Implementation)

```
Sale Order
    payment_type = 'regular'
    ↓
Sale Order Line
    ↓
_get_pricelist_price()
    ↓
_get_pricelist_context()
    → Adds: payment_type='regular', installment_num, first_payment
    ↓
Odoo's _compute_price_rule()
    ↓
_get_applicable_rules() [OVERRIDDEN]
    → Filters pricelist items:
      - Product match ✓
      - Date range ✓
      - Min quantity ✓
      - payment_type match ✓ [NEW]
    ↓
_compute_price()
    → Uses expression with installment context
    ↓
Final Price (based on payment_type-specific rule)
```

## Use Cases

### Use Case 1: Different Prices for Different Payment Types
```
Product: Laptop
├── Pricelist Item 1: payment_type='immediate'
│   └── Price: $1000 (5% discount for immediate payment)
├── Pricelist Item 2: payment_type='regular'
│   └── Price: $1050 (standard price for installments)
└── Pricelist Item 3: payment_type='irregular'
    └── Price: $1100 (higher price for irregular installments)
```

### Use Case 2: Expression-Based Pricing
```
Pricelist Item with payment_type='regular':
    Expression: price + (installment_num * 10)
    → Adds $10 per installment to base price
```

### Use Case 3: Flexible Rules
```
Pricelist Item with payment_type=False (empty):
    → Applies to ALL payment types (fallback rule)
```

## Implementation Steps

1. ✅ **Done**: Add `payment_type` field to model
2. ✅ **Done**: Add `payment_type` to form view
3. ⚠️ **TODO**: Override `_get_applicable_rules()` to filter by payment_type
4. ⚠️ **TODO**: Pass `payment_type` in pricelist context from sale order
5. ⚠️ **TODO**: Test with different payment types

## Testing

After implementation, test:
1. Create pricelist items with different `payment_type` values
2. Create sale orders with different `payment_type` values
3. Verify correct pricelist items are selected
4. Verify prices match expected values




