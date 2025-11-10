#!/usr/bin/env python3
"""
Diagnostic script to check if required database columns exist for res.partner fields
Run this script in Odoo shell or as a standalone script
"""

def check_res_partner_fields(env):
    """
    Check if all required fields exist in res_partner table
    Returns a dictionary with field status
    """
    cr = env.cr
    fields_to_check = [
        'has_installments',
        'installment_count',
        'paid_installment_count',
        'partial_paid_installment_count',
        'pending_installment_count',
        'overdue_installment_count',
        'total_installment_amount',
        'total_paid_amount',
        'total_remaining_amount',
        'view_installments',
    ]
    
    results = {}
    
    # Check each field
    for field_name in fields_to_check:
        cr.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'res_partner' 
            AND column_name = %s
        """, (field_name,))
        
        exists = cr.fetchone() is not None
        results[field_name] = {
            'exists': exists,
            'status': 'OK' if exists else 'MISSING'
        }
    
    return results

def print_report(results):
    """Print a formatted report of field status"""
    print("\n" + "="*60)
    print("RES.PARTNER FIELD COLUMN STATUS REPORT")
    print("="*60 + "\n")
    
    missing_fields = []
    for field_name, status in results.items():
        marker = "✓" if status['exists'] else "✗"
        print(f"{marker} {field_name:35s} - {status['status']}")
        if not status['exists']:
            missing_fields.append(field_name)
    
    print("\n" + "="*60)
    if missing_fields:
        print(f"WARNING: {len(missing_fields)} field(s) are missing:")
        for field in missing_fields:
            print(f"  - {field}")
        print("\nSOLUTION: Upgrade the 'invoice_installment_extension' module:")
        print("  odoo-bin -u invoice_installment_extension -d your_database")
    else:
        print("SUCCESS: All fields exist in the database!")
    print("="*60 + "\n")

if __name__ == '__main__':
    # Usage in Odoo shell:
    # >>> from invoice_installment_extension.check_field_columns import check_res_partner_fields, print_report
    # >>> results = check_res_partner_fields(env)
    # >>> print_report(results)
    print("This script should be run in Odoo shell:")
    print(">>> from invoice_installment_extension.check_field_columns import *")
    print(">>> results = check_res_partner_fields(env)")
    print(">>> print_report(results)")


