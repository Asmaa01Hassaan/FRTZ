# FRTZ Customer Module - Customer Views Explanation

## Overview

The `frtz_customer` module enhances customer (res.partner) management with custom fields, display improvements, and guarantees functionality.

## Module Structure

```
frtz_customer/
├── models/
│   ├── res_partner.py          # Extends res.partner (Customer)
│   ├── customer_guarantees.py  # Customer guarantees model
│   ├── sale_order.py           # Extends sale.order
│   └── account_move.py         # Extends account.move
├── views/
│   ├── customer_view.xml       # Customer form view modifications
│   ├── customer_guarantees_view.xml  # Guarantees views
│   ├── sale_order_view.xml     # Sale order view modifications
│   └── res_partner_installment_views.xml
```

## Customer View Modifications (`customer_view.xml`)

### 1. **Customer Code Field (ref) on Same Line as Name**

**Location:** Lines 18-25

```xml
<xpath expr="//div[hasclass('oe_title')]//h1" position="attributes">
    <attribute name="class">d-flex align-items-center gap-3</attribute>
</xpath>
<xpath expr="//div[hasclass('oe_title')]//h1/field[@name='name']" position="after">
    <field name="ref"
           style="width: 200px; font-size: 14px;"
           placeholder="Customer Code"/>
</xpath>
```

**How it works:**
- Modifies the title section (`oe_title`) to use flexbox layout (`d-flex align-items-center gap-3`)
- Adds the `ref` field (Customer Code) right after the `name` field
- Both fields appear on the same line in the header
- The `ref` field uses standard Odoo field (not custom) - it's the built-in "Reference" field

**Visual Result:**
```
[Customer Name] [Customer Code]
```

### 2. **Name Field Placeholders**

**Location:** Lines 10-16

```xml
<xpath expr="(//field[@name='name'])[1]" position="attributes">
    <attribute name="placeholder">Enter full name...</attribute>
</xpath>
<xpath expr="(//field[@name='name'])[2]" position="attributes">
    <attribute name="placeholder">Enter full name...</attribute>
</xpath>
```

**How it works:**
- Updates placeholder text for all `name` fields in the form
- Provides helpful hint text to users

### 3. **Status Field**

**Location:** Lines 26-28

```xml
<xpath expr="//field[@name='category_id']" position="after">
    <field name="status"/>
</xpath>
```

**How it works:**
- Adds a `status` field after the `category_id` field
- Status can be: 'active' or 'suspended'
- Helps track customer account status

### 4. **Company Name Label**

**Location:** Lines 30-32

```xml
<xpath expr="//field[@name='parent_id']" position="before">
    <span>Company Name</span>
</xpath>
```

**How it works:**
- Adds a label "Company Name" before the `parent_id` field
- Improves form clarity

## Model Extensions (`res_partner.py`)

### 1. **Display Name Computation**

```python
@api.depends('name', 'ref')
def _compute_display_name(self):
    for partner in self:
        name = partner.name or ''
        if partner.ref:
            name = f"{partner.ref} {name}"
        partner.display_name = name
```

**How it works:**
- Computes a custom display name that combines `ref` (code) and `name`
- Format: `[CODE] [NAME]` (e.g., "CUST001 John Doe")
- Stored in database for performance

### 2. **Name Get Override**

```python
def name_get(self):
    result = []
    for partner in self:
        result.append((partner.id, partner.display_name or partner.name))
    return result
```

**How it works:**
- Overrides `name_get()` to return the computed `display_name`
- Used when displaying partners in dropdowns, lists, etc.
- Shows "CODE NAME" format everywhere

### 3. **Name Search Enhancement**

```python
@api.model
def name_search(self, name='', args=None, operator='ilike', limit=100):
    args = args or []
    domain = []
    if name:
        domain = ['|', ('name', 'ilike', name), ('ref', 'ilike', name)]
    records = self.search(domain + args, limit=limit)
    return records.name_get()
```

**How it works:**
- Allows searching by both `name` and `ref` (code)
- When you type in a search field, it searches both fields
- Returns results with the formatted display name

### 4. **Status Field**

```python
status = fields.Selection([
    ('active', 'Active'),
    ('suspended', 'Suspended'),
], string='Status', default='active')
```

**How it works:**
- Adds status tracking to customers
- Default is 'active'
- Can be used to filter or restrict access

## Customer Guarantees Integration

### Model: `customer.guarantees`

- Links customers to sale orders
- Tracks guarantee status
- Stores notes and dates

### View Integration

- Added as a page in sale order form
- Shows list of customer guarantees
- Editable inline list

## Data Flow

```
1. User creates/edits customer
   ↓
2. Enters name and code (ref) on same line
   ↓
3. display_name is computed: "CODE NAME"
   ↓
4. name_get() returns formatted display_name
   ↓
5. name_search() allows searching by code or name
   ↓
6. Customer appears everywhere as "CODE NAME"
```

## Key Features

✅ **Code + Name on Same Line** - Visual improvement in form header  
✅ **Smart Display Name** - Shows "CODE NAME" format everywhere  
✅ **Enhanced Search** - Search by code or name  
✅ **Status Tracking** - Active/Suspended status  
✅ **Guarantees Management** - Link guarantees to customers and orders  

## Usage Examples

### Creating a Customer
1. Go to Contacts > Create
2. Enter name: "John Doe"
3. Enter code (ref): "CUST001"
4. Both appear on same line in header
5. Display name becomes: "CUST001 John Doe"

### Searching
- Type "CUST001" → Finds customer
- Type "John" → Finds customer
- Both searches work because of `name_search` override

### Display
- In dropdowns: Shows "CUST001 John Doe"
- In lists: Shows "CUST001 John Doe"
- In forms: Shows name and code on same line

