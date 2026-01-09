# Free Text Input for Product Attributes

## Overview

This guide explains how to allow users to enter free text when configuring product attributes. Odoo provides built-in support for this through the `is_custom` field on attribute values.

## How to Enable Free Text Input

### Step 1: Create or Edit a Product Attribute

1. Go to **Products > Configuration > Attributes**
2. Create a new attribute or edit an existing one
3. Set the **Display Type** to any of the available options:
   - Radio
   - Pills
   - Select
   - Color
   - Multi-checkbox

### Step 2: Add Attribute Values

1. In the **Attribute Values** tab, add one or more values
2. For each value that should allow free text input:
   - Check the **"Free text"** checkbox (this sets `is_custom=True`)
   - The value name can be used as a label or placeholder

### Step 3: Use on Products

1. When adding the attribute to a product template
2. Select the attribute values (including the one with `is_custom=True`)
3. When customers configure the product, they will see a text input field for values marked as "Free text"

## Example

**Scenario:** You want customers to be able to enter custom text for "Engraving" on a product.

1. **Create Attribute:**
   - Name: "Engraving"
   - Display Type: "Radio" or "Select"

2. **Add Value:**
   - Name: "Custom Text"
   - Check **"Free text"** checkbox
   - Save

3. **Add to Product:**
   - Go to product form
   - Add attribute "Engraving"
   - Select value "Custom Text"
   - Save

4. **Result:**
   - When customers configure the product, they will see a text input field where they can enter their custom engraving text

## Technical Details

- The `is_custom` field is a boolean on `product.attribute.value`
- When `is_custom=True`, the frontend displays a text input instead of a selection
- Multiple values can have `is_custom=True` in the same attribute
- The custom text is stored in `product.attribute.custom.value` model

## Benefits of Using `is_custom`

✅ **No frontend modifications needed** - Works with existing Odoo components  
✅ **Standard Odoo functionality** - Fully supported and tested  
✅ **Flexible** - Can mix predefined values with custom text options  
✅ **No JavaScript errors** - Avoids validation issues with custom display types  

## Notes

- The "Free text" option is available in the attribute value form view
- You can have both regular values and custom text values in the same attribute
- Custom text values work with all display types (radio, pills, select, etc.)


