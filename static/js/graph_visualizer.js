/**
 * 图谱可视化管理器
 */
class GraphVisualizer {
    /**
     * 构造函数
     * @param {Object} options 配置选项
     */
    constructor(options = {}) {
        this.container = options.container || '#graph-container';
        this.width = options.width || 800;
        this.height = options.height || 600;
        this.nodeSize = options.nodeSize || 10;
        this.edgeWidth = options.edgeWidth || 1;
        this.showLabels = options.showLabels !== undefined ? options.showLabels : true;
        
        this.simulation = null;
        this.svg = null;
        this.zoom = null;
        this.transform = null;
        
        this.nodes = [];
        this.edges = [];
        
        this.selectedNode = null;
        this.highlightedNodes = new Set();
        this.highlightedEdges = new Set();
        
        this.events = {};
        this.initialized = false;
    }
    
    /**
     * 初始化可视化
     */
    init() {
        if (this.initialized) return;
        
        // 创建SVG容器
        this.svg = d3.select(this.container)
            .append('svg')
            .attr('width', '100%')
            .attr('height', '100%')
            .attr('viewBox', [0, 0, this.width, this.height]);
        
        // 创建缩放行为
        this.zoom = d3.zoom()
            .scaleExtent([0.1, 10])
            .on('zoom', (event) => {
                this.transform = event.transform;
                this.svg.select('g').attr('transform', event.transform);
            });
        
        // 应用缩放
        this.svg.call(this.zoom);
        
        // 创建主图层
        this.svg.append('g');
        
        // 创建力导向模拟
        this.simulation = d3.forceSimulation()
            .force('link', d3.forceLink().id(d => d.id))
            .force('charge', d3.forceManyBody().strength(-100))
            .force('center', d3.forceCenter(this.width / 2, this.height / 2))
            .force('collision', d3.forceCollide().radius(this.nodeSize * 2));
        
        this.initialized = true;
    }
    
    /**
     * 设置数据
     * @param {Array} nodes 节点数据
     * @param {Array} edges 边数据
     */
    setData(nodes, edges) {
        this.nodes = nodes;
        this.edges = edges;
        this.updateVisualization();
    }
    
    /**
     * 更新可视化
     */
    updateVisualization() {
        const svg = this.svg.select('g');
        
        // 创建边
        const edge = svg.selectAll('.edge')
            .data(this.edges, d => d.id)
            .join(
                enter => this.createEdges(enter),
                update => this.updateEdges(update),
                exit => this.removeEdges(exit)
            );
        
        // 创建节点
        const node = svg.selectAll('.node')
            .data(this.nodes, d => d.id)
            .join(
                enter => this.createNodes(enter),
                update => this.updateNodes(update),
                exit => this.removeNodes(exit)
            );
        
        // 更新力导向模拟
        this.simulation
            .nodes(this.nodes)
            .force('link').links(this.edges);
        
        this.simulation.alpha(1).restart();
    }
    
    /**
     * 创建边元素
     */
    createEdges(enter) {
        const edge = enter.append('g')
            .attr('class', 'edge');
        
        edge.append('line')
            .attr('stroke', '#999')
            .attr('stroke-width', this.edgeWidth)
            .attr('stroke-opacity', 0.6);
        
        if (this.showLabels) {
            edge.append('text')
                .attr('class', 'edge-label')
                .attr('text-anchor', 'middle')
                .attr('dy', -5)
                .text(d => d.label || '');
        }
        
        return edge;
    }
    
    /**
     * 更新边元素
     */
    updateEdges(update) {
        update.select('line')
            .attr('stroke-width', this.edgeWidth);
        
        if (this.showLabels) {
            update.select('.edge-label')
                .text(d => d.label || '');
        }
        
        return update;
    }
    
    /**
     * 移除边元素
     */
    removeEdges(exit) {
        return exit.remove();
    }
    
    /**
     * 创建节点元素
     */
    createNodes(enter) {
        const node = enter.append('g')
            .attr('class', 'node')
            .call(this.drag());
        
        node.append('circle')
            .attr('r', this.nodeSize)
            .attr('fill', d => this.getNodeColor(d))
            .attr('stroke', '#fff')
            .attr('stroke-width', 1.5);
        
        if (this.showLabels) {
            node.append('text')
                .attr('class', 'node-label')
                .attr('dx', this.nodeSize + 5)
                .attr('dy', '.35em')
                .text(d => d.label || d.id);
        }
        
        node.on('click', (event, d) => this.handleNodeClick(event, d))
            .on('mouseover', (event, d) => this.handleNodeMouseOver(event, d))
            .on('mouseout', (event, d) => this.handleNodeMouseOut(event, d));
        
        return node;
    }
    
    /**
     * 更新节点元素
     */
    updateNodes(update) {
        update.select('circle')
            .attr('r', this.nodeSize)
            .attr('fill', d => this.getNodeColor(d));
        
        if (this.showLabels) {
            update.select('.node-label')
                .text(d => d.label || d.id);
        }
        
        return update;
    }
    
    /**
     * 移除节点元素
     */
    removeNodes(exit) {
        return exit.remove();
    }
    
    /**
     * 获取节点颜色
     */
    getNodeColor(node) {
        if (this.selectedNode === node) {
            return '#ff4444';
        }
        if (this.highlightedNodes.has(node)) {
            return '#44ff44';
        }
        return node.color || '#4444ff';
    }
    
    /**
     * 创建拖拽行为
     */
    drag() {
        return d3.drag()
            .on('start', (event, d) => {
                if (!event.active) this.simulation.alphaTarget(0.3).restart();
                d.fx = d.x;
                d.fy = d.y;
            })
            .on('drag', (event, d) => {
                d.fx = event.x;
                d.fy = event.y;
            })
            .on('end', (event, d) => {
                if (!event.active) this.simulation.alphaTarget(0);
                d.fx = null;
                d.fy = null;
            });
    }
    
    /**
     * 处理节点点击
     */
    handleNodeClick(event, node) {
        this.selectedNode = this.selectedNode === node ? null : node;
        this.updateVisualization();
        this.emit('nodeClick', node);
    }
    
    /**
     * 处理节点鼠标悬停
     */
    handleNodeMouseOver(event, node) {
        this.highlightedNodes.add(node);
        // 高亮相关节点和边
        this.edges.forEach(edge => {
            if (edge.source === node || edge.target === node) {
                this.highlightedEdges.add(edge);
                this.highlightedNodes.add(edge.source);
                this.highlightedNodes.add(edge.target);
            }
        });
        this.updateVisualization();
        this.emit('nodeMouseOver', node);
    }
    
    /**
     * 处理节点鼠标离开
     */
    handleNodeMouseOut(event, node) {
        this.highlightedNodes.clear();
        this.highlightedEdges.clear();
        this.updateVisualization();
        this.emit('nodeMouseOut', node);
    }
    
    /**
     * 缩放到适应屏幕
     */
    fitToScreen() {
        const bounds = this.svg.select('g').node().getBBox();
        const parent = this.svg.node().parentElement;
        const fullWidth = parent.clientWidth;
        const fullHeight = parent.clientHeight;
        
        const midX = bounds.x + bounds.width / 2;
        const midY = bounds.y + bounds.height / 2;
        
        const scale = 0.8 * Math.min(
            fullWidth / bounds.width,
            fullHeight / bounds.height
        );
        
        const transform = d3.zoomIdentity
            .translate(fullWidth / 2 - scale * midX, fullHeight / 2 - scale * midY)
            .scale(scale);
        
        this.svg.transition()
            .duration(750)
            .call(this.zoom.transform, transform);
    }
    
    /**
     * 放大
     */
    zoomIn() {
        this.svg.transition()
            .duration(300)
            .call(this.zoom.scaleBy, 1.2);
    }
    
    /**
     * 缩小
     */
    zoomOut() {
        this.svg.transition()
            .duration(300)
            .call(this.zoom.scaleBy, 0.8);
    }
    
    /**
     * 切换布局
     */
    setLayout(type) {
        switch (type) {
            case 'force':
                this.simulation
                    .force('link', d3.forceLink().id(d => d.id))
                    .force('charge', d3.forceManyBody().strength(-100))
                    .force('center', d3.forceCenter(this.width / 2, this.height / 2));
                break;
            
            case 'circular':
                this.simulation
                    .force('link', d3.forceLink().id(d => d.id))
                    .force('charge', null)
                    .force('center', null)
                    .force('radial', d3.forceRadial(
                        Math.min(this.width, this.height) / 3,
                        this.width / 2,
                        this.height / 2
                    ));
                break;
            
            case 'hierarchical':
                // 使用dagre布局
                const g = new dagre.graphlib.Graph();
                g.setGraph({});
                g.setDefaultEdgeLabel(() => ({}));
                
                this.nodes.forEach(node => g.setNode(node.id, {
                    width: this.nodeSize * 2,
                    height: this.nodeSize * 2
                }));
                this.edges.forEach(edge => g.setEdge(edge.source.id, edge.target.id));
                
                dagre.layout(g);
                
                this.nodes.forEach(node => {
                    const n = g.node(node.id);
                    node.x = n.x;
                    node.y = n.y;
                });
                
                this.simulation.stop();
                this.updateVisualization();
                break;
            
            case 'grid':
                const cols = Math.ceil(Math.sqrt(this.nodes.length));
                const gridSize = Math.min(this.width, this.height) / (cols + 1);
                
                this.nodes.forEach((node, i) => {
                    node.x = (i % cols + 1) * gridSize;
                    node.y = (Math.floor(i / cols) + 1) * gridSize;
                });
                
                this.simulation.stop();
                this.updateVisualization();
                break;
        }
        
        if (type !== 'hierarchical' && type !== 'grid') {
            this.simulation.alpha(1).restart();
        }
    }
    
    /**
     * 注册事件监听
     */
    on(event, callback) {
        if (!this.events[event]) {
            this.events[event] = [];
        }
        this.events[event].push(callback);
    }
    
    /**
     * 触发事件
     */
    emit(event, data) {
        if (this.events[event]) {
            this.events[event].forEach(callback => callback(data));
        }
    }
    
    /**
     * 设置选项
     */
    setOptions(options) {
        Object.assign(this, options);
        this.updateVisualization();
    }
    
    /**
     * 销毁实例
     */
    destroy() {
        if (this.simulation) {
            this.simulation.stop();
        }
        if (this.svg) {
            this.svg.remove();
        }
        this.events = {};
        this.initialized = false;
    }
}

// 导出可视化管理器
window.GraphVisualizer = GraphVisualizer;
