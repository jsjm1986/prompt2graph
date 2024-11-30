/**
 * 设置面板组件
 */
class SettingsPanel {
    constructor(uiUtils) {
        this.uiUtils = uiUtils;
        this.panel = null;
        this.isVisible = false;
    }

    /**
     * 初始化设置面板
     */
    init() {
        this.createPanel();
        this.setupEventListeners();
        this.loadSettings();
    }

    /**
     * 创建设置面板
     */
    createPanel() {
        this.panel = document.createElement('div');
        this.panel.className = 'settings-panel';
        this.panel.innerHTML = `
            <div class="settings-header">
                <h3 data-i18n="settings.title">系统设置</h3>
            </div>
            <div class="settings-content">
                <!-- 常规设置 -->
                <div class="settings-group">
                    <div class="settings-group-title" data-i18n="settings.general.title">常规设置</div>
                    
                    <!-- 语言设置 -->
                    <div class="form-group">
                        <label data-i18n="settings.general.language">语言</label>
                        <select id="locale-selector" class="form-control">
                            <option value="zh-CN">简体中文</option>
                            <option value="en-US">English</option>
                        </select>
                    </div>
                    
                    <!-- 主题设置 -->
                    <div class="form-group">
                        <label data-i18n="settings.general.theme">主题</label>
                        <select id="theme-selector" class="form-control">
                            <option value="light">Light</option>
                            <option value="dark">Dark</option>
                            <option value="blue">Blue</option>
                            <option value="green">Green</option>
                        </select>
                    </div>
                </div>

                <!-- 可视化设置 -->
                <div class="settings-group">
                    <div class="settings-group-title" data-i18n="settings.visualization.title">可视化设置</div>
                    
                    <!-- 默认布局 -->
                    <div class="form-group">
                        <label data-i18n="settings.visualization.defaultLayout">默认布局</label>
                        <select id="layout-selector" class="form-control">
                            <option value="force">Force</option>
                            <option value="circular">Circular</option>
                            <option value="hierarchical">Hierarchical</option>
                            <option value="grid">Grid</option>
                        </select>
                    </div>
                    
                    <!-- 节点大小 -->
                    <div class="form-group">
                        <label data-i18n="settings.visualization.nodeSize">节点大小</label>
                        <input type="range" id="node-size" class="form-control" min="1" max="50" value="10">
                    </div>
                    
                    <!-- 边宽度 -->
                    <div class="form-group">
                        <label data-i18n="settings.visualization.edgeWidth">边宽度</label>
                        <input type="range" id="edge-width" class="form-control" min="1" max="10" value="1">
                    </div>
                    
                    <!-- 显示标签 -->
                    <div class="form-group">
                        <label data-i18n="settings.visualization.labels">显示标签</label>
                        <input type="checkbox" id="show-labels" class="form-control" checked>
                    </div>
                </div>

                <!-- 性能设置 -->
                <div class="settings-group">
                    <div class="settings-group-title" data-i18n="settings.performance.title">性能设置</div>
                    
                    <!-- 缓存大小 -->
                    <div class="form-group">
                        <label data-i18n="settings.performance.cacheSize">缓存大小</label>
                        <select id="cache-size" class="form-control">
                            <option value="small">Small (100MB)</option>
                            <option value="medium">Medium (500MB)</option>
                            <option value="large">Large (1GB)</option>
                        </select>
                    </div>
                    
                    <!-- 渲染限制 -->
                    <div class="form-group">
                        <label data-i18n="settings.performance.renderLimit">渲染限制</label>
                        <input type="number" id="render-limit" class="form-control" min="100" max="10000" value="1000">
                    </div>
                    
                    <!-- 动画速度 -->
                    <div class="form-group">
                        <label data-i18n="settings.performance.animationSpeed">动画速度</label>
                        <input type="range" id="animation-speed" class="form-control" min="0" max="100" value="50">
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(this.panel);
    }

    /**
     * 设置事件监听
     */
    setupEventListeners() {
        // 语言切换
        const localeSelector = document.getElementById('locale-selector');
        localeSelector?.addEventListener('change', (e) => {
            this.uiUtils.i18n.setLocale(e.target.value);
            this.uiUtils.applyCurrentLocale();
            this.saveSettings();
        });

        // 主题切换
        const themeSelector = document.getElementById('theme-selector');
        themeSelector?.addEventListener('change', (e) => {
            this.uiUtils.theme.setTheme(e.target.value);
            this.uiUtils.applyCurrentTheme();
            this.saveSettings();
        });

        // 其他设置变更
        const settingsInputs = this.panel.querySelectorAll('input, select');
        settingsInputs.forEach(input => {
            input.addEventListener('change', () => {
                this.saveSettings();
            });
        });
    }

    /**
     * 加载设置
     */
    loadSettings() {
        try {
            const settings = JSON.parse(localStorage.getItem('settings') || '{}');
            
            // 设置语言
            if (settings.locale) {
                const localeSelector = document.getElementById('locale-selector');
                if (localeSelector) {
                    localeSelector.value = settings.locale;
                    this.uiUtils.i18n.setLocale(settings.locale);
                }
            }
            
            // 设置主题
            if (settings.theme) {
                const themeSelector = document.getElementById('theme-selector');
                if (themeSelector) {
                    themeSelector.value = settings.theme;
                    this.uiUtils.theme.setTheme(settings.theme);
                }
            }
            
            // 设置其他选项
            Object.entries(settings).forEach(([key, value]) => {
                const element = document.getElementById(key);
                if (element) {
                    if (element.type === 'checkbox') {
                        element.checked = value;
                    } else {
                        element.value = value;
                    }
                }
            });
            
        } catch (error) {
            console.error('加载设置失败:', error);
        }
    }

    /**
     * 保存设置
     */
    saveSettings() {
        try {
            const settings = {
                locale: document.getElementById('locale-selector')?.value,
                theme: document.getElementById('theme-selector')?.value,
                layout: document.getElementById('layout-selector')?.value,
                nodeSize: document.getElementById('node-size')?.value,
                edgeWidth: document.getElementById('edge-width')?.value,
                showLabels: document.getElementById('show-labels')?.checked,
                cacheSize: document.getElementById('cache-size')?.value,
                renderLimit: document.getElementById('render-limit')?.value,
                animationSpeed: document.getElementById('animation-speed')?.value
            };
            
            localStorage.setItem('settings', JSON.stringify(settings));
            this.uiUtils.showMessage(this.uiUtils.i18n.getText('messages.success.save'), 'success');
            
        } catch (error) {
            console.error('保存设置失败:', error);
            this.uiUtils.showMessage(this.uiUtils.i18n.getText('messages.error.general'), 'error');
        }
    }

    /**
     * 显示设置面板
     */
    show() {
        if (!this.isVisible) {
            this.panel.classList.add('show');
            this.isVisible = true;
        }
    }

    /**
     * 隐藏设置面板
     */
    hide() {
        if (this.isVisible) {
            this.panel.classList.remove('show');
            this.isVisible = false;
        }
    }

    /**
     * 切换设置面板显示状态
     */
    toggle() {
        if (this.isVisible) {
            this.hide();
        } else {
            this.show();
        }
    }
}

// 导出设置面板组件
window.SettingsPanel = SettingsPanel;
