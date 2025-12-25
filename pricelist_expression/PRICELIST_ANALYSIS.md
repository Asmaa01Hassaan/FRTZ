# Price List Analysis: Odoo 18 Default vs Custom pricelist_expression Module

## Table of Contents
1. [How Price Lists Work in Odoo 18](#how-price-lists-work-in-odoo-18)
2. [Price List Assignment (Roles/Country Groups)](#price-list-assignment-rolescountry-groups)
3. [Custom Module Analysis](#custom-module-analysis)
4. [Comparison: Default vs Custom](#comparison-default-vs-custom)

---

## How Price Lists Work in Odoo 18

### Overview
Price lists in Odoo 18 are used to define different pricing rules for products based on various criteria. They consist of:
- **Pricelist**: A collection of pricing rules
- **Pricelist Items/Rules**: Individual rules that determine how prices are calculated

### Core Components

#### 1. Pricelist Model (`product.pricelist`)
Located in: `addons/product/models/product_pricelist.py`

**Key Fields:**
- `name`: Pricelist name
- `currency_id`: Currency for the pricelist
- `company_id`: Company association
- `country_group_ids`: Many2many relationship with country groups (for geographic-based assignment)
- `item_ids`: One2many relationship with pricelist items/rules
- `active`: Whether the pricelist is active

**Key Methods:**
- `_compute_price_rule()`: Main method that computes prices for products
- `_get_applicable_rules()`: Finds rules that match products, date, and other criteria
- `_get_partner_pricelist_multi()`: Determines which pricelist to use for partners

#### 2. Pricelist Item Model (`product.pricelist.item`)
Located in: `addons/product/models/product_pricelist_item.py`

**Key Fields:**

**Application Scope (`applied_on`):**
- `3_global`: Applies to all products
- `2_product_category`: Applies to a specific product category
- `1_product`: Applies to a specific product template
- `0_product_variant`: Applies to a specific product variant

**Base Price (`base`):**
- `list_price`: Based on product's sales price
- `standard_price`: Based on product's cost
- `pricelist`: Based on another pricelist

**Compute Price Method (`compute_price`):**
- `fixed`: Fixed price regardless of base price
- `percentage`: Percentage discount/markup
- `formula`: Complex formula with discount, rounding, surcharge, and margins

**Additional Fields:**
- `min_quantity`: Minimum quantity for rule to apply
- `date_start` / `date_end`: Validity period
- `price_discount`: Discount percentage (for formula)
- `price_markup`: Markup percentage (for formula, when base is cost)
- `price_round`: Rounding value
- `price_surcharge`: Fixed amount to add/subtract
- `price_min_margin` / `price_max_margin`: Min/max margin constraints

### Price Computation Flow

1. **Rule Selection** (`_get_applicable_rules`):
   - Searches for rules matching:
     - Pricelist ID
     - Product category (or parent categories)
     - Product template/variant
     - Date range (if specified)
   - Orders by: `applied_on, min_quantity desc, categ_id desc, id desc`
   - First matching rule is selected

2. **Price Calculation** (`_compute_price`):
   ```python
   if compute_price == 'fixed':
       price = fixed_price
   elif compute_price == 'percentage':
       price = base_price - (base_price * (percent_price / 100))
   elif compute_price == 'formula':
       # Apply discount/markup
       discount = price_discount if base != 'standard_price' else -price_markup
       price = base_price - (base_price * (discount / 100))
       # Apply rounding
       if price_round:
           price = round(price, precision_rounding=price_round)
       # Apply surcharge
       if price_surcharge:
           price += surcharge
       # Apply margin constraints
       if price_min_margin:
           price = max(price, base_price + price_min_margin)
       if price_max_margin:
           price = min(price, base_price + price_max_margin)
   ```

3. **Base Price Calculation** (`_compute_base_price`):
   - If `base == 'pricelist'`: Recursively gets price from another pricelist
   - If `base == 'standard_price'`: Gets product cost
   - If `base == 'list_price'`: Gets product sales price
   - Handles currency conversion if needed

---

## Price List Assignment (Roles/Country Groups)

### Partner-Based Assignment

Odoo uses **partner properties** to assign pricelists, not traditional "roles". The assignment follows this priority:

1. **Partner-Specific Pricelist** (`specific_property_product_pricelist`):
   - Set directly on the partner form
   - Highest priority
   - Company-specific

2. **Country Group-Based Assignment**:
   - Pricelists can be assigned to `country_group_ids`
   - When a partner has no specific pricelist, Odoo looks for pricelists matching the partner's country
   - Logic in `_get_partner_pricelist_multi()`:
     ```python
     # Groups partners by country
     partners_by_country = remaining_partners.grouped('country_id')
     for country, partners in partners_by_country.items():
         # Find pricelist matching country group
         pl = Pricelist.search([
             ('country_group_ids.country_ids', '=', country.id),
             ('active', '=', True),
             ('company_id', 'in', [company_id, False])
         ], limit=1)
     ```

3. **Generic Property**:
   - System-wide default pricelist
   - Stored in `ir.config_parameter`

4. **Fallback**:
   - First available active pricelist

### Sale Order Integration

When creating a sale order:
```python
# In sale.order model
@api.depends('partner_id')
def _compute_pricelist_id(self):
    order.pricelist_id = order.partner_id.property_product_pricelist
```

The pricelist is automatically assigned from the partner's property.

### Country Groups

Country groups (`res.country.group`) allow grouping countries together. Pricelists can be assigned to country groups, making it easy to:
- Set regional pricing (e.g., "Europe", "Middle East")
- Apply different currencies by region
- Manage pricing for multiple countries at once

---

## Custom Module Analysis

### Module: `pricelist_expression`

**Location:** `custom_frtz/FRTZ/pricelist_expression/`

**Purpose:** Adds expression-based pricing with installment support

### Key Features

#### 1. New Compute Price Method: "Expression"

**File:** `models/product_pricelist_item.py`

**Changes:**
- Extends `compute_price` selection field to include `'expression'`
- Adds `price_expression` field (Char) for Python expressions

**Expression Context Variables:**
- `price`: Base price (from rule's base price setting)
- `cost`: Product standard cost (`standard_price`)
- `qty`: Order line quantity
- `installment_num`: Number of installments (from sale order line)
- `first_payment`: First payment amount (from sale order line)
- `round()`: Rounding function
- `ceil()`: Ceiling function (from math module)

**Example Expression:**
```python
(price * 0.5 * round(installment_num/11, 1)) + 2
```

#### 2. Price Computation Logic

**Method:** `_compute_price()` override

**Flow:**
1. Calls parent `_compute_price()` to get base price
2. If `compute_price == 'expression'` and expression exists:
   - Builds evaluation environment with context variables
   - Uses `safe_eval()` to evaluate expression safely
   - Returns computed price
   - Falls back to base price on error

**Safety:**
- Uses `safe_eval()` to prevent code injection
- Wraps in try/except for error handling
- Logs errors for debugging

#### 3. Sale Order Line Integration

**File:** `models/sale_order_line.py`

**New Fields:**
- `installment_num`: Float field for number of installments
- `first_payment`: Float field for first payment amount
- `is_immediate_term`: Related boolean from sale order

**Key Methods:**
- `_get_pricelist_context()`: Builds context with installment info
- `_recompute_price_from_installments()`: Recomputes price when installments change
- `_get_pricelist_price()`: Override to pass installment context

**Onchange Handlers:**
- `_onchange_installment_related()`: Recomputes price when installments change
- `_onchange_product_or_qty()`: Recomputes price when product/qty changes
- `_onchange_order_id()`: Resets installments if payment is immediate

**Integration Points:**
- `create()`: Recomputes price after creation
- `write()`: Recomputes price when relevant fields change

#### 4. Pricelist Model Enhancement

**File:** `models/product_pricelist.py`

**Changes:**
- Overrides `_compute_price_rule()` to log installment context
- Passes context through to item computation

#### 5. UI Changes

**File:** `views/pricelist_item_views.xml`

**Pricelist Item Form:**
- Adds `price_expression` field
- Visible only when `compute_price == 'expression'`
- Uses radio widget for compute_price selection

**Sale Order Form:**
- Adds `installment_num` and `first_payment` fields to order lines
- Fields hidden when `is_immediate_term == True`
- Visible in both list and form views

### Dependencies

- `product`: Core product module
- `sale`: Sale order functionality
- `account_invoice_installments`: Installment functionality (custom module)

---

## Comparison: Default vs Custom

### Default Odoo 18 Price List

| Feature | Implementation |
|---------|---------------|
| **Compute Methods** | Fixed, Percentage, Formula |
| **Formula Components** | Discount/Markup, Rounding, Surcharge, Min/Max Margin |
| **Context Variables** | None (static calculation) |
| **Dynamic Pricing** | Limited to formula-based calculations |
| **Installment Support** | None |
| **Expression Evaluation** | No Python expression support |

**Strengths:**
- Simple, predictable pricing rules
- Well-tested and stable
- Good performance
- Clear UI for non-technical users

**Limitations:**
- Cannot use dynamic variables (quantity, dates, etc.) in complex ways
- No Python expression evaluation
- No installment-aware pricing

### Custom pricelist_expression Module

| Feature | Implementation |
|---------|---------------|
| **Compute Methods** | Fixed, Percentage, Formula, **Expression** |
| **Formula Components** | All default + Python expressions |
| **Context Variables** | price, cost, qty, installment_num, first_payment |
| **Dynamic Pricing** | Full Python expression support |
| **Installment Support** | Yes, with automatic price recomputation |
| **Expression Evaluation** | Yes, using safe_eval |

**Strengths:**
- Flexible Python expression evaluation
- Installment-aware pricing
- Real-time price updates on installment changes
- Safe evaluation with error handling

**Limitations:**
- Requires technical knowledge to write expressions
- Potential performance impact (expression evaluation)
- Additional complexity in codebase
- Dependency on custom `account_invoice_installments` module

### Key Differences

#### 1. Expression Evaluation

**Default:**
```python
# Formula-based (predefined structure)
price = base_price - (base_price * (discount / 100))
if price_round:
    price = round(price, precision_rounding=price_round)
price += surcharge
```

**Custom:**
```python
# Python expression (user-defined)
env = {
    "price": base_price,
    "cost": product.standard_price,
    "qty": quantity,
    "installment_num": context.get("installment_num", 0),
    "first_payment": context.get("first_payment", 0),
    "round": round,
    "ceil": math.ceil,
}
price = safe_eval(expression, env)
```

#### 2. Context Passing

**Default:**
- No context variables passed to price computation
- Static calculation based on product and rule settings

**Custom:**
- Passes installment context through `env.context`
- Sale order line fields available in pricing context
- Dynamic variables based on order state

#### 3. Price Recalculation

**Default:**
- Price recalculated on:
  - Product change
  - Quantity change
  - Pricelist change

**Custom:**
- Price recalculated on:
  - All default triggers
  - Installment number change
  - First payment change
  - Payment type change (immediate vs installment)

#### 4. Use Cases

**Default Odoo:**
- Standard discount/markup pricing
- Quantity-based pricing
- Category-based pricing
- Time-based pricing (via date ranges)

**Custom Module:**
- Installment-based pricing calculations
- Complex mathematical formulas
- Dynamic pricing based on order context
- Custom business logic in expressions

### Code Quality Comparison

#### Default Odoo
- ✅ Well-documented
- ✅ Extensive error handling
- ✅ Performance optimized
- ✅ Follows Odoo conventions
- ✅ Comprehensive tests

#### Custom Module
- ✅ Good logging for debugging
- ✅ Error handling with fallbacks
- ⚠️ Limited documentation (README only)
- ⚠️ No visible test coverage
- ✅ Follows Odoo inheritance patterns
- ⚠️ Some hardcoded logic (immediate_term check)

### Recommendations

#### When to Use Default Odoo:
- Standard pricing requirements
- Non-technical users managing prices
- Performance-critical scenarios
- Standard discount/markup needs

#### When to Use Custom Module:
- Installment-based pricing required
- Complex mathematical formulas needed
- Dynamic pricing based on order context
- Technical team available to write expressions

#### Improvements for Custom Module:
1. Add comprehensive test coverage
2. Add expression validation before saving
3. Add expression examples/templates in UI
4. Consider caching expression results
5. Add expression syntax help/documentation
6. Consider adding more context variables (date, partner, etc.)

---

## Summary

The custom `pricelist_expression` module extends Odoo's default price list functionality by:
1. Adding Python expression evaluation capability
2. Integrating installment information into pricing
3. Providing real-time price recalculation based on installment changes

While it adds significant flexibility, it also increases complexity and requires technical expertise. The default Odoo price list system is more suitable for standard use cases, while the custom module is ideal for businesses with specific installment pricing requirements.



