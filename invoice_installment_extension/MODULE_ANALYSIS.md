# Invoice Installment Extension Module - Analysis

## Module Overview
**Name:** `invoice_installment_extension`  
**Version:** 18.0.1.0.0  
**Category:** Accounting/Invoicing  
**Purpose:** Enhanced invoice management with comprehensive installment support, automatic payment term generation, and installment tracking.

---

## Dependencies
- `base`
- `account`
- `sale`
- `account_invoice_installments`
- `pricelist_expression`
- `sale_invoice_per_line`
- `frtz_customer`

---

## Core Models

### 1. **AccountMove (account.move)** - Invoice Model Extension
**File:** `models/account_move.py`

#### Key Fields:
- `installment_num` (Float): Number of installments for the invoice
- `first_payment` (Monetary): First payment amount for installment calculations
- `view_generate` (Boolean): Controls visibility of generate buttons (for export group)
- `hide_buttons_setting` (Boolean): Computed field for hiding buttons based on config
- `to_pay_amount` (Monetary): Amount to be distributed among installments
- `amount_to_pay` (Monetary): Computed field equal to `to_pay_amount` (readonly)
- `installment_list_ids` (One2many): Related installments (inherited from base module)
- `has_installments` (Boolean): Computed field indicating if invoice has installments
- `installment_count`, `paid_installment_count`, `pending_installment_count`, `overdue_installment_count`: Count fields
- `total_paid_amount`, `total_remaining_amount`: Monetary totals
- `nearest_due_installment_amount`, `nearest_due_installment_date`: Nearest due installment info
- `due_date_filter` (Date): Date filter for calculating due amounts
- `due_amount` (Monetary): Computed total of installments due on/before `due_date_filter`

#### Key Methods:
1. **`_auto_generate_payment_terms()`**: Automatically creates payment terms based on `installment_num`
   - Creates "Regular Installment" payment term if needed
   - Auto-assigns "Regular Installment" when `installment_num == 1` and `first_payment == 0`

2. **`action_generate_payment_term()`**: Opens wizard to manually generate payment terms

3. **`action_create_regular_installment_term()`**: Creates/gets "Regular Installment" payment term (100% due at end of next month)

4. **`action_post()`**: Override to auto-generate installments after invoice confirmation

5. **`_auto_generate_installments()`**: Generates installment list automatically
   - For "Regular Installment" payment term: Uses `_generate_from_installment_num_with_payment_term()`
   - For other payment terms: Uses `_generate_from_payment_terms()` or `_generate_from_installment_num()`

6. **`_generate_from_payment_terms()`**: Creates installments from payment term lines
   - Uses payment term line's `_get_due_date()` for accurate due date calculation
   - Handles `days_after_end_of_next_month` delay type

7. **`_generate_from_installment_num_with_payment_term()`**: Generates installments based on `installment_num` but uses payment term for due date calculation
   - First installment uses payment term's base due date
   - Subsequent installments add months incrementally

8. **`_generate_from_installment_num()`**: Fallback method using fixed 30-day intervals

9. **`action_pay_installments()`**: Distributes `to_pay_amount` among eligible installments
   - Prioritizes `partial_paid` installments first, then `pending` by due date
   - Updates installment states and paid amounts

10. **`_compute_due_amount()`**: Computes total remaining amount of installments due on/before `due_date_filter`

11. **`_compute_nearest_due_installment()`**: Finds nearest pending/partial_paid/overdue installment

12. **`_compute_installment_count()`**: Counts installments by state

13. **`_compute_installment_totals()`**: Calculates total paid and remaining amounts

#### Sale Order Extension:
- `hide_buttons_setting`: Controls visibility of send/preview buttons
- Blocks `action_quotation_send()` when config enabled
- Blocks state transition to 'sent' when config enabled

---

### 2. **InstallmentList (installment.list)** - Installment Tracking Model
**File:** `models/installment_list.py`

#### Key Fields:
- `name` (Char): Installment reference (auto-generated from sequence)
- `sequence` (Integer): Installment sequence number
- `invoice_id` (Many2one): Related invoice
- `amount` (Monetary): Installment amount
- `due_date` (Date): Due date
- `paid_date` (Date): Date when paid
- `paid_amount` (Monetary): Amount paid (supports partial payments)
- `remaining_amount` (Monetary): Computed `amount - paid_amount`
- `state` (Selection): Status (`pending`, `partial_paid`, `paid`, `overdue`, `cancelled`)
- `is_late` (Boolean): Computed field for overdue status
- `days_overdue` (Integer): Computed days overdue
- `customer_guarantees_names` (Char): Related customer guarantees names

#### Key Methods:
1. **`action_mark_paid()`**: Marks installment as fully paid
2. **`action_mark_partial_paid()`**: Marks installment as partially paid or updates partial payment
3. **`action_mark_overdue()`**: Marks installment as overdue
4. **`action_cancel()`**: Cancels installment
5. **`_compute_remaining_amount()`**: Calculates remaining amount
6. **`_compute_is_late()`**: Checks if installment is overdue
7. **`_compute_days_overdue()`**: Calculates days overdue
8. **`_cron_check_overdue_installments()`**: Scheduled action to mark overdue installments

#### Features:
- Automatic sequence generation
- Partial payment support with `partial_paid` state
- Automatic overdue detection via cron job
- Customer guarantee tracking

---

### 3. **AccountPaymentTerm (account.payment.term)** - Payment Term Extension
**File:** `models/account_payment_term.py`

#### Key Fields:
- `is_installment_term` (Boolean): Indicates if term is for installments
- `installment_count` (Integer): Number of installments
- `first_payment_percentage` (Float): First payment percentage

#### Key Methods:
1. **`create_installment_term()`**: Creates payment term for installments
   - Supports first payment (fixed amount or percentage)
   - Creates regular installments with configurable intervals
   - Returns created payment term

---

### 4. **PaymentTermGenerationWizard (payment.term.generation.wizard)** - Payment Term Wizard
**File:** `models/payment_term_wizard.py`

#### Purpose:
Wizard for manually generating payment terms with customizable settings.

#### Key Fields:
- `invoice_id`: Related invoice
- `installment_num`: Number of installments
- `first_payment_type`: Percentage or Fixed Amount
- `first_payment_percentage`: Percentage value
- `first_payment_amount`: Fixed amount value
- `payment_interval`: Days between payments

#### Key Methods:
- **`action_generate_payment_term()`**: Generates and assigns payment term to invoice

---

### 5. **PaymentInvoiceWizard (payment.invoice.wizard)** - Payment Invoice Wizard
**File:** `models/payment_invoice_wizard.py`

#### Purpose:
Wizard for paying multiple invoices from a payment form. Shows unpaid invoices for a customer and allows batch payment processing.

#### Key Fields:
- `payment_id`: Related payment
- `partner_id`: Customer (related)
- `invoice_ids`: One2many to wizard lines
- `total_due_amount`: Sum of all due amounts
- `total_to_pay`: Sum of all to_pay amounts

#### Wizard Line Model (`payment.invoice.wizard.line`):
- `invoice_id`: Invoice
- `invoice_name`, `invoice_date`, `amount_total`, `total_remaining_amount`: Invoice fields
- `due_date_filter`: Date filter
- `due_amount`: Computed due amount
- `to_pay`: Amount to pay for this invoice

#### Key Methods:
- **`action_pay_all_invoices()`**: Processes payments for all invoices with `to_pay > 0`

---

### 6. **PaymentInvoiceToPay (payment.invoice.to.pay)** - Payment Invoice Link
**File:** `models/payment_invoice_to_pay.py`

#### Purpose:
Intermediate model to store `to_pay_amount` and `due_date_filter` for each invoice in a payment (currently unused since account.payment was removed).

#### Key Fields:
- `payment_id`: Related payment
- `invoice_id`: Related invoice
- `to_pay_amount`: Amount to pay
- `due_date_filter`: Date filter
- `due_amount`: Computed due amount

---

### 7. **ResPartner (res.partner)** - Partner Extension
**File:** `models/res_partner.py`

#### Key Fields (Computed):
- `has_installments`: Boolean indicating if partner has installments
- `installment_count`, `paid_installment_count`, `partial_paid_installment_count`, `pending_installment_count`, `overdue_installment_count`: Count fields
- `total_installment_amount`, `total_paid_amount`, `total_remaining_amount`: Monetary totals

#### Key Methods:
- **`action_view_installments()`**: Opens installment list view filtered by partner

---

### 8. **ResConfigSettings (res.config.settings)** - Configuration
**File:** `models/res_config_settings.py`

#### Purpose:
System-wide configuration settings.

#### Key Fields:
- `hide_buttons`: Hides buttons on account moves
- `hide_sale_send_preview_buttons`: Hides send/preview buttons on sale orders

Stored as `ir.config_parameter`:
- `account.hide_buttons`
- `sale.hide_send_preview_buttons`

---

## Data Files

### `data/installment_data.xml`
1. **Installment List Sequence**: Auto-generates installment reference numbers (prefix: INST)
2. **Regular Installment Payment Term**: Pre-defined payment term with 100% due at end of next month

---

## Views

### 1. **Account Move Views** (`views/account_move_views.xml`)
- Adds installment fields to invoice header (`installment_num`, `first_payment`)
- Adds "Generate Payment Term" and "Generate Regular Installment" buttons
- Adds "Installment Information" notebook page with:
  - Installment counts and totals
  - Nearest due installment info
  - Due Amount Calculation section (`due_date_filter`, `due_amount`, `to_pay_amount`)
  - "Pay Installment" button
  - Installment list view
- Adds green ribbon widget when all installments are paid
- Hides buttons based on `hide_buttons_setting`

### 2. **Sale Order Views** (in `account_move_views.xml`)
- Hides "Send by Email" and "Preview" buttons based on config
- Hides "Quotation Sent" state from statusbar and filters

### 3. **Installment List Views** (`views/installment_list_views.xml`)
- List and form views for installment tracking
- Shows installment details, payment status, and actions

### 4. **Payment Term Views** (`views/account_payment_term_views.xml`)
- Extends payment term form with installment-related fields

### 5. **Payment Term Wizard Views** (`views/payment_term_wizard_views.xml`)
- Wizard form for generating payment terms

### 6. **Payment Invoice Wizard Views** (`views/payment_invoice_wizard_views.xml`)
- Wizard form for paying multiple invoices

### 7. **Partner Views** (`views/res_partner_installment_views.xml`)
- Adds "Installment Information" page to partner form
- Shows installment statistics and totals

### 8. **Menu Views** (`views/menu_views.xml`)
- Adds FRTZ menu structure with sub-menus

### 9. **Config Settings Views** (`views/res_config_settings_view.xml`)
- Settings page for hiding buttons

---

## Key Workflows

### 1. **Installment Creation Workflow**
1. User sets `installment_num` and `first_payment` on invoice
2. On create/write, `_auto_generate_payment_terms()` is called
3. If "Regular Installment" should be used, it's created/assigned
4. On invoice confirmation (`action_post()`), `_auto_generate_installments()` is called
5. Installments are generated based on payment term or `installment_num`

### 2. **Regular Installment Workflow**
1. User clicks "Generate Regular Installment" button
2. Payment term "Regular Installment" is created/retrieved (100% due at end of next month)
3. If `installment_num == 1` and `first_payment == 0`, term is auto-assigned
4. Installments are generated using payment term's due date logic

### 3. **Payment Processing Workflow**
1. User sets `due_date_filter` and `to_pay_amount` on invoice
2. `due_amount` is computed automatically
3. User clicks "Pay Installment" button
4. `action_pay_installments()` distributes payment:
   - Prioritizes `partial_paid` installments (oldest first)
   - Then `pending` installments (oldest first)
   - Updates states and paid amounts accordingly

### 4. **Wizard Payment Workflow**
1. User opens "Pay for Invoices" wizard from payment form
2. Wizard loads unpaid invoices for customer
3. User sets `due_date_filter` and `to_pay` for each invoice
4. User clicks "Pay All Selected Invoices"
5. Payments are processed for all invoices with `to_pay > 0`

---

## Features

### ✅ **Installment Management**
- Automatic installment generation from payment terms or `installment_num`
- Support for first payment (custom amount)
- Partial payment support (`partial_paid` state)
- Automatic overdue detection and marking
- Installment tracking and statistics

### ✅ **Payment Term Automation**
- Automatic payment term creation based on installment data
- "Regular Installment" payment term (100% due at end of next month)
- Manual payment term generation wizard
- Support for complex payment term structures

### ✅ **Payment Processing**
- Date-based due amount calculation
- Smart payment distribution (prioritizes partial payments)
- Batch payment processing via wizard
- Real-time payment tracking

### ✅ **UI Enhancements**
- Installment information page on invoices
- Installment statistics on partner forms
- Green ribbon when all installments paid
- Configurable button hiding
- Menu structure organization

### ✅ **Integration**
- Sale order installment data transfer
- Customer guarantee tracking
- Integration with pricelist expressions
- Multi-currency support

---

## Technical Notes

### Payment Term Due Date Calculation
- Uses payment term line's `_get_due_date()` method
- Properly handles `days_after_end_of_next_month` delay type
- For "Regular Installment": First installment due at end of next month, subsequent installments monthly

### Installment Generation Logic
1. **Regular Installment**: Uses `_generate_from_installment_num_with_payment_term()` - calculates amounts from `installment_num`, uses payment term for due dates
2. **Other Payment Terms**: Uses `_generate_from_payment_terms()` - creates installments from payment term lines
3. **Fallback**: Uses `_generate_from_installment_num()` - fixed 30-day intervals

### State Management
- `pending`: Initial state, not paid
- `partial_paid`: Partially paid (has `paid_amount` < `amount`)
- `paid`: Fully paid (`paid_amount` == `amount`)
- `overdue`: Past due date (set by cron or manually)
- `cancelled`: Cancelled installments

---

## Security
- Access rights defined in `security/ir.model.access.csv`
- Button visibility controlled by user groups (`base.group_allow_export`)
- Configurable button hiding via system parameters

---

## Internationalization
- Arabic translations in `i18n/ar.po`
- Pot file for translation template

---

## Current Status
- ✅ All core functionality implemented
- ✅ Account payment customizations removed (as requested)
- ✅ Wizard for batch invoice payment available
- ✅ Partial payment support working
- ✅ Automatic installment generation working
- ✅ Payment term automation working

---

## Potential Improvements
1. Add installment payment reconciliation
2. Add installment reminders/notifications
3. Add installment reporting/dashboards
4. Add installment templates
5. Add installment approval workflows
