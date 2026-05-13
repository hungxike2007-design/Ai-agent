/**
 * Theme Toggle — Dark / Light mode switcher
 * Persists preference in localStorage and syncs across tabs.
 *
 * Usage: include this script in any page AFTER the impeccable-theme.css.
 * It auto-creates the floating toggle button on DOMContentLoaded.
 */
(function () {
    'use strict';

    const STORAGE_KEY = 'ai-agent-theme';

    /* ── Helpers ── */
    function getPreferred() {
        const saved = localStorage.getItem(STORAGE_KEY);
        if (saved === 'dark' || saved === 'light') return saved;
        // Respect OS preference
        return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }

    function applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem(STORAGE_KEY, theme);
        updateToggleButton(theme);
    }

    function updateToggleButton(theme) {
        const btn = document.getElementById('themeToggleBtn');
        if (!btn) return;
        const icon = btn.querySelector('.theme-icon');
        if (theme === 'dark') {
            icon.className = 'fas fa-sun theme-icon';
            btn.setAttribute('data-tooltip', 'Chuyển sang Sáng');
            btn.setAttribute('aria-label', 'Chuyển sang chế độ sáng');
        } else {
            icon.className = 'fas fa-moon theme-icon';
            btn.setAttribute('data-tooltip', 'Chuyển sang Tối');
            btn.setAttribute('aria-label', 'Chuyển sang chế độ tối');
        }
    }

    function toggle() {
        const current = document.documentElement.getAttribute('data-theme') || 'light';
        const next = current === 'dark' ? 'light' : 'dark';

        // Spin animation
        const btn = document.getElementById('themeToggleBtn');
        if (btn) {
            btn.classList.add('spin');
            setTimeout(() => btn.classList.remove('spin'), 500);
        }

        applyTheme(next);
    }

    /* ── Inject button ── */
    function createButton() {
        if (document.getElementById('themeToggleBtn')) return; // already exists
        const btn = document.createElement('button');
        btn.id = 'themeToggleBtn';
        btn.className = 'theme-toggle';
        btn.type = 'button';
        btn.innerHTML = '<i class="fas fa-moon theme-icon"></i>';
        btn.addEventListener('click', toggle);
        document.body.appendChild(btn);
    }

    /* ── Apply immediately (before DOMContentLoaded to prevent flash) ── */
    applyTheme(getPreferred());

    /* ── Create button when DOM is ready ── */
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function () {
            createButton();
            updateToggleButton(getPreferred());
        });
    } else {
        createButton();
        updateToggleButton(getPreferred());
    }

    /* ── Sync across tabs ── */
    window.addEventListener('storage', function (e) {
        if (e.key === STORAGE_KEY && e.newValue) {
            applyTheme(e.newValue);
        }
    });
})();
