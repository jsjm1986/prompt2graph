/**
 * 前端工具类
 */
class UIUtils {
    /**
     * 初始化UI工具类
     * @param {Object} options 配置选项
     */
    constructor(options = {}) {
        this.i18n = new I18nHelper(options.defaultLocale || 'zh-CN');
        this.theme = new ThemeHelper(options.defaultTheme || 'light');
        this.initialized = false;
    }

    /**
     * 初始化UI
     */
    async init() {
        if (this.initialized) return;

        try {
            // 加载语言和主题
            await Promise.all([
                this.i18n.init(),
                this.theme.init()
            ]);

            // 应用当前语言和主题
            this.applyCurrentLocale();
            this.applyCurrentTheme();

            // 设置事件监听
            this.setupEventListeners();

            this.initialized = true;
            console.log('UI工具初始化完成');
        } catch (error) {
            console.error('UI工具初始化失败:', error);
        }
    }

    /**
     * 设置事件监听
     */
    setupEventListeners() {
        // 语言切换
        document.getElementById('locale-selector')?.addEventListener('change', (e) => {
            this.i18n.setLocale(e.target.value);
            this.applyCurrentLocale();
        });

        // 主题切换
        document.getElementById('theme-selector')?.addEventListener('change', (e) => {
            this.theme.setTheme(e.target.value);
            this.applyCurrentTheme();
        });
    }

    /**
     * 应用当前语言
     */
    applyCurrentLocale() {
        document.querySelectorAll('[data-i18n]').forEach(element => {
            const key = element.getAttribute('data-i18n');
            if (key) {
                element.textContent = this.i18n.getText(key);
            }
        });

        document.querySelectorAll('[data-i18n-placeholder]').forEach(element => {
            const key = element.getAttribute('data-i18n-placeholder');
            if (key) {
                element.placeholder = this.i18n.getText(key);
            }
        });

        document.querySelectorAll('[data-i18n-title]').forEach(element => {
            const key = element.getAttribute('data-i18n-title');
            if (key) {
                element.title = this.i18n.getText(key);
            }
        });
    }

    /**
     * 应用当前主题
     */
    applyCurrentTheme() {
        const theme = this.theme.getCurrentTheme();
        if (!theme) return;

        // 应用主题变量
        Object.entries(theme.cssVariables).forEach(([key, value]) => {
            document.documentElement.style.setProperty(key, value);
        });

        // 更新主题类
        document.body.classList.remove('theme-light', 'theme-dark');
        document.body.classList.add(`theme-${theme.id}`);
    }

    /**
     * 显示加载中
     */
    showLoading() {
        const loading = document.getElementById('loading');
        if (loading) {
            loading.style.display = 'flex';
        }
    }

    /**
     * 隐藏加载中
     */
    hideLoading() {
        const loading = document.getElementById('loading');
        if (loading) {
            loading.style.display = 'none';
        }
    }

    /**
     * 显示消息
     * @param {string} message 消息内容
     * @param {string} type 消息类型
     */
    showMessage(message, type = 'info') {
        const messageEl = document.createElement('div');
        messageEl.className = `message message-${type}`;
        messageEl.textContent = message;

        const container = document.getElementById('message-container') || document.body;
        container.appendChild(messageEl);

        setTimeout(() => {
            messageEl.classList.add('show');
            setTimeout(() => {
                messageEl.classList.remove('show');
                setTimeout(() => messageEl.remove(), 300);
            }, 3000);
        }, 100);
    }

    /**
     * 确认对话框
     * @param {string} message 消息内容
     * @returns {Promise<boolean>}
     */
    confirm(message) {
        return new Promise((resolve) => {
            const dialog = document.createElement('div');
            dialog.className = 'dialog';
            dialog.innerHTML = `
                <div class="dialog-content">
                    <p>${message}</p>
                    <div class="dialog-buttons">
                        <button class="btn btn-cancel" data-i18n="actions.cancel">取消</button>
                        <button class="btn btn-confirm" data-i18n="actions.confirm">确认</button>
                    </div>
                </div>
            `;

            const container = document.getElementById('dialog-container') || document.body;
            container.appendChild(dialog);

            // 应用国际化
            this.applyCurrentLocale();

            // 绑定事件
            dialog.querySelector('.btn-cancel').onclick = () => {
                dialog.remove();
                resolve(false);
            };
            dialog.querySelector('.btn-confirm').onclick = () => {
                dialog.remove();
                resolve(true);
            };

            setTimeout(() => dialog.classList.add('show'), 100);
        });
    }
}

/**
 * 国际化助手类
 */
class I18nHelper {
    constructor(defaultLocale) {
        this.defaultLocale = defaultLocale;
        this.currentLocale = defaultLocale;
        this.translations = {};
        this.availableLocales = [];
    }

    async init() {
        try {
            // 获取可用语言列表
            const response = await fetch('/api/i18n/locales');
            const data = await response.json();
            this.availableLocales = data.locales;

            // 加载当前语言
            await this.loadTranslations(this.currentLocale);

            console.log('国际化助手初始化完成');
        } catch (error) {
            console.error('国际化助手初始化失败:', error);
        }
    }

    async loadTranslations(locale) {
        try {
            const response = await fetch(`/api/i18n/translations/${locale}`);
            const data = await response.json();
            this.translations[locale] = data;
        } catch (error) {
            console.error(`加载语言包失败 ${locale}:`, error);
        }
    }

    async setLocale(locale) {
        if (locale === this.currentLocale) return;

        try {
            if (!this.translations[locale]) {
                await this.loadTranslations(locale);
            }
            this.currentLocale = locale;
            localStorage.setItem('locale', locale);
        } catch (error) {
            console.error(`切换语言失败 ${locale}:`, error);
        }
    }

    getText(key, params = {}) {
        const keys = key.split('.');
        let value = this.translations[this.currentLocale] || {};

        for (const k of keys) {
            value = value[k];
            if (!value) break;
        }

        if (!value) {
            console.warn(`未找到翻译 ${key}`);
            return key;
        }

        return this.formatText(value, params);
    }

    formatText(text, params) {
        return text.replace(/\{(\w+)\}/g, (match, key) => {
            return params[key] !== undefined ? params[key] : match;
        });
    }
}

/**
 * 主题助手类
 */
class ThemeHelper {
    constructor(defaultTheme) {
        this.defaultTheme = defaultTheme;
        this.currentTheme = defaultTheme;
        this.themes = {};
        this.availableThemes = [];
    }

    async init() {
        try {
            // 获取可用主题列表
            const response = await fetch('/api/themes');
            const data = await response.json();
            this.availableThemes = data.themes;

            // 加载所有主题
            await Promise.all(
                this.availableThemes.map(theme => this.loadTheme(theme.id))
            );

            // 应用保存的主题或默认主题
            const savedTheme = localStorage.getItem('theme');
            if (savedTheme && this.themes[savedTheme]) {
                this.currentTheme = savedTheme;
            }

            console.log('主题助手初始化完成');
        } catch (error) {
            console.error('主题助手初始化失败:', error);
        }
    }

    async loadTheme(themeId) {
        try {
            const response = await fetch(`/api/themes/${themeId}`);
            const data = await response.json();
            this.themes[themeId] = data;
        } catch (error) {
            console.error(`加载主题失败 ${themeId}:`, error);
        }
    }

    setTheme(themeId) {
        if (themeId === this.currentTheme) return;

        const theme = this.themes[themeId];
        if (!theme) {
            console.error(`未找到主题 ${themeId}`);
            return;
        }

        this.currentTheme = themeId;
        localStorage.setItem('theme', themeId);
    }

    getCurrentTheme() {
        return this.themes[this.currentTheme];
    }
}

// 导出工具类
window.UIUtils = UIUtils;
