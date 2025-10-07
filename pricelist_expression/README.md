# Pricelist Expression (Odoo 18)

Adds a new **Expression** type to pricelist rules so you can write Python expressions
that compute the final unit price using variables like:

- `price` (taken from the rule's **Based price**)
- `cost`  (product `standard_price`)
- `qty`   (order line quantity)
- `installment_num` (value on the sale order line)
- `round(value, ndigits)` and `math` module

### Example
```
(price * 0.5 * round(installment_num/11, 1)) + 2
```

This reproduces your sheet logic (half the base price, times rounded fraction of installments, plus 2).

### How to use
1. Install the module.
2. In **Sales > Products > Pricelists**, create/edit a rule:
   - Price Type: **Formula**
   - Based price: choose Sales Price or Cost (affects `price` variable)
   - Compute Price: **Expression**
   - Expression: write your formula
3. On the sale order line fill **Installments**; Odoo will pass it into pricing context.