/**
 * 查询面板组件
 */
class QueryPanel {
    constructor(options = {}) {
        this.container = options.container || '#query-panel';
        this.onSearch = options.onSearch || (() => {});
        this.onFilter = options.onFilter || (() => {});
        this.onReset = options.onReset || (() => {});
        
        this.init();
    }

    /**
     * 初始化面板
     */
    init() {
        const container = document.querySelector(this.container);
        if (!container) return;

        // 创建查询表单
        const form = document.createElement('form');
        form.className = 'query-form';
        form.innerHTML = `
            <div class="query-type">
                <select id="queryType" class="form-select">
                    <option value="basic" data-i18n="query.basic">基本查询</option>
                    <option value="path" data-i18n="query.path">路径查询</option>
                    <option value="neighbor" data-i18n="query.neighbor">邻居查询</option>
                    <option value="complex" data-i18n="query.complex">复杂查询</option>
                </select>
            </div>

            <div class="query-input">
                <div class="basic-query query-section">
                    <input type="text" id="basicQuery" class="form-input" data-i18n="query.basicPlaceholder" placeholder="输入关键词搜索...">
                    <div class="filter-options">
                        <label><input type="checkbox" value="label"> <span data-i18n="query.filterLabel">标签</span></label>
                        <label><input type="checkbox" value="type"> <span data-i18n="query.filterType">类型</span></label>
                        <label><input type="checkbox" value="property"> <span data-i18n="query.filterProperty">属性</span></label>
                    </div>
                </div>

                <div class="path-query query-section hidden">
                    <input type="text" id="startNode" class="form-input" data-i18n="query.startNode" placeholder="起始节点...">
                    <input type="text" id="endNode" class="form-input" data-i18n="query.endNode" placeholder="目标节点...">
                    <input type="number" id="maxDepth" class="form-input" value="5" min="1" max="10">
                </div>

                <div class="neighbor-query query-section hidden">
                    <input type="text" id="centerNode" class="form-input" data-i18n="query.centerNode" placeholder="中心节点...">
                    <input type="number" id="depth" class="form-input" value="1" min="1" max="5">
                    <div class="filter-options">
                        <label><input type="checkbox" value="incoming"> <span data-i18n="query.filterIncoming">入边</span></label>
                        <label><input type="checkbox" value="outgoing"> <span data-i18n="query.filterOutgoing">出边</span></label>
                    </div>
                </div>

                <div class="complex-query query-section hidden">
                    <textarea id="complexQuery" class="form-input" data-i18n="query.complexPlaceholder" 
                        placeholder="输入复杂查询条件...&#10;示例: type=Person AND (age>20 OR role=admin)"></textarea>
                </div>
            </div>

            <div class="query-actions">
                <button type="submit" class="btn btn-primary" data-i18n="query.search">搜索</button>
                <button type="button" class="btn btn-secondary" data-i18n="query.reset">重置</button>
            </div>
        `;

        container.appendChild(form);

        // 绑定事件
        this.bindEvents(form);
    }

    /**
     * 绑定事件
     */
    bindEvents(form) {
        const queryType = form.querySelector('#queryType');
        const sections = form.querySelectorAll('.query-section');
        const submitBtn = form.querySelector('button[type="submit"]');
        const resetBtn = form.querySelector('button[type="reset"]');

        // 切换查询类型
        queryType.addEventListener('change', () => {
            sections.forEach(section => section.classList.add('hidden'));
            form.querySelector(`.${queryType.value}-query`).classList.remove('hidden');
        });

        // 提交查询
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            const type = queryType.value;
            const query = this.getQueryData(type, form);
            this.onSearch(type, query);
        });

        // 过滤选项变化
        form.querySelectorAll('.filter-options input').forEach(checkbox => {
            checkbox.addEventListener('change', () => {
                const filters = Array.from(form.querySelectorAll('.filter-options input:checked'))
                    .map(input => input.value);
                this.onFilter(filters);
            });
        });

        // 重置
        resetBtn.addEventListener('click', () => {
            form.reset();
            this.onReset();
        });
    }

    /**
     * 获取查询数据
     */
    getQueryData(type, form) {
        switch (type) {
            case 'basic':
                return {
                    keyword: form.querySelector('#basicQuery').value,
                    filters: Array.from(form.querySelectorAll('.basic-query .filter-options input:checked'))
                        .map(input => input.value)
                };

            case 'path':
                return {
                    start: form.querySelector('#startNode').value,
                    end: form.querySelector('#endNode').value,
                    maxDepth: parseInt(form.querySelector('#maxDepth').value)
                };

            case 'neighbor':
                return {
                    center: form.querySelector('#centerNode').value,
                    depth: parseInt(form.querySelector('#depth').value),
                    filters: Array.from(form.querySelectorAll('.neighbor-query .filter-options input:checked'))
                        .map(input => input.value)
                };

            case 'complex':
                return {
                    query: form.querySelector('#complexQuery').value
                };

            default:
                return {};
        }
    }

    /**
     * 设置查询结果
     */
    setResults(results) {
        const container = document.querySelector(this.container);
        let resultsDiv = container.querySelector('.query-results');
        
        if (!resultsDiv) {
            resultsDiv = document.createElement('div');
            resultsDiv.className = 'query-results';
            container.appendChild(resultsDiv);
        }

        if (results.length === 0) {
            resultsDiv.innerHTML = '<div class="no-results" data-i18n="query.noResults">没有找到匹配的结果</div>';
            return;
        }

        resultsDiv.innerHTML = `
            <div class="results-header">
                <span data-i18n="query.resultsCount">找到 ${results.length} 个结果</span>
            </div>
            <div class="results-list">
                ${results.map(item => this.renderResultItem(item)).join('')}
            </div>
        `;
    }

    /**
     * 渲染结果项
     */
    renderResultItem(item) {
        if (item.type === 'node') {
            return `
                <div class="result-item node-result" data-id="${item.id}">
                    <div class="result-icon">
                        <i class="fas fa-circle"></i>
                    </div>
                    <div class="result-content">
                        <div class="result-title">${item.label}</div>
                        <div class="result-type">${item.type}</div>
                        ${item.properties ? `
                            <div class="result-properties">
                                ${Object.entries(item.properties)
                                    .map(([key, value]) => `<span>${key}: ${value}</span>`)
                                    .join('')}
                            </div>
                        ` : ''}
                    </div>
                </div>
            `;
        }

        if (item.type === 'edge') {
            return `
                <div class="result-item edge-result" data-id="${item.id}">
                    <div class="result-icon">
                        <i class="fas fa-arrow-right"></i>
                    </div>
                    <div class="result-content">
                        <div class="result-title">${item.label}</div>
                        <div class="result-nodes">
                            ${item.source} → ${item.target}
                        </div>
                        ${item.properties ? `
                            <div class="result-properties">
                                ${Object.entries(item.properties)
                                    .map(([key, value]) => `<span>${key}: ${value}</span>`)
                                    .join('')}
                            </div>
                        ` : ''}
                    </div>
                </div>
            `;
        }

        return '';
    }

    /**
     * 清空结果
     */
    clearResults() {
        const container = document.querySelector(this.container);
        const resultsDiv = container.querySelector('.query-results');
        if (resultsDiv) {
            resultsDiv.innerHTML = '';
        }
    }
}

// 导出查询面板
window.QueryPanel = QueryPanel;
