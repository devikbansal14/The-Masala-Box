/**
 * REFACTORED E-COMMERCE CORE
 * Improvements: Event Delegation, Optimistic Formatting, 
 * Error Handling, and Security.
 */

// State management
let products = [];
let cart = [];

// DOM Elements
const signatureProductsGrid = document.getElementById('signature-products');
const singleOriginProductsGrid = document.getElementById('single-origin-products');
const cartBtn = document.getElementById('cart-btn');
const cartBadge = document.getElementById('cart-badge');
const cartSidebar = document.getElementById('cart-sidebar');
const cartClose = document.getElementById('cart-close');
const cartItems = document.getElementById('cart-items');
const cartFooter = document.getElementById('cart-footer');
const totalAmount = document.getElementById('total-amount');
const productModal = document.getElementById('product-modal');
const modalOverlay = document.getElementById('modal-overlay');
const modalClose = document.getElementById('modal-close');
const modalBody = document.getElementById('modal-body');
const hamburger = document.getElementById('hamburger');
const nav = document.getElementById('nav');
const searchBtn = document.querySelector('.search-btn');
const searchModal = document.getElementById('search-modal');
const searchInput = document.getElementById('search-input');
const searchResults = document.getElementById('search-results');
const searchClose = document.getElementById('search-close');
const searchModalOverlay = document.getElementById('search-modal-overlay');
const contactModal = document.getElementById('contact-modal');
const contactClose = document.getElementById('contact-close');
const contactModalOverlay = document.getElementById('contact-modal-overlay');
const contactForm = document.getElementById('contact-form');
const contactLink = document.getElementById('contact-link');
const currencySelect = document.getElementById('currency-select');

// Auth elements
const authBtn = document.getElementById('auth-btn');
const authModal = document.getElementById('auth-modal');
const authClose = document.getElementById('auth-close');
const authModalOverlay = document.getElementById('auth-modal-overlay');
const authTabs = document.querySelectorAll('.auth-tab');
const loginForm = document.getElementById('login-form');
const signupForm = document.getElementById('signup-form');
const loggedInView = document.getElementById('logged-in-view');
const logoutBtn = document.getElementById('logout-btn');
const authUserName = document.getElementById('auth-user-name');

// Current user state
let currentUser = null;
let userAddresses = [];
let selectedAddressId = null;
// --- DYNAMIC CURRENCY CONFIGURATION ---
const currencyConfig = {
    'IN': { code: 'INR', symbol: '₹', locale: 'en-IN', rate: 1 },
    'US': { code: 'USD', symbol: '$', locale: 'en-US', rate: 0.012 }, // 1 INR = 0.012 USD
    'GB': { code: 'GBP', symbol: '£', locale: 'en-GB', rate: 0.0095 } // 1 INR = 0.0095 GBP
};

// Default to INR
let currentCurrency = currencyConfig['IN'];

// Get formatter for current currency
function getCurrencyFormatter() {
    return new Intl.NumberFormat(currentCurrency.locale, {
        style: 'currency',
        currency: currentCurrency.code,
        minimumFractionDigits: currentCurrency.code === 'INR' ? 0 : 2,
        maximumFractionDigits: 2
    });
}

let currencyFormatter = getCurrencyFormatter();

// Convert price from INR to selected currency
function convertPrice(priceInINR) {
    return priceInINR * currentCurrency.rate;
}

// Format price with currency conversion
function formatPrice(priceInINR) {
    const convertedPrice = convertPrice(priceInINR);
    return currencyFormatter.format(convertedPrice);
}

// Change currency
function changeCurrency(countryCode) {
    if (currencyConfig[countryCode]) {
        currentCurrency = currencyConfig[countryCode];
        currencyFormatter = getCurrencyFormatter();
        // Re-render products and cart with new currency
        renderProducts();
        updateCartUI();
    }
}


// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    loadProducts();
    loadCart();
    checkAuthStatus();
    setupEventListeners();
});

// Event Listeners (Refactored for Event Delegation)
function setupEventListeners() {
    cartBtn.addEventListener('click', toggleCart);
    cartClose.addEventListener('click', toggleCart);
    modalOverlay.addEventListener('click', closeModal);
    modalClose.addEventListener('click', closeModal);
    hamburger.addEventListener('click', toggleMobileMenu);
    document.querySelector('.btn-checkout').addEventListener('click', openCheckout);
    document.getElementById('apply-token-btn')?.addEventListener('click', applyToken);
    document.getElementById('pay-now-btn')?.addEventListener('click', processPayment);

    // Search functionality
    searchBtn.addEventListener('click', openSearch);
    searchClose.addEventListener('click', closeSearch);
    searchModalOverlay.addEventListener('click', closeSearch);
    searchInput.addEventListener('input', debounce(handleSearch, 300));

    // Close search on Escape
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && searchModal.classList.contains('active')) {
            closeSearch();
        }
        if (e.key === 'Escape' && contactModal.classList.contains('active')) {
            closeContact();
        }
    });

    // Contact modal
    contactLink.addEventListener('click', (e) => {
        e.preventDefault();
        openContact();
    });
    contactClose.addEventListener('click', closeContact);
    contactModalOverlay.addEventListener('click', closeContact);
    contactForm.addEventListener('submit', handleContactSubmit);

    // Currency selector
    currencySelect.addEventListener('change', (e) => {
        changeCurrency(e.target.value);
    });

    // Auth modal
    authBtn.addEventListener('click', openAuthModal);
    authClose.addEventListener('click', closeAuthModal);
    authModalOverlay.addEventListener('click', closeAuthModal);

    // Auth tabs
    authTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const tabName = tab.dataset.tab;
            switchAuthTab(tabName);
        });
    });

    // Auth forms
    loginForm.addEventListener('submit', handleLogin);
    signupForm.addEventListener('submit', handleSignup);
    logoutBtn.addEventListener('click', handleLogout);

    // Forgot password
    document.getElementById('forgot-password-link').addEventListener('click', (e) => {
        e.preventDefault();
        showForgotPasswordForm();
    });
    document.getElementById('back-to-login-link').addEventListener('click', (e) => {
        e.preventDefault();
        hideForgotPasswordForm();
    });
    document.getElementById('forgot-password-form').addEventListener('submit', handleForgotPassword);
    document.getElementById('reset-password-form').addEventListener('submit', handleResetPassword);

    // Check for reset token in URL
    checkResetToken();

    // Address form
    document.getElementById('add-address-btn').addEventListener('click', () => showAddressForm());
    document.getElementById('cancel-address-btn').addEventListener('click', hideAddressForm);
    document.getElementById('address-form').addEventListener('submit', handleAddressSubmit);

    // Orders view
    const viewOrdersBtn = document.getElementById('view-orders-btn');
    const backToAccountBtn = document.getElementById('back-to-account');
    if (viewOrdersBtn) viewOrdersBtn.addEventListener('click', showOrdersView);
    if (backToAccountBtn) backToAccountBtn.addEventListener('click', hideOrdersView);

    // Checkout add address button
    document.getElementById('checkout-add-address-btn').addEventListener('click', () => {
        closeCheckout();
        openAuthModal();
        setTimeout(() => showAddressForm(), 100);
    });

    // Close auth modal on Escape
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && authModal.classList.contains('active')) {
            closeAuthModal();
        }
    });


// Modify your existing checkout button event listener:


    // 1. PRODUCT GRID DELEGATION
    // Listens for clicks on any grid once, instead of adding listeners to every card
    [signatureProductsGrid, singleOriginProductsGrid].forEach(grid => {
        grid.addEventListener('click', (e) => {
            const card = e.target.closest('.product-card');
            if (!card) return;
            const productId = parseInt(card.dataset.productId);

            // Handle weight button clicks
            if (e.target.classList.contains('weight-btn')) {
                const weightBtn = e.target;
                const weight = weightBtn.dataset.weight;
                const price = parseInt(weightBtn.dataset.price);

                // Update active state
                card.querySelectorAll('.weight-btn').forEach(btn => btn.classList.remove('active'));
                weightBtn.classList.add('active');

                // Update price display
                const priceEl = card.querySelector('.product-price');
                priceEl.textContent = formatPrice(price);
                priceEl.dataset.basePrice = price;

                // Update add button with selected weight
                const addBtn = card.querySelector('.btn-add');
                addBtn.dataset.selectedWeight = weight;
                return;
            }

            if (e.target.classList.contains('btn-view-ingredients')) {
                loadProductDetails(productId);
            } else if (e.target.classList.contains('btn-add')) {
                const selectedWeight = e.target.dataset.selectedWeight || '200g';
                const priceEl = card.querySelector('.product-price');
                const selectedPrice = priceEl ? parseInt(priceEl.dataset.basePrice) : null;
                addToCart(productId, selectedWeight, selectedPrice);
            }
        });
    });

    // 2. CART ITEM DELEGATION
    cartItems.addEventListener('click', (e) => {
        const btn = e.target.closest('button');
        if (!btn) return;

        const productId = parseInt(btn.dataset.productId);
        const weight = btn.dataset.weight || '200g';

        if (btn.classList.contains('qty-decrease')) {
            updateCartItem(productId, 'decrease', weight);
        } else if (btn.classList.contains('qty-increase')) {
            updateCartItem(productId, 'increase', weight);
        } else if (btn.classList.contains('remove-btn')) {
            removeFromCart(productId, weight);
        }
    });

    // 3. MODAL DELEGATION (Fixes inline onclick security issue)
    modalBody.addEventListener('click', (e) => {
        if (e.target.classList.contains('btn-add-cart')) {
            const productId = parseInt(e.target.dataset.productId);
            addToCart(productId);
            closeModal();
        }
    });

    // Navigation and Scroll logic
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const target = document.querySelector(link.getAttribute('href'));
            if (target) {
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
                if (nav.classList.contains('active')) toggleMobileMenu();
            }
        });
    });
}

// Utility: Debounce function
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// UI Toggles
function toggleMobileMenu() {
    nav.classList.toggle('active');
    hamburger.classList.toggle('active');
}

function toggleCart() {
    cartSidebar.classList.toggle('active');
}

// Search Functions
function openSearch() {
    searchModal.classList.add('active');
    searchInput.focus();
    document.body.style.overflow = 'hidden';
}

function closeSearch() {
    searchModal.classList.remove('active');
    searchInput.value = '';
    searchResults.innerHTML = '';
    document.body.style.overflow = '';
}

// Auth Functions
function openAuthModal() {
    authModal.classList.add('active');
    document.body.style.overflow = 'hidden';
    updateAuthModalView();
}

function closeAuthModal() {
    authModal.classList.remove('active');
    document.body.style.overflow = '';
    // Clear errors
    document.getElementById('login-error').textContent = '';
    document.getElementById('signup-error').textContent = '';
}

function switchAuthTab(tabName) {
    authTabs.forEach(t => t.classList.remove('active'));
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

    if (tabName === 'login') {
        loginForm.style.display = 'flex';
        signupForm.style.display = 'none';
        document.getElementById('auth-title').textContent = 'Welcome Back';
    } else {
        loginForm.style.display = 'none';
        signupForm.style.display = 'flex';
        document.getElementById('auth-title').textContent = 'Create Account';
    }
}

function updateAuthModalView() {
    if (currentUser) {
        // Show logged in view
        loginForm.style.display = 'none';
        signupForm.style.display = 'none';
        document.querySelector('.auth-tabs').style.display = 'none';
        document.getElementById('address-form-view').style.display = 'none';
        loggedInView.style.display = 'block';
        document.getElementById('auth-title').textContent = 'Your Account';
        document.getElementById('user-display-name').textContent = currentUser.name;
        document.getElementById('user-display-email').textContent = currentUser.email;
        loadAddresses();
    } else {
        // Show login form
        document.querySelector('.auth-tabs').style.display = 'flex';
        loggedInView.style.display = 'none';
        document.getElementById('address-form-view').style.display = 'none';
        switchAuthTab('login');
    }
}

function updateAuthUI() {
    if (currentUser) {
        authUserName.textContent = currentUser.name.split(' ')[0];
        authUserName.style.display = 'inline';
    } else {
        authUserName.style.display = 'none';
    }
}

async function checkAuthStatus() {
    try {
        const response = await fetch('/api/auth/me');
        const data = await response.json();
        if (data.logged_in) {
            currentUser = data.user;
            updateAuthUI();
        }
    } catch (error) {
        console.error('Auth check failed:', error);
    }
}

async function handleLogin(e) {
    e.preventDefault();
    const errorEl = document.getElementById('login-error');
    errorEl.textContent = '';

    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;

    const submitBtn = loginForm.querySelector('button[type="submit"]');
    submitBtn.disabled = true;
    submitBtn.textContent = 'Logging in...';

    try {
        const response = await fetch('/api/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });

        const data = await response.json();

        if (data.success) {
            currentUser = data.user;
            updateAuthUI();
            updateAuthModalView();
            // Reload cart for logged in user
            await loadCart();
            showNotification(`Welcome back, ${currentUser.name}!`);
            loginForm.reset();
        } else {
            errorEl.textContent = data.error || 'Login failed';
        }
    } catch (error) {
        errorEl.textContent = 'Network error. Please try again.';
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Login';
    }
}

async function handleSignup(e) {
    e.preventDefault();
    const errorEl = document.getElementById('signup-error');
    errorEl.textContent = '';

    const name = document.getElementById('signup-name').value;
    const email = document.getElementById('signup-email').value;
    const phone = document.getElementById('signup-phone').value;
    const password = document.getElementById('signup-password').value;

    const submitBtn = signupForm.querySelector('button[type="submit"]');
    submitBtn.disabled = true;
    submitBtn.textContent = 'Creating account...';

    try {
        const response = await fetch('/api/auth/signup', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, email, phone, password })
        });

        const data = await response.json();

        if (data.success) {
            currentUser = data.user;
            updateAuthUI();
            updateAuthModalView();
            // Load cart for newly signed up user (will be empty)
            await loadCart();
            showNotification(`Welcome, ${currentUser.name}! Account created.`);
            signupForm.reset();
        } else {
            errorEl.textContent = data.error || 'Signup failed';
        }
    } catch (error) {
        errorEl.textContent = 'Network error. Please try again.';
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Create Account';
    }
}

async function handleLogout() {
    try {
        await fetch('/api/auth/logout', { method: 'POST' });
        currentUser = null;
        userAddresses = [];
        // Clear cart on logout
        cart = [];
        updateCartUI();
        updateAuthUI();
        closeAuthModal();
        showNotification('Logged out successfully');
    } catch (error) {
        showNotification('Logout failed');
    }
}

// Forgot Password Functions
function showForgotPasswordForm() {
    document.querySelector('.auth-tabs').style.display = 'none';
    loginForm.style.display = 'none';
    signupForm.style.display = 'none';
    document.getElementById('forgot-password-form').style.display = 'flex';
    document.getElementById('auth-title').textContent = 'Reset Password';
    document.getElementById('forgot-error').textContent = '';
    document.getElementById('forgot-success').textContent = '';
}

function hideForgotPasswordForm() {
    document.querySelector('.auth-tabs').style.display = 'flex';
    document.getElementById('forgot-password-form').style.display = 'none';
    switchAuthTab('login');
}

async function handleForgotPassword(e) {
    e.preventDefault();
    const errorEl = document.getElementById('forgot-error');
    const successEl = document.getElementById('forgot-success');
    errorEl.textContent = '';
    successEl.textContent = '';

    const email = document.getElementById('forgot-email').value;
    const submitBtn = e.target.querySelector('button[type="submit"]');
    submitBtn.disabled = true;
    submitBtn.textContent = 'Sending...';

    try {
        const response = await fetch('/api/auth/forgot-password', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email })
        });

        const data = await response.json();

        if (data.success) {
            successEl.textContent = data.message;
            // For testing, show the debug token if available
            if (data.debug_token) {
                successEl.innerHTML += `<br><br><small style="color: var(--text-muted);">Debug: <a href="#" onclick="showResetForm('${data.debug_token}'); return false;">Click here to reset</a></small>`;
            }
            document.getElementById('forgot-email').value = '';
        } else {
            errorEl.textContent = data.error || 'Failed to send reset link';
        }
    } catch (error) {
        errorEl.textContent = 'Network error. Please try again.';
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Send Reset Link';
    }
}

function showResetForm(token) {
    document.querySelector('.auth-tabs').style.display = 'none';
    loginForm.style.display = 'none';
    signupForm.style.display = 'none';
    document.getElementById('forgot-password-form').style.display = 'none';
    document.getElementById('reset-password-form').style.display = 'flex';
    document.getElementById('auth-title').textContent = 'Set New Password';
    document.getElementById('reset-token').value = token;
    document.getElementById('reset-error').textContent = '';
    document.getElementById('reset-success').textContent = '';
}

async function handleResetPassword(e) {
    e.preventDefault();
    const errorEl = document.getElementById('reset-error');
    const successEl = document.getElementById('reset-success');
    errorEl.textContent = '';
    successEl.textContent = '';

    const password = document.getElementById('reset-password').value;
    const confirmPassword = document.getElementById('reset-password-confirm').value;
    const token = document.getElementById('reset-token').value;

    if (password !== confirmPassword) {
        errorEl.textContent = 'Passwords do not match';
        return;
    }

    const submitBtn = e.target.querySelector('button[type="submit"]');
    submitBtn.disabled = true;
    submitBtn.textContent = 'Resetting...';

    try {
        const response = await fetch('/api/auth/reset-password', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ token, password })
        });

        const data = await response.json();

        if (data.success) {
            successEl.textContent = data.message;
            // After 2 seconds, redirect to login
            setTimeout(() => {
                document.getElementById('reset-password-form').style.display = 'none';
                document.querySelector('.auth-tabs').style.display = 'flex';
                switchAuthTab('login');
                // Clear URL parameters
                window.history.replaceState({}, document.title, window.location.pathname);
            }, 2000);
        } else {
            errorEl.textContent = data.error || 'Failed to reset password';
        }
    } catch (error) {
        errorEl.textContent = 'Network error. Please try again.';
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Reset Password';
    }
}

function checkResetToken() {
    const urlParams = new URLSearchParams(window.location.search);
    const token = urlParams.get('token');
    if (token) {
        // Open auth modal and show reset form
        openAuthModal();
        showResetForm(token);
    }
}

// Address Management Functions
async function loadAddresses() {
    if (!currentUser) return;

    try {
        const response = await fetch('/api/addresses');
        const data = await response.json();
        if (data.success) {
            userAddresses = data.addresses;
            renderAddressList();
        }
    } catch (error) {
        console.error('Failed to load addresses:', error);
    }
}

function renderAddressList() {
    const container = document.getElementById('addresses-list');
    if (!container) return;

    if (userAddresses.length === 0) {
        container.innerHTML = '<p class="no-addresses">No saved addresses yet</p>';
        return;
    }

    container.innerHTML = userAddresses.map(addr => `
        <div class="address-card" data-address-id="${addr.id}">
            <div class="address-card-header">
                <span class="address-label">
                    ${addr.label}
                    ${addr.is_default ? '<span class="address-default-badge">Default</span>' : ''}
                </span>
                <div class="address-actions">
                    <button class="address-action-btn edit-address" data-id="${addr.id}" title="Edit">
                        <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M11.5 2.5L13.5 4.5M2 14L2.5 11.5L12 2L14 4L4.5 13.5L2 14Z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
                    </button>
                    <button class="address-action-btn delete delete-address" data-id="${addr.id}" title="Delete">
                        <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M4 5H12M6 7V11M10 7V11M5 5L6 13H10L11 5M7 3H9" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
                    </button>
                </div>
            </div>
            <div class="address-name">${addr.full_name}</div>
            <div class="address-text">${addr.address_line1}${addr.address_line2 ? ', ' + addr.address_line2 : ''}</div>
            <div class="address-text">${addr.city}, ${addr.state} - ${addr.pincode}</div>
            <div class="address-phone">Phone: ${addr.phone}</div>
        </div>
    `).join('');

    // Add event listeners for edit/delete
    container.querySelectorAll('.edit-address').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            editAddress(parseInt(btn.dataset.id));
        });
    });

    container.querySelectorAll('.delete-address').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            deleteAddress(parseInt(btn.dataset.id));
        });
    });
}

function showAddressForm(address = null) {
    const loggedInView = document.getElementById('logged-in-view');
    const addressFormView = document.getElementById('address-form-view');
    const formTitle = document.querySelector('.address-form-title');
    const form = document.getElementById('address-form');

    loggedInView.style.display = 'none';
    addressFormView.style.display = 'block';

    if (address) {
        formTitle.textContent = 'Edit Address';
        document.getElementById('addr-id').value = address.id;
        document.getElementById('addr-label').value = address.label;
        document.getElementById('addr-name').value = address.full_name;
        document.getElementById('addr-phone').value = address.phone;
        document.getElementById('addr-line1').value = address.address_line1;
        document.getElementById('addr-line2').value = address.address_line2 || '';
        document.getElementById('addr-city').value = address.city;
        document.getElementById('addr-state').value = address.state;
        document.getElementById('addr-pincode').value = address.pincode;
        document.getElementById('addr-default').checked = address.is_default;
    } else {
        formTitle.textContent = 'Add New Address';
        form.reset();
        document.getElementById('addr-id').value = '';
    }
}

function hideAddressForm() {
    document.getElementById('logged-in-view').style.display = 'block';
    document.getElementById('address-form-view').style.display = 'none';
    document.getElementById('address-error').textContent = '';
}

function editAddress(addressId) {
    const address = userAddresses.find(a => a.id === addressId);
    if (address) {
        showAddressForm(address);
    }
}

async function deleteAddress(addressId) {
    if (!confirm('Are you sure you want to delete this address?')) return;

    try {
        const response = await fetch(`/api/addresses/${addressId}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            showNotification('Address deleted');
            await loadAddresses();
        } else {
            showNotification('Failed to delete address');
        }
    } catch (error) {
        showNotification('Network error');
    }
}

async function handleAddressSubmit(e) {
    e.preventDefault();
    const errorEl = document.getElementById('address-error');
    errorEl.textContent = '';

    const form = e.target;
    const addressId = document.getElementById('addr-id').value;
    const isEdit = !!addressId;

    const data = {
        label: document.getElementById('addr-label').value,
        full_name: document.getElementById('addr-name').value,
        phone: document.getElementById('addr-phone').value,
        address_line1: document.getElementById('addr-line1').value,
        address_line2: document.getElementById('addr-line2').value,
        city: document.getElementById('addr-city').value,
        state: document.getElementById('addr-state').value,
        pincode: document.getElementById('addr-pincode').value,
        is_default: document.getElementById('addr-default').checked
    };

    const submitBtn = form.querySelector('button[type="submit"]');
    submitBtn.disabled = true;
    submitBtn.textContent = 'Saving...';

    try {
        const url = isEdit ? `/api/addresses/${addressId}` : '/api/addresses';
        const method = isEdit ? 'PUT' : 'POST';

        const response = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (result.success) {
            showNotification(isEdit ? 'Address updated' : 'Address added');
            await loadAddresses();
            hideAddressForm();
        } else {
            errorEl.textContent = result.error || 'Failed to save address';
        }
    } catch (error) {
        errorEl.textContent = 'Network error. Please try again.';
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Save Address';
    }
}

// Checkout address functions
function renderCheckoutAddresses() {
    const container = document.getElementById('checkout-addresses');
    if (!container) return;

    if (userAddresses.length === 0) {
        container.innerHTML = '<p class="no-addresses">No saved addresses. Please add one.</p>';
        return;
    }

    // Set default selected address
    if (!selectedAddressId) {
        const defaultAddr = userAddresses.find(a => a.is_default);
        selectedAddressId = defaultAddr ? defaultAddr.id : userAddresses[0].id;
    }

    container.innerHTML = userAddresses.map(addr => `
        <div class="checkout-address-card ${addr.id === selectedAddressId ? 'selected' : ''}" data-address-id="${addr.id}">
            <span class="address-label">
                ${addr.label}
                ${addr.is_default ? '<span class="address-default-badge">Default</span>' : ''}
            </span>
            <div class="address-name">${addr.full_name}</div>
            <div class="address-text">${addr.address_line1}${addr.address_line2 ? ', ' + addr.address_line2 : ''}, ${addr.city}, ${addr.state} - ${addr.pincode}</div>
            <div class="address-phone">Phone: ${addr.phone}</div>
        </div>
    `).join('');

    // Add click handlers for selection
    container.querySelectorAll('.checkout-address-card').forEach(card => {
        card.addEventListener('click', () => {
            selectedAddressId = parseInt(card.dataset.addressId);
            container.querySelectorAll('.checkout-address-card').forEach(c => c.classList.remove('selected'));
            card.classList.add('selected');
        });
    });
}

// Contact Functions
function openContact() {
    contactModal.classList.add('active');
    document.body.style.overflow = 'hidden';
}

function closeContact() {
    contactModal.classList.remove('active');
    document.body.style.overflow = '';
    // Reset form and hide success message after closing
    setTimeout(() => {
        contactForm.reset();
        contactForm.style.display = '';
        document.getElementById('contact-success').style.display = 'none';
    }, 300);
}

async function handleContactSubmit(e) {
    e.preventDefault();

    const formData = new FormData(contactForm);
    const data = Object.fromEntries(formData);

    // Disable submit button while sending
    const submitBtn = contactForm.querySelector('button[type="submit"]');
    const originalText = submitBtn.textContent;
    submitBtn.disabled = true;
    submitBtn.textContent = 'Sending...';

    try {
        const response = await fetch('/api/contact', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (result.success) {
            // Show success message
            contactForm.style.display = 'none';
            document.getElementById('contact-success').style.display = 'block';
            // Auto close after 3 seconds
            setTimeout(closeContact, 3000);
        } else {
            showNotification(result.error || 'Failed to send message');
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
        }
    } catch (error) {
        showNotification('Network error. Please try WhatsApp instead.');
        submitBtn.disabled = false;
        submitBtn.textContent = originalText;
    }
}

function handleSearch() {
    const query = searchInput.value.toLowerCase().trim();

    if (!query) {
        searchResults.innerHTML = '';
        return;
    }

    const results = products.filter(product => {
        const nameMatch = product.name.toLowerCase().includes(query);
        const subtitleMatch = product.subtitle.toLowerCase().includes(query);
        const categoryMatch = product.category.toLowerCase().includes(query);
        const taglineMatch = (product.tagline || '').toLowerCase().includes(query);
        const descriptionMatch = (product.description || '').toLowerCase().includes(query);

        return nameMatch || subtitleMatch || categoryMatch || taglineMatch || descriptionMatch;
    });

    if (results.length === 0) {
        searchResults.innerHTML = '<div class="search-no-results">No products found</div>';
        return;
    }

    searchResults.innerHTML = results.map(product => `
        <div class="search-result-item" data-product-id="${product.id}">
            <img src="${product.image_url}" alt="${product.name}" class="search-result-image">
            <div class="search-result-info">
                <div class="search-result-name">${product.name}</div>
                <div class="search-result-category">${product.subtitle}</div>
            </div>
            <span class="search-result-price">${formatPrice(product.price)}</span>
        </div>
    `).join('');

    // Add click handlers to search results
    searchResults.querySelectorAll('.search-result-item').forEach(item => {
        item.addEventListener('click', () => {
            const productId = parseInt(item.dataset.productId);
            const product = products.find(p => p.id === productId);
            closeSearch();
            if (product) {
                loadProductDetails(productId);
            }
        });
    });
}

async function openCheckout() {
    const checkoutView = document.getElementById('checkout-view');
    const summaryDiv = document.getElementById('checkout-summary-details');
    const loginPrompt = document.getElementById('checkout-login-prompt');
    const checkoutContent = document.getElementById('checkout-content');

    document.getElementById('cart-sidebar').classList.remove('active');

    // Check if user is logged in
    if (!currentUser) {
        loginPrompt.style.display = 'block';
        checkoutContent.style.display = 'none';
        checkoutView.style.display = 'flex';
        return;
    }

    loginPrompt.style.display = 'none';
    checkoutContent.style.display = 'block';

    // Load addresses if not loaded
    if (userAddresses.length === 0) {
        await loadAddresses();
    }
    renderCheckoutAddresses();

    let subtotal = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);

    // Delivery logic: free shipping above 500 INR
    let deliveryThreshold = 500;
    let deliveryFeeAmount = 50;
    let delivery = (subtotal >= deliveryThreshold || subtotal === 0) ? 0 : deliveryFeeAmount;
    let total = subtotal + delivery;

    // Reset promo input
    const tokenInput = document.getElementById('promo-token');
    const applyBtn = document.getElementById('apply-token-btn');
    const tokenStatus = document.getElementById('token-status');
    if (tokenInput) {
        tokenInput.disabled = false;
        tokenInput.value = '';
    }
    if (applyBtn) applyBtn.disabled = false;
    if (tokenStatus) tokenStatus.innerText = '';

    summaryDiv.innerHTML = `
        <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
            <span>Subtotal</span>
            <span>${formatPrice(subtotal)}</span>
        </div>
        <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
            <span>Delivery</span>
            <span>${delivery === 0 ? 'FREE' : formatPrice(delivery)}</span>
        </div>
        <div style="display: flex; justify-content: space-between; margin-top: 15px; font-size: 1.2rem; font-weight: bold; color: #d4a853; border-top: 1px solid #333; padding-top: 10px;">
            <span>Total Amount</span>
            <span id="display-total">${formatPrice(total)}</span>
        </div>
    `;

    checkoutView.style.display = 'flex';
}

function closeCheckout() {
    document.getElementById('checkout-view').style.display = 'none';
}

async function applyToken() {
    const tokenInput = document.getElementById('promo-token');
    const status = document.getElementById('token-status');
    const summaryDiv = document.getElementById('checkout-summary-details');
    const applyBtn = document.getElementById('apply-token-btn');
    const code = tokenInput.value.toUpperCase().trim();

    if (!code) {
        status.innerText = "Please enter a promo code";
        status.style.color = "#ff4444";
        return;
    }

    // Disable inputs while validating
    tokenInput.disabled = true;
    applyBtn.disabled = true;
    status.innerText = "Validating...";
    status.style.color = "#999";

    try {
        // Validate promo code via API (checks if user has already used it)
        const response = await fetch('/api/promo/validate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ promo_code: code })
        });
        const data = await response.json();

        if (!data.valid) {
            status.innerText = data.error || "Invalid promo code";
            status.style.color = "#ff4444";
            tokenInput.disabled = false;
            applyBtn.disabled = false;
            return;
        }

        // Promo code is valid - apply the discount
        const promo = data;
        let subtotal = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
        let deliveryThreshold = 500;
        let deliveryFeeAmount = 50;
        let delivery = (subtotal >= deliveryThreshold || subtotal === 0) ? 0 : deliveryFeeAmount;

        let discount = promo.type === 'percent'
            ? subtotal * (promo.value / 100)
            : promo.value;

        discount = Math.min(discount, subtotal);
        let newTotal = subtotal - discount + delivery;

        summaryDiv.innerHTML = `
            <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                <span>Subtotal</span>
                <span>${formatPrice(subtotal)}</span>
            </div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 10px; color: #4CAF50; font-weight: bold;">
                <span>Discount ${promo.type === 'percent' ? `(${promo.value}%)` : ''}</span>
                <span>-${formatPrice(discount)}</span>
            </div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                <span>Delivery</span>
                <span>${delivery === 0 ? 'FREE' : formatPrice(delivery)}</span>
            </div>
            <div style="display: flex; justify-content: space-between; margin-top: 15px; font-size: 1.2rem; font-weight: bold; color: #d4a853; border-top: 1px solid #333; padding-top: 10px;">
                <span>Total Amount</span>
                <span id="display-total">${formatPrice(newTotal)}</span>
            </div>
        `;

        status.innerText = "Promo applied successfully!";
        status.style.color = "#4CAF50";
        // Keep inputs disabled after successful application
    } catch (error) {
        status.innerText = "Error validating promo code. Please try again.";
        status.style.color = "#ff4444";
        tokenInput.disabled = false;
        applyBtn.disabled = false;
    }
}

async function processPayment() {
    // Validate address selection
    if (!selectedAddressId) {
        showNotification('Please select a delivery address');
        return;
    }

    if (userAddresses.length === 0) {
        showNotification('Please add a delivery address first');
        return;
    }

    const payBtn = document.getElementById('pay-now-btn');
    payBtn.disabled = true;
    payBtn.textContent = 'Processing...';

    try {
        // Get promo code if applied
        const promoInput = document.getElementById('promo-token');
        const promoCode = promoInput ? promoInput.value.toUpperCase().trim() : '';

        // Step 1: Create order
        const orderResponse = await fetch('/api/orders', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                address_id: selectedAddressId,
                promo_code: promoCode
            })
        });

        const orderData = await orderResponse.json();
        if (!orderData.success) {
            throw new Error(orderData.error || 'Failed to create order');
        }

        const orderId = orderData.order.id;
        const orderNumber = orderData.order.order_number;
        const totalAmount = orderData.order.total_amount;

        // Step 2: Create payment
        const paymentResponse = await fetch('/api/payment/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ order_id: orderId })
        });

        const paymentData = await paymentResponse.json();
        if (!paymentData.success) {
            throw new Error(paymentData.error || 'Failed to create payment');
        }

        // Check if test mode
        if (paymentData.test_mode) {
            // Test mode - simulate payment
            const confirmed = confirm(`TEST MODE: Confirm payment of ${formatPrice(totalAmount)}?\n\nOrder: ${orderNumber}`);
            if (confirmed) {
                await verifyPayment(orderId, null, null, null, true);
                showOrderSuccess(orderNumber, totalAmount);
            } else {
                payBtn.disabled = false;
                payBtn.textContent = 'PAY NOW';
            }
            return;
        }

        // Step 3: Open Razorpay checkout
        const options = {
            key: paymentData.razorpay_key,
            amount: paymentData.amount,
            currency: paymentData.currency,
            name: 'The Masala Box',
            description: `Order ${orderNumber}`,
            order_id: paymentData.razorpay_order_id,
            handler: async function(response) {
                // Verify payment
                await verifyPayment(
                    orderId,
                    response.razorpay_payment_id,
                    response.razorpay_order_id,
                    response.razorpay_signature,
                    false
                );
                showOrderSuccess(orderNumber, totalAmount);
            },
            prefill: {
                name: currentUser ? currentUser.name : '',
                email: currentUser ? currentUser.email : ''
            },
            theme: {
                color: '#d4a853'
            },
            modal: {
                ondismiss: function() {
                    payBtn.disabled = false;
                    payBtn.textContent = 'PAY NOW';
                }
            }
        };

        const rzp = new Razorpay(options);
        rzp.open();

    } catch (error) {
        showNotification(error.message || 'Payment failed');
        payBtn.disabled = false;
        payBtn.textContent = 'PAY NOW';
    }
}

async function verifyPayment(orderId, paymentId, razorpayOrderId, signature, testMode) {
    const response = await fetch('/api/payment/verify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            order_id: orderId,
            razorpay_payment_id: paymentId,
            razorpay_order_id: razorpayOrderId,
            razorpay_signature: signature,
            test_mode: testMode
        })
    });

    const data = await response.json();
    if (!data.success) {
        throw new Error(data.error || 'Payment verification failed');
    }
}

function showOrderSuccess(orderNumber, totalAmount) {
    const checkoutView = document.getElementById('checkout-view');
    const modalBody = checkoutView.querySelector('.modal-body');

    modalBody.innerHTML = `
        <div class="order-success">
            <svg class="order-success-icon" viewBox="0 0 80 80" fill="none">
                <circle cx="40" cy="40" r="38" stroke="#4CAF50" stroke-width="3"/>
                <path d="M25 40L35 50L55 30" stroke="#4CAF50" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <h3>Order Placed!</h3>
            <p>Thank you for your order</p>
            <div class="order-number-display">${orderNumber}</div>
            <p>Total: ${formatPrice(totalAmount)}</p>
            <p style="margin-top: 1rem; font-size: 0.875rem;">You will receive a confirmation email shortly.</p>
            <button class="btn btn-primary" style="width: 100%; margin-top: 1.5rem;" onclick="window.location.reload();">
                Continue Shopping
            </button>
        </div>
    `;
}

// Order History Functions
async function loadOrderHistory() {
    const container = document.getElementById('orders-list');
    if (!container) return;

    container.innerHTML = '<p class="no-orders">Loading orders...</p>';

    try {
        const response = await fetch('/api/orders');
        const data = await response.json();

        if (data.success) {
            renderOrderHistory(data.orders);
        } else {
            container.innerHTML = '<p class="no-orders">Failed to load orders. Please try again.</p>';
        }
    } catch (error) {
        console.error('Failed to load orders:', error);
        container.innerHTML = '<p class="no-orders">Failed to load orders. Please try again.</p>';
    }
}

function renderOrderHistory(orders) {
    const container = document.getElementById('orders-list');
    if (!container) return;

    if (!orders || orders.length === 0) {
        container.innerHTML = '<p class="no-orders">No orders yet. Start shopping!</p>';
        return;
    }

    container.innerHTML = orders.map(order => {
        const items = order.items || [];
        const itemsPreview = items.slice(0, 2).map(i => i.product_name).join(', ') || 'Items unavailable';
        const moreItems = items.length > 2 ? ` +${items.length - 2} more` : '';
        const date = new Date(order.created_at).toLocaleDateString('en-IN', {
            day: 'numeric', month: 'short', year: 'numeric'
        });

        return `
            <div class="order-card">
                <div class="order-header">
                    <span class="order-number">${order.order_number}</span>
                    <span class="order-status ${order.order_status}">${order.order_status}</span>
                </div>
                <div class="order-date">${date}</div>
                <div class="order-items-preview">${itemsPreview}${moreItems}</div>
                <div class="order-total">${formatPrice(order.total_amount)}</div>
            </div>
        `;
    }).join('');
}

function showOrdersView() {
    document.getElementById('logged-in-view').style.display = 'none';
    document.getElementById('address-form-view').style.display = 'none';
    document.getElementById('orders-view').style.display = 'block';
    document.getElementById('auth-title').textContent = 'My Orders';
    loadOrderHistory();
}

function hideOrdersView() {
    document.getElementById('orders-view').style.display = 'none';
    document.getElementById('logged-in-view').style.display = 'block';
    document.getElementById('auth-title').textContent = 'Your Account';
}

// API Calls (Enhanced Error Handling)
async function loadProducts() {
    try {
        const response = await fetch('/api/products');
        if (!response.ok) throw new Error('Failed to fetch products');
        products = await response.json();
        renderProducts();
    } catch (error) {
        console.error('Error loading products:', error);
        showNotification('Failed to load products. Please refresh.');
    }
}

async function loadCart() {
    try {
        const response = await fetch('/api/cart');
        if (!response.ok) throw new Error('Failed to fetch cart');
        cart = await response.json();
        updateCartUI();
    } catch (error) {
        console.error('Error loading cart:', error);
    }
}

async function addToCart(productId, selectedWeight = null, selectedPrice = null) {
    try {
        const payload = { product_id: productId, quantity: 1 };
        if (selectedWeight) {
            payload.weight = selectedWeight;
        }
        if (selectedPrice) {
            payload.price_override = selectedPrice;
        }

        const response = await fetch('/api/cart/add', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (response.ok) {
            await loadCart();
            const weightText = selectedWeight ? ` (${selectedWeight})` : '';
            showNotification(`Added to cart!${weightText}`);
        } else {
            throw new Error('Could not add to cart');
        }
    } catch (error) {
        showNotification('Error adding to cart');
    }
}

async function updateCartItem(productId, action, weight = '200g') {
    try {
        const response = await fetch('/api/cart/update', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ product_id: productId, action: action, weight: weight })
        });
        if (response.ok) await loadCart();
    } catch (error) {
        console.error('Update failed');
    }
}

async function removeFromCart(productId, weight = '200g') {
    try {
        const response = await fetch('/api/cart/remove', {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ product_id: productId, weight: weight })
        });
        if (response.ok) await loadCart();
    } catch (error) {
        console.error('Remove failed');
    }
}

async function loadProductDetails(productId) {
    try {
        const response = await fetch(`/api/products/${productId}`);
        const product = await response.json();
        showProductModal(product);
    } catch (error) {
        showNotification('Error loading details');
    }
}

// Render Functions
function renderProducts() {
    const signatureBlends = products.filter(p => p.category === 'signature_blend');
    const singleOrigins = products.filter(p => p.category === 'single_origin');
    
    signatureProductsGrid.innerHTML = signatureBlends.map(product => createProductCard(product, true)).join('');
    singleOriginProductsGrid.innerHTML = singleOrigins.map(product => createProductCard(product, false)).join('');
}

function createProductCard(product, isSignature) {
    const formattedPrice = formatPrice(product.price || 0);
    if (isSignature) {
        return `
            <div class="product-card" data-product-id="${product.id}">
                <div class="product-image-wrapper">
                    <img src="${product.image_url}" alt="${product.name}" class="product-image" loading="lazy">
                    <span class="weight-badge">200g</span>
                </div>
                <div class="product-info">
                    <h3 class="product-name">${product.name}</h3>
                    <p class="product-subtitle">${product.subtitle}</p>
                    <p class="product-tagline">${product.tagline || ''}</p>
                    <p class="product-price">${formattedPrice}</p>
                    <div class="product-buttons">
                        <button class="btn btn-primary btn-small btn-add">Add to Cart</button>
                        <button class="btn btn-outline btn-small btn-view-ingredients">View Ingredients</button>
                    </div>
                </div>
            </div>`;
    } else {
        // Single origin with weight options
        const weightOptions = product.weight_options || { '200g': product.price };
        const weights = Object.keys(weightOptions);
        const defaultWeight = weights[0];
        const defaultPrice = weightOptions[defaultWeight];

        return `
            <div class="product-card single-origin-card" data-product-id="${product.id}" data-weight-options='${JSON.stringify(weightOptions)}'>
                <div class="product-image-wrapper">
                    <img src="${product.image_url}" alt="${product.name}" class="product-image" loading="lazy">
                </div>
                <div class="product-info">
                    <h3 class="product-name">${product.name}</h3>
                    <p class="product-subtitle">${product.subtitle}</p>
                    <div class="weight-selector">
                        ${weights.map((w, i) => `
                            <button class="weight-btn ${i === 0 ? 'active' : ''}" data-weight="${w}" data-price="${weightOptions[w]}">
                                ${w}
                            </button>
                        `).join('')}
                    </div>
                    <p class="product-price" data-base-price="${defaultPrice}">${formatPrice(defaultPrice)}</p>
                    <button class="btn btn-primary btn-small btn-add" data-selected-weight="${defaultWeight}">Add</button>
                </div>
            </div>`;
    }
}

function showProductModal(product) {
    const stars = '★'.repeat(product.rating || 0) + '☆'.repeat(5 - (product.rating || 0));
    const ingredients = product.ingredients?.length 
        ? product.ingredients.map(ing => `<span class="ingredient-tag">${ing}</span>`).join('') 
        : '<p class="ingredient-tag">No ingredients listed</p>';
    
    const allergyBox = product.allergy_info ? `
            <div class="allergy-box">
                <div class="allergy-text">
                    <strong>Allergy Information:</strong><br>
                    ${product.allergy_info}
                </div>
            </div>` : '';
    
    modalBody.innerHTML = `
        <div class="modal-image-wrapper">
            <img src="${product.image_url}" alt="${product.name}" class="modal-image">
        </div>
        <div class="modal-details">
            <span class="modal-label">The Masala Box</span>
            <h2 class="modal-title">${product.name} - ${product.subtitle}</h2>
            <div class="modal-rating">
                <span class="stars">${stars}</span>
                <span class="review-count">(${product.reviews || 0} reviews)</span>
            </div>
            <div class="modal-price">${formatPrice(product.price || 0)}</div>
            <p class="modal-description">${product.description || ''}</p>
            ${allergyBox}
            <button class="btn btn-primary btn-add-cart" data-product-id="${product.id}">
                Add to Cart
            </button>
            <div class="ingredients-section">
                <h3 class="ingredients-title">What's Inside</h3>
                <div class="ingredients-list">${ingredients}</div>
            </div>
        </div>`;
    
    productModal.classList.add('active');
    document.body.style.overflow = 'hidden';
}

function closeModal() {
    productModal.classList.remove('active');
    document.body.style.overflow = '';
}

// Cart UI
function updateCartUI() {
    const itemCount = cart.reduce((sum, item) => sum + item.quantity, 0);
    cartBadge.textContent = itemCount;
    
    if (cart.length === 0) {
        cartItems.innerHTML = '<div class="cart-empty"><p>Your cart is empty</p></div>';
        cartFooter.style.display = 'none';
    } else {
        cartItems.innerHTML = cart.map(item => createCartItem(item)).join('');
        cartFooter.style.display = 'block';
        const total = cart.reduce((sum, item) => sum + ((item.price || 0) * item.quantity), 0);
        totalAmount.textContent = formatPrice(total);
    }
}

function createCartItem(item) {
    const weight = item.weight || '200g';
    const weightDisplay = item.category === 'single_origin' ? ` · ${weight}` : '';
    return `
        <div class="cart-item">
            <img src="${item.image_url}" alt="${item.name}" class="cart-item-image">
            <div class="cart-item-details">
                <div class="cart-item-name">${item.name}</div>
                <div class="cart-item-subtitle">${item.subtitle}${weightDisplay}</div>
                <div class="cart-item-price">${formatPrice(item.price || 0)}</div>
                <div class="cart-item-controls">
                    <button class="qty-btn qty-decrease" data-product-id="${item.product_id}" data-weight="${weight}" aria-label="Decrease quantity">−</button>
                    <span class="qty-display">${item.quantity}</span>
                    <button class="qty-btn qty-increase" data-product-id="${item.product_id}" data-weight="${weight}" aria-label="Increase quantity">+</button>
                    <button class="remove-btn" data-product-id="${item.product_id}" data-weight="${weight}" aria-label="Remove item">
                        <svg width="20" height="20" viewBox="0 0 20 20" fill="none"><path d="M5 7H15M8 10V14M12 10V14M6 7L7 17H13L14 7M9 4H11" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
                    </button>
                </div>
            </div>
        </div>`;
}

// Notifications
function showNotification(message) {
    const notification = document.createElement('div');
    notification.className = 'toast-notification';
    notification.textContent = message;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.classList.add('fade-out');
        setTimeout(() => notification.remove(), 300);
    }, 2000);
}

// Animation Styles
const style = document.createElement('style');
style.textContent = `
    .toast-notification {
        position: fixed; top: 100px; right: 20px;
        background-color: #d4a853; color: #1a1a1a;
        padding: 1rem 1.5rem; border-radius: 10px;
        font-weight: 600; z-index: 4000;
        animation: slideInRight 0.3s ease;
    }
    .fade-out { animation: slideOutRight 0.3s ease forwards; }
    @keyframes slideInRight { from { transform: translateX(100%); opacity: 0; } to { transform: translateX(0); opacity: 1; } }
    @keyframes slideOutRight { from { transform: translateX(0); opacity: 1; } to { transform: translateX(100%); opacity: 0; } }
`;
document.head.appendChild(style);