#!/usr/bin/env python3
"""
Verification script for frtz_customer module
Run this script to verify the module is properly configured
"""

import sys
import os

def verify_module():
    """Verify the frtz_customer module configuration"""
    print("🔍 Verifying frtz_customer module...")
    
    # Check if res_partner.py exists and has correct class name
    res_partner_file = "models/res_partner.py"
    if os.path.exists(res_partner_file):
        with open(res_partner_file, 'r') as f:
            content = f.read()
            if "class ResPartner(models.Model):" in content:
                print("✅ res_partner.py: Correct class name (ResPartner)")
            elif "class FrtzCustomer(models.Model):" in content:
                print("❌ res_partner.py: Incorrect class name (FrtzCustomer) - NEEDS FIX")
                return False
            else:
                print("❌ res_partner.py: Class name not found")
                return False
            
            if "status = fields.Selection" in content:
                print("✅ res_partner.py: status field defined")
            else:
                print("❌ res_partner.py: status field not found")
                return False
    else:
        print("❌ res_partner.py: File not found")
        return False
    
    # Check if customer_view.xml exists and references status field
    customer_view_file = "views/customer_view.xml"
    if os.path.exists(customer_view_file):
        with open(customer_view_file, 'r') as f:
            content = f.read()
            if '<field name="status"/>' in content:
                print("✅ customer_view.xml: status field referenced")
            else:
                print("❌ customer_view.xml: status field not referenced")
                return False
    else:
        print("❌ customer_view.xml: File not found")
        return False
    
    # Check __init__.py files
    if os.path.exists("__init__.py"):
        print("✅ __init__.py: Found")
    else:
        print("❌ __init__.py: Not found")
        return False
    
    if os.path.exists("models/__init__.py"):
        with open("models/__init__.py", 'r') as f:
            content = f.read()
            if "from . import res_partner" in content:
                print("✅ models/__init__.py: res_partner imported")
            else:
                print("❌ models/__init__.py: res_partner not imported")
                return False
    else:
        print("❌ models/__init__.py: Not found")
        return False
    
    print("\n🎉 Module verification completed successfully!")
    print("📋 Next steps:")
    print("1. Upload the corrected files to your server")
    print("2. Restart Odoo service")
    print("3. Update the module in Odoo interface")
    return True

if __name__ == "__main__":
    success = verify_module()
    sys.exit(0 if success else 1)
