document.addEventListener('DOMContentLoaded', () => {
    const langBtn = document.getElementById('langBtn');
    const langDropdown = document.getElementById('langDropdown');
    const currentLangFlag = document.getElementById('currentLangFlag');
    const currentLangCode = document.getElementById('currentLangCode');
    const langOptions = document.querySelectorAll('.lang-option');

    // Mobile menu toggle
    const mobileMenuToggle = document.getElementById('mobileMenuToggle');
    const headerMenu = document.getElementById('headerMenu');

    if (mobileMenuToggle) {
        mobileMenuToggle.addEventListener('click', () => {
            mobileMenuToggle.classList.toggle('active');
            headerMenu.classList.toggle('active');
        });

        // Close menu when clicking on a link
        const navLinks = document.querySelectorAll('.nav-link');
        navLinks.forEach(link => {
            link.addEventListener('click', () => {
                mobileMenuToggle.classList.remove('active');
                headerMenu.classList.remove('active');
            });
        });

        // Close menu when clicking outside
        document.addEventListener('click', (e) => {
            if (!headerMenu.contains(e.target) && !mobileMenuToggle.contains(e.target)) {
                mobileMenuToggle.classList.remove('active');
                headerMenu.classList.remove('active');
            }
        });
    }

    // Toggle Dropdown
    langBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        langDropdown.classList.toggle('active');
    });

    // Close Dropdown when clicking outside
    document.addEventListener('click', () => {
        langDropdown.classList.remove('active');
    });

    // Language Selection
    langOptions.forEach(option => {
        option.addEventListener('click', () => {
            const lang = option.dataset.lang;
            const flag = option.dataset.flag;
            const dir = option.dataset.dir;

            setLanguage(lang, flag, dir);
        });
    });

    // Load Language
    async function setLanguage(lang, flag, dir) {
        // Update UI
        currentLangFlag.textContent = flag;
        currentLangCode.textContent = lang.toUpperCase();
        document.documentElement.lang = lang;
        document.documentElement.dir = dir;

        // Load translations
        try {
            const response = await fetch(`locales/${lang}.json`);
            if (!response.ok) throw new Error('Translation not found');
            const translations = await response.json();

            applyTranslations(translations);

            // Save preference
            localStorage.setItem('recrutder_lang', lang);
            localStorage.setItem('recrutder_flag', flag);
            localStorage.setItem('recrutder_dir', dir);

            // Update chatbot language if it exists
            if (window.recrutderChatbot) {
                window.recrutderChatbot.updateLanguage(lang);
            }
        } catch (error) {
            console.error('Error loading translations:', error);
        }
    }

    function applyTranslations(translations) {
        const elements = document.querySelectorAll('[data-i18n]');
        elements.forEach(el => {
            const key = el.dataset.i18n;
            const keys = key.split('.');
            let value = translations;

            for (const k of keys) {
                value = value[k];
            }

            if (value) {
                el.textContent = value;
            }
        });
    }

    // Initialize
    const savedLang = localStorage.getItem('recrutder_lang') || 'en';
    const savedFlag = localStorage.getItem('recrutder_flag') || '🇬🇧';
    const savedDir = localStorage.getItem('recrutder_dir') || 'ltr';

    setLanguage(savedLang, savedFlag, savedDir);
});
