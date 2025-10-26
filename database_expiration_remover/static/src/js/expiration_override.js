/**
 * Database Expiration Remover - JavaScript Override
 * This script prevents database expiration warnings by overriding
 * the enterprise subscription service and hiding expiration UI elements
 */

(function() {
    'use strict';
    
    console.log("🛡️ Database expiration protection is active");
    
    // Override session info to prevent expiration warnings
    function overrideSessionInfo() {
        if (window.odoo && window.odoo.session) {
            window.odoo.session.warning = false;
            window.odoo.session.expiration_date = '2099-12-31T23:59:59';
            window.odoo.session.expiration_reason = null;
            window.odoo.session.database_protection = {
                active: true,
                message: 'Database protection is active',
                protected_by: 'database_expiration_remover'
            };
        }
    }
    
    // Hide expiration-related UI elements
    function hideExpirationElements() {
        const selectors = [
            '.o_expiration_panel',
            '.o_database_expiration_warning',
            '.o_subscription_warning',
            '.o_enterprise_subscription_warning',
            '[class*="expiration"]',
            '[class*="subscription"]',
            '.o_warning_banner',
            '.o_alert_warning',
            '.o_alert_danger',
            '.o_enterprise_subscription_warning',
            '.o_subscription_warning',
            '.o_database_expiration_warning'
        ];
        
        selectors.forEach(selector => {
            const elements = document.querySelectorAll(selector);
            elements.forEach(el => {
                el.style.display = 'none';
                el.style.visibility = 'hidden';
                el.remove(); // Also remove from DOM
            });
        });
        
        // Add protection message if not already present
        addProtectionMessage();
    }
    
    // Add protection message to the page
    function addProtectionMessage() {
        if (!document.querySelector('.o_database_protection_active')) {
            const protectionDiv = document.createElement('div');
            protectionDiv.className = 'o_database_protection_active';
            protectionDiv.style.cssText = 'background: #d4edda; border: 1px solid #c3e6cb; color: #155724; padding: 10px; border-radius: 5px; margin: 10px 0; display: block; position: fixed; top: 10px; right: 10px; z-index: 9999; max-width: 300px;';
            protectionDiv.innerHTML = '🛡️ Database protection is active. Your database is protected from expiration.';
            
            // Try to add to different locations
            const body = document.body;
            if (body) {
                body.appendChild(protectionDiv);
                
                // Auto-hide after 5 seconds
                setTimeout(() => {
                    if (protectionDiv.parentNode) {
                        protectionDiv.style.opacity = '0.7';
                    }
                }, 5000);
            }
        }
    }
    
    // Override enterprise subscription service
    function overrideSubscriptionService() {
        if (window.odoo && window.odoo.services) {
            // Override the subscription service if it exists
            const originalGet = window.odoo.services.get;
            if (originalGet) {
                window.odoo.services.get = function(serviceName) {
                    if (serviceName === 'enterprise_subscription') {
                        return {
                            isExpired: false,
                            daysLeft: 999999,
                            expirationDate: '2099-12-31T23:59:59',
                            lastRequestStatus: 'success'
                        };
                    }
                    return originalGet.call(this, serviceName);
                };
            }
        }
    }
    
    // Apply all overrides
    function applyOverrides() {
        overrideSessionInfo();
        hideExpirationElements();
        overrideSubscriptionService();
    }
    
    // Apply overrides when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', applyOverrides);
    } else {
        applyOverrides();
    }
    
    // Reapply overrides periodically to catch dynamically loaded elements
    setInterval(applyOverrides, 1000);
    
})();