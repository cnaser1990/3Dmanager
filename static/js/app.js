// static/js/app.js

// Time Summary Elements
const timeSummary = document.getElementById('timeSummary');
const timeSummaryText = document.getElementById('timeSummaryText');
const printHoursInput = document.getElementById('id_print_hours');
const printMinutesInput = document.getElementById('id_print_minutes');


document.addEventListener('DOMContentLoaded', function () {
    
    // ========== INITIALIZATION ==========
    initAnimations();
    initNavbar();
    initAlerts();
    initForms();
    initTelegram();
    initTooltips();
    initTimeSummary(); 
    // Page-specific init
    const page = document.body.dataset.page || '';
    const pageInitializers = {
        'index': initDashboardPage,
        'filaments': initFilamentsPage,
        'add_project': initProjectFormPage,
        'edit_project': initProjectFormPage,
        'add_filament': initFilamentFormPage,
        'edit_filament': initFilamentFormPage,
        'sales': initSalesPage,
        'sales_history': initSalesHistoryPage,
        'reports': initReportsPage,
        'pricing_settings': initSettingsPage,
        'view_filament': initViewFilamentPage,
        'view_project': initViewProjectPage,
        'assign_project_to_filament': initAssignProjectPage,
    };
    
    if (pageInitializers[page]) {
        pageInitializers[page]();
    }
});

// ========== UTILITIES ==========

function formatNumber(n) {
    return new Intl.NumberFormat('fa-IR').format(Math.round(n || 0));
}

function formatNumberEn(n) {
    return new Intl.NumberFormat('en-US').format(Math.round(n || 0));
}

function toEnDigits(s) {
    return (s || '').toString()
        .replace(/[۰-۹]/g, d => '۰۱۲۳۴۵۶۷۸۹'.indexOf(d))
        .replace(/[٠-٩]/g, d => '٠١٢٣٤٥٦٧٨٩'.indexOf(d));
}

function toFaDigits(s) {
    return (s || '').toString().replace(/\d/g, d => '۰۱۲۳۴۵۶۷۸۹'[d]);
}

function debounce(fn, wait) {
    let timeout;
    return function (...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => fn.apply(this, args), wait);
    };
}

function throttle(fn, limit) {
    let inThrottle;
    return function (...args) {
        if (!inThrottle) {
            fn.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function showToast(message, type = 'info') {
    const container = document.querySelector('.toast-container') || createToastContainer();
    const toast = document.createElement('div');
    toast.className = `toast-item toast-${type} fade-in-up`;
    
    const icons = {
        success: 'fa-check-circle',
        error: 'fa-exclamation-circle',
        warning: 'fa-exclamation-triangle',
        info: 'fa-info-circle'
    };
    
    toast.innerHTML = `
        <i class="fas ${icons[type] || icons.info}"></i>
        <span>${message}</span>
        <button class="toast-close" onclick="this.parentElement.remove()">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.classList.add('fade-out');
        setTimeout(() => toast.remove(), 300);
    }, 5000);
}

function createToastContainer() {
    const container = document.createElement('div');
    container.className = 'toast-container';
    container.style.cssText = `
        position: fixed;
        top: 100px;
        left: 20px;
        z-index: 9999;
        display: flex;
        flex-direction: column;
        gap: 10px;
    `;
    document.body.appendChild(container);
    return container;
}

// ========== ANIMATIONS ==========

function initAnimations() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry, index) => {
            if (entry.isIntersecting) {
                const delay = Math.min(index * 50, 500);
                setTimeout(() => {
                    entry.target.classList.add('visible');
                }, delay);
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);
    
    const animatedElements = document.querySelectorAll(
        '.animate-in, .animate-scale, .stat-card, .card-modern, .filament-card, ' +
        '.project-card, .product-item, .table-row, .sale-row, .usage-card'
    );
    
    animatedElements.forEach(el => {
        observer.observe(el);
    });
    
    // Stagger animations for grid items
    document.querySelectorAll('.stats-grid .stat-card').forEach((card, index) => {
        card.style.transitionDelay = `${index * 100}ms`;
    });
}

// ========== NAVBAR ==========

function initNavbar() {
    const navbar = document.querySelector('.app-navbar');
    if (!navbar) return;
    
    const currentPath = window.location.pathname.replace(/\/$/, '');
    let lastScroll = 0;
    
    // Scroll effect
    window.addEventListener('scroll', throttle(() => {
        const currentScroll = window.pageYOffset;
        if (currentScroll > 50) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
        lastScroll = currentScroll;
    }, 100));
    
    // Active link highlighting
    document.querySelectorAll('.app-nav-links .nav-link').forEach(link => {
        const href = link.getAttribute('href');
        
        // === FIX START: STRICTLY IGNORE HASH LINKS ===
        if (!href || href.trim() === '#' || href.indexOf('javascript') !== -1) {
            return; 
        }
        // === FIX END ===

        try {
            const linkPath = new URL(href, window.location.origin).pathname.replace(/\/$/, '');
            
            if (linkPath === currentPath) {
                link.classList.add('active');
            } else if (currentPath.startsWith(linkPath) && linkPath !== '' && linkPath !== '/') {
                link.classList.add('active');
            }
        } catch (e) {
            // Ignore errors
        }
    });
    
    // Mobile menu logic
    document.querySelectorAll('.navbar-nav .nav-link').forEach(link => {
        link.addEventListener('click', () => {
            const navbarCollapse = document.querySelector('.navbar-collapse');
            if (navbarCollapse && navbarCollapse.classList.contains('show')) {
                // Only close if it's NOT a dropdown toggle
                if (!link.classList.contains('dropdown-toggle')) {
                    const bsCollapse = bootstrap.Collapse.getInstance(navbarCollapse);
                    if (bsCollapse) bsCollapse.hide();
                }
            }
        });
    });
}

// ========== ALERTS ==========

function initAlerts() {
    // Auto-dismiss success/info alerts after 5 seconds
    setTimeout(() => {
        document.querySelectorAll('.alert-success, .alert-info').forEach(alert => {
            if (!alert.classList.contains('alert-permanent')) {
                fadeOutAndRemove(alert);
            }
        });
    }, 5000);
}

function fadeOutAndRemove(element) {
    element.style.transition = 'all 0.4s ease';
    element.style.opacity = '0';
    element.style.transform = 'translateY(-20px)';
    setTimeout(() => {
        if (element.parentNode) {
            element.parentNode.removeChild(element);
        }
    }, 400);
}

// ========== FORMS ==========

function initForms() {
    // Prevent double submit
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function (e) {
            const submitBtn = form.querySelector('button[type="submit"], input[type="submit"]');
            if (!submitBtn) return;
            
            if (submitBtn.dataset.submitting === '1') {
                e.preventDefault();
                return;
            }
            
            submitBtn.dataset.submitting = '1';
            submitBtn.classList.add('btn-loading');
            
            const originalContent = submitBtn.innerHTML;
            const btnText = submitBtn.querySelector('.btn-text') || submitBtn;
            
            if (!submitBtn.querySelector('.btn-text')) {
                submitBtn.innerHTML = `<span class="btn-text">${originalContent}</span>`;
            }
            
            // Reset after timeout (fallback)
            setTimeout(() => {
                submitBtn.dataset.submitting = '0';
                submitBtn.classList.remove('btn-loading');
                submitBtn.innerHTML = originalContent;
            }, 15000);
        });
    });
    
    // Input focus animations
    document.querySelectorAll('.form-control, .form-select').forEach(input => {
        const wrapper = input.closest('.form-group') || input.parentElement;
        
        input.addEventListener('focus', function() {
            wrapper.classList.add('focused');
        });
        
        input.addEventListener('blur', function() {
            wrapper.classList.remove('focused');
            
            // Add 'has-value' class for floating labels
            if (this.value) {
                wrapper.classList.add('has-value');
            } else {
                wrapper.classList.remove('has-value');
            }
        });
        
        // Initial check for pre-filled inputs
        if (input.value) {
            wrapper.classList.add('has-value');
        }
    });
    
    // Number input formatting
    document.querySelectorAll('input[type="number"]').forEach(input => {
        input.addEventListener('wheel', function(e) {
            if (document.activeElement === this) {
                e.preventDefault();
            }
        });
    });
}

// ========== TOOLTIPS ==========

function initTooltips() {
    // Initialize Bootstrap tooltips if available
    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
        const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
        tooltipTriggerList.forEach(el => new bootstrap.Tooltip(el));
    }
    
    // Custom tooltip support
    document.querySelectorAll('[data-tooltip]').forEach(el => {
        el.addEventListener('mouseenter', showCustomTooltip);
        el.addEventListener('mouseleave', hideCustomTooltip);
    });
}

function showCustomTooltip(e) {
    const text = e.target.dataset.tooltip;
    if (!text) return;
    
    const tooltip = document.createElement('div');
    tooltip.className = 'custom-tooltip fade-in';
    tooltip.textContent = text;
    tooltip.style.cssText = `
        position: fixed;
        background: var(--gray-800, #1f2937);
        color: white;
        padding: 6px 12px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: 600;
        z-index: 10000;
        pointer-events: none;
        white-space: nowrap;
    `;
    
    document.body.appendChild(tooltip);
    
    const rect = e.target.getBoundingClientRect();
    tooltip.style.top = `${rect.top - tooltip.offsetHeight - 8}px`;
    tooltip.style.left = `${rect.left + (rect.width - tooltip.offsetWidth) / 2}px`;
    
    e.target._tooltip = tooltip;
}

function hideCustomTooltip(e) {
    if (e.target._tooltip) {
        e.target._tooltip.remove();
        e.target._tooltip = null;
    }
}

// ========== TELEGRAM BUTTON ==========

function initTelegram() {
    const btn = document.querySelector('.telegram-btn');
    if (!btn) return;
    
    btn.addEventListener('click', function(e) {
        this.style.transform = 'scale(0.9)';
        setTimeout(() => {
            this.style.transform = '';
        }, 150);
    });
    
    // Animate on scroll into view
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
            }
        });
    });
    
    observer.observe(btn.parentElement);
}

// ========== IMAGE PREVIEW ==========

function setupImagePreview() {
    document.querySelectorAll('input[type="file"][data-preview-target]').forEach(input => {
        const targetId = input.dataset.previewTarget;
        const preview = document.getElementById(targetId);
        if (!preview) return;
        
        input.addEventListener('change', function(e) {
            const file = e.target.files?.[0];
            
            if (!file) {
                preview.src = '';
                preview.classList.add('d-none');
                return;
            }
            
            // Validate file type
            if (!file.type.startsWith('image/')) {
                showToast('لطفاً یک فایل تصویری انتخاب کنید', 'error');
                input.value = '';
                return;
            }
            
            // Validate file size (5MB max)
            if (file.size > 5 * 1024 * 1024) {
                showToast('حجم فایل نباید بیشتر از 5 مگابایت باشد', 'error');
                input.value = '';
                return;
            }
            
            const reader = new FileReader();
            reader.onload = function(ev) {
                preview.src = ev.target.result;
                preview.classList.remove('d-none');
                preview.classList.add('fade-in');
            };
            reader.onerror = function() {
                showToast('خطا در خواندن فایل', 'error');
            };
            reader.readAsDataURL(file);
        });
        
        // Drag and drop support
        const dropZone = input.closest('.form-group') || input.parentElement;
        
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, preventDefaults, false);
        });
        
        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }
        
        ['dragenter', 'dragover'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => dropZone.classList.add('dragover'), false);
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => dropZone.classList.remove('dragover'), false);
        });
        
        dropZone.addEventListener('drop', function(e) {
            const dt = e.dataTransfer;
            const files = dt.files;
            if (files.length) {
                input.files = files;
                input.dispatchEvent(new Event('change'));
            }
        });
    });
}

// ========== COLOR PREVIEW ==========

function setupColorPreview() {
    const colorInput = document.getElementById('id_color');
    const colorPreview = document.querySelector('.color-preview');
    
    if (!colorInput || !colorPreview) return;
    
    function updateColor() {
        let color = colorInput.value.trim();
        
        if (!color) {
            colorPreview.style.backgroundColor = '#6b7280';
            return;
        }
        
        // Add # if it's a hex code without it
        if (/^[0-9A-Fa-f]{6}$/.test(color)) {
            color = '#' + color;
        } else if (/^[0-9A-Fa-f]{3}$/.test(color)) {
            color = '#' + color;
        }
        
        colorPreview.style.backgroundColor = color;
    }
    
    colorInput.addEventListener('input', updateColor);
    colorInput.addEventListener('change', updateColor);
    
    // Initial update
    updateColor();
}

// ========== COST PREVIEW CALCULATION ==========

function setupCostPreview() {
    const container = document.querySelector('[data-cost-preview]');
    if (!container) return;
    
    const calcUrl = container.dataset.calcUrl;
    if (!calcUrl) return;
    
    const elements = {
        filamentUsed: document.getElementById('id_filament_used_mm'),
        printHours: document.getElementById('id_print_hours'),
        printMinutes: document.getElementById('id_print_minutes'),
        sizeX: document.getElementById('id_size_x'),
        sizeY: document.getElementById('id_size_y'),
        sizeZ: document.getElementById('id_size_z'),
        postProcessing: document.getElementById('id_post_processing_enabled'),
        painting: document.getElementById('id_painting_enabled'),
        filamentCost: document.getElementById('preview-filament-cost'),
    };
    
    const outputs = {
        weight: document.getElementById('filament-weight'),
        material: document.getElementById('material-cost'),
        electricity: document.getElementById('electricity-cost'),
        depreciation: document.getElementById('depreciation-cost'),
        postProcessing: document.getElementById('post-processing-cost'),
        painting: document.getElementById('painting-cost'),
        total: document.getElementById('total-cost'),
        selling: document.getElementById('selling-price'),
        profit: document.getElementById('profit-margin'),
    };
    
    const csrfToken = getCookie('csrftoken') || 
                      document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
    
    let isCalculating = false;
    let calculationTimeout = null;
    
    function getPrintTimeHours() {
        const h = parseFloat(toEnDigits(elements.printHours?.value || 0)) || 0;
        const m = parseFloat(toEnDigits(elements.printMinutes?.value || 0)) || 0;
        return h + m / 60;
    }
    
    function hasValidInputs() {
        const filament = parseFloat(toEnDigits(elements.filamentUsed?.value || 0)) || 0;
        const time = getPrintTimeHours();
        const x = parseFloat(toEnDigits(elements.sizeX?.value || 0)) || 0;
        const y = parseFloat(toEnDigits(elements.sizeY?.value || 0)) || 0;
        const z = parseFloat(toEnDigits(elements.sizeZ?.value || 0)) || 0;
        return filament > 0 && time > 0 && x > 0 && y > 0 && z > 0;
    }
    
    function clearOutputs() {
        Object.values(outputs).forEach(el => {
            if (el) el.textContent = '—';
        });
    }
    
    function setLoading(loading) {
        Object.values(outputs).forEach(el => {
            if (el) {
                if (loading) {
                    el.innerHTML = '<span class="skeleton" style="width: 60px; height: 1em; display: inline-block;"></span>';
                }
            }
        });
    }
    
    async function updatePreview() {
        if (!hasValidInputs()) {
            clearOutputs();
            return;
        }
        
        if (isCalculating) return;
        isCalculating = true;
        
        const data = {
            filament_used_mm: parseFloat(toEnDigits(elements.filamentUsed.value || 0)) || 0,
            print_time_hours: getPrintTimeHours(),
            size_x: parseFloat(toEnDigits(elements.sizeX.value || 0)) || 0,
            size_y: parseFloat(toEnDigits(elements.sizeY.value || 0)) || 0,
            size_z: parseFloat(toEnDigits(elements.sizeZ.value || 0)) || 0,
            filament_cost_per_kg: parseFloat(toEnDigits(elements.filamentCost?.value || 0)) || 0,
            post_processing_enabled: elements.postProcessing?.checked || false,
            painting_enabled: elements.painting?.checked || false,
            packaging_cost: 0
        };
        
        try {
            const response = await fetch(calcUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify(data)
            });
            
            if (!response.ok) throw new Error('Network response was not ok');
            
            const result = await response.json();
            
            if (result.error) throw new Error(result.error);
            
            // Update outputs with animation
            updateOutput(outputs.weight, formatNumber(result.filament_weight) + ' گرم');
            updateOutput(outputs.material, formatNumber(result.material_cost) + ' تومان');
            updateOutput(outputs.electricity, formatNumber(result.electricity_cost) + ' تومان');
            updateOutput(outputs.depreciation, formatNumber(result.depreciation_cost) + ' تومان');
            updateOutput(outputs.postProcessing, formatNumber(result.post_processing_cost) + ' تومان');
            updateOutput(outputs.painting, formatNumber(result.painting_cost) + ' تومان');
            updateOutput(outputs.total, formatNumber(result.total_cost) + ' تومان');
            updateOutput(outputs.selling, formatNumber(result.selling_price) + ' تومان');
            
            const profit = (result.selling_price || 0) - (result.total_cost || 0);
            updateOutput(outputs.profit, 'سود: ' + formatNumber(profit) + ' تومان');
            
        } catch (error) {
            console.error('Calculation error:', error);
            clearOutputs();
        } finally {
            isCalculating = false;
        }
    }
    
    function updateOutput(element, value) {
        if (!element) return;
        element.style.opacity = '0';
        setTimeout(() => {
            element.textContent = value;
            element.style.opacity = '1';
        }, 150);
    }
    
    const debouncedUpdate = debounce(updatePreview, 400);
    
    // Attach event listeners
    Object.values(elements).forEach(el => {
        if (!el) return;
        const eventType = el.type === 'checkbox' ? 'change' : 'input';
        el.addEventListener(eventType, debouncedUpdate);
    });
    
    // Initial calculation
    setTimeout(updatePreview, 500);
}

// ========== PAGE: DASHBOARD ==========

// static/js/app.js

function initDashboardPage() {
    // 1. DATE FIX: Manually construct the string to ensure order
    const dateEl = document.getElementById('currentDate');
    if (dateEl) {
        const date = new Date();
        const formatter = new Intl.DateTimeFormat('fa-IR', {
            weekday: 'long',
            day: 'numeric',
            month: 'long',
            year: 'numeric'
        });
        
        // This splits the date into parts so we can reorder them exactly how we want
        // However, standard fa-IR usually puts weekday first. 
        // Let's force it: "Friday, 10 Esfand 1403"
        
        const parts = formatter.formatToParts(date);
        const dayName = parts.find(p => p.type === 'weekday').value;
        const day = parts.find(p => p.type === 'day').value;
        const month = parts.find(p => p.type === 'month').value;
        const year = parts.find(p => p.type === 'year').value;
        
        // Construct: "DayName، Day Month Year"
        dateEl.textContent = `${dayName}، ${day} ${month} ${year}`;
    }
    
    // 2. COUNTER ANIMATION (Existing code)
    document.querySelectorAll('.hero-title, .stat-number').forEach(el => {
        // Extract only numbers for calculation
        const rawText = el.innerText;
        const target = parseInt(rawText.replace(/[^\d]/g, '')) || 0;
        
        // If it's 0 or empty, don't animate
        if (target === 0) return;

        // Keep the "Toman" or unit if it exists inside a small tag
        const smallTag = el.querySelector('small');
        const unit = smallTag ? smallTag.outerHTML : '';

        let current = 0;
        const increment = Math.ceil(target / 40); // Speed of count
        
        const timer = setInterval(() => {
            current += increment;
            if (current >= target) {
                // Final set to ensure accuracy
                el.innerHTML = new Intl.NumberFormat('fa-IR').format(target) + (unit ? ' ' + unit : '');
                clearInterval(timer);
            } else {
                el.innerHTML = new Intl.NumberFormat('fa-IR').format(current) + (unit ? ' ' + unit : '');
            }
        }, 20);
    });

    // 3. HOVER EFFECTS (Existing code)
    document.querySelectorAll('.hover-lift').forEach(el => {
        el.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-4px)';
        });
        el.addEventListener('mouseleave', function() {
            this.style.transform = '';
        });
    });
}

// ========== PAGE: FILAMENTS ==========

function initFilamentsPage() {
    const viewInput = document.getElementById('viewInput');
    const filtersForm = document.getElementById('filtersForm');
    
    // View toggle (grid/table)
    document.querySelectorAll('.toggle-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            document.querySelectorAll('.toggle-btn').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            
            if (viewInput) {
                viewInput.value = this.dataset.view;
            }
            
            if (filtersForm) {
                filtersForm.submit();
            }
        });
    });
    
    // Auto-submit on filter change
    document.querySelectorAll('#filtersForm select').forEach(select => {
        select.addEventListener('change', () => {
            if (filtersForm) filtersForm.submit();
        });
    });
    
    // Search with debounce
    const searchInput = document.querySelector('#filtersForm input[name="q"]');
    if (searchInput) {
        let searchTimeout;
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                // Optional: auto-submit search after typing stops
                // filtersForm.submit();
            }, 500);
        });
    }
    
    // Keyboard shortcut for search
    document.addEventListener('keydown', function(e) {
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            searchInput?.focus();
        }
    });
}

// ========== PAGE: PROJECT FORM ==========

function initProjectFormPage() {
    setupImagePreview();
    setupCostPreview();
    initFilamentUnitConverter()
    // Service checkboxes visual feedback
    document.querySelectorAll('.form-check-input').forEach(checkbox => {
        const wrapper = checkbox.closest('.form-check')?.parentElement;
        if (!wrapper) return;
        
        function updateStyle() {
            if (checkbox.checked) {
                wrapper.style.borderColor = 'var(--primary-400)';
                wrapper.style.background = 'linear-gradient(135deg, var(--primary-50), white)';
            } else {
                wrapper.style.borderColor = 'var(--border-color)';
                wrapper.style.background = 'var(--bg-secondary)';
            }
        }
        
        checkbox.addEventListener('change', updateStyle);
        updateStyle(); // Initial state
    });
}

// ========== PAGE: FILAMENT FORM ==========

function initFilamentFormPage() {
    setupColorPreview();
    
    // Amount calculator helper
    const initialAmountInput = document.getElementById('id_initial_amount');
    if (initialAmountInput) {
        // Add quick buttons for common amounts
        const wrapper = initialAmountInput.closest('.form-group');
        if (wrapper) {
            const quickBtns = document.createElement('div');
            quickBtns.className = 'd-flex gap-2 mt-2';
            quickBtns.innerHTML = `
                <button type="button" class="btn-modern btn-ghost btn-sm" data-amount="330">1kg (330m)</button>
                <button type="button" class="btn-modern btn-ghost btn-sm" data-amount="165">0.5kg (165m)</button>
                <button type="button" class="btn-modern btn-ghost btn-sm" data-amount="100">100m</button>
            `;
            
            wrapper.appendChild(quickBtns);
            
            quickBtns.querySelectorAll('button').forEach(btn => {
                btn.addEventListener('click', function() {
                    initialAmountInput.value = this.dataset.amount;
                    initialAmountInput.dispatchEvent(new Event('input'));
                });
            });
        }
    }
}

// ========== PAGE: SALES ==========

function initSalesPage() {
    const tabs = document.querySelectorAll('.method-tab');
    const views = document.querySelectorAll('.method-view');
    
    // Tab switching
    function switchMethod(method) {
        tabs.forEach(t => t.classList.remove('active'));
        views.forEach(v => v.classList.remove('active'));
        
        const activeTab = document.querySelector(`.method-tab[data-method="${method}"]`);
        const activeView = document.getElementById(`view-${method}`);
        
        if (activeTab) activeTab.classList.add('active');
        if (activeView) {
            activeView.classList.add('active');
            activeView.classList.add('fade-in');
        }
    }
    
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const method = tab.dataset.method;
            if (method) switchMethod(method);
        });
    });
    
    // Form elements
    const projectField = document.getElementById('projectField');
    const qtyField = document.getElementById('qtyField');
    const priceField = document.getElementById('priceField');
    const pkgField = document.getElementById('pkgField');
    const calcPreview = document.getElementById('calcPreview');
    const sugPriceEl = document.getElementById('sugPrice');
    const totalPriceEl = document.getElementById('totalPrice');
    
    function updateCalculation() {
        if (!projectField?.value) {
            if (calcPreview) calcPreview.classList.remove('show');
            return;
        }
        
        const opt = projectField.options[projectField.selectedIndex];
        const grams = parseFloat(opt?.dataset.grams || 0) || 0;
        const suggested = Math.round(grams * 2000); // Price per gram estimate
        const qty = parseInt(qtyField?.value || 1) || 1;
        const price = parseFloat(priceField?.value || 0) || 0;
        const pkg = parseFloat(pkgField?.value || 0) || 0;
        const total = qty * price + pkg;
        
        if (sugPriceEl) sugPriceEl.textContent = formatNumber(suggested) + ' تومان';
        if (totalPriceEl) totalPriceEl.textContent = formatNumber(total) + ' تومان';
        if (calcPreview) calcPreview.classList.add('show');
    }
    
    // Event listeners
    if (projectField) {
        projectField.addEventListener('change', function() {
            if (this.value && priceField) {
                const opt = this.options[this.selectedIndex];
                const grams = parseFloat(opt?.dataset.grams || 0) || 0;
                if (!priceField.value || parseFloat(priceField.value) === 0) {
                    priceField.value = Math.round(grams * 2000);
                }
            }
            updateCalculation();
        });
    }
    
    [qtyField, priceField, pkgField].forEach(field => {
        if (field) field.addEventListener('input', updateCalculation);
    });
    
    // Product list click to select
    document.querySelectorAll('.js-product-item').forEach(item => {
        item.addEventListener('click', function() {
            const id = this.dataset.id;
            const grams = parseFloat(this.dataset.grams || 0) || 0;
            
            // Remove selected from others
            document.querySelectorAll('.js-product-item').forEach(p => p.classList.remove('selected'));
            this.classList.add('selected');
            
            switchMethod('select');
            
            if (projectField && id) {
                projectField.value = id;
                projectField.dispatchEvent(new Event('change'));
            }
            
            if (priceField && grams > 0) {
                priceField.value = Math.round(grams * 2000);
                priceField.dispatchEvent(new Event('input'));
            }
            
            // Scroll to form on mobile
            if (window.innerWidth < 992) {
                document.querySelector('.method-tabs')?.scrollIntoView({ 
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
    
    // Search filter
    const searchBox = document.getElementById('searchBox');
    if (searchBox) {
        searchBox.addEventListener('input', debounce(function() {
            const query = this.value.toLowerCase().trim();
            
            document.querySelectorAll('.js-product-item').forEach(item => {
                const name = (item.dataset.name || '').toLowerCase();
                const code = (item.dataset.code || '').toLowerCase();
                const match = name.includes(query) || code.includes(query);
                
                item.style.display = match ? 'flex' : 'none';
                
                if (match && query) {
                    item.classList.add('fade-in');
                }
            });
            
            // Show "no results" message
            const visibleItems = document.querySelectorAll('.js-product-item[style="display: flex"]');
            const noResultsMsg = document.getElementById('noResultsMsg');
            
            if (visibleItems.length === 0 && query) {
                if (!noResultsMsg) {
                    const msg = document.createElement('div');
                    msg.id = 'noResultsMsg';
                    msg.className = 'text-center text-muted py-4';
                    msg.innerHTML = '<i class="fas fa-search mb-2" style="font-size: 2rem; opacity: 0.3;"></i><div>نتیجه‌ای یافت نشد</div>';
                    document.getElementById('productsList')?.appendChild(msg);
                }
            } else if (noResultsMsg) {
                noResultsMsg.remove();
            }
        }, 200));
        
        // Clear search on Escape
        searchBox.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                this.value = '';
                this.dispatchEvent(new Event('input'));
            }
        });
    }
    
    // URL params (for code-based entry)
    const params = new URLSearchParams(window.location.search);
    const codeParam = params.get('code');
    if (codeParam) {
        switchMethod('code');
        const codeField = document.getElementById('codeField');
        if (codeField) {
            codeField.value = codeParam;
            codeField.focus();
        }
    }
    
    // Initial state
    if (projectField?.value) {
        updateCalculation();
    }
}

// ========== PAGE: SALES HISTORY ==========

function initSalesHistoryPage() {
    const periodSelect = document.getElementById('periodSelect');
    const sortSelect = document.getElementById('sortSelect');
    const filterForm = document.getElementById('filterForm');
    
    // Auto-submit on select change
    [periodSelect, sortSelect].forEach(el => {
        if (el) {
            el.addEventListener('change', () => {
                if (filterForm) filterForm.submit();
            });
        }
    });
    
    // Delete confirmation with details
    document.querySelectorAll('form[action*="delete_sale"]').forEach(form => {
        form.addEventListener('submit', function(e) {
            const row = this.closest('tr');
            const productName = row?.querySelector('td:nth-child(4)')?.textContent?.trim() || '';
            const price = row?.querySelector('td:nth-child(7)')?.textContent?.trim() || '';
            
            if (!confirm(`آیا از حذف این فروش اطمینان دارید?\n\nمحصول: ${productName}\nمبلغ: ${price}`)) {
                e.preventDefault();
            }
        });
    });
}

// ========== PAGE: REPORTS ==========

function initReportsPage() {
    // Print button
    const printBtn = document.querySelector('[onclick*="print"]');
    if (printBtn) {
        printBtn.addEventListener('click', function(e) {
            e.preventDefault();
            window.print();
        });
    }
    
    // Period filter auto-submit
    const periodSelect = document.querySelector('select[name="period"]');
    if (periodSelect) {
        periodSelect.addEventListener('change', function() {
            this.closest('form')?.submit();
        });
    }
}

// ========== PAGE: SETTINGS ==========

function initSettingsPage() {
    const form = document.getElementById('settingsForm');
    if (!form) return;
    
    let hasChanges = false;
    const originalValues = {};
    
    // Store original values
    form.querySelectorAll('input, select, textarea').forEach(input => {
        originalValues[input.name] = input.value;
        
        input.addEventListener('input', () => {
            hasChanges = true;
            updateSaveIndicator();
        });
    });
    
    function updateSaveIndicator() {
        const saveBtn = form.querySelector('button[type="submit"]');
        if (saveBtn && hasChanges) {
            saveBtn.classList.add('pulse');
        }
    }
    
    // Warn before leaving with unsaved changes
    window.addEventListener('beforeunload', (e) => {
        if (hasChanges) {
            e.preventDefault();
            e.returnValue = 'تغییرات ذخیره نشده دارید. آیا می‌خواهید خارج شوید?';
        }
    });
    
    form.addEventListener('submit', () => {
        hasChanges = false;
    });
    
    // Input validation feedback
    form.querySelectorAll('input[type="number"]').forEach(input => {
        input.addEventListener('input', function() {
            const min = parseFloat(this.min);
            const max = parseFloat(this.max);
            const value = parseFloat(this.value);
            
            if (!isNaN(min) && value < min) {
                this.classList.add('is-invalid');
            } else if (!isNaN(max) && value > max) {
                this.classList.add('is-invalid');
            } else {
                this.classList.remove('is-invalid');
            }
        });
    });
}

// ========== PAGE: VIEW FILAMENT ==========

function initViewFilamentPage() {
    // Animate circular progress
    const progressCircle = document.querySelector('svg path[stroke-dasharray]');
    if (progressCircle) {
        const finalValue = progressCircle.getAttribute('stroke-dasharray').split(',')[0];
        progressCircle.style.strokeDasharray = '0, 100';
        
        setTimeout(() => {
            progressCircle.style.transition = 'stroke-dasharray 1s ease-out';
            progressCircle.style.strokeDasharray = `${finalValue}, 100`;
        }, 300);
    }
    
    // Usage cards hover effect
    document.querySelectorAll('.usage-card').forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-4px)';
            this.style.boxShadow = 'var(--shadow-lg)';
        });
        card.addEventListener('mouseleave', function() {
            this.style.transform = '';
            this.style.boxShadow = '';
        });
    });
}

// ========== PAGE: VIEW PROJECT ==========

function initViewProjectPage() {
    // Similar to view filament
    initViewFilamentPage();
    
    // Image lightbox (optional)
    const projectImage = document.querySelector('.project-card-image img, .card-modern img');
    if (projectImage) {
        projectImage.style.cursor = 'zoom-in';
        projectImage.addEventListener('click', function() {
            openLightbox(this.src, this.alt);
        });
    }
}

function openLightbox(src, alt) {
    const lightbox = document.createElement('div');
    lightbox.className = 'lightbox fade-in';
    lightbox.style.cssText = `
        position: fixed;
        inset: 0;
        background: rgba(0, 0, 0, 0.9);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 10000;
        cursor: zoom-out;
    `;
    
    lightbox.innerHTML = `
        <img src="${src}" alt="${alt}" style="max-width: 90%; max-height: 90%; object-fit: contain; border-radius: 8px;">
        <button style="position: absolute; top: 20px; left: 20px; background: white; border: none; width: 40px; height: 40px; border-radius: 50%; cursor: pointer; font-size: 1.2rem;">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    document.body.appendChild(lightbox);
    document.body.style.overflow = 'hidden';
    
    lightbox.addEventListener('click', function() {
        this.classList.add('fade-out');
        setTimeout(() => {
            this.remove();
            document.body.style.overflow = '';
        }, 300);
    });
    
    // Close on Escape
    document.addEventListener('keydown', function closeOnEscape(e) {
        if (e.key === 'Escape') {
            lightbox.click();
            document.removeEventListener('keydown', closeOnEscape);
        }
    });
}

// ========== PAGE: ASSIGN PROJECT ==========

function initAssignProjectPage() {
    const projectSelect = document.getElementById('id_project') || document.querySelector('select[name="project"]');
    const quantityInput = document.getElementById('id_quantity') || document.querySelector('input[name="quantity"]');
    
    // Table row click to select project
    document.querySelectorAll('.table-row[onclick], .modern-table tbody tr').forEach(row => {
        row.style.cursor = 'pointer';
        
        row.addEventListener('click', function(e) {
            // Don't trigger if clicking a button or link
            if (e.target.closest('a, button')) return;
            
            const projectId = this.dataset.projectId || 
                              this.querySelector('[data-project-id]')?.dataset.projectId ||
                              this.querySelector('td:first-child')?.textContent?.trim();
            
            // Try to find the project ID from the row
            const codeCell = this.querySelector('.badge');
            if (codeCell && projectSelect) {
                const code = codeCell.textContent.trim();
                
                // Find option by code
                Array.from(projectSelect.options).forEach(opt => {
                    if (opt.textContent.includes(code)) {
                        projectSelect.value = opt.value;
                        projectSelect.dispatchEvent(new Event('change'));
                    }
                });
            }
            
            // Highlight selected row
            document.querySelectorAll('.table-row').forEach(r => {
                r.style.background = '';
            });
            this.style.background = 'var(--primary-50)';
            
            // Focus on quantity
            if (quantityInput) {
                quantityInput.focus();
                quantityInput.select();
            }
        });
    });
}

// ========== KEYBOARD SHORTCUTS ==========

document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + S to save forms
    if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        const form = document.querySelector('form:not([data-no-shortcut])');
        if (form) {
            e.preventDefault();
            form.dispatchEvent(new Event('submit'));
        }
    }
    
    // Escape to close modals/overlays
    if (e.key === 'Escape') {
        const lightbox = document.querySelector('.lightbox');
        if (lightbox) lightbox.click();
    }
});

// ========== GLOBAL ERROR HANDLER ==========

window.addEventListener('error', function(e) {
    console.error('Global error:', e.error);
});

window.addEventListener('unhandledrejection', function(e) {
    console.error('Unhandled promise rejection:', e.reason);
});

// ========== EXPORT FOR GLOBAL USE ==========

window.PrintCost = {
    formatNumber,
    formatNumberEn,
    toEnDigits,
    toFaDigits,
    debounce,
    throttle,
    showToast,
    getCookie,
};


// static/js/add_project.js

document.addEventListener('DOMContentLoaded', function() {
    
    // ========== ELEMENTS ==========
    const displayInput = document.getElementById('filament_input_display');
    const hiddenInput = document.getElementById('id_filament_used_mm');
    const unitBtns = document.querySelectorAll('.unit-btn');
    const conversionInfo = document.getElementById('conversionInfo');
    const conversionValue = document.getElementById('conversionValue');
    const densitySelector = document.getElementById('densitySelector');
    const densityOptions = document.querySelectorAll('.density-option');
    const hintMM = document.getElementById('hintMM');
    const hintM = document.getElementById('hintM');
    const hintG = document.getElementById('hintG');
    const costPreviewCard = document.getElementById('costPreviewCard');
    
    // ========== STATE ==========
    let currentUnit = 'mm';
    let currentDensity = 3.0; // گرم بر متر
    const MM_PER_METER = 1000;
    
    // ========== INITIALIZATION ==========
    if (displayInput && hiddenInput) {
        // Initialize hidden input with existing value
        if (displayInput.value) {
            hiddenInput.value = displayInput.value;
        }
        
        initUnitSelector();
        initDensitySelector();
        initInputHandler();
        initFormSubmit();
    }
    
    initServiceBoxes();
    initImagePreview();
    initCostPreview();
    
    // ========== UNIT SELECTOR ==========
    function initUnitSelector() {
        unitBtns.forEach(btn => {
            btn.addEventListener('click', function() {
                const newUnit = this.dataset.unit;
                if (newUnit === currentUnit) return;
                
                // Update active state
                unitBtns.forEach(b => b.classList.remove('active'));
                this.classList.add('active');
                
                // Convert existing value to new unit for display
                const mmValue = parseFloat(hiddenInput.value) || 0;
                
                if (mmValue > 0) {
                    displayInput.value = convertFromMM(mmValue, newUnit);
                }
                
                currentUnit = newUnit;
                updateHints();
                updateConversionDisplay();
            });
        });
    }
    
    // ========== DENSITY SELECTOR ==========
    function initDensitySelector() {
        densityOptions.forEach(opt => {
            opt.addEventListener('click', function() {
                densityOptions.forEach(o => o.classList.remove('active'));
                this.classList.add('active');
                currentDensity = parseFloat(this.dataset.density);
                
                // Recalculate if we have a value
                if (displayInput.value) {
                    updateHiddenValue();
                    updateConversionDisplay();
                    triggerCostUpdate();
                }
            });
        });
    }
    
    // ========== INPUT HANDLER ==========
    function initInputHandler() {
        displayInput.addEventListener('input', function() {
            updateHiddenValue();
            updateConversionDisplay();
            triggerCostUpdate();
        });
    }
    
    // ========== FORM SUBMIT ==========
    function initFormSubmit() {
        const form = document.getElementById('projectForm');
        if (form) {
            form.addEventListener('submit', function(e) {
                updateHiddenValue();
            });
        }
    }
    
    // ========== CONVERSION FUNCTIONS ==========
    function updateHiddenValue() {
        const displayValue = parseFloat(displayInput.value) || 0;
        let mmValue = 0;
        
        switch (currentUnit) {
            case 'mm':
                mmValue = displayValue;
                break;
            case 'm':
                mmValue = displayValue * MM_PER_METER;
                break;
            case 'g':
                // گرم به متر: gram / density = meters
                // متر به میلی‌متر: meters * 1000
                const meters = displayValue / currentDensity;
                mmValue = meters * MM_PER_METER;
                break;
        }
        
        hiddenInput.value = Math.round(mmValue * 100) / 100;
    }
    
    function convertFromMM(mmValue, unit) {
        switch (unit) {
            case 'mm':
                return Math.round(mmValue * 100) / 100;
            case 'm':
                return Math.round((mmValue / MM_PER_METER) * 1000) / 1000;
            case 'g':
                const meters = mmValue / MM_PER_METER;
                return Math.round((meters * currentDensity) * 100) / 100;
        }
        return mmValue;
    }
    
    function updateConversionDisplay() {
        if (!conversionInfo || !conversionValue || !hiddenInput) return;
        
        const mmValue = parseFloat(hiddenInput.value) || 0;
        
        if (mmValue <= 0 || currentUnit === 'mm') {
            conversionInfo.style.display = 'none';
            return;
        }
        
        conversionInfo.style.display = 'flex';
        
        const meters = mmValue / MM_PER_METER;
        const grams = meters * currentDensity;
        
        let conversionText = '';
        if (currentUnit === 'm') {
            conversionText = `${formatNumber(mmValue)} میلی‌متر = ${formatNumber(grams)} گرم`;
        } else if (currentUnit === 'g') {
            conversionText = `${formatNumber(meters)} متر = ${formatNumber(mmValue)} میلی‌متر`;
        }
        
        conversionValue.textContent = conversionText;
    }
    
    function updateHints() {
        if (hintMM) hintMM.style.display = currentUnit === 'mm' ? 'inline' : 'none';
        if (hintM) hintM.style.display = currentUnit === 'm' ? 'inline' : 'none';
        if (hintG) hintG.style.display = currentUnit === 'g' ? 'inline' : 'none';
        
        // Show/hide density selector
        if (densitySelector) {
            if (currentUnit === 'g') {
                densitySelector.classList.add('show');
            } else {
                densitySelector.classList.remove('show');
            }
        }
    }
    
    // ========== FORMAT NUMBER ==========
    function formatNumber(num) {
        return new Intl.NumberFormat('fa-IR', { 
            maximumFractionDigits: 2 
        }).format(num);
    }
    
    // ========== SERVICE BOXES ==========
    function initServiceBoxes() {
        // Post Processing Box
        const postProcessingBox = document.getElementById('postProcessingBox');
        const postProcessingCheckbox = document.getElementById('id_post_processing_enabled');
        
        if (postProcessingBox && postProcessingCheckbox) {
            // Click on box (but not on checkbox itself)
            postProcessingBox.addEventListener('click', function(e) {
                // Prevent double toggle if clicking directly on checkbox
                if (e.target === postProcessingCheckbox || e.target.tagName === 'LABEL') {
                    return;
                }
                postProcessingCheckbox.checked = !postProcessingCheckbox.checked;
                updateServiceBoxStyle(postProcessingBox, postProcessingCheckbox.checked);
                triggerCostUpdate();
            });
            
            // Direct checkbox change
            postProcessingCheckbox.addEventListener('change', function() {
                updateServiceBoxStyle(postProcessingBox, this.checked);
                triggerCostUpdate();
            });
            
            // Initial state
            updateServiceBoxStyle(postProcessingBox, postProcessingCheckbox.checked);
        }
        
        // Painting Box
        const paintingBox = document.getElementById('paintingBox');
        const paintingCheckbox = document.getElementById('id_painting_enabled');
        
        if (paintingBox && paintingCheckbox) {
            // Click on box (but not on checkbox itself)
            paintingBox.addEventListener('click', function(e) {
                // Prevent double toggle if clicking directly on checkbox
                if (e.target === paintingCheckbox || e.target.tagName === 'LABEL') {
                    return;
                }
                paintingCheckbox.checked = !paintingCheckbox.checked;
                updateServiceBoxStyle(paintingBox, paintingCheckbox.checked);
                triggerCostUpdate();
            });
            
            // Direct checkbox change
            paintingCheckbox.addEventListener('change', function() {
                updateServiceBoxStyle(paintingBox, this.checked);
                triggerCostUpdate();
            });
            
            // Initial state
            updateServiceBoxStyle(paintingBox, paintingCheckbox.checked);
        }
    }
    
    function updateServiceBoxStyle(box, isChecked) {
        if (!box) return;
        
        if (isChecked) {
            box.style.borderColor = 'var(--primary-400)';
            box.style.background = 'linear-gradient(135deg, var(--primary-50), white)';
            box.classList.add('checked');
        } else {
            box.style.borderColor = 'var(--border-color)';
            box.style.background = 'var(--bg-secondary)';
            box.classList.remove('checked');
        }
    }
    
    // ========== IMAGE PREVIEW ==========
    function initImagePreview() {
        const imageInput = document.querySelector('input[data-preview-target]');
        if (!imageInput) return;
        
        const previewId = imageInput.dataset.previewTarget;
        const preview = document.getElementById(previewId);
        if (!preview) return;
        
        imageInput.addEventListener('change', function(e) {
            const file = e.target.files?.[0];
            if (!file) {
                preview.classList.add('d-none');
                return;
            }
            
            if (!file.type.startsWith('image/')) {
                alert('لطفاً یک فایل تصویری انتخاب کنید');
                imageInput.value = '';
                return;
            }
            
            if (file.size > 5 * 1024 * 1024) {
                alert('حجم فایل نباید بیشتر از 5 مگابایت باشد');
                imageInput.value = '';
                return;
            }
            
            const reader = new FileReader();
            reader.onload = function(ev) {
                preview.src = ev.target.result;
                preview.classList.remove('d-none');
            };
            reader.readAsDataURL(file);
        });
    }
    
    // ========== COST PREVIEW ==========
    let costUpdateTimeout;
    
    function initCostPreview() {
        if (!costPreviewCard) return;
        
        const calcUrl = costPreviewCard.dataset.calcUrl;
        if (!calcUrl) return;
        
        // Attach to all relevant inputs
        const watchInputs = [
            'id_print_hours', 
            'id_print_minutes',
            'id_size_x', 
            'id_size_y', 
            'id_size_z',
            'preview-filament-cost'
        ];
        
        watchInputs.forEach(id => {
            const el = document.getElementById(id);
            if (el) {
                el.addEventListener('input', debouncedCostUpdate);
            }
        });
        
        // Initial update after a short delay
        setTimeout(updateCostPreview, 500);
    }
    
    function debouncedCostUpdate() {
        clearTimeout(costUpdateTimeout);
        costUpdateTimeout = setTimeout(updateCostPreview, 400);
    }
    
    function triggerCostUpdate() {
        debouncedCostUpdate();
    }
    
    function updateCostPreview() {
        if (!costPreviewCard) return;
        
        const calcUrl = costPreviewCard.dataset.calcUrl;
        if (!calcUrl) return;
        
        const data = getCostPreviewData();
        
        // Check if we have minimum required data
        if (data.filament_used_mm <= 0 || data.print_time_hours <= 0) {
            return;
        }
        
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
        
        fetch(calcUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(result => {
            if (result.error) return;
            
            updateElement('filament-weight', formatNumber(result.filament_weight) + ' گرم');
            updateElement('material-cost', formatNumber(result.material_cost) + ' تومان');
            updateElement('electricity-cost', formatNumber(result.electricity_cost) + ' تومان');
            updateElement('depreciation-cost', formatNumber(result.depreciation_cost) + ' تومان');
            updateElement('post-processing-cost', formatNumber(result.post_processing_cost) + ' تومان');
            updateElement('painting-cost', formatNumber(result.painting_cost) + ' تومان');
            updateElement('total-cost', formatNumber(result.total_cost) + ' تومان');
            updateElement('selling-price', formatNumber(result.selling_price) + ' تومان');
            
            const profit = (result.selling_price || 0) - (result.total_cost || 0);
            updateElement('profit-margin', 'سود: ' + formatNumber(profit) + ' تومان');
        })
        .catch(err => console.error('Cost preview error:', err));
    }
    
    function getCostPreviewData() {
        const filamentMM = parseFloat(hiddenInput?.value) || 0;
        const printHours = parseFloat(document.getElementById('id_print_hours')?.value) || 0;
        const printMinutes = parseFloat(document.getElementById('id_print_minutes')?.value) || 0;
        const sizeX = parseFloat(document.getElementById('id_size_x')?.value) || 0;
        const sizeY = parseFloat(document.getElementById('id_size_y')?.value) || 0;
        const sizeZ = parseFloat(document.getElementById('id_size_z')?.value) || 0;
        const filamentCost = parseFloat(document.getElementById('preview-filament-cost')?.value) || 0;
        
        // Get checkbox states correctly
        const postProcessingCheckbox = document.getElementById('id_post_processing_enabled');
        const paintingCheckbox = document.getElementById('id_painting_enabled');
        
        const postProcessing = postProcessingCheckbox ? postProcessingCheckbox.checked : false;
        const painting = paintingCheckbox ? paintingCheckbox.checked : false;
        
        return {
            filament_used_mm: filamentMM,
            print_time_hours: printHours + (printMinutes / 60),
            size_x: sizeX,
            size_y: sizeY,
            size_z: sizeZ,
            filament_cost_per_kg: filamentCost,
            post_processing_enabled: postProcessing,
            painting_enabled: painting,
            packaging_cost: 0
        };
    }
    
    function updateElement(id, value) {
        const el = document.getElementById(id);
        if (el) {
            el.style.transition = 'opacity 0.15s ease';
            el.style.opacity = '0';
            setTimeout(() => {
                el.textContent = value;
                el.style.opacity = '1';
            }, 100);
        }
    }
    
});

// ========== TIME SUMMARY ==========
function initTimeSummary() {
    if (!printHoursInput || !printMinutesInput || !timeSummary || !timeSummaryText) {
        return;
    }
    
    function updateTimeSummary() {
        const hours = parseInt(printHoursInput.value) || 0;
        const minutes = parseInt(printMinutesInput.value) || 0;
        
        if (hours === 0 && minutes === 0) {
            timeSummary.style.display = 'none';
            return;
        }
        
        timeSummary.style.display = 'flex';
        
        // Calculate total
        const totalMinutes = (hours * 60) + minutes;
        const totalHours = hours + (minutes / 60);
        
        // Format display text
        let displayText = '';
        
        // Persian formatted time
        if (hours > 0 && minutes > 0) {
            displayText = `<span class="time-value">${toPersianNum(hours)}</span> ساعت و <span class="time-value">${toPersianNum(minutes)}</span> دقیقه`;
        } else if (hours > 0) {
            displayText = `<span class="time-value">${toPersianNum(hours)}</span> ساعت`;
        } else {
            displayText = `<span class="time-value">${toPersianNum(minutes)}</span> دقیقه`;
        }
        
        // Add decimal hours
        const decimalHours = totalHours.toFixed(2);
        displayText += `<span class="time-decimal">≈ <span class="time-value">${toPersianNum(decimalHours)}</span> ساعت</span>`;
        
        timeSummaryText.innerHTML = displayText;
    }
    
    // Convert to Persian numerals
    function toPersianNum(num) {
        const persianDigits = ['۰', '۱', '۲', '۳', '۴', '۵', '۶', '۷', '۸', '۹'];
        return num.toString().replace(/\d/g, d => persianDigits[parseInt(d)]);
    }
    
    // Attach event listeners
    printHoursInput.addEventListener('input', updateTimeSummary);
    printMinutesInput.addEventListener('input', updateTimeSummary);
    
    // Initial update
    updateTimeSummary();
}

// static/js/projects.js

document.addEventListener('DOMContentLoaded', function() {
    
    // ========== STAGGER ANIMATION ==========
    const projectCards = document.querySelectorAll('.project-card');
    projectCards.forEach((card, index) => {
        card.style.animationDelay = `${index * 50}ms`;
    });
    
    // ========== KEYBOARD SHORTCUT ==========
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + K for search focus
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            const searchInput = document.querySelector('input[name="q"]');
            if (searchInput) {
                searchInput.focus();
                searchInput.select();
            }
        }
        
        // Escape to clear search
        if (e.key === 'Escape') {
            const searchInput = document.querySelector('input[name="q"]');
            if (searchInput && document.activeElement === searchInput) {
                searchInput.value = '';
                searchInput.blur();
            }
        }
    });
    
    // ========== LAZY LOAD IMAGES ==========
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    if (img.dataset.src) {
                        img.src = img.dataset.src;
                        img.removeAttribute('data-src');
                    }
                    img.classList.add('loaded');
                    observer.unobserve(img);
                }
            });
        });
        
        document.querySelectorAll('.project-card-image img').forEach(img => {
            imageObserver.observe(img);
        });
    }
    
    // ========== CARD HOVER EFFECTS ==========
    projectCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-8px)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = '';
        });
    });
    
    // ========== FILTER FORM AUTO-SUBMIT ==========
    const sortSelect = document.querySelector('select[name="sort"]');
    if (sortSelect) {
        sortSelect.addEventListener('change', function() {
            this.closest('form').submit();
        });
    }
    
});

// static/js/pricing_settings.js

document.addEventListener('DOMContentLoaded', function() {
    
    // ========== PERSIAN DATE FOR LAST UPDATED ==========
    const lastUpdatedEl = document.getElementById('lastUpdatedDate');
    if (lastUpdatedEl) {
        const isoDate = lastUpdatedEl.dataset.date;
        if (isoDate) {
            const date = new Date(isoDate);
            
            // Get parts separately for correct Persian format
            const weekday = date.toLocaleDateString('fa-IR', { weekday: 'long' });
            const day = date.toLocaleDateString('fa-IR', { day: 'numeric' });
            const month = date.toLocaleDateString('fa-IR', { month: 'long' });
            const year = date.toLocaleDateString('fa-IR', { year: 'numeric' });
            const time = date.toLocaleTimeString('fa-IR', { hour: '2-digit', minute: '2-digit' });
            
            // Format: جمعه، ۱۵ خرداد ۱۴۰۴ - ۱۴:۳۰
            lastUpdatedEl.textContent = `${weekday}، ${day} ${month} ${year} - ${time}`;
        }
    }
    
    // ========== TRACK UNSAVED CHANGES ==========
    const form = document.getElementById('settingsForm');
    let hasChanges = false;
    const originalValues = {};
    
    if (form) {
        // Store original values
        form.querySelectorAll('input, select, textarea').forEach(input => {
            originalValues[input.name] = input.value;
            
            input.addEventListener('input', function() {
                hasChanges = true;
                updateSaveButton();
            });
            
            input.addEventListener('change', function() {
                hasChanges = true;
                updateSaveButton();
            });
        });
        
        // Update save button appearance
        function updateSaveButton() {
            const saveBtn = form.querySelector('button[type="submit"]');
            if (saveBtn && hasChanges) {
                saveBtn.classList.add('btn-pulse');
            }
        }
        
        // Warn before leaving with unsaved changes
        window.addEventListener('beforeunload', function(e) {
            if (hasChanges) {
                e.preventDefault();
                e.returnValue = 'تغییرات ذخیره نشده دارید. آیا می‌خواهید خارج شوید؟';
            }
        });
        
        // Reset flag on form submit
        form.addEventListener('submit', function() {
            hasChanges = false;
        });
    }
    
    // ========== INPUT VALIDATION FEEDBACK ==========
    const numberInputs = document.querySelectorAll('input[type="number"]');
    numberInputs.forEach(input => {
        input.addEventListener('input', function() {
            const value = parseFloat(this.value);
            const min = parseFloat(this.min);
            const max = parseFloat(this.max);
            
            // Remove previous state
            this.classList.remove('is-invalid', 'is-valid');
            
            if (isNaN(value)) {
                return;
            }
            
            if (!isNaN(min) && value < min) {
                this.classList.add('is-invalid');
            } else if (!isNaN(max) && value > max) {
                this.classList.add('is-invalid');
            } else if (value >= 0) {
                this.classList.add('is-valid');
            }
        });
    });
    
    // ========== KEYBOARD SHORTCUT FOR SAVE ==========
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + S to save
        if ((e.ctrlKey || e.metaKey) && e.key === 's') {
            e.preventDefault();
            if (form) {
                form.dispatchEvent(new Event('submit', { bubbles: true }));
                form.submit();
            }
        }
    });
    
});

// static/js/license_page.js

document.addEventListener('DOMContentLoaded', function() {
    
    // ========== PLAN NAME TRANSLATION ==========
    const planTranslations = {
        'monthly': 'ماهانه',
        'yearly': 'سالانه',
        'lifetime': 'مادام‌العمر',
        'trial': 'آزمایشی',
        'standard': 'استاندارد',
        'pro': 'حرفه‌ای',
        'enterprise': 'سازمانی',
        'basic': 'پایه',
        'premium': 'ویژه',
        'free': 'رایگان'
    };
    
    const planBadge = document.getElementById('planBadge');
    if (planBadge) {
        const planKey = planBadge.dataset.plan?.toLowerCase() || 'standard';
        planBadge.textContent = planTranslations[planKey] || planBadge.dataset.plan || 'استاندارد';
    }
    
    // ========== PERSIAN DATE CONVERSION ==========
    function toPersianDate(isoDateStr) {
        if (!isoDateStr) return '';
        
        try {
            const date = new Date(isoDateStr);
            if (isNaN(date.getTime())) return isoDateStr;
            
            const day = date.toLocaleDateString('fa-IR', { day: 'numeric' });
            const month = date.toLocaleDateString('fa-IR', { month: 'long' });
            const year = date.toLocaleDateString('fa-IR', { year: 'numeric' });
            
            return `${day} ${month} ${year}`;
        } catch (e) {
            console.error('Date conversion error:', e);
            return isoDateStr;
        }
    }
    
    function toPersianNumber(num) {
        const persianDigits = ['۰', '۱', '۲', '۳', '۴', '۵', '۶', '۷', '۸', '۹'];
        return num.toString().replace(/\d/g, d => persianDigits[parseInt(d)]);
    }
    
    // Convert issued date
    const issuedDateEl = document.getElementById('issuedDate');
    if (issuedDateEl && issuedDateEl.dataset.date) {
        issuedDateEl.textContent = toPersianDate(issuedDateEl.dataset.date);
    }
    
    // Convert expires date
    const expiresDateEl = document.getElementById('expiresDate');
    if (expiresDateEl && expiresDateEl.dataset.date) {
        expiresDateEl.textContent = toPersianDate(expiresDateEl.dataset.date);
    }
    
    // Convert remaining days to Persian
    const remainingDaysEl = document.getElementById('remainingDays');
    if (remainingDaysEl && remainingDaysEl.dataset.days) {
        const days = remainingDaysEl.dataset.days;
        remainingDaysEl.textContent = toPersianNumber(days) + ' روز';
    }
    
    // ========== FILE UPLOAD ==========
    const uploadZone = document.getElementById('uploadZone');
    const fileInput = document.getElementById('licenseFile');
    const selectedFile = document.getElementById('selectedFile');
    const selectedFileName = document.getElementById('selectedFileName');
    const uploadContent = document.querySelector('.upload-content');
    
    if (uploadZone && fileInput) {
        // Click to select file
        uploadZone.addEventListener('click', function(e) {
            if (e.target !== fileInput && !e.target.closest('.upload-remove')) {
                fileInput.click();
            }
        });
        
        // File selected
        fileInput.addEventListener('change', function() {
            if (this.files && this.files[0]) {
                showSelectedFile(this.files[0].name);
            }
        });
        
        // Drag and drop
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            uploadZone.addEventListener(eventName, preventDefaults, false);
        });
        
        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }
        
        ['dragenter', 'dragover'].forEach(eventName => {
            uploadZone.addEventListener(eventName, function() {
                uploadZone.classList.add('dragover');
            }, false);
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            uploadZone.addEventListener(eventName, function() {
                uploadZone.classList.remove('dragover');
            }, false);
        });
        
        uploadZone.addEventListener('drop', function(e) {
            const dt = e.dataTransfer;
            const files = dt.files;
            if (files.length) {
                fileInput.files = files;
                showSelectedFile(files[0].name);
            }
        });
    }
    
    function showSelectedFile(name) {
        if (uploadContent) uploadContent.style.display = 'none';
        if (selectedFile) {
            selectedFile.style.display = 'flex';
            selectedFileName.textContent = name;
        }
        if (uploadZone) uploadZone.classList.add('has-file');
    }
    
    // Clear file (global function)
    window.clearFile = function() {
        if (fileInput) fileInput.value = '';
        if (uploadContent) uploadContent.style.display = 'flex';
        if (selectedFile) selectedFile.style.display = 'none';
        if (uploadZone) uploadZone.classList.remove('has-file');
    };
    
    // ========== COPY FINGERPRINT ==========
    window.copyFingerprint = function() {
        const fingerprintCode = document.getElementById('fingerprintCode');
        const copyBtn = document.getElementById('copyBtn');
        
        if (!fingerprintCode) return;
        
        const text = fingerprintCode.textContent;
        
        navigator.clipboard.writeText(text).then(() => {
            // Success feedback
            const originalHTML = copyBtn.innerHTML;
            copyBtn.innerHTML = '<i class="fas fa-check"></i><span>کپی شد!</span>';
            copyBtn.classList.add('btn-success');
            copyBtn.classList.remove('btn-primary');
            
            // Highlight effect
            const fingerprintBox = document.getElementById('fingerprintBox');
            if (fingerprintBox) {
                fingerprintBox.classList.add('copied');
                setTimeout(() => fingerprintBox.classList.remove('copied'), 1000);
            }
            
            // Reset button after 2 seconds
            setTimeout(() => {
                copyBtn.innerHTML = originalHTML;
                copyBtn.classList.remove('btn-success');
                copyBtn.classList.add('btn-primary');
            }, 2000);
            
        }).catch(err => {
            console.error('خطا در کپی:', err);
            alert('خطا در کپی. لطفاً دستی کپی کنید.');
        });
    };
    
});

// static/js/filaments.js

document.addEventListener('DOMContentLoaded', function() {
    
    // ========== VIEW TOGGLE ==========
    const viewInput = document.getElementById('viewInput');
    const filtersForm = document.getElementById('filtersForm');
    const viewToggleBtns = document.querySelectorAll('.view-toggle-btn');
    
    viewToggleBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const view = this.dataset.view;
            
            // Update active state
            viewToggleBtns.forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            
            // Update hidden input and submit
            if (viewInput) {
                viewInput.value = view;
            }
            
            if (filtersForm) {
                filtersForm.submit();
            }
        });
    });
    
    // ========== AUTO-SUBMIT ON SELECT CHANGE ==========
    const selectFilters = document.querySelectorAll('#filtersForm select');
    selectFilters.forEach(select => {
        select.addEventListener('change', function() {
            // Optional: auto-submit on filter change
            // filtersForm.submit();
        });
    });
    
    // ========== KEYBOARD SHORTCUT ==========
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + K for search
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            const searchInput = document.querySelector('input[name="q"]');
            if (searchInput) {
                searchInput.focus();
                searchInput.select();
            }
        }
    });
    
    // ========== STAGGER ANIMATION ==========
    const cards = document.querySelectorAll('.filament-card-new');
    cards.forEach((card, index) => {
        card.style.animationDelay = `${index * 50}ms`;
    });
    
    // ========== PERSIAN DATE CONVERSION ==========
    document.querySelectorAll('.date-display').forEach(el => {
        const isoDate = el.dataset.date;
        if (isoDate) {
            try {
                const date = new Date(isoDate);
                const day = date.toLocaleDateString('fa-IR', { day: 'numeric' });
                const month = date.toLocaleDateString('fa-IR', { month: 'short' });
                const year = date.toLocaleDateString('fa-IR', { year: 'numeric' });
                el.textContent = `${day} ${month} ${year}`;
            } catch (e) {
                // Keep original
            }
        }
    });
    
});

// static/js/add_filament.js

document.addEventListener('DOMContentLoaded', function() {
    
    // ========== ELEMENTS ==========
    const colorInput = document.getElementById('id_color');
    const colorPreviewInner = document.getElementById('colorPreviewInner');
    const previewSpoolColor = document.getElementById('previewSpoolColor');
    const colorPresets = document.querySelectorAll('.color-preset');
    
    const nameInput = document.getElementById('id_name');
    const materialInput = document.getElementById('id_material');
    const amountInput = document.getElementById('id_initial_amount');
    const priceInput = document.getElementById('id_cost_per_kg');
    
    const previewName = document.getElementById('previewName');
    const previewMaterial = document.getElementById('previewMaterial');
    const previewAmount = document.getElementById('previewAmount');
    const previewPrice = document.getElementById('previewPrice');
    
    const costCalculator = document.getElementById('costCalculator');
    const pricePerMeter = document.getElementById('pricePerMeter');
    const totalValue = document.getElementById('totalValue');
    
    const quickAmountBtns = document.querySelectorAll('.quick-amount-btn');
    
    // ========== COLOR PREVIEW ==========
    function updateColorPreview() {
        let color = colorInput?.value?.trim() || '';
        
        if (!color) {
            color = '#6B7280';
        } else if (/^[0-9A-Fa-f]{6}$/.test(color)) {
            color = '#' + color;
        } else if (/^[0-9A-Fa-f]{3}$/.test(color)) {
            color = '#' + color;
        } else if (!color.startsWith('#')) {
            // Named color - try to use it directly
            color = color;
        }
        
        if (colorPreviewInner) {
            colorPreviewInner.style.backgroundColor = color;
        }
        if (previewSpoolColor) {
            previewSpoolColor.style.backgroundColor = color;
        }
    }
    
    if (colorInput) {
        colorInput.addEventListener('input', updateColorPreview);
        colorInput.addEventListener('change', updateColorPreview);
        updateColorPreview();
    }
    
    // ========== COLOR PRESETS ==========
    colorPresets.forEach(preset => {
        preset.addEventListener('click', function() {
            const color = this.dataset.color;
            if (colorInput && color) {
                colorInput.value = color;
                updateColorPreview();
                
                // Visual feedback
                colorPresets.forEach(p => p.classList.remove('active'));
                this.classList.add('active');
            }
        });
    });
    
    // ========== LIVE PREVIEW ==========
    function updatePreview() {
        // Name
        if (previewName && nameInput) {
            previewName.textContent = nameInput.value || 'نام فیلامنت';
        }
        
        // Material
        if (previewMaterial && materialInput) {
            previewMaterial.textContent = materialInput.value || 'PLA';
        }
        
        // Amount
        if (previewAmount && amountInput) {
            const amount = parseFloat(amountInput.value) || 0;
            previewAmount.textContent = toPersianNum(amount);
        }
        
        // Price
        if (previewPrice && priceInput) {
            const price = parseFloat(priceInput.value) || 0;
            previewPrice.textContent = toPersianNum(formatNumber(price));
        }
    }
    
    if (nameInput) nameInput.addEventListener('input', updatePreview);
    if (materialInput) materialInput.addEventListener('change', updatePreview);
    if (amountInput) amountInput.addEventListener('input', updatePreview);
    if (priceInput) priceInput.addEventListener('input', updatePreview);
    
    updatePreview();
    
    // ========== COST CALCULATOR ==========
    function updateCostCalculator() {
        const amount = parseFloat(amountInput?.value) || 0;
        const pricePerKg = parseFloat(priceInput?.value) || 0;
        
        if (amount > 0 && pricePerKg > 0) {
            costCalculator.style.display = 'block';
            
            // Price per meter (assuming 330m per kg)
            const pricePerM = pricePerKg / 330;
            pricePerMeter.textContent = toPersianNum(Math.round(pricePerM)) + ' تومان';
            
            // Total value
            const total = (amount / 330) * pricePerKg;
            totalValue.textContent = toPersianNum(formatNumber(Math.round(total))) + ' تومان';
        } else {
            costCalculator.style.display = 'none';
        }
    }
    
    if (amountInput) amountInput.addEventListener('input', updateCostCalculator);
    if (priceInput) priceInput.addEventListener('input', updateCostCalculator);
    
    // ========== QUICK AMOUNT BUTTONS ==========
    quickAmountBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const amount = this.dataset.amount;
            if (amountInput && amount) {
                amountInput.value = amount;
                amountInput.dispatchEvent(new Event('input'));
                
                // Visual feedback
                quickAmountBtns.forEach(b => b.classList.remove('active'));
                this.classList.add('active');
            }
        });
    });
    
    // ========== HELPER FUNCTIONS ==========
    function toPersianNum(num) {
        const persianDigits = ['۰', '۱', '۲', '۳', '۴', '۵', '۶', '۷', '۸', '۹'];
        return num.toString().replace(/\d/g, d => persianDigits[parseInt(d)]);
    }
    
    function formatNumber(num) {
        return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    }
    
});