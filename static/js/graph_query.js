/**
 * 图谱查询管理器
 */
class GraphQuery {
    constructor() {
        this.nodes = new Map();
        this.edges = new Map();
        this.nodeIndex = new Map();
        this.edgeIndex = new Map();
    }

    /**
     * 设置图数据
     */
    setData(nodes, edges) {
        this.nodes.clear();
        this.edges.clear();
        this.nodeIndex.clear();
        this.edgeIndex.clear();
        
        // 构建节点索引
        nodes.forEach(node => {
            this.nodes.set(node.id, node);
            this.indexNode(node);
        });
        
        // 构建边索引
        edges.forEach(edge => {
            this.edges.set(edge.id, edge);
            this.indexEdge(edge);
        });
    }

    /**
     * 索引节点
     */
    indexNode(node) {
        // 索引标签
        this.addToIndex(this.nodeIndex, 'label', node.label.toLowerCase(), node);
        
        // 索引类型
        if (node.type) {
            this.addToIndex(this.nodeIndex, 'type', node.type.toLowerCase(), node);
        }
        
        // 索引属性
        if (node.properties) {
            Object.entries(node.properties).forEach(([key, value]) => {
                this.addToIndex(this.nodeIndex, key, String(value).toLowerCase(), node);
            });
        }
    }

    /**
     * 索引边
     */
    indexEdge(edge) {
        // 索引标签
        this.addToIndex(this.edgeIndex, 'label', edge.label.toLowerCase(), edge);
        
        // 索引属性
        if (edge.properties) {
            Object.entries(edge.properties).forEach(([key, value]) => {
                this.addToIndex(this.edgeIndex, key, String(value).toLowerCase(), edge);
            });
        }
    }

    /**
     * 添加到索引
     */
    addToIndex(index, key, value, item) {
        if (!index.has(key)) {
            index.set(key, new Map());
        }
        
        const valueIndex = index.get(key);
        if (!valueIndex.has(value)) {
            valueIndex.set(value, new Set());
        }
        
        valueIndex.get(value).add(item);
    }

    /**
     * 按类型查询节点
     */
    queryNodesByType(type) {
        return this.queryNodesByProperty('type', type);
    }

    /**
     * 按标签查询节点
     */
    queryNodesByLabel(label) {
        return this.queryNodesByProperty('label', label);
    }

    /**
     * 按属性查询节点
     */
    queryNodesByProperty(key, value) {
        const valueIndex = this.nodeIndex.get(key);
        if (!valueIndex) return new Set();
        
        const results = valueIndex.get(String(value).toLowerCase());
        return results || new Set();
    }

    /**
     * 按标签查询边
     */
    queryEdgesByLabel(label) {
        return this.queryEdgesByProperty('label', label);
    }

    /**
     * 按属性查询边
     */
    queryEdgesByProperty(key, value) {
        const valueIndex = this.edgeIndex.get(key);
        if (!valueIndex) return new Set();
        
        const results = valueIndex.get(String(value).toLowerCase());
        return results || new Set();
    }

    /**
     * 模糊查询节点
     */
    fuzzyQueryNodes(text) {
        text = text.toLowerCase();
        const results = new Set();
        
        // 搜索标签
        this.nodes.forEach(node => {
            if (node.label.toLowerCase().includes(text)) {
                results.add(node);
            }
        });
        
        // 搜索属性
        this.nodes.forEach(node => {
            if (node.properties) {
                Object.values(node.properties).forEach(value => {
                    if (String(value).toLowerCase().includes(text)) {
                        results.add(node);
                    }
                });
            }
        });
        
        return results;
    }

    /**
     * 模糊查询边
     */
    fuzzyQueryEdges(text) {
        text = text.toLowerCase();
        const results = new Set();
        
        // 搜索标签
        this.edges.forEach(edge => {
            if (edge.label.toLowerCase().includes(text)) {
                results.add(edge);
            }
        });
        
        // 搜索属性
        this.edges.forEach(edge => {
            if (edge.properties) {
                Object.values(edge.properties).forEach(value => {
                    if (String(value).toLowerCase().includes(text)) {
                        results.add(edge);
                    }
                });
            }
        });
        
        return results;
    }

    /**
     * 路径查询
     */
    queryPath(startNode, endNode, maxDepth = 5) {
        const visited = new Set();
        const paths = [];
        
        const dfs = (current, path) => {
            if (path.length > maxDepth) return;
            if (current === endNode) {
                paths.push([...path]);
                return;
            }
            
            visited.add(current);
            
            this.edges.forEach(edge => {
                if (edge.source === current && !visited.has(edge.target)) {
                    path.push(edge);
                    dfs(edge.target, path);
                    path.pop();
                }
            });
            
            visited.delete(current);
        };
        
        dfs(startNode, []);
        return paths;
    }

    /**
     * 邻居查询
     */
    queryNeighbors(nodeId, depth = 1) {
        const neighbors = new Set();
        const visited = new Set([nodeId]);
        let currentLevel = new Set([nodeId]);
        
        for (let i = 0; i < depth; i++) {
            const nextLevel = new Set();
            
            currentLevel.forEach(current => {
                this.edges.forEach(edge => {
                    if (edge.source === current && !visited.has(edge.target)) {
                        nextLevel.add(edge.target);
                        neighbors.add(this.nodes.get(edge.target));
                        visited.add(edge.target);
                    }
                    if (edge.target === current && !visited.has(edge.source)) {
                        nextLevel.add(edge.source);
                        neighbors.add(this.nodes.get(edge.source));
                        visited.add(edge.source);
                    }
                });
            });
            
            if (nextLevel.size === 0) break;
            currentLevel = nextLevel;
        }
        
        return neighbors;
    }

    /**
     * 复杂查询
     */
    complexQuery(query) {
        const results = new Set();
        
        // 解析查询条件
        const conditions = this.parseQuery(query);
        
        // 执行查询
        this.nodes.forEach(node => {
            if (this.matchConditions(node, conditions)) {
                results.add(node);
            }
        });
        
        return results;
    }

    /**
     * 解析查询语句
     */
    parseQuery(query) {
        // 简单的查询语法解析
        // 示例: type=Person AND (age>20 OR role=admin)
        const conditions = [];
        const tokens = query.split(/\s+(?:AND|OR)\s+/);
        
        tokens.forEach(token => {
            const match = token.match(/(\w+)(=|>|<|>=|<=)(.+)/);
            if (match) {
                conditions.push({
                    field: match[1],
                    operator: match[2],
                    value: match[3]
                });
            }
        });
        
        return conditions;
    }

    /**
     * 匹配查询条件
     */
    matchConditions(node, conditions) {
        return conditions.every(condition => {
            const value = node.properties?.[condition.field] || node[condition.field];
            if (value === undefined) return false;
            
            switch (condition.operator) {
                case '=':
                    return String(value).toLowerCase() === String(condition.value).toLowerCase();
                case '>':
                    return Number(value) > Number(condition.value);
                case '<':
                    return Number(value) < Number(condition.value);
                case '>=':
                    return Number(value) >= Number(condition.value);
                case '<=':
                    return Number(value) <= Number(condition.value);
                default:
                    return false;
            }
        });
    }
}

// 导出查询器
window.GraphQuery = GraphQuery;
