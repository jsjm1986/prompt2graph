/**
 * 图谱分析管理器
 */
class GraphAnalyzer {
    constructor() {
        this.graph = null;
        this.nodes = new Map();
        this.edges = new Map();
    }

    /**
     * 设置图数据
     */
    setData(nodes, edges) {
        this.nodes.clear();
        this.edges.clear();
        
        nodes.forEach(node => this.nodes.set(node.id, node));
        edges.forEach(edge => this.edges.set(edge.id, edge));
        
        this.graph = this.buildAdjacencyList();
    }

    /**
     * 构建邻接表
     */
    buildAdjacencyList() {
        const graph = new Map();
        
        this.nodes.forEach((node, id) => {
            graph.set(id, new Set());
        });
        
        this.edges.forEach(edge => {
            graph.get(edge.source).add(edge.target);
            graph.get(edge.target).add(edge.source); // 无向图
        });
        
        return graph;
    }

    /**
     * 计算度中心性
     */
    calculateDegreeCentrality() {
        const centrality = new Map();
        
        this.graph.forEach((neighbors, nodeId) => {
            centrality.set(nodeId, neighbors.size);
        });
        
        return centrality;
    }

    /**
     * 计算接近中心性
     */
    calculateClosenessCentrality() {
        const centrality = new Map();
        
        this.nodes.forEach((_, startNode) => {
            const distances = this.shortestPaths(startNode);
            let sum = 0;
            
            distances.forEach((distance, _) => {
                if (distance !== Infinity) {
                    sum += distance;
                }
            });
            
            centrality.set(startNode, sum > 0 ? (distances.size - 1) / sum : 0);
        });
        
        return centrality;
    }

    /**
     * 计算介数中心性
     */
    calculateBetweennessCentrality() {
        const centrality = new Map();
        this.nodes.forEach((_, node) => centrality.set(node, 0));
        
        this.nodes.forEach((_, startNode) => {
            const stack = [];
            const predecessors = new Map();
            const sigma = new Map();
            const delta = new Map();
            const distances = new Map();
            
            // 初始化
            this.nodes.forEach((_, node) => {
                predecessors.set(node, []);
                sigma.set(node, 0);
                delta.set(node, 0);
                distances.set(node, -1);
            });
            
            sigma.set(startNode, 1);
            distances.set(startNode, 0);
            
            const queue = [startNode];
            
            // BFS
            while (queue.length > 0) {
                const node = queue.shift();
                stack.push(node);
                
                this.graph.get(node).forEach(neighbor => {
                    // 首次访问
                    if (distances.get(neighbor) < 0) {
                        queue.push(neighbor);
                        distances.set(neighbor, distances.get(node) + 1);
                    }
                    
                    // 最短路径
                    if (distances.get(neighbor) === distances.get(node) + 1) {
                        sigma.set(neighbor, sigma.get(neighbor) + sigma.get(node));
                        predecessors.get(neighbor).push(node);
                    }
                });
            }
            
            // 累积依赖
            while (stack.length > 0) {
                const node = stack.pop();
                predecessors.get(node).forEach(pred => {
                    const coeff = (sigma.get(pred) / sigma.get(node)) * (1 + delta.get(node));
                    delta.set(pred, delta.get(pred) + coeff);
                });
                
                if (node !== startNode) {
                    centrality.set(node, centrality.get(node) + delta.get(node));
                }
            }
        });
        
        return centrality;
    }

    /**
     * 计算特征向量中心性
     */
    calculateEigenvectorCentrality(iterations = 100, tolerance = 1e-6) {
        const centrality = new Map();
        let prevCentrality = new Map();
        
        // 初始化
        this.nodes.forEach((_, node) => {
            centrality.set(node, 1);
            prevCentrality.set(node, 0);
        });
        
        // 幂迭代法
        for (let i = 0; i < iterations; i++) {
            let diff = 0;
            const temp = new Map(centrality);
            
            this.nodes.forEach((_, node) => {
                let sum = 0;
                this.graph.get(node).forEach(neighbor => {
                    sum += centrality.get(neighbor);
                });
                temp.set(node, sum);
            });
            
            // 归一化
            let norm = 0;
            temp.forEach(value => norm += value * value);
            norm = Math.sqrt(norm);
            
            temp.forEach((value, node) => {
                const normalizedValue = norm > 0 ? value / norm : 0;
                diff += Math.abs(normalizedValue - prevCentrality.get(node));
                prevCentrality.set(node, normalizedValue);
                centrality.set(node, normalizedValue);
            });
            
            if (diff < tolerance) break;
        }
        
        return centrality;
    }

    /**
     * 社区检测 (Louvain算法)
     */
    detectCommunities() {
        const communities = new Map();
        let bestModularity = -1;
        
        // 初始化社区
        this.nodes.forEach((_, node) => {
            communities.set(node, node);
        });
        
        let improved = true;
        while (improved) {
            improved = false;
            
            this.nodes.forEach((_, node) => {
                const neighborCommunities = new Map();
                let bestCommunity = communities.get(node);
                let maxGain = 0;
                
                // 计算邻居社区
                this.graph.get(node).forEach(neighbor => {
                    const community = communities.get(neighbor);
                    neighborCommunities.set(community, (neighborCommunities.get(community) || 0) + 1);
                });
                
                // 计算模块度增益
                neighborCommunities.forEach((count, community) => {
                    const gain = this.calculateModularityGain(node, community, communities);
                    if (gain > maxGain) {
                        maxGain = gain;
                        bestCommunity = community;
                    }
                });
                
                // 更新社区
                if (bestCommunity !== communities.get(node)) {
                    communities.set(node, bestCommunity);
                    improved = true;
                }
            });
            
            const modularity = this.calculateModularity(communities);
            if (modularity > bestModularity) {
                bestModularity = modularity;
            } else {
                break;
            }
        }
        
        return communities;
    }

    /**
     * 计算模块度
     */
    calculateModularity(communities) {
        let modularity = 0;
        const m = this.edges.size;
        
        this.edges.forEach(edge => {
            if (communities.get(edge.source) === communities.get(edge.target)) {
                const ki = this.graph.get(edge.source).size;
                const kj = this.graph.get(edge.target).size;
                modularity += 1 - (ki * kj) / (2 * m);
            }
        });
        
        return modularity / (2 * m);
    }

    /**
     * 计算模块度增益
     */
    calculateModularityGain(node, newCommunity, communities) {
        const oldCommunity = communities.get(node);
        if (oldCommunity === newCommunity) return 0;
        
        let gain = 0;
        const ki = this.graph.get(node).size;
        const m = this.edges.size;
        
        this.graph.get(node).forEach(neighbor => {
            if (communities.get(neighbor) === newCommunity) {
                gain += 1;
            }
            if (communities.get(neighbor) === oldCommunity) {
                gain -= 1;
            }
        });
        
        return gain;
    }

    /**
     * 最短路径算法(Dijkstra)
     */
    shortestPaths(startNode) {
        const distances = new Map();
        const visited = new Set();
        
        // 初始化距离
        this.nodes.forEach((_, node) => {
            distances.set(node, Infinity);
        });
        distances.set(startNode, 0);
        
        while (visited.size < this.nodes.size) {
            // 找到最近的未访问节点
            let minDistance = Infinity;
            let current = null;
            
            distances.forEach((distance, node) => {
                if (!visited.has(node) && distance < minDistance) {
                    minDistance = distance;
                    current = node;
                }
            });
            
            if (current === null) break;
            
            visited.add(current);
            
            // 更新邻居距离
            this.graph.get(current).forEach(neighbor => {
                if (!visited.has(neighbor)) {
                    const distance = distances.get(current) + 1;
                    if (distance < distances.get(neighbor)) {
                        distances.set(neighbor, distance);
                    }
                }
            });
        }
        
        return distances;
    }

    /**
     * 计算聚类系数
     */
    calculateClusteringCoefficient() {
        const coefficients = new Map();
        
        this.nodes.forEach((_, node) => {
            const neighbors = this.graph.get(node);
            if (neighbors.size < 2) {
                coefficients.set(node, 0);
                return;
            }
            
            let triangles = 0;
            const possibleTriangles = (neighbors.size * (neighbors.size - 1)) / 2;
            
            neighbors.forEach(neighbor1 => {
                neighbors.forEach(neighbor2 => {
                    if (neighbor1 < neighbor2 && this.graph.get(neighbor1).has(neighbor2)) {
                        triangles++;
                    }
                });
            });
            
            coefficients.set(node, triangles / possibleTriangles);
        });
        
        return coefficients;
    }

    /**
     * 计算图的基本统计信息
     */
    calculateGraphStatistics() {
        const stats = {
            nodeCount: this.nodes.size,
            edgeCount: this.edges.size,
            averageDegree: 0,
            density: 0,
            diameter: 0,
            averagePathLength: 0,
            globalClusteringCoefficient: 0
        };
        
        // 平均度
        const degreeCentrality = this.calculateDegreeCentrality();
        let totalDegree = 0;
        degreeCentrality.forEach(degree => totalDegree += degree);
        stats.averageDegree = totalDegree / this.nodes.size;
        
        // 密度
        stats.density = (2 * this.edges.size) / (this.nodes.size * (this.nodes.size - 1));
        
        // 直径和平均路径长度
        let maxDistance = 0;
        let totalDistance = 0;
        let pathCount = 0;
        
        this.nodes.forEach((_, startNode) => {
            const distances = this.shortestPaths(startNode);
            distances.forEach((distance, endNode) => {
                if (startNode !== endNode && distance !== Infinity) {
                    maxDistance = Math.max(maxDistance, distance);
                    totalDistance += distance;
                    pathCount++;
                }
            });
        });
        
        stats.diameter = maxDistance;
        stats.averagePathLength = pathCount > 0 ? totalDistance / pathCount : 0;
        
        // 全局聚类系数
        const clusteringCoefficients = this.calculateClusteringCoefficient();
        let totalClustering = 0;
        clusteringCoefficients.forEach(coeff => totalClustering += coeff);
        stats.globalClusteringCoefficient = totalClustering / this.nodes.size;
        
        return stats;
    }
}

// 导出分析器
window.GraphAnalyzer = GraphAnalyzer;
