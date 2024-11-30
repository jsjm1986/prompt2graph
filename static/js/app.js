/**
 * 知识图谱可视化系统
 */
class KnowledgeGraphApp {
    constructor(options = {}) {
        this.container = options.container || '#app';
        this.language = options.language || 'zh-CN';
        this.theme = options.theme || 'light';
        
        // 组件实例
        this.visualizer = null;
        this.analyzer = null;
        this.query = null;
        this.queryPanel = null;
        this.analysisPanel = null;
        
        // 数据
        this.data = null;
        
        this.init();
    }

    /**
     * 初始化应用
     */
    async init() {
        try {
            // 初始化容器
            this.initContainer();
            
            // 创建组件实例
            this.visualizer = new GraphVisualizer({
                container: '#graph-container',
                width: window.innerWidth,
                height: window.innerHeight - 100
            });
            
            this.analyzer = new GraphAnalyzer();
            this.query = new GraphQuery();
            
            this.queryPanel = new QueryPanel({
                container: '#query-panel',
                onSearch: this.handleSearch.bind(this),
                onFilter: this.handleFilter.bind(this),
                onReset: this.handleReset.bind(this)
            });
            
            this.analysisPanel = new AnalysisPanel({
                container: '#analysis-panel',
                analyzer: this.analyzer,
                onAnalysis: this.handleAnalysis.bind(this)
            });
            
            // 加载示例数据
            this.loadDemoData();
            
            // 绑定事件
            this.bindEvents();
            
            // 应用主题
            this.applyTheme(this.theme);
            
        } catch (error) {
            console.error('Failed to initialize app:', error);
            this.showError('Failed to initialize application');
        }
    }

    /**
     * 初始化容器
     */
    initContainer() {
        const container = document.querySelector(this.container);
        if (!container) return;

        container.innerHTML = `
            <div class="app-header">
                <div class="app-title">
                    <h1 data-i18n="app.title">知识图谱可视化系统</h1>
                </div>
                <div class="app-toolbar">
                    <button class="btn btn-icon" id="settingsBtn">
                        <i class="fas fa-cog"></i>
                    </button>
                </div>
            </div>

            <div class="app-main">
                <div class="app-sidebar">
                    <div id="query-panel"></div>
                    <div id="analysis-panel"></div>
                </div>
                <div id="graph-container"></div>
            </div>

            <div class="app-settings" id="settingsPanel">
                <div class="settings-header">
                    <h2 data-i18n="settings.title">设置</h2>
                    <button class="btn btn-icon" id="closeSettingsBtn">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="settings-content">
                    <div class="settings-section">
                        <h3 data-i18n="settings.language">语言</h3>
                        <select id="languageSelect" class="form-select">
                            <option value="zh-CN">中文</option>
                            <option value="en-US">English</option>
                        </select>
                    </div>
                    <div class="settings-section">
                        <h3 data-i18n="settings.theme">主题</h3>
                        <select id="themeSelect" class="form-select">
                            <option value="light" data-i18n="settings.themeLight">浅色</option>
                            <option value="dark" data-i18n="settings.themeDark">深色</option>
                        </select>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * 绑定事件
     */
    bindEvents() {
        // 设置按钮
        const settingsBtn = document.querySelector('#settingsBtn');
        const closeSettingsBtn = document.querySelector('#closeSettingsBtn');
        const settingsPanel = document.querySelector('#settingsPanel');
        
        settingsBtn.addEventListener('click', () => {
            settingsPanel.classList.add('show');
        });
        
        closeSettingsBtn.addEventListener('click', () => {
            settingsPanel.classList.remove('show');
        });
        
        // 语言切换
        const languageSelect = document.querySelector('#languageSelect');
        languageSelect.value = this.language;
        languageSelect.addEventListener('change', () => {
            this.language = languageSelect.value;
            this.updateLanguage();
        });
        
        // 主题切换
        const themeSelect = document.querySelector('#themeSelect');
        themeSelect.value = this.theme;
        themeSelect.addEventListener('change', () => {
            this.theme = themeSelect.value;
            this.applyTheme(this.theme);
        });
        
        // 窗口大小变化
        window.addEventListener('resize', this.handleResize.bind(this));
    }

    /**
     * 加载示例数据
     */
    loadDemoData() {
        try {
            // 生成知识图谱数据
            this.data = DemoDataGenerator.generateKnowledgeGraph();
            
            // 更新各组件数据
            this.visualizer.setData(this.data.nodes, this.data.edges);
            this.analyzer.setData(this.data.nodes, this.data.edges);
            this.query.setData(this.data.nodes, this.data.edges);
            
            // 计算并显示分析结果
            this.updateAnalysis();
            
        } catch (error) {
            console.error('Failed to load demo data:', error);
            this.showError('Failed to load demo data');
        }
    }

    /**
     * 处理搜索
     */
    handleSearch(type, query) {
        try {
            let results = [];
            
            switch (type) {
                case 'basic':
                    if (query.filters.includes('label')) {
                        results = [...this.query.queryNodesByLabel(query.keyword)];
                    }
                    if (query.filters.includes('type')) {
                        results = [...results, ...this.query.queryNodesByType(query.keyword)];
                    }
                    if (query.filters.includes('property')) {
                        results = [...results, ...this.query.fuzzyQueryNodes(query.keyword)];
                    }
                    break;
                
                case 'path':
                    results = this.query.queryPath(query.start, query.end, query.maxDepth);
                    break;
                
                case 'neighbor':
                    results = [...this.query.queryNeighbors(query.center, query.depth)];
                    break;
                
                case 'complex':
                    results = [...this.query.complexQuery(query.query)];
                    break;
            }
            
            // 更新查询结果
            this.queryPanel.setResults(results);
            
            // 高亮显示结果
            this.visualizer.highlightNodes(results);
            
        } catch (error) {
            console.error('Search failed:', error);
            this.showError('Search failed');
        }
    }

    /**
     * 处理过滤
     */
    handleFilter(filters) {
        try {
            this.visualizer.setFilter(filters);
        } catch (error) {
            console.error('Filter failed:', error);
            this.showError('Filter failed');
        }
    }

    /**
     * 处理重置
     */
    handleReset() {
        try {
            this.visualizer.clearHighlight();
            this.queryPanel.clearResults();
        } catch (error) {
            console.error('Reset failed:', error);
            this.showError('Reset failed');
        }
    }

    /**
     * 处理分析
     */
    handleAnalysis(type) {
        try {
            switch (type) {
                case 'centrality':
                    const centralityType = document.querySelector('#centralityType').value;
                    this.analysisPanel.calculateCentrality(centralityType);
                    break;
                
                case 'community':
                    this.analysisPanel.detectCommunities();
                    break;
                
                case 'path':
                    const stats = this.analyzer.calculateGraphStatistics();
                    this.analysisPanel.updatePathAnalysis(stats);
                    break;
            }
        } catch (error) {
            console.error('Analysis failed:', error);
            this.showError('Analysis failed');
        }
    }

    /**
     * 更新分析结果
     */
    updateAnalysis() {
        try {
            // 计算基础统计
            const stats = this.analyzer.calculateGraphStatistics();
            this.analysisPanel.updateBasicStats(stats);
            
            // 计算度分布
            const degreeCentrality = this.analyzer.calculateDegreeCentrality();
            const distribution = {};
            degreeCentrality.forEach(degree => {
                distribution[degree] = (distribution[degree] || 0) + 1;
            });
            this.analysisPanel.updateDegreeDistribution(distribution);
            
        } catch (error) {
            console.error('Failed to update analysis:', error);
            this.showError('Failed to update analysis');
        }
    }

    /**
     * 处理窗口大小变化
     */
    handleResize() {
        try {
            this.visualizer.setSize(window.innerWidth, window.innerHeight - 100);
            this.analysisPanel.resizeCharts();
        } catch (error) {
            console.error('Resize failed:', error);
        }
    }

    /**
     * 更新语言
     */
    async updateLanguage() {
        try {
            // 加载语言文件
            const response = await fetch(`/static/i18n/${this.language}.json`);
            const translations = await response.json();
            
            // 更新所有带有 data-i18n 属性的元素
            document.querySelectorAll('[data-i18n]').forEach(element => {
                const key = element.dataset.i18n;
                const translation = key.split('.').reduce((obj, key) => obj?.[key], translations);
                if (translation) {
                    if (element.tagName === 'INPUT' && element.type === 'placeholder') {
                        element.placeholder = translation;
                    } else {
                        element.textContent = translation;
                    }
                }
            });
            
        } catch (error) {
            console.error('Failed to update language:', error);
            this.showError('Failed to update language');
        }
    }

    /**
     * 应用主题
     */
    applyTheme(theme) {
        document.body.classList.remove('theme-light', 'theme-dark');
        document.body.classList.add(`theme-${theme}`);
    }

    /**
     * 显示错误信息
     */
    showError(message) {
        // 实现错误提示
        console.error(message);
    }
}

// 导出应用
window.KnowledgeGraphApp = KnowledgeGraphApp;

// 启动应用
document.addEventListener('DOMContentLoaded', () => {
    window.app = new KnowledgeGraphApp({
        container: '#app',
        language: 'zh-CN',
        theme: 'light'
    });
});
