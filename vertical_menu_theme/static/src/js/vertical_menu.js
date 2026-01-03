/** @odoo-module **/

/**
 * Vertical Menu Theme - Optimized for Fast Loading
 * 
 * WHY IT WAS SLOW:
 * 1. Line 329: setTimeout(1500ms) - waited 1.5 seconds before starting
 * 2. Line 712: setTimeout(2000ms) - waited another 2 seconds (total 3.5s!)
 * 3. Line 648: setInterval(1000ms) - polling every second for URL changes
 * 4. Line 651: setTimeout(300ms) - additional delay inside interval
 * 
 * OPTIMIZATIONS:
 * - Removed all setTimeout delays
 * - Use MutationObserver instead of setInterval (instant detection)
 * - Initialize immediately when DOM ready
 * - Use requestAnimationFrame for smooth updates
 */

let currentModule = '';
let isMenuOpen = true;
const MENU_WIDTH = 200;
let urlObserver = null;
let menuObserver = null;

// Initialize immediately - no delays!
function initialize() {
    // Try immediately if DOM ready
    if (document.readyState !== 'loading') {
        initializeOverlayMenu();
    } else {
        // Wait for DOMContentLoaded only (no extra delay)
        document.addEventListener('DOMContentLoaded', initializeOverlayMenu, { once: true });
    }
}

function initializeOverlayMenu() {
    // Check if menu already exists to avoid duplicates
    if (document.getElementById('overlayOdooMenu')) return;
    
    // Try immediately first
    const odooMenu = document.querySelector('.o_menu_sections, .o_main_navbar');
    if (odooMenu) {
        removeExistingMenu();
        createOverlayMenu();
        addOverlayToggleButton();
        // Wait a bit for menu items to be fully rendered
        requestAnimationFrame(() => {
            requestAnimationFrame(() => {
                updateMenuForCurrentModule();
            });
        });
        setupOverlayListeners();
        observeOdooMenuChanges();
        return;
    }
    
    // Use MutationObserver instead of polling - much faster!
    let retryCount = 0;
    const maxRetries = 50; // ~5 seconds max wait
    
    const initObserver = new MutationObserver(() => {
        const odooMenu = document.querySelector('.o_menu_sections, .o_main_navbar');
        if (odooMenu) {
            initObserver.disconnect();
            removeExistingMenu();
            createOverlayMenu();
            addOverlayToggleButton();
            // Wait for menu items to be fully rendered
            requestAnimationFrame(() => {
                requestAnimationFrame(() => {
                    updateMenuForCurrentModule();
                    // If still no items, retry after a short delay
                    const menu = document.getElementById('overlayOdooMenu');
                    if (menu && menu.querySelectorAll('.menu-overlay-item').length === 0) {
                        setTimeout(() => {
                            updateMenuForCurrentModule();
                        }, 500);
                    }
                });
            });
            setupOverlayListeners();
            observeOdooMenuChanges();
        } else {
            retryCount++;
            if (retryCount >= maxRetries) {
                initObserver.disconnect();
                // Still create menu even if Odoo menu not found
                removeExistingMenu();
                createOverlayMenu();
                addOverlayToggleButton();
                updateMenuForCurrentModule();
            }
        }
    });
    
    // Observe document body for menu appearance
    initObserver.observe(document.body, {
        childList: true,
        subtree: true
    });
    
    // Fallback: stop observing after 5 seconds
    setTimeout(() => {
        initObserver.disconnect();
    }, 5000);
}

function observeOdooMenuChanges() {
    // Watch for changes in Odoo menu structure
    const menuContainer = document.querySelector('.o_menu_sections');
    if (!menuContainer) return;
    
    if (menuObserver) {
        menuObserver.disconnect();
    }
    
    menuObserver = new MutationObserver(() => {
        // Update overlay menu when Odoo menu changes
        requestAnimationFrame(() => {
            updateMenuForCurrentModule();
        });
    });
    
    menuObserver.observe(menuContainer, {
        childList: true,
        subtree: true,
        attributes: true,
        attributeFilter: ['class']
    });
}

function removeExistingMenu() {
    const oldMenu = document.getElementById('overlayOdooMenu');
    const oldToggle = document.querySelector('.overlay-menu-toggle');

    if (oldMenu) oldMenu.remove();
    if (oldToggle) oldToggle.remove();
}

function createOverlayMenu() {
    const menu = document.createElement('div');
    menu.id = 'overlayOdooMenu';
    menu.className = 'overlay-odoo-menu';

    Object.assign(menu.style, {
        position: 'fixed',
        left: '0',
        top: '100px',
        width: MENU_WIDTH + 'px',
        height: 'calc(100vh - 100px)',
        backgroundColor: 'white',
        boxShadow: '2px 0 10px rgba(0,0,0,0.1)',
        zIndex: '999',
        overflowY: 'auto',
        transition: 'transform 0.3s ease',
        transform: 'translateX(0)'
    });

    document.body.appendChild(menu);

    menu.innerHTML = `
        <div style="padding: 15px; background: #f8f9fa; border-bottom: 1px solid #dee2e6;">
            <div style="font-weight: bold; color: #017e84; font-size: 14px;">Menu</div>
        </div>
        <div style="padding: 20px; text-align: center; color: #6c757d;">
            <i class="fa fa-spinner fa-spin"></i>
            <div style="margin-top: 10px;">Loading...</div>
        </div>
    `;
}

function addOverlayToggleButton() {
    const toggleBtn = document.createElement('button');
    toggleBtn.className = 'overlay-menu-toggle';
    toggleBtn.innerHTML = '☰';
    toggleBtn.title = 'Toggle Menu';

    const buttonLeft = isMenuOpen ? (MENU_WIDTH - 30) + 'px' : '10px';

    Object.assign(toggleBtn.style, {
        position: 'fixed',
        top: '50px',
        left: buttonLeft,
        zIndex: '1000',
        backgroundColor: '#017e84',
        color: 'white',
        border: 'none',
        borderRadius: '4px',
        width: '30px',
        height: '30px',
        cursor: 'pointer',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontSize: '14px',
        transition: 'all 0.3s ease'
    });

    document.body.appendChild(toggleBtn);

    toggleBtn.addEventListener('click', function() {
        const menu = document.getElementById('overlayOdooMenu');

        if (isMenuOpen) {
            menu.style.transform = 'translateX(-100%)';
            this.style.left = '10px';
            this.innerHTML = '☰';
            isMenuOpen = false;
        } else {
            menu.style.transform = 'translateX(0)';
            this.style.left = (MENU_WIDTH - 30) + 'px';
            this.innerHTML = '✕';
            isMenuOpen = true;
            updateMenuForCurrentModule();
        }

        adjustContentWithMinimalShift();
    });
}

function detectCurrentModule() {
    // Try to get active menu section header
    const activeSection = document.querySelector('.o_menu_section_header.active, .o_menu_section_header:has(.o_menu_item.active)');
    if (activeSection) {
        return activeSection.textContent.trim();
    }

    // Try breadcrumbs
    const breadcrumbs = document.querySelectorAll('.breadcrumb-item');
    if (breadcrumbs.length >= 2) {
        return breadcrumbs[1].textContent.trim();
    }

    // Try active menu item's parent section
    const activeMenu = document.querySelector('.o_menu_item.active');
    if (activeMenu) {
        const section = activeMenu.closest('.o_menu_section');
        if (section) {
            const header = section.querySelector('.o_menu_section_header');
            if (header) {
                return header.textContent.trim();
            }
        }
    }

    return 'Menu';
}

function getOdooMenuItems() {
    const menuItems = [];
    
    // Strategy 0: Apps on home (grid) - ensure Purchases, Accounting, etc. appear
    const appTiles = document.querySelectorAll('.o_app, .o_app_switcher .o_app, .o_app_grid .o_app');
    if (appTiles.length > 0) {
        appTiles.forEach(app => {
            const name = (app.querySelector('.o_app_name, span') || app).textContent.trim();
            const iconEl = app.querySelector('.o_app_icon, .fa, i[class*="fa-"]');
            let iconClass = 'fa-th-large';
            if (iconEl) {
                const classes = iconEl.className.split(' ');
                const faClass = classes.find(c => c.startsWith('fa-') && c !== 'fa-fw' && c !== 'fa');
                if (faClass) {
                    iconClass = faClass;
                }
            }
            const href = app.getAttribute('href') || app.dataset.menuId ? `/web#menu_id=${app.dataset.menuId}` : '#';
            menuItems.push({
                name,
                icon: iconClass,
                href,
                section: 'Apps',
                isActive: false
            });
        });
    }
    
    // Try multiple selector strategies to find menu items
    // Strategy 1: Menu sections structure
    let menuSections = document.querySelectorAll('.o_menu_section');
    
    // Strategy 2: If no sections, try direct menu items
    if (menuSections.length === 0) {
        const directItems = document.querySelectorAll('.o_menu_item');
        if (directItems.length > 0) {
            directItems.forEach(item => {
                const menuItem = extractMenuItemData(item, '');
                if (menuItem) menuItems.push(menuItem);
            });
            return menuItems;
        }
    }
    
    // Strategy 3: Try list-group items (Bootstrap style)
    if (menuSections.length === 0) {
        const listItems = document.querySelectorAll('.o_menu_section_items .list-group-item, .o_menu_section_items a');
        if (listItems.length > 0) {
            listItems.forEach(item => {
                const menuItem = extractMenuItemData(item, '');
                if (menuItem) menuItems.push(menuItem);
            });
            return menuItems;
        }
    }
    
    // Process sections if found
    menuSections.forEach(section => {
        const sectionHeader = section.querySelector('.o_menu_section_header');
        const sectionName = sectionHeader ? sectionHeader.textContent.trim() : '';
        
        // Get all menu items in this section - try multiple selectors
        const items = section.querySelectorAll('.o_menu_item, .list-group-item, a[data-menu-id], a[href*="#menu_id"]');
        
        items.forEach(item => {
            const menuItem = extractMenuItemData(item, sectionName);
            if (menuItem) menuItems.push(menuItem);
        });
    });
    
    // If still no items, try to find any clickable menu elements
    if (menuItems.length === 0) {
        const allMenuLinks = document.querySelectorAll('.o_main_navbar a, .o_menu_sections a');
        allMenuLinks.forEach(link => {
            const menuItem = extractMenuItemData(link, '');
            if (menuItem && menuItem.name && menuItem.name.trim() !== '') {
                menuItems.push(menuItem);
            }
        });
    }
    
    return menuItems;
}

function extractMenuItemData(item, sectionName) {
    // Skip if it's not a real menu item (check for common non-menu elements)
    if (item.classList.contains('o_menu_toggle') || 
        item.classList.contains('o_navbar_toggle') ||
        item.tagName === 'BUTTON') {
        return null;
    }
    
    // Get menu item text - try multiple strategies
    let name = '';
    const textSelectors = [
        '.o_menu_item_text',
        '.o_dashboard_name',
        'span:not(.fa)',
        '.menu-item-text'
    ];
    
    for (const selector of textSelectors) {
        const textElement = item.querySelector(selector);
        if (textElement && textElement.textContent.trim()) {
            name = textElement.textContent.trim();
            break;
        }
    }
    
    // Fallback: get text directly from item
    if (!name) {
        // Clone to avoid modifying original
        const clone = item.cloneNode(true);
        // Remove icon elements
        clone.querySelectorAll('.fa, i').forEach(el => el.remove());
        name = clone.textContent.trim();
    }
    
    // Skip if no name found
    if (!name || name.length === 0) {
        return null;
    }
    
    // Get menu identifiers
    const menuId = getMenuId(item);
    const parentMenuId = getParentMenuId(item);

    // Get menu item link
    let link = '#';
    if (item.tagName === 'A') {
        link = item.getAttribute('href') || '#';
    } else {
        // Try to find link inside
        const linkElement = item.querySelector('a');
        if (linkElement) {
            link = linkElement.getAttribute('href') || '#';
        } else {
            // Try data attributes
            link = item.getAttribute('data-menu-id') || item.getAttribute('href') || '#';
        }
    }
    
    // Get icon - try multiple strategies
    let iconClass = 'fa-circle';
    const iconSelectors = ['.fa', 'i[class*="fa-"]', '[class*="fa-"]'];
    
    for (const selector of iconSelectors) {
        const iconElement = item.querySelector(selector);
        if (iconElement) {
            const classes = iconElement.className.split(' ');
            const faClass = classes.find(c => c.startsWith('fa-') && c !== 'fa-fw' && c !== 'fa');
            if (faClass) {
                iconClass = faClass;
                break;
            }
        }
    }
    
    // Check if active
    const isActive = item.classList.contains('active') || 
                     item.closest('.active') !== null ||
                     item.querySelector('.active') !== null;
    
    return {
        name: name,
        icon: iconClass,
        href: link,
        section: sectionName,
        isActive: isActive,
        id: menuId || null,
        parentId: parentMenuId || null
    };
}

function getMenuId(el) {
    const attr = el.getAttribute('data-menu-id');
    if (attr) return attr;
    const href = el.getAttribute('href') || '';
    const match = href.match(/[?&#]menu_id=(\d+)/);
    if (match) return match[1];
    return null;
}

function getParentMenuId(el) {
    const attr = el.getAttribute('data-parent-menu-id');
    if (attr) return attr;
    const parentWithId = el.closest('[data-menu-id][data-parent-menu-id]');
    if (parentWithId) return parentWithId.getAttribute('data-parent-menu-id');
    return null;
}

function updateMenuForCurrentModule() {
    const menu = document.getElementById('overlayOdooMenu');
    if (!menu) return;

    const detectedModule = detectCurrentModule();
    const odooMenuItems = getOdooMenuItems();

    // Debug: log if no items found
    if (odooMenuItems.length === 0) {
        console.log('Vertical Menu: No menu items found. Checking Odoo menu structure...');
        console.log('Menu sections:', document.querySelectorAll('.o_menu_section').length);
        console.log('Menu items:', document.querySelectorAll('.o_menu_item').length);
        console.log('Menu navbar:', document.querySelector('.o_main_navbar') ? 'Found' : 'Not found');
    }

    // Always update to show latest menu items from Odoo
    renderMenuContent(menu, detectedModule, odooMenuItems);
    currentModule = detectedModule;
}

function renderMenuContent(menuElement, moduleName, menuItems) {
    const displayName = moduleName.length > 20 ? moduleName.substring(0, 17) + '...' : moduleName;

    const header = `
        <div style="
            padding: 15px;
            background: #017e84;
            color: white;
            border-bottom: 1px solid #016a6f;
        ">
            <div style="display: flex; align-items: center; gap: 10px;">
                <i class="fa fa-fw fa-th-large"></i>
                <div style="flex: 1;">
                    <div style="font-weight: bold; font-size: 14px;">${displayName}</div>
                    <div style="font-size: 11px; opacity: 0.9;">Odoo Menu</div>
                </div>
            </div>
        </div>
    `;

    // Group items by section if they have sections
    const groupedItems = {};
    menuItems.forEach(item => {
        const section = item.section || 'Main';
        if (!groupedItems[section]) {
            groupedItems[section] = [];
        }
        groupedItems[section].push(item);
    });

    let itemsHTML = '';
    
    // Render items grouped by section with collapsible behavior + hierarchical children
    Object.keys(groupedItems).forEach(sectionName => {
        const sectionItems = groupedItems[sectionName];

        const hasMultipleSections = Object.keys(groupedItems).length > 1;
        const headerLabel = hasMultipleSections ? sectionName : 'Menu';

        itemsHTML += `
            <div class="menu-section" data-section="${headerLabel}">
                <div class="menu-section-header" style="
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    padding: 8px 15px;
                    background: #f8f9fa;
                    color: #6c757d;
                    font-size: 11px;
                    font-weight: 600;
                    text-transform: uppercase;
                    border-bottom: 1px solid #e9ecef;
                    cursor: pointer;
                ">
                    <span>${headerLabel}</span>
                    <i class="fa fa-angle-down" style="font-size: 12px;"></i>
                </div>
                <div class="menu-section-items" style="display: block;">
        `;

        // Build tree for this section
        const tree = buildMenuTree(sectionItems);
        itemsHTML += renderMenuTree(tree, 0);

        itemsHTML += `
                </div>
            </div>
        `;
    });

    // If no items found, show message with retry button
    if (menuItems.length === 0) {
        itemsHTML = `
            <div style="padding: 20px; text-align: center; color: #6c757d;">
                <i class="fa fa-info-circle" style="font-size: 24px; margin-bottom: 10px;"></i>
                <div style="margin-top: 10px; margin-bottom: 15px;">No menu items found</div>
                <button onclick="location.reload()" style="
                    padding: 8px 16px;
                    background: #017e84;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 12px;
                ">Refresh Page</button>
                <div style="margin-top: 10px; font-size: 11px; color: #999;">
                    Or check browser console for details
                </div>
            </div>
        `;
    }

    menuElement.innerHTML = header + itemsHTML;

    // Handle clicks - let Odoo handle navigation naturally (leaves only)
    menuElement.querySelectorAll('.menu-overlay-item').forEach(item => {
        const hasChildren = item.dataset.hasChildren === 'true';
        const caret = item.querySelector('.menu-caret');

        if (hasChildren) {
            item.addEventListener('click', function(e) {
                // Toggle children, don't navigate
                e.preventDefault();
                const node = this.closest('.menu-node');
                const children = node ? node.querySelector(':scope > .menu-children') : null;
                const icon = caret;
                const isCollapsed = children && children.style.display === 'none';
                if (children) {
                    children.style.display = isCollapsed ? 'block' : 'none';
                }
                if (icon) {
                    icon.className = isCollapsed ? 'fa fa-angle-down menu-caret' : 'fa fa-angle-right menu-caret';
                }
            });
        } else {
            item.addEventListener('click', function() {
                // Update active state visually for leaves
                menuElement.querySelectorAll('.menu-overlay-item').forEach(i => {
                    if (i !== this) {
                        i.style.background = 'transparent';
                        i.style.color = '#495057';
                    }
                });

                this.style.background = '#e6f2f3';
                this.style.color = '#017e84';
            });
        }
    });

    // Collapsible sections: toggle children visibility
    menuElement.querySelectorAll('.menu-section-header').forEach(header => {
        header.addEventListener('click', () => {
            const section = header.closest('.menu-section');
            const body = section.querySelector('.menu-section-items');
            const icon = header.querySelector('i');
            const isCollapsed = body.style.display === 'none';
            body.style.display = isCollapsed ? 'block' : 'none';
            if (icon) {
                icon.className = isCollapsed ? 'fa fa-angle-down' : 'fa fa-angle-right';
            }
        });
    });
}

function buildMenuTree(items) {
    const byId = {};
    const roots = [];

    // First pass: create stable node ids and store
    items.forEach((it, idx) => {
        const nodeId = it.id || `id-${it.name}-${idx}`;
        const node = Object.assign({}, it, { id: nodeId, children: [] });
        byId[nodeId] = node;
    });

    // Second pass: attach children
    items.forEach((it, idx) => {
        const nodeId = it.id || `id-${it.name}-${idx}`;
        const parentId = it.parentId;
        const node = byId[nodeId];
        if (!node) return; // safety guard

        if (parentId && byId[parentId]) {
            byId[parentId].children.push(node);
        } else {
            roots.push(node);
        }
    });
    return roots;
}

function renderMenuTree(nodes, level) {
    let html = '';
    nodes.forEach(node => {
        if (!node) return; // guard against undefined
        const hasChildren = node.children && node.children.length > 0;
        const activeStyle = node.isActive ? '#017e84' : '#495057';
        const activeBg = node.isActive ? '#e6f2f3' : 'transparent';
        const indent = level * 12;
        const caretIcon = hasChildren ? 'fa-angle-down' : 'fa-circle';

        html += `
            <div class="menu-node" style="margin-left: ${indent}px;">
                <a href="${hasChildren ? '#' : node.href}" class="menu-overlay-item" data-item="${node.name}" data-has-children="${hasChildren}"
                   style="
                        display: block;
                        padding: 10px 15px;
                        color: ${activeStyle};
                        text-decoration: none;
                        border-bottom: 1px solid #f1f1f1;
                        background: ${activeBg};
                        transition: all 0.2s;
                        cursor: pointer;
                   "
                   onmouseover="this.style.background='#f8f9fa'; this.style.color='#017e84'"
                   onmouseout="this.style.background='${activeBg}'; this.style.color='${activeStyle}'">
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <i class="fa fa-fw ${caretIcon} menu-caret" style="width: 16px;"></i>
                        <i class="fa fa-fw ${node.icon}" style="width: 16px;"></i>
                        <span>${node.name}</span>
                    </div>
                </a>
                ${hasChildren ? `<div class="menu-children" style="display: none;">${renderMenuTree(node.children, level + 1)}</div>` : ''}
            </div>
        `;
    });
    return html;
}

function adjustContentWithMinimalShift() {
    const contentShift = isMenuOpen ? '65px' : '0';

    const contentSelectors = [
        '.o_action_manager',
        '.o_content',
        '.o_view_controller',
        '.o_form_view',
        '.o_list_view',
        '.o_kanban_view',
        '.o_control_panel',
        '.breadcrumb'
    ];

    // Use requestAnimationFrame for smooth updates
    requestAnimationFrame(() => {
        contentSelectors.forEach(selector => {
            const elements = document.querySelectorAll(selector);
            elements.forEach(element => {
                if (element) {
                    if (isMenuOpen) {
                        element.style.marginLeft = contentShift;
                        element.style.transition = 'margin-left 0.3s ease';
                        element.style.boxShadow = '-2px 0 10px rgba(0,0,0,0.05)';
                    } else {
                        element.style.marginLeft = '0';
                        element.style.boxShadow = 'none';
                    }
                    element.style.visibility = 'visible';
                    element.style.opacity = '1';
                    element.style.position = 'relative';
                    element.style.zIndex = '1';
                }
            });
        });
        const buttons = document.querySelectorAll('button');
        buttons.forEach(button => {
            button.style.visibility = 'visible';
            button.style.opacity = '1';
        });
    });
}

function showNavigationNotification(itemName) {
    const notification = document.createElement('div');
    notification.innerHTML = `
        <div style="
            position: fixed;
            top: 70px;
            right: 20px;
            background: #017e84;
            color: white;
            padding: 10px 15px;
            border-radius: 4px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            z-index: 9999;
            animation: slideIn 0.3s ease;
            max-width: 200px;
        ">
            <i class="fa fa-check-circle"></i>
            ${itemName}
        </div>
    `;

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 2000);
}

function setupOverlayListeners() {
    // OPTIMIZED: Use MutationObserver instead of setInterval for URL changes
    let lastUrl = window.location.href;
    
    // Monitor URL changes via history API (Odoo uses pushState/replaceState)
    const originalPushState = history.pushState;
    const originalReplaceState = history.replaceState;
    
    history.pushState = function(...args) {
        originalPushState.apply(history, args);
        requestAnimationFrame(() => {
            if (window.location.href !== lastUrl) {
                lastUrl = window.location.href;
                // Update immediately - use double RAF to ensure Odoo has updated
                requestAnimationFrame(() => {
                    requestAnimationFrame(() => {
                        if (isMenuOpen) {
                            updateMenuForCurrentModule();
                        }
                    });
                });
                adjustContentWithMinimalShift();
            }
        });
    };
    
    history.replaceState = function(...args) {
        originalReplaceState.apply(history, args);
        requestAnimationFrame(() => {
            if (window.location.href !== lastUrl) {
                lastUrl = window.location.href;
                requestAnimationFrame(() => {
                    requestAnimationFrame(() => {
                        if (isMenuOpen) {
                            updateMenuForCurrentModule();
                        }
                    });
                });
                adjustContentWithMinimalShift();
            }
        });
    };
    
    // Also listen for popstate (browser back/forward)
    window.addEventListener('popstate', () => {
        requestAnimationFrame(() => {
            if (window.location.href !== lastUrl) {
                lastUrl = window.location.href;
                requestAnimationFrame(() => {
                    requestAnimationFrame(() => {
                        if (isMenuOpen) {
                            updateMenuForCurrentModule();
                        }
                    });
                });
                adjustContentWithMinimalShift();
            }
        });
    });
    
    // Watch for active class changes on menu items
    const activeObserver = new MutationObserver(() => {
        if (isMenuOpen) {
            requestAnimationFrame(() => {
                updateMenuForCurrentModule();
            });
        }
    });
    
    const menuContainer = document.querySelector('.o_menu_sections');
    if (menuContainer) {
        activeObserver.observe(menuContainer, {
            attributes: true,
            attributeFilter: ['class'],
            subtree: true
        });
    }
    
    // Throttled resize handler
    let resizeTimeout;
    window.addEventListener('resize', () => {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(adjustContentWithMinimalShift, 100);
    }, { passive: true });
}

// Add styles (only once)
if (!document.getElementById('vertical-menu-styles')) {
    const style = document.createElement('style');
    style.id = 'vertical-menu-styles';
    style.textContent = `
        @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }

        @keyframes slideOut {
            from { transform: translateX(0); opacity: 1; }
            to { transform: translateX(100%); opacity: 0; }
        }

        .overlay-odoo-menu {
            box-shadow: 2px 0 15px rgba(0,0,0,0.1) !important;
        }

        .overlay-odoo-menu::-webkit-scrollbar {
            width: 4px;
        }

        .overlay-odoo-menu::-webkit-scrollbar-track {
            background: #f1f1f1;
        }

        .overlay-odoo-menu::-webkit-scrollbar-thumb {
            background: #017e84;
            border-radius: 2px;
        }

        .overlay-menu-toggle:hover {
            background: #016a6f !important;
            transform: scale(1.1);
        }

        .o_main_navbar {
            z-index: 1001 !important;
        }

        @media (max-width: 768px) {
            #overlayOdooMenu {
                width: 180px !important;
            }

            .overlay-menu-toggle {
                left: 150px !important;
                top: 45px !important;
            }
        }
    `;
    document.head.appendChild(style);
}

// Start immediately - no delays!
initialize();
