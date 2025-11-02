# Invoice Installment Extension - Module Analysis

## 📋 Overview

The **Invoice Installment Extension** module is a comprehensive Odoo 18 addon that extends invoice management with automated installment payment functionality. It enables businesses to manage invoices with multiple payment installments, automatically generates payment terms, and provides tracking and reporting capabilities for installment-based sales.

---

## 🎯 Core Functionality

### **1. Installment Management**
- **Installment Fields**: Adds `installment_num` (number of installments) and `first_payment` (first payment amount) fields to invoices
- **Automatic Payment Term Generation**: Creates payment terms automatically based on installment data
- **Installment List Tracking**: Maintains detailed records of each installment payment

### **2. Payment Term Automation**
- **Auto-Generation**: Automatically creates payment terms when installment data is entered
- **Flexible Configuration**: Supports different first payment types (percentage or fixed amount)
- **Payment Intervals**: Configurable days between payments (default: 30 days)

### **3. Installment Tracking**
- **State Management**: Tracks installment status (Pending, Paid, Overdue, Cancelled)
- **Due Date Calculation**: Automatically calculates due dates based on payment intervals
- **Overdue Detection**: Identifies and marks overdue installments

---

## 🏗️ Module Architecture

### **Models (Python Files)**

#### **1. account_move.py** - Invoice Extensions
**Purpose**: Extends `account.move` (Invoice) model with installment functionality

**Key Features**:
- **Fields Added**:
  - `installment_num`: Number of installments
  - `first_payment`: First payment amount
  - `hide_buttons_setting`: Configuration to hide buttons
  - `installment_list_ids`: Related installment records
  
- **Automatic Behaviors**:
  - **On Create**: Auto-generates payment terms if `installment_num > 0`
  - **On Write**: Re-generates payment terms if installment data changes
  - **On Post (Confirm)**: Auto-generates installment list records

- **Generation Methods**:
  - `_auto_generate_payment_terms()`: Creates payment terms from installment data
  - `_auto_generate_installments()`: Creates installment list from payment terms
  - `_generate_from_payment_terms()`: Extracts installments from payment term lines
  - `_generate_from_installment_num()`: Creates installments when no payment terms exist

**Sale Order Extensions**:
- Hides "Send by Email" and "Preview" buttons based on configuration
- Prevents state transition to "sent" when configuration is enabled
- Removes "Quotation Sent" state from statusbar

#### **2. account_move_line.py** - Invoice Line Extensions
**Purpose**: Extends invoice lines with installment data from sale order lines

**Key Features**:
- Transfers `installment_num` and `first_payment` from sale order lines to invoice lines
- Automatically syncs installment data when invoice lines are created/updated

#### **3. account_payment_term.py** - Payment Term Extensions
**Purpose**: Extends payment terms with installment-specific functionality

**Key Methods**:
- `create_installment_term()`: Factory method to create payment terms for installments
  - Parameters: `installment_num`, `first_payment`, `total_amount`, `payment_interval`
  - Creates payment term lines with percentages and due dates
  - Supports first payment (if specified) and regular installments

**Fields Added**:
- `is_installment_term`: Boolean flag to identify installment payment terms
- `installment_count`: Number of installments
- `first_payment_percentage`: Percentage of first payment

#### **4. installment_list.py** - Installment Tracking Model
**Purpose**: Core model for tracking individual installment payments

**Key Features**:
- **Fields**:
  - Basic info: `name`, `sequence`, `invoice_id`, `partner_id`
  - Payment: `amount`, `currency_id`, `due_date`, `paid_date`
  - Status: `state` (pending/paid/overdue/cancelled)
  - Payment details: `payment_method_id`, `payment_reference`, `notes`
  
- **Computed Fields**:
  - `display_name`: Formatted display name
  - `is_late`: Boolean flag for overdue installments
  - `days_overdue`: Number of days past due date
  
- **Actions**:
  - `action_mark_paid()`: Mark installment as paid
  - `action_mark_overdue()`: Mark as overdue
  - `action_cancel()`: Cancel installment
  
- **Cron Job**: `_cron_check_overdue_installments()` - Automatically marks overdue installments

**Account Move Extensions** (in same file):
- Adds installment list relationship and computed statistics:
  - `installment_count`, `paid_installment_count`, `pending_installment_count`, `overdue_installment_count`
  - `total_paid_amount`, `total_remaining_amount`

#### **5. payment_term_wizard.py** - Payment Term Generation Wizard
**Purpose**: Interactive wizard to manually generate payment terms

**Features**:
- Allows configuring installment parameters
- First payment can be percentage or fixed amount
- Calculates payment intervals
- Validates input before generation

#### **6. res_partner.py** - Customer Installment Tracking
**Purpose**: Extends customers/partners with installment information

**Key Features**:
- Tracks all installments for a customer
- Computed statistics: counts and totals for installments
- Action to view all customer installments

#### **7. res_config_settings.py** - Configuration Settings
**Purpose**: System configuration for hiding buttons

**Settings**:
- Hide buttons in invoices
- Hide "Send by Email" and "Preview" buttons in sale orders

---

## 🔄 Workflow & Process Flow

### **Invoice Creation with Installments**

1. **Invoice Creation**:
   ```
   User creates invoice → Sets installment_num and first_payment
   ```

2. **Automatic Payment Term Generation**:
   ```
   create() or write() → _auto_generate_payment_terms()
   → account.payment.term.create_installment_term()
   → Creates payment term with lines
   → Assigns to invoice.invoice_payment_term_id
   ```

3. **Invoice Confirmation**:
   ```
   action_post() → _auto_generate_installments()
   → Generates installment.list records
   → Creates records with due dates and amounts
   ```

4. **Payment Tracking**:
   ```
   Installments tracked individually
   → States: pending → paid/overdue
   → Statistics updated automatically
   ```

### **Sale Order Integration**

1. **Data Flow**:
   ```
   Sale Order Line (installment_num, first_payment)
   → Invoice Line (transferred automatically)
   → Invoice Header (aggregated)
   → Payment Terms (auto-generated)
   → Installment List (on confirmation)
   ```

---

## 🎨 User Interface Components

### **Views**

1. **Invoice Form Views**:
   - Adds installment fields to invoice header
   - "Generate Payment Term" button (conditional)
   - Installment Information tab with statistics
   - Installment List view with all installments

2. **Payment Term Wizard**:
   - Form wizard for manual payment term generation
   - Configurable first payment (percentage/fixed)
   - Payment interval settings

3. **Installment List Views**:
   - List view showing all installments
   - Form view for installment details
   - Statistics and totals

4. **Partner/Customer Views**:
   - Installment Information tab
   - Statistics: counts, totals, payment status
   - Link to view all customer installments

5. **Sale Order Views**:
   - Hides "Send by Email" and "Preview" buttons (configurable)
   - Removes "Quotation Sent" state from statusbar

### **Menu Structure** (via dependency on account_invoice_installments)
- Integrated into FRTZ menu system
- Access to installment-related views

---

## 🔧 Key Methods Explained

### **Payment Term Creation**
```python
create_installment_term(installment_num, first_payment, total_amount, payment_interval)
```
- **Input**: Installment count, first payment, total amount, days between payments
- **Process**:
  1. Calculates first payment percentage (if first_payment > 0)
  2. Calculates remaining installments and amount per installment
  3. Creates payment term lines with percentages and due dates
  4. Returns payment term record
- **Output**: Payment term with installment structure

### **Installment Generation**
```python
_auto_generate_installments()
```
- **Trigger**: When invoice is confirmed (posted)
- **Process**:
  1. Checks if installments already exist
  2. Clears existing if any
  3. Generates from payment terms (if available) OR from installment_num field
  4. Creates installment.list records with amounts and due dates
- **Output**: List of installment records

### **Payment Term Generation from Installments**
```python
_generate_from_payment_terms(move)
```
- **Process**:
  1. Iterates through payment term lines
  2. Calculates amounts (percentage or fixed)
  3. Calculates due dates based on nb_days
  4. Creates installment records
- **Output**: List of installment dictionaries

### **Installment Generation without Payment Terms**
```python
_generate_from_installment_num(move)
```
- **Process**:
  1. Calculates amount per installment
  2. Handles first payment (if specified)
  3. Creates equal installments for remaining amount
  4. Sets due dates with 30-day intervals
- **Output**: List of installment dictionaries

---

## 📊 Data Relationships

```
account.move (Invoice)
├── installment_num (Float)
├── first_payment (Monetary)
├── invoice_payment_term_id (Many2one) → account.payment.term
└── installment_list_ids (One2many) → installment.list

installment.list
├── invoice_id (Many2one) → account.move
├── partner_id (Many2one) → res.partner
├── payment_term_id (Many2one) → account.payment.term (related)
└── state (Selection: pending/paid/overdue/cancelled)

res.partner (Customer)
└── installment_list_ids (One2many) → installment.list

account.move.line (Invoice Line)
├── installment_num (Float) [from sale order line]
└── first_payment (Monetary) [from sale order line]

account.payment.term
├── is_installment_term (Boolean)
├── installment_count (Integer)
└── first_payment_percentage (Float)
```

---

## 🔐 Security & Access Control

- **Access Rights**: Defined in `security/ir.model.access.csv`
- **Group Permissions**: Some features restricted to specific user groups
- **Button Visibility**: Configurable via system settings

---

## 🌍 Internationalization

- **Arabic Translation**: Full `ar.po` file with translations
- **Translation Support**: All user-facing strings are translatable

---

## ⚙️ Configuration

### **System Settings**:
1. **Hide Invoice Buttons**: Toggle to hide certain invoice buttons
2. **Hide Sale Order Buttons**: Toggle to hide "Send by Email" and "Preview" buttons
3. **Hide Quotation Sent State**: Removes "sent" state from sale order workflow

### **Payment Term Settings**:
- **Payment Interval**: Configurable days between installments (default: 30)
- **First Payment Type**: Percentage or Fixed Amount
- **Automatic Generation**: Enabled by default when installment_num is set

---

## 🔄 Integration Points

### **Dependencies**:
1. **account_invoice_installments**: Base installment functionality
2. **pricelist_expression**: Expression-based pricing with installment support
3. **sale_invoice_per_line**: Per-line invoice generation
4. **frtz_customer**: Customer management with guarantees

### **Integration Flow**:
```
Sale Order (pricelist_expression)
  ↓ (with installment_num, first_payment)
Invoice Creation (sale_invoice_per_line)
  ↓ (transfers installment data)
Invoice (invoice_installment_extension)
  ↓ (auto-generates payment terms)
Payment Terms (account.payment.term)
  ↓ (on invoice confirmation)
Installment List (installment.list)
  ↓ (tracking and payment)
Customer Records (res.partner)
```

---

## 📈 Business Logic

### **Installment Calculation Logic**:

**Scenario 1: With First Payment**
```
Total Amount: 10,000
First Payment: 2,000
Installments: 5

Calculation:
- First Payment: 2,000 (20%)
- Remaining: 8,000
- Remaining Installments: 4
- Amount per Installment: 8,000 / 4 = 2,000 each
```

**Scenario 2: Equal Installments**
```
Total Amount: 10,000
First Payment: 0
Installments: 5

Calculation:
- Amount per Installment: 10,000 / 5 = 2,000 each
```

### **Due Date Calculation**:
- First payment: Due immediately (nb_days = 0)
- Subsequent installments: Due date = Today + (installment_number × payment_interval)
- Example: If payment_interval = 30, installment 2 is due in 30 days, installment 3 in 60 days, etc.

---

## 🎯 Use Cases

1. **Regular Installment Sales**:
   - Customer purchases with 12 monthly installments
   - Automatic generation of payment schedule
   - Tracking of payment status

2. **First Payment Required**:
   - Down payment of 30% required
   - Remaining 70% split into installments
   - Tracks first payment separately

3. **Customer Payment Tracking**:
   - View all installments for a customer
   - Track overdue payments
   - Generate reports on payment status

4. **Automated Workflow**:
   - Sale order → Invoice → Payment terms → Installment list
   - Minimal manual intervention required

---

## 🔍 Technical Highlights

### **Strengths**:
1. ✅ **Automatic Generation**: Reduces manual work
2. ✅ **Flexible Configuration**: Supports various installment scenarios
3. ✅ **Comprehensive Tracking**: Detailed installment records
4. ✅ **Integration**: Seamless integration with sale orders and invoices
5. ✅ **Error Handling**: Robust exception handling and logging
6. ✅ **State Management**: Proper workflow states for installments

### **Key Design Patterns**:
- **Factory Method**: `create_installment_term()` for payment term creation
- **Computed Fields**: Real-time statistics calculation
- **Auto-Actions**: Automatic generation on create/write/post
- **Wizard Pattern**: Payment term generation wizard
- **Observer Pattern**: Cron job for overdue detection

---

## 📝 Summary

The **Invoice Installment Extension** module provides a complete solution for managing installment-based invoices in Odoo. It automates payment term generation, tracks individual installments, provides customer-level reporting, and integrates seamlessly with the sales workflow. The module is well-structured, follows Odoo best practices, and includes comprehensive error handling and logging.

