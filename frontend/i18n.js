// LIMBO frontend i18n module
// Loads translation catalog from /api/i18n/<lang> and applies it to elements
// marked with data-i18n="key". Supports dynamic language switching.

const I18n = (() => {
    const STORAGE_KEY = 'limbo.lang';
    let catalog = {};
    let locale = 'en';
    let listeners = [];

    function getInitialLocale() {
        const stored = localStorage.getItem(STORAGE_KEY);
        if (stored) return stored;
        const browser = (navigator.language || 'en').toLowerCase();
        return browser.startsWith('zh') ? 'zh' : 'en';
    }

    async function load(lang) {
        try {
            const resp = await fetch(`/api/i18n/${encodeURIComponent(lang)}`);
            const data = await resp.json();
            catalog = data.strings || {};
            locale = data.locale || lang;
            localStorage.setItem(STORAGE_KEY, locale);
            applyAll();
            syncSwitcher();
            listeners.forEach(fn => { try { fn(locale); } catch (e) { console.warn(e); } });
            return locale;
        } catch (e) {
            console.warn('Failed to load i18n catalog:', e);
            return null;
        }
    }

    function t(key, fallback) {
        if (catalog[key]) return catalog[key];
        return fallback !== undefined ? fallback : key;
    }

    function applyAll(root) {
        const scope = root || document;
        scope.querySelectorAll('[data-i18n]').forEach(el => {
            const key = el.getAttribute('data-i18n');
            const text = t(key, el.textContent);
            if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
                if (el.placeholder !== undefined && !el.value) {
                    el.placeholder = text;
                }
            } else {
                el.textContent = text;
            }
        });
        scope.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
            const key = el.getAttribute('data-i18n-placeholder');
            el.placeholder = t(key, el.placeholder);
        });
        scope.querySelectorAll('[data-i18n-title]').forEach(el => {
            const key = el.getAttribute('data-i18n-title');
            el.title = t(key, el.title);
        });
    }

    function onChange(fn) { listeners.push(fn); }

    function getLocale() { return locale; }

    function syncSwitcher() {
        const sel = document.getElementById('langSwitcher');
        if (sel && sel.value !== locale) sel.value = locale;
    }

    return { load, t, applyAll, onChange, getLocale, syncSwitcher };
})();

// Initialize on page load
document.addEventListener('DOMContentLoaded', async () => {
    await I18n.load(I18n.getLocale() || (navigator.language.startsWith('zh') ? 'zh' : 'en'));
});