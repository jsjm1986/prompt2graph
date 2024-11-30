/**
 * 分析面板组件
 */
class AnalysisPanel {
    constructor(options = {}) {
        this.container = options.container || '#analysis-panel';
        this.analyzer = options.analyzer || null;
        this.onAnalysis = options.onAnalysis || (() => {});
        
        this.charts = new Map();
        this.init();
    }

    /**
     * 初始化面板
     */
    init() {
        const container = document.querySelector(this.container);
        if (!container) return;

        container.innerHTML = `
            <div class="analysis-tabs">
                <button class="tab-btn active" data-tab="statistics" data-i18n="analysis.statistics">统计分析</button>
                <button class="tab-btn" data-tab="centrality" data-i18n="analysis.centrality">中心性分析</button>
                <button class="tab-btn" data-tab="community" data-i18n="analysis.community">社区分析</button>
                <button class="tab-btn" data-tab="path" data-i18n="analysis.path">路径分析</button>
            </div>

            <div class="analysis-content">
                <div class="tab-panel active" data-panel="statistics">
                    <div class="stat-cards">
                        <div class="stat-card" id="basicStats">
                            <h3 data-i18n="analysis.basicStats">基础统计</h3>
                            <div class="stat-content"></div>
                        </div>
                        <div class="stat-card" id="degreeStats">
                            <h3 data-i18n="analysis.degreeStats">度分布</h3>
                            <div class="stat-content">
                                <canvas></canvas>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="tab-panel" data-panel="centrality">
                    <div class="centrality-options">
                        <select id="centralityType" class="form-select">
                            <option value="degree" data-i18n="analysis.degreeCentrality">度中心性</option>
                            <option value="closeness" data-i18n="analysis.closenessCentrality">接近中心性</option>
                            <option value="betweenness" data-i18n="analysis.betweennessCentrality">介数中心性</option>
                            <option value="eigenvector" data-i18n="analysis.eigenvectorCentrality">特征向量中心性</option>
                        </select>
                        <button class="btn btn-primary" id="calculateCentrality" data-i18n="analysis.calculate">计算</button>
                    </div>
                    <div class="centrality-chart">
                        <canvas></canvas>
                    </div>
                    <div class="centrality-table"></div>
                </div>

                <div class="tab-panel" data-panel="community">
                    <div class="community-options">
                        <button class="btn btn-primary" id="detectCommunities" data-i18n="analysis.detect">检测社区</button>
                        <div class="community-stats"></div>
                    </div>
                    <div class="community-chart">
                        <canvas></canvas>
                    </div>
                </div>

                <div class="tab-panel" data-panel="path">
                    <div class="path-stats">
                        <div class="stat-card">
                            <h3 data-i18n="analysis.averagePath">平均路径长度</h3>
                            <div class="stat-value"></div>
                        </div>
                        <div class="stat-card">
                            <h3 data-i18n="analysis.diameter">图直径</h3>
                            <div class="stat-value"></div>
                        </div>
                    </div>
                    <div class="path-distribution">
                        <canvas></canvas>
                    </div>
                </div>
            </div>
        `;

        this.bindEvents();
        this.initCharts();
    }

    /**
     * 绑定事件
     */
    bindEvents() {
        const container = document.querySelector(this.container);

        // 标签切换
        container.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                container.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
                container.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
                
                btn.classList.add('active');
                container.querySelector(`[data-panel="${btn.dataset.tab}"]`).classList.add('active');
                
                // 重新渲染图表
                this.resizeCharts();
            });
        });

        // 中心性分析
        const calculateBtn = container.querySelector('#calculateCentrality');
        calculateBtn.addEventListener('click', () => {
            const type = container.querySelector('#centralityType').value;
            this.calculateCentrality(type);
        });

        // 社区检测
        const detectBtn = container.querySelector('#detectCommunities');
        detectBtn.addEventListener('click', () => {
            this.detectCommunities();
        });
    }

    /**
     * 初始化图表
     */
    initCharts() {
        // 度分布图表
        this.charts.set('degree', new Chart(
            document.querySelector('#degreeStats canvas'),
            {
                type: 'bar',
                data: {
                    labels: [],
                    datasets: [{
                        label: '节点数量',
                        data: [],
                        backgroundColor: 'rgba(54, 162, 235, 0.5)'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            }
        ));

        // 中心性图表
        this.charts.set('centrality', new Chart(
            document.querySelector('.centrality-chart canvas'),
            {
                type: 'scatter',
                data: {
                    datasets: [{
                        label: '节点中心性',
                        data: [],
                        backgroundColor: 'rgba(255, 99, 132, 0.5)'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: {
                            type: 'linear',
                            position: 'bottom'
                        },
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            }
        ));

        // 社区图表
        this.charts.set('community', new Chart(
            document.querySelector('.community-chart canvas'),
            {
                type: 'pie',
                data: {
                    labels: [],
                    datasets: [{
                        data: [],
                        backgroundColor: []
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false
                }
            }
        ));

        // 路径分布图表
        this.charts.set('path', new Chart(
            document.querySelector('.path-distribution canvas'),
            {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: '路径数量',
                        data: [],
                        borderColor: 'rgb(75, 192, 192)',
                        tension: 0.1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            }
        ));
    }

    /**
     * 更新基础统计
     */
    updateBasicStats(stats) {
        const container = document.querySelector('#basicStats .stat-content');
        container.innerHTML = `
            <div class="stat-item">
                <span class="stat-label" data-i18n="analysis.nodes">节点数：</span>
                <span class="stat-value">${stats.nodeCount}</span>
            </div>
            <div class="stat-item">
                <span class="stat-label" data-i18n="analysis.edges">边数：</span>
                <span class="stat-value">${stats.edgeCount}</span>
            </div>
            <div class="stat-item">
                <span class="stat-label" data-i18n="analysis.averageDegree">平均度：</span>
                <span class="stat-value">${stats.averageDegree.toFixed(2)}</span>
            </div>
            <div class="stat-item">
                <span class="stat-label" data-i18n="analysis.density">密度：</span>
                <span class="stat-value">${stats.density.toFixed(4)}</span>
            </div>
            <div class="stat-item">
                <span class="stat-label" data-i18n="analysis.clustering">聚类系数：</span>
                <span class="stat-value">${stats.globalClusteringCoefficient.toFixed(4)}</span>
            </div>
        `;
    }

    /**
     * 更新度分布
     */
    updateDegreeDistribution(distribution) {
        const chart = this.charts.get('degree');
        chart.data.labels = Object.keys(distribution);
        chart.data.datasets[0].data = Object.values(distribution);
        chart.update();
    }

    /**
     * 计算中心性
     */
    calculateCentrality(type) {
        if (!this.analyzer) return;

        let centrality;
        switch (type) {
            case 'degree':
                centrality = this.analyzer.calculateDegreeCentrality();
                break;
            case 'closeness':
                centrality = this.analyzer.calculateClosenessCentrality();
                break;
            case 'betweenness':
                centrality = this.analyzer.calculateBetweennessCentrality();
                break;
            case 'eigenvector':
                centrality = this.analyzer.calculateEigenvectorCentrality();
                break;
        }

        this.updateCentralityChart(centrality);
        this.updateCentralityTable(centrality);
    }

    /**
     * 更新中心性图表
     */
    updateCentralityChart(centrality) {
        const chart = this.charts.get('centrality');
        const data = Array.from(centrality.entries()).map((node, index) => ({
            x: index,
            y: node[1]
        }));

        chart.data.datasets[0].data = data;
        chart.update();
    }

    /**
     * 更新中心性表格
     */
    updateCentralityTable(centrality) {
        const container = document.querySelector('.centrality-table');
        const sorted = Array.from(centrality.entries())
            .sort((a, b) => b[1] - a[1])
            .slice(0, 10);

        container.innerHTML = `
            <table class="table">
                <thead>
                    <tr>
                        <th data-i18n="analysis.rank">排名</th>
                        <th data-i18n="analysis.node">节点</th>
                        <th data-i18n="analysis.value">值</th>
                    </tr>
                </thead>
                <tbody>
                    ${sorted.map((node, index) => `
                        <tr>
                            <td>${index + 1}</td>
                            <td>${node[0]}</td>
                            <td>${node[1].toFixed(4)}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
    }

    /**
     * 检测社区
     */
    detectCommunities() {
        if (!this.analyzer) return;

        const communities = this.analyzer.detectCommunities();
        this.updateCommunityChart(communities);
        this.updateCommunityStats(communities);
    }

    /**
     * 更新社区图表
     */
    updateCommunityChart(communities) {
        const chart = this.charts.get('community');
        const counts = new Map();

        communities.forEach(community => {
            counts.set(community, (counts.get(community) || 0) + 1);
        });

        chart.data.labels = Array.from(counts.keys()).map(c => `社区 ${c}`);
        chart.data.datasets[0].data = Array.from(counts.values());
        chart.data.datasets[0].backgroundColor = this.generateColors(counts.size);
        chart.update();
    }

    /**
     * 更新社区统计
     */
    updateCommunityStats(communities) {
        const container = document.querySelector('.community-stats');
        const communityCount = new Set(communities.values()).size;
        const modularity = this.analyzer.calculateModularity(communities);

        container.innerHTML = `
            <div class="stat-item">
                <span class="stat-label" data-i18n="analysis.communityCount">社区数：</span>
                <span class="stat-value">${communityCount}</span>
            </div>
            <div class="stat-item">
                <span class="stat-label" data-i18n="analysis.modularity">模块度：</span>
                <span class="stat-value">${modularity.toFixed(4)}</span>
            </div>
        `;
    }

    /**
     * 更新路径分析
     */
    updatePathAnalysis(stats) {
        // 更新统计值
        document.querySelector('.path-stats .stat-value:first-child')
            .textContent = stats.averagePathLength.toFixed(2);
        document.querySelector('.path-stats .stat-value:last-child')
            .textContent = stats.diameter;

        // 更新分布图表
        const chart = this.charts.get('path');
        const distribution = stats.pathLengthDistribution;

        chart.data.labels = Object.keys(distribution);
        chart.data.datasets[0].data = Object.values(distribution);
        chart.update();
    }

    /**
     * 生成颜色
     */
    generateColors(count) {
        const colors = [];
        for (let i = 0; i < count; i++) {
            const hue = (i * 360 / count) % 360;
            colors.push(`hsla(${hue}, 70%, 60%, 0.7)`);
        }
        return colors;
    }

    /**
     * 调整图表大小
     */
    resizeCharts() {
        this.charts.forEach(chart => chart.resize());
    }

    /**
     * 设置分析器
     */
    setAnalyzer(analyzer) {
        this.analyzer = analyzer;
    }
}

// 导出分析面板
window.AnalysisPanel = AnalysisPanel;
