/** @odoo-module **/

// Vertical Menu Theme JavaScript - Odoo Enterprise 18 Style
document.addEventListener('DOMContentLoaded', function() {
    // Wait for Odoo to load
    setTimeout(function() {
        initializeVerticalMenu();
    }, 1000);
});

function initializeVerticalMenu() {
    // Apply vertical menu styles
    applyVerticalMenuStyles();
    
    // Add main navbar toggle button
    addNavbarToggleButton();
    
    // Add menu interactions
    addMenuInteractions();
    
    // Handle responsive menu
    handleResponsiveMenu();
    
    // Hide menu on home page
    hideMenuOnHomePage();
}

function applyVerticalMenuStyles() {
    // Find menu sections
    const menuSections = document.querySelector('.o_menu_sections');
    if (menuSections) {
        // Add custom class for styling
        menuSections.classList.add('vertical-menu-theme');
        
        // Apply vertical layout with Odoo Enterprise style
        menuSections.style.display = 'flex';
        menuSections.style.flexDirection = 'column';
        menuSections.style.width = '100%';
        menuSections.style.height = '100%';
        menuSections.style.overflowY = 'auto';
        menuSections.style.padding = '0';
        menuSections.style.background = 'white';
        menuSections.style.borderRight = '1px solid #dee2e6';
        menuSections.style.flexGrow = '0';
        menuSections.style.flexShrink = '0';
        menuSections.style.position = 'relative';
        menuSections.style.marginTop = '50px';
    }

    // Style individual menu sections with Odoo Enterprise style
    const sections = document.querySelectorAll('.o_menu_section');
    sections.forEach(section => {
        section.style.display = 'flex';
        section.style.flexDirection = 'column';
        section.style.width = '100%';
        section.style.marginBottom = '0';
        section.style.borderBottom = 'none';
        section.style.paddingBottom = '0';
        section.style.background = 'transparent';
    });

    // Style menu items with Odoo Enterprise dashboard style
    const menuItems = document.querySelectorAll('.o_menu_item');
    menuItems.forEach(item => {
        // Add list-group-item classes
        item.classList.add('list-group-item', 'cursor-pointer', 'border-0', 'd-flex', 'justify-content-between', 'align-items-center');
        
        item.style.display = 'flex';
        item.style.alignItems = 'center';
        item.style.justifyContent = 'space-between';
        item.style.padding = '8px 16px';
        item.style.margin = '0';
        item.style.color = '#495057';
        item.style.textDecoration = 'none';
        item.style.borderRadius = '0';
        item.style.transition = 'all 0.2s ease';
        item.style.fontSize = '14px';
        item.style.background = 'transparent';
        item.style.border = 'none';
        item.style.width = '100%';
        item.style.textAlign = 'left';
        item.style.cursor = 'pointer';
        item.style.borderBottom = '1px solid #f8f9fa';
        
        // Wrap text in o_dashboard_name div exactly like dashboard
        const text = item.textContent.trim();
        item.innerHTML = `<div class="o_dashboard_name">${text}</div><div xml:space="preserve"></div>`;
    });
}

// Removed addToggleButton function - no longer needed

function addNavbarToggleButton() {
    // Create main navbar toggle button
    if (!document.querySelector('.o_navbar_toggle')) {
        const navbarToggleButton = document.createElement('button');
        navbarToggleButton.className = 'o_navbar_toggle';
        navbarToggleButton.innerHTML = '<i class="fa fa-fw fa-bars"></i>';
        navbarToggleButton.title = 'Toggle Top Navigation';
        
        // Ensure button doesn't interfere with content
        navbarToggleButton.style.position = 'fixed';
        navbarToggleButton.style.top = '10px';
        navbarToggleButton.style.right = '10px';
        navbarToggleButton.style.zIndex = '1002';
        navbarToggleButton.style.pointerEvents = 'auto';
        
        document.body.appendChild(navbarToggleButton);
        
        // Add click event with dynamic page sizing
        navbarToggleButton.addEventListener('click', function() {
            const navbar = document.querySelector('.o_navbar');
            const body = document.body;
            
            if (navbar) {
                navbar.classList.toggle('hidden');
                
                // Add body classes for dynamic sizing
                if (navbar.classList.contains('hidden')) {
                    body.classList.add('navbar-hidden');
                    body.classList.remove('navbar-visible');
                } else {
                    body.classList.add('navbar-visible');
                    body.classList.remove('navbar-hidden');
                }
                
                // Update icon
                const icon = navbarToggleButton.querySelector('i');
                if (navbar.classList.contains('hidden')) {
                    icon.className = 'fa fa-fw fa-eye-slash';
                    navbarToggleButton.title = 'Show Top Navigation';
                } else {
                    icon.className = 'fa fa-fw fa-bars';
                    navbarToggleButton.title = 'Hide Top Navigation';
                }
                
                // Trigger responsive adjustment
                setTimeout(() => {
                    handleResponsiveMenu();
                }, 100);
            }
        });
        
        // Ensure toggle button positioning on view changes
        ensureToggleButtonPositioning();
    }
}

function ensureToggleButtonPositioning() {
    // Monitor for view changes and ensure toggle button is positioned correctly
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.type === 'childList') {
                const toggleButton = document.querySelector('.o_navbar_toggle');
                if (toggleButton) {
                    // Ensure button is always positioned correctly
                    toggleButton.style.position = 'fixed';
                    toggleButton.style.top = '10px';
                    toggleButton.style.right = '10px';
                    toggleButton.style.zIndex = '1002';
                    toggleButton.style.pointerEvents = 'auto';
                }
            }
        });
    });
    
    // Observe changes to the document body
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
}

function addMenuInteractions() {
    // Add hover effects with Odoo Enterprise style
    const menuItems = document.querySelectorAll('.o_menu_item');
    menuItems.forEach(item => {
        item.addEventListener('mouseenter', function(e) {
            if (!e.target.classList.contains('active')) {
                e.target.style.background = 'rgba(0, 0, 0, 0.08)';
                e.target.style.color = '#111827';
                e.target.style.transform = 'none';
                e.target.style.boxShadow = 'none';
            }
        });

        item.addEventListener('mouseleave', function(e) {
            if (!e.target.classList.contains('active')) {
                e.target.style.background = 'transparent';
                e.target.style.color = '#495057';
                e.target.style.transform = 'none';
                e.target.style.boxShadow = 'none';
            }
        });
    });

    // Add click effects with Odoo Enterprise style
    menuItems.forEach(item => {
        item.addEventListener('click', function(e) {
            // Remove active class from all items
            menuItems.forEach(i => {
                i.classList.remove('active');
                i.style.background = 'transparent';
                i.style.color = '#495057';
                i.style.fontWeight = 'normal';
                i.style.boxShadow = 'none';
                i.style.borderLeft = 'none';
            });
            // Add active class to clicked item
            e.target.classList.add('active');
            e.target.style.background = '#e6f2f3';
            e.target.style.color = '#017e84';
            e.target.style.fontWeight = '500';
            e.target.style.borderLeft = '3px solid #017e84';
            e.target.style.boxShadow = 'none';
        });
    });
}

function handleResponsiveMenu() {
    // Handle window resize with dynamic page sizing
    function handleResize() {
        const navbar = document.querySelector('.o_main_navbar');
        const content = document.querySelector('.o_main_content');
        const topNavbar = document.querySelector('.o_navbar');
        const body = document.body;
        
        // Check if top navbar is hidden
        const isTopNavbarHidden = topNavbar && topNavbar.classList.contains('hidden');
        
        // Set body classes for dynamic sizing
        if (isTopNavbarHidden) {
            body.classList.add('navbar-hidden');
            body.classList.remove('navbar-visible');
        } else {
            body.classList.add('navbar-visible');
            body.classList.remove('navbar-hidden');
        }
        
        if (window.innerWidth <= 768) {
            if (navbar) {
                navbar.style.width = '240px';
            }
            if (content) {
                content.style.marginLeft = '240px';
                content.style.width = 'calc(100% - 240px)';
                content.style.marginTop = isTopNavbarHidden ? '0' : '';
                content.style.paddingTop = isTopNavbarHidden ? '0' : '';
            }
        } else if (window.innerWidth <= 480) {
            if (navbar) {
                navbar.style.width = '200px';
            }
            if (content) {
                content.style.marginLeft = '200px';
                content.style.width = 'calc(100% - 200px)';
                content.style.marginTop = isTopNavbarHidden ? '0' : '';
                content.style.paddingTop = isTopNavbarHidden ? '0' : '';
            }
        } else {
            if (navbar) {
                navbar.style.width = '280px';
            }
            if (content) {
                content.style.marginLeft = '280px';
                content.style.width = 'calc(100% - 280px)';
                content.style.marginTop = isTopNavbarHidden ? '0' : '';
                content.style.paddingTop = isTopNavbarHidden ? '0' : '';
            }
        }
    }

    window.addEventListener('resize', handleResize);
    handleResize(); // Initial call
}

function hideMenuOnHomePage() {
    // Check if we're on the home page
    function checkHomePage() {
        const body = document.body;
        const navbar = document.querySelector('.o_main_navbar');
        
        if (body.classList.contains('o_home') || window.location.pathname === '/web' || window.location.pathname === '/') {
            if (navbar) {
                navbar.style.display = 'none';
            }
        } else {
            if (navbar) {
                navbar.style.display = 'flex';
            }
        }
    }
    
    // Check on page load
    checkHomePage();
    
    // Check on navigation
    window.addEventListener('popstate', checkHomePage);
    
    // Check on URL changes (for SPA navigation)
    let currentUrl = window.location.href;
    setInterval(() => {
        if (window.location.href !== currentUrl) {
            currentUrl = window.location.href;
            checkHomePage();
        }
    }, 100);
}
