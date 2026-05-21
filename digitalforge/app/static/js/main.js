/**
 * DigitalForge Main JavaScript
 * Handles UI interactions, search, and common functionality
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize Lucide icons
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }

    // Mobile menu toggle
    const mobileMenuBtn = document.getElementById('mobileMenuBtn');
    const mobileMenu = document.getElementById('mobileMenu');

    if (mobileMenuBtn && mobileMenu) {
        mobileMenuBtn.addEventListener('click', () => {
            mobileMenu.classList.toggle('hidden');
        });
    }

    // Search autocomplete
    const searchInput = document.querySelector('input[name="q"]');
    if (searchInput) {
        let debounceTimer;

        searchInput.addEventListener('input', function() {
            clearTimeout(debounceTimer);
            const query = this.value.trim();

            if (query.length < 2) return;

            debounceTimer = setTimeout(async () => {
                try {
                    const response = await fetch(`/api/search/suggestions?q=${encodeURIComponent(query)}`);
                    const suggestions = await response.json();

                    // Could implement dropdown here
                    console.log('Suggestions:', suggestions);
                } catch (err) {
                    console.error('Search error:', err);
                }
            }, 300);
        });
    }

    // Image lazy loading
    const lazyImages = document.querySelectorAll('img[data-src]');
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                Here's the rest of the code files:

---

## `app/static/js/main.js` (Complete)

```javascript
/**
 * DigitalForge Main JavaScript
 * Handles UI interactions, search, and common functionality
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize Lucide icons
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }

    // Mobile menu toggle
    const mobileMenuBtn = document.getElementById('mobileMenuBtn');
    const mobileMenu = document.getElementById('mobileMenu');

    if (mobileMenuBtn && mobileMenu) {
        mobileMenuBtn.addEventListener('click', () => {
            mobileMenu.classList.toggle('hidden');
        });
    }

    // Search autocomplete
    const searchInput = document.querySelector('input[name="q"]');
    if (searchInput) {
        let debounceTimer;

        searchInput.addEventListener('input', function() {
            clearTimeout(debounceTimer);
            const query = this.value.trim();

            if (query.length < 2) return;

            debounceTimer = setTimeout(async () => {
                try {
                    const response = await fetch(`/api/search/suggestions?q=${encodeURIComponent(query)}`);
                    const suggestions = await response.json();

                    // Could implement dropdown here
                    console.log('Suggestions:', suggestions);
                } catch (err) {
                    console.error('Search error:', err);
                }
            }, 300);
        });
    }

    // Image lazy loading
    const lazyImages = document.querySelectorAll('img[data-src]');
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.removeAttribute('data-src');
                observer.unobserve(img);
            }
        });
    });

    lazyImages.forEach(img => imageObserver.observe(img));

    // File upload preview
    const fileInput = document.getElementById('productFile');
    if (fileInput) {
        fileInput.addEventListener('change', function() {
            const file = this.files[0];
            if (file) {
                const sizeMB = (file.size / 1024 / 1024).toFixed(2);
                const info = document.getElementById('fileInfo');
                if (info) {
                    info.textContent = `Selected: ${file.name} (${sizeMB} MB)`;
                    info.className = 'mt-1 text-sm text-green-600';
                }
            }
        });
    }

    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    });

    // Form validation feedback
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const requiredFields = form.querySelectorAll('[required]');
            let valid = true;

            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    valid = false;
                    field.classList.add('border-red-500', 'focus:ring-red-500');
                    field.classList.remove('border-gray-300', 'focus:ring-primary-500');
                } else {
                    field.classList.remove('border-red-500', 'focus:ring-red-500');
                    field.classList.add('border-gray-300', 'focus:ring-primary-500');
                }
            });

            if (!valid) {
                e.preventDefault();
                // Show error message
                const existingError = form.querySelector('.form-error');
                if (!existingError) {
                    const errorDiv = document.createElement('div');
                    errorDiv.className = 'form-error bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-xl mb-4 text-sm';
                    errorDiv.innerHTML = '<strong>Error:</strong> Please fill in all required fields.';
                    form.insertBefore(errorDiv, form.firstChild);
                }
            }
        });
    });

    // Copy to clipboard utility
    window.copyToClipboard = async function(text) {
        try {
            await navigator.clipboard.writeText(text);
            // Show toast
            showToast('Copied to clipboard!', 'success');
        } catch (err) {
            console.error('Copy failed:', err);
            showToast('Failed to copy', 'error');
        }
    };

    // Toast notification
    window.showToast = function(message, type = 'info') {
        const toast = document.createElement('div');
        const colors = {
            success: 'bg-green-500',
            error: 'bg-red-500',
            warning: 'bg-yellow-500',
            info: 'bg-primary-600'
        };

        toast.className = `fixed bottom-4 right-4 ${colors[type] || colors.info} text-white px-6 py-3 rounded-xl shadow-lg z-50 transform translate-y-0 transition-all duration-300`;
        toast.textContent = message;

        document.body.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(20px)';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    };

    // Intersection Observer for scroll animations
    const animateElements = document.querySelectorAll('.animate-on-scroll');
    const animationObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-fade-in');
                animationObserver.unobserve(entry.target);
            }
        });
    }, { threshold: 0.1 });

    animateElements.forEach(el => animationObserver.observe(el));
});