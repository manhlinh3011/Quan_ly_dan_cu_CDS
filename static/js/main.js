/**
 * Vietnamese Commune Administration Digital Transformation System
 * Main JavaScript functionality
 */

// Global variables
let currentUser = null;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    setupEventListeners();
    setupFormValidation();
    setupTooltips();
    setupConfirmations();
});

/**
 * Initialize the application
 */
function initializeApp() {
    // Set up CSRF protection for AJAX requests
    setupCSRFProtection();
    
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Auto-hide alerts with custom rules:
    // - All success messages keep visible longer (60s)
    // - Info alerts auto-hide after 5s by default
    // - Danger/error alerts remain until user closes them
    setTimeout(function() {
        var alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            var text = (alert.textContent || '').trim();
            var bsAlert = new bootstrap.Alert(alert);

            if (alert.classList.contains('alert-success')) {
                // Close all success messages after 60 seconds
                setTimeout(function() { bsAlert.close(); }, 60000);
            } else if (alert.classList.contains('alert-info')) {
                // Default short timeout for info messages
                setTimeout(function() { bsAlert.close(); }, 5000);
            }
            // alert-danger stays until manually closed
        });
    }, 100); // small delay to allow alerts to render
    
    console.log('Hệ thống UBND xã đã khởi tạo thành công');
}

/**
 * Setup event listeners
 */
function setupEventListeners() {
    // Search functionality
    setupSearchHandlers();
    
    // Form auto-save (for long forms)
    setupAutoSave();
    
    // File upload preview
    setupFileUploadPreview();
    
    // Table sorting
    setupTableSorting();
    
    // Print functionality
    setupPrintHandlers();
    
    // Mobile menu handling
    setupMobileMenu();

    // Tabs handling on benefits page
    setupTabs();
}

/**
 * Setup CSRF protection
 */
function setupCSRFProtection() {
    // Get CSRF token from meta tag if available
    const csrfToken = document.querySelector('meta[name="csrf-token"]');
    if (csrfToken) {
        // Setup default headers for fetch requests
        const originalFetch = window.fetch;
        window.fetch = function(url, options = {}) {
            if (!options.headers) {
                options.headers = {};
            }
            options.headers['X-CSRFToken'] = csrfToken.getAttribute('content');
            return originalFetch(url, options);
        };
    }
}

/**
 * Setup search handlers
 */
function setupSearchHandlers() {
    const searchInputs = document.querySelectorAll('input[type="search"], .search-input');
    
    searchInputs.forEach(function(input) {
        let searchTimeout;
        
        input.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(function() {
                performSearch(input);
            }, 500); // Debounce search
        });
        
        // Clear search
        const clearBtn = input.parentElement.querySelector('.search-clear');
        if (clearBtn) {
            clearBtn.addEventListener('click', function() {
                input.value = '';
                performSearch(input);
            });
        }
    });
}

/**
 * Perform search operation
 */
function performSearch(input) {
    const searchTerm = input.value.toLowerCase().trim();
    const targetTable = input.getAttribute('data-target');
    
    if (targetTable) {
        const table = document.querySelector(targetTable);
        if (table) {
            const rows = table.querySelectorAll('tbody tr');
            
            rows.forEach(function(row) {
                const text = row.textContent.toLowerCase();
                if (searchTerm === '' || text.includes(searchTerm)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
            
            // Update result count
            const visibleRows = table.querySelectorAll('tbody tr[style=""]').length;
            updateSearchResults(visibleRows);
        }
    }
}

/**
 * Update search results count
 */
function updateSearchResults(count) {
    const resultElement = document.querySelector('.search-results');
    if (resultElement) {
        if (count === 0) {
            resultElement.textContent = 'Không tìm thấy kết quả';
            resultElement.className = 'search-results text-muted';
        } else {
            resultElement.textContent = `Tìm thấy ${count} kết quả`;
            resultElement.className = 'search-results text-success';
        }
    }
}

/**
 * Setup form validation
 */
function setupFormValidation() {
    const forms = document.querySelectorAll('.needs-validation');
    
    forms.forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
                
                // Focus on first invalid field
                const firstInvalid = form.querySelector(':invalid');
                if (firstInvalid) {
                    firstInvalid.focus();
                    showValidationMessage(firstInvalid);
                }
            }
            
            form.classList.add('was-validated');
        });
        
        // Real-time validation
        const inputs = form.querySelectorAll('input, select, textarea');
        inputs.forEach(function(input) {
            input.addEventListener('blur', function() {
                validateField(input);
            });
            
            input.addEventListener('input', function() {
                if (input.classList.contains('is-invalid')) {
                    validateField(input);
                }
            });
        });
    });
}

/**
 * Validate individual field
 */
function validateField(field) {
    if (field.checkValidity()) {
        field.classList.remove('is-invalid');
        field.classList.add('is-valid');
        hideValidationMessage(field);
    } else {
        field.classList.remove('is-valid');
        field.classList.add('is-invalid');
        showValidationMessage(field);
    }
}

/**
 * Show validation message
 */
function showValidationMessage(field) {
    const existingFeedback = field.parentElement.querySelector('.invalid-feedback');
    if (!existingFeedback) {
        const feedback = document.createElement('div');
        feedback.className = 'invalid-feedback';
        feedback.textContent = getValidationMessage(field);
        field.parentElement.appendChild(feedback);
    }
}

/**
 * Hide validation message
 */
function hideValidationMessage(field) {
    const feedback = field.parentElement.querySelector('.invalid-feedback');
    if (feedback && !feedback.textContent.includes('error')) {
        feedback.remove();
    }
}

/**
 * Get validation message for field
 */
function getValidationMessage(field) {
    if (field.validity.valueMissing) {
        return 'Trường này là bắt buộc.';
    } else if (field.validity.typeMismatch) {
        if (field.type === 'email') {
            return 'Vui lòng nhập địa chỉ email hợp lệ.';
        } else if (field.type === 'url') {
            return 'Vui lòng nhập URL hợp lệ.';
        }
    } else if (field.validity.patternMismatch) {
        return 'Định dạng không đúng.';
    } else if (field.validity.tooShort) {
        return `Tối thiểu ${field.minLength} ký tự.`;
    } else if (field.validity.tooLong) {
        return `Tối đa ${field.maxLength} ký tự.`;
    } else if (field.validity.rangeUnderflow) {
        return `Giá trị phải lớn hơn hoặc bằng ${field.min}.`;
    } else if (field.validity.rangeOverflow) {
        return `Giá trị phải nhỏ hơn hoặc bằng ${field.max}.`;
    }
    return 'Giá trị không hợp lệ.';
}

/**
 * Setup auto-save functionality
 */
function setupAutoSave() {
    const autoSaveForms = document.querySelectorAll('[data-auto-save]');
    
    autoSaveForms.forEach(function(form) {
        const inputs = form.querySelectorAll('input, select, textarea');
        let saveTimeout;
        
        inputs.forEach(function(input) {
            input.addEventListener('input', function() {
                clearTimeout(saveTimeout);
                saveTimeout = setTimeout(function() {
                    autoSaveForm(form);
                }, 2000); // Save after 2 seconds of inactivity
            });
        });
    });
}

/**
 * Auto-save form data to localStorage
 */
function autoSaveForm(form) {
    const formData = new FormData(form);
    const data = {};
    
    for (let [key, value] of formData.entries()) {
        data[key] = value;
    }
    
    const formId = form.id || 'autosave-form';
    localStorage.setItem(`autosave-${formId}`, JSON.stringify(data));
    
    // Show save indicator
    showAutoSaveIndicator();
}

/**
 * Show auto-save indicator
 */
function showAutoSaveIndicator() {
    let indicator = document.querySelector('.autosave-indicator');
    if (!indicator) {
        indicator = document.createElement('div');
        indicator.className = 'autosave-indicator position-fixed bottom-0 end-0 m-3 p-2 bg-success text-white rounded';
        indicator.innerHTML = '<i class="fas fa-save me-1"></i>Đã lưu tự động';
        document.body.appendChild(indicator);
    }
    
    indicator.style.display = 'block';
    setTimeout(function() {
        indicator.style.display = 'none';
    }, 2000);
}

/**
 * Setup file upload preview
 */
function setupFileUploadPreview() {
    const fileInputs = document.querySelectorAll('input[type="file"]');
    
    fileInputs.forEach(function(input) {
        input.addEventListener('change', function() {
            showFilePreview(input);
        });
    });
}

/**
 * Show file preview
 */
function showFilePreview(input) {
    const files = input.files;
    const previewContainer = input.parentElement.querySelector('.file-preview') || createPreviewContainer(input);
    
    previewContainer.innerHTML = '';
    
    Array.from(files).forEach(function(file, index) {
        const preview = createFilePreviewElement(file, index);
        previewContainer.appendChild(preview);
    });
}

/**
 * Create preview container
 */
function createPreviewContainer(input) {
    const container = document.createElement('div');
    container.className = 'file-preview mt-2';
    input.parentElement.appendChild(container);
    return container;
}

/**
 * Create file preview element
 */
function createFilePreviewElement(file, index) {
    const preview = document.createElement('div');
    preview.className = 'file-preview-item d-flex align-items-center p-2 border rounded mb-2';
    
    const icon = getFileIcon(file.type);
    const size = formatFileSize(file.size);
    
    preview.innerHTML = `
        <i class="fas fa-${icon} me-2 text-primary"></i>
        <div class="flex-grow-1">
            <div class="fw-bold">${file.name}</div>
            <small class="text-muted">${size}</small>
        </div>
        <button type="button" class="btn btn-sm btn-outline-danger" onclick="removeFilePreview(this, ${index})">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    // Image preview
    if (file.type.startsWith('image/')) {
        const reader = new FileReader();
        reader.onload = function(e) {
            const img = document.createElement('img');
            img.src = e.target.result;
            img.className = 'file-thumbnail me-2';
            img.style.width = '50px';
            img.style.height = '50px';
            img.style.objectFit = 'cover';
            img.style.borderRadius = '4px';
            preview.insertBefore(img, preview.firstChild);
        };
        reader.readAsDataURL(file);
    }
    
    return preview;
}

/**
 * Get file icon based on type
 */
function getFileIcon(fileType) {
    if (fileType.startsWith('image/')) return 'image';
    if (fileType.startsWith('video/')) return 'video';
    if (fileType.includes('pdf')) return 'file-pdf';
    if (fileType.includes('word')) return 'file-word';
    if (fileType.includes('excel')) return 'file-excel';
    return 'file';
}

/**
 * Format file size
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * Remove file preview
 */
function removeFilePreview(button, index) {
    const previewItem = button.closest('.file-preview-item');
    const fileInput = previewItem.closest('.mb-3, .mb-4').querySelector('input[type="file"]');
    
    // Remove preview
    previewItem.remove();
    
    // Clear file input if this was the only file
    const remainingPreviews = previewItem.parentElement.children.length;
    if (remainingPreviews === 0) {
        fileInput.value = '';
    }
}

/**
 * Setup tooltips
 */
function setupTooltips() {
    // Add tooltips to buttons without text
    const iconButtons = document.querySelectorAll('button i.fas, a i.fas');
    iconButtons.forEach(function(icon) {
        const button = icon.parentElement;
        if (!button.getAttribute('title') && !button.getAttribute('data-bs-original-title')) {
            const tooltip = getButtonTooltip(icon.className);
            if (tooltip) {
                button.setAttribute('title', tooltip);
                button.setAttribute('data-bs-toggle', 'tooltip');
                new bootstrap.Tooltip(button);
            }
        }
    });
}

/**
 * Get tooltip text for button icons
 */
function getButtonTooltip(iconClass) {
    const tooltips = {
        'fa-edit': 'Chỉnh sửa',
        'fa-trash': 'Xóa',
        'fa-eye': 'Xem chi tiết',
        'fa-download': 'Tải xuống',
        'fa-print': 'In',
        'fa-share': 'Chia sẻ',
        'fa-save': 'Lưu',
        'fa-plus': 'Thêm mới',
        'fa-search': 'Tìm kiếm',
        'fa-filter': 'Lọc',
        'fa-refresh': 'Làm mới',
        'fa-upload': 'Tải lên'
    };
    
    for (let iconName in tooltips) {
        if (iconClass.includes(iconName)) {
            return tooltips[iconName];
        }
    }
    return null;
}

/**
 * Setup confirmation dialogs
 */
function setupConfirmations() {
    const confirmButtons = document.querySelectorAll('[data-confirm]');
    
    confirmButtons.forEach(function(button) {
        button.addEventListener('click', function(e) {
            const message = button.getAttribute('data-confirm');
            if (!confirm(message)) {
                e.preventDefault();
                return false;
            }
        });
    });
}

/**
 * Setup table sorting
 */
function setupTableSorting() {
    const sortableHeaders = document.querySelectorAll('th[data-sort]');
    
    sortableHeaders.forEach(function(header) {
        header.style.cursor = 'pointer';
        header.addEventListener('click', function() {
            sortTable(header);
        });
        
        // Add sort icon
        if (!header.querySelector('.sort-icon')) {
            const icon = document.createElement('i');
            icon.className = 'fas fa-sort sort-icon ms-1';
            header.appendChild(icon);
        }
    });
}

/**
 * Sort table by column
 */
function sortTable(header) {
    const table = header.closest('table');
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    const columnIndex = Array.from(header.parentElement.children).indexOf(header);
    const sortType = header.getAttribute('data-sort');
    
    // Determine sort direction
    const currentSort = header.getAttribute('data-sort-direction') || 'asc';
    const newSort = currentSort === 'asc' ? 'desc' : 'asc';
    
    // Clear all sort indicators
    table.querySelectorAll('th .sort-icon').forEach(function(icon) {
        icon.className = 'fas fa-sort sort-icon ms-1';
    });
    
    // Set new sort indicator
    const icon = header.querySelector('.sort-icon');
    icon.className = `fas fa-sort-${newSort === 'asc' ? 'up' : 'down'} sort-icon ms-1`;
    header.setAttribute('data-sort-direction', newSort);
    
    // Sort rows
    rows.sort(function(a, b) {
        const aValue = getCellValue(a, columnIndex, sortType);
        const bValue = getCellValue(b, columnIndex, sortType);
        
        if (sortType === 'number') {
            return newSort === 'asc' ? aValue - bValue : bValue - aValue;
        } else if (sortType === 'date') {
            return newSort === 'asc' ? 
                new Date(aValue) - new Date(bValue) : 
                new Date(bValue) - new Date(aValue);
        } else {
            return newSort === 'asc' ? 
                aValue.localeCompare(bValue, 'vi') : 
                bValue.localeCompare(aValue, 'vi');
        }
    });
    
    // Reorder table rows
    rows.forEach(function(row) {
        tbody.appendChild(row);
    });
}

/**
 * Get cell value for sorting
 */
function getCellValue(row, columnIndex, sortType) {
    const cell = row.children[columnIndex];
    let value = cell.textContent.trim();
    
    if (sortType === 'number') {
        return parseFloat(value.replace(/[^\d.-]/g, '')) || 0;
    } else if (sortType === 'date') {
        return value;
    } else {
        return value.toLowerCase();
    }
}

/**
 * Setup print handlers
 */
function setupPrintHandlers() {
    const printButtons = document.querySelectorAll('[data-print]');
    
    printButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            const target = button.getAttribute('data-print');
            printElement(target);
        });
    });
}

/**
 * Print specific element
 */
function printElement(selector) {
    const element = document.querySelector(selector);
    if (!element) return;
    
    const printWindow = window.open('', '_blank');
    printWindow.document.write(`
        <!DOCTYPE html>
        <html>
        <head>
            <title>In - UBND Xã</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
            <style>
                body { font-family: 'Times New Roman', serif; }
                @media print {
                    .no-print { display: none !important; }
                }
            </style>
        </head>
        <body>
            <div class="container">
                ${element.outerHTML}
            </div>
        </body>
        </html>
    `);
    printWindow.document.close();
    printWindow.print();
}

/**
 * Setup mobile menu
 */
function setupMobileMenu() {
    // Enhanced mobile navigation
    const navbar = document.querySelector('.navbar');
    if (navbar) {
        let lastScrollTop = 0;
        window.addEventListener('scroll', function() {
            const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
            if (scrollTop > lastScrollTop && scrollTop > 100) {
                navbar.style.transform = 'translateY(-100%)';
            } else {
                navbar.style.transform = 'translateY(0)';
            }
            lastScrollTop = scrollTop;
        });
    }
}

/**
 * Setup simple tab switching for pages using .btn-tab[data-tab]
 * Each pane should have id: `tab-<name>` matching data-tab.
 */
function setupTabs() {
    const tabButtons = document.querySelectorAll('.btn-tab[data-tab]');
    if (!tabButtons.length) return; // no tabs on page

    const tabNames = Array.from(tabButtons).map(btn => btn.dataset.tab);
    const panes = tabNames
        .map(name => document.getElementById(`tab-${name}`))
        .filter(pane => pane);

    function showTab(name) {
        panes.forEach(pane => {
            const isTarget = pane.id === `tab-${name}`;
            pane.classList.toggle('d-none', !isTarget);
        });

        tabButtons.forEach(btn => {
            const active = btn.dataset.tab === name;
            btn.classList.toggle('btn-primary', active);
            btn.classList.toggle('btn-outline-primary', !active);
        });
    }

    // Default: use the first button as initial tab
    const defaultName = tabButtons[0].dataset.tab;
    showTab(defaultName);

    // Bind click handlers
    tabButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            showTab(this.dataset.tab);
        });
    });
}

/**
 * Utility Functions
 */

/**
 * Show loading spinner
 */
function showLoading(element) {
    const loader = document.createElement('div');
    loader.className = 'text-center p-3 loading-spinner';
    loader.innerHTML = '<div class="spinner-border text-primary" role="status"><span class="visually-hidden">Đang tải...</span></div>';
    
    if (typeof element === 'string') {
        element = document.querySelector(element);
    }
    
    element.appendChild(loader);
    return loader;
}

/**
 * Hide loading spinner
 */
function hideLoading(element) {
    if (typeof element === 'string') {
        element = document.querySelector(element);
    }
    
    const loader = element.querySelector('.loading-spinner');
    if (loader) {
        loader.remove();
    }
}

/**
 * Show toast notification
 */
function showToast(message, type = 'info') {
    const toastContainer = getOrCreateToastContainer();
    const toast = createToast(message, type);
    
    toastContainer.appendChild(toast);
    
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    // Remove toast after it's hidden
    toast.addEventListener('hidden.bs.toast', function() {
        toast.remove();
    });
}

/**
 * Get or create toast container
 */
function getOrCreateToastContainer() {
    let container = document.querySelector('.toast-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container position-fixed top-0 end-0 p-3';
        document.body.appendChild(container);
    }
    return container;
}

/**
 * Create toast element
 */
function createToast(message, type) {
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.setAttribute('role', 'alert');
    
    const iconMap = {
        'success': 'check-circle',
        'error': 'exclamation-triangle',
        'warning': 'exclamation-circle',
        'info': 'info-circle'
    };
    
    const colorMap = {
        'success': 'success',
        'error': 'danger',
        'warning': 'warning',
        'info': 'info'
    };
    
    toast.innerHTML = `
        <div class="toast-header">
            <i class="fas fa-${iconMap[type]} text-${colorMap[type]} me-2"></i>
            <strong class="me-auto">UBND Xã</strong>
            <button type="button" class="btn-close" data-bs-dismiss="toast"></button>
        </div>
        <div class="toast-body">
            ${message}
        </div>
    `;
    
    return toast;
}

/**
 * Format Vietnamese date
 */
function formatVietnameseDate(date) {
    if (!date) return '';
    
    const d = new Date(date);
    const day = d.getDate().toString().padStart(2, '0');
    const month = (d.getMonth() + 1).toString().padStart(2, '0');
    const year = d.getFullYear();
    
    return `${day}/${month}/${year}`;
}

/**
 * Format Vietnamese currency
 */
function formatVietnameseCurrency(amount) {
    return new Intl.NumberFormat('vi-VN', {
        style: 'currency',
        currency: 'VND'
    }).format(amount);
}

/**
 * Validate Vietnamese phone number
 */
function validateVietnamesePhone(phone) {
    const phoneRegex = /^(\+84|84|0)(3[2-9]|5[689]|7[06-9]|8[1-689]|9[0-46-9])[0-9]{7}$/;
    return phoneRegex.test(phone.replace(/\s/g, ''));
}

/**
 * Validate Vietnamese ID number (CMND/CCCD)
 */
function validateVietnameseID(id) {
    // CMND: 9 digits, CCCD: 12 digits
    const idRegex = /^(\d{9}|\d{12})$/;
    return idRegex.test(id.replace(/\s/g, ''));
}

// Export functions for use in other scripts
window.UBNDSystem = {
    showLoading,
    hideLoading,
    showToast,
    formatVietnameseDate,
    formatVietnameseCurrency,
    validateVietnamesePhone,
    validateVietnameseID,
    performSearch,
    sortTable,
    printElement
};

// Console message
console.log('🏛️ Hệ thống Chuyển đổi Số UBND Xã đã sẵn sàng!');
