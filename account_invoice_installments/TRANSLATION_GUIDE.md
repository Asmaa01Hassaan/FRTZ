# دليل الترجمة - Translation Guide
## account_invoice_installments Module

### ✅ الملفات المحدّثة (Updated Files):

1. **`i18n/ar.po`** - ملف الترجمة العربية الكامل
2. **`models/sales_order.py`** - تم تحديثه لاستخدام `_()` مع جميع النصوص
3. **`views/sales_orders_view.xml`** - يحتوي على `string` attributes واضحة

---

## 📋 الترجمات الموجودة في `ar.po`:

### حقول Sale Order (Fields):
| English | العربية |
|---------|---------|
| Payment Type | نوع خطة الدفع |
| Order Type | نوع الطلب |
| Vendor Name | اسم المورد |

### خيارات نوع الدفع (Payment Type Options):
| English | العربية |
|---------|---------|
| Immediate Payment | دفع فوري |
| Regular Installments | أقساط منتظمة |
| Irregular Installments | أقساط غير منتظمة |

### خيارات نوع الطلب (Order Type Options):
| English | العربية |
|---------|---------|
| Standard Sale Order | طلب البيع |
| Warehouse Sale Order | طلب بيع مستودع |
| External Sales Order | طلب بيع خارجي |
| Service Sales Order | طلب بيع خدمة |

### القوائم (Menus):
| English | العربية |
|---------|---------|
| FRTZ | حركات الجمعية |
| Payment Request | طلب الدفع |
| Payment Term | شروط الدفع |
| Product | المنتج |
| Products | المنتجات |
| Product Variants | متغيرات المنتج |
| Price List | قائمة الأسعار |
| Partners | الشركاء |
| Customers | العملاء |
| Companies | الشركات |

### رسائل أخرى (Other Messages):
| English | العربية |
|---------|---------|
| New | جديد |
| Sales Order | أمر البيع |
| Select the payment plan for this order | اختر خطة الدفع لهذا الطلب |
| Select the type of sale order | اختر نوع طلب البيع |

---

## 🚀 كيفية تطبيق الترجمات (How to Apply Translations):

### الطريقة 1: من واجهة Odoo (مفضّلة)

1. **أعد تشغيل خادم Odoo**
   ```bash
   sudo systemctl restart odoo
   # أو
   python3 odoo-bin -c odoo.conf
   ```

2. **حدّث الموديول**
   - افتح Odoo في المتصفح
   - اذهب إلى: **Apps** (التطبيقات)
   - فعّل Developer Mode: **Settings → Activate the developer mode**
   - ابحث عن `account_invoice_installments`
   - انقر على ⋮ (ثلاث نقاط) → **Upgrade**

3. **استورد الترجمة العربية**
   - اذهب إلى: **Settings → Translations → Import Translation**
   - اختر:
     - **Language**: Arabic / العربية
     - **File**: اختر ملف `i18n/ar.po`
     - **☑ Overwrite Existing Terms**
   - انقر **Import**

4. **امسح الكاش (Cache)**
   - Settings → Technical → Database Structure → **Clear Assets & Cache**
   - أو اضغط **Ctrl+Shift+R** في المتصفح

5. **تحقق من النتيجة**
   - غيّر لغة المستخدم إلى العربية
   - افتح أي Sale Order
   - يجب أن تظهر "نوع خطة الدفع" ✅

---

### الطريقة 2: من سطر الأوامر

```bash
cd /home/odoo/PycharmProjects/odoo18/odoo18

# حدّث الموديول وأعد تحميل الترجمات
python3 odoo-bin -c odoo.conf -d DATABASE_NAME -u account_invoice_installments --i18n-import=custom_frtz/FRTZ/account_invoice_installments/i18n/ar.po --i18n-overwrite --stop-after-init
```

---

## 📝 تعديل الترجمات يدوياً (Manual Translation Editing):

إذا أردت تعديل أي ترجمة:

1. **افتح ملف** `i18n/ar.po`
2. **ابحث عن النص** الإنجليزي المراد ترجمته:
   ```po
   msgid "Payment Type"
   msgstr "خطة الدفع"
   ```
3. **عدّل الترجمة** في السطر `msgstr`
4. **احفظ الملف**
5. **أعد استيراد الترجمة** من Odoo كما في الخطوات أعلاه

---

## 🔍 إنشاء ملف .pot جديد (Generate New .pot File):

إذا أضفت نصوصاً جديدة في الكود وتريد تحديث ملف الترجمة:

```bash
cd /home/odoo/PycharmProjects/odoo18/odoo18

# إنشاء ملف .pot جديد
python3 odoo-bin -c odoo.conf -d DATABASE_NAME --i18n-export=custom_frtz/FRTZ/account_invoice_installments/i18n/account_invoice_installments.pot --modules=account_invoice_installments --stop-after-init
```

---

## ⚠️ نصائح مهمة (Important Tips):

1. **استخدم دائماً `_()`** مع النصوص في الكود Python:
   ```python
   string=_("Payment Type")  # ✅ صحيح
   string="Payment Type"      # ❌ خطأ - لن يترجم
   ```

2. **في ملفات XML**، النصوص في `string=""` تترجم تلقائياً:
   ```xml
   <field name="payment_type" string="Payment Type"/>  <!-- يترجم تلقائياً -->
   ```

3. **بعد أي تعديل**:
   - أعد تشغيل Odoo
   - حدّث الموديول
   - استورد الترجمة من جديد
   - امسح الكاش

4. **تأكد من إعداد اللغة**:
   - Settings → Users → اختر المستخدم
   - Language: **Arabic / العربية**

---

## 📧 المساعدة (Support):

إذا واجهت أي مشكلة:
1. تحقق من سجل أخطاء Odoo (Odoo log)
2. تأكد من صحة صيغة ملف `.po`
3. تأكد من تطابق `msgid` مع النص الموجود في الكود
4. جرّب إعادة تثبيت الموديول بالكامل

---

**آخر تحديث**: 2025-11-10
**إصدار Odoo**: 18.0+e

