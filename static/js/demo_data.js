/**
 * 示例数据生成器
 */
class DemoDataGenerator {
    /**
     * 生成随机图数据
     * @param {number} nodeCount 节点数量
     * @param {number} edgeCount 边数量
     * @returns {Object} 图数据
     */
    static generateRandomGraph(nodeCount = 50, edgeCount = 100) {
        const nodes = [];
        const edges = [];
        
        // 生成节点
        for (let i = 0; i < nodeCount; i++) {
            nodes.push({
                id: `node${i}`,
                label: `Node ${i}`,
                type: ['Person', 'Organization', 'Location'][Math.floor(Math.random() * 3)],
                properties: {
                    weight: Math.random() * 10,
                    created: new Date(Date.now() - Math.random() * 365 * 24 * 60 * 60 * 1000)
                }
            });
        }
        
        // 生成边
        for (let i = 0; i < edgeCount; i++) {
            const source = nodes[Math.floor(Math.random() * nodes.length)];
            const target = nodes[Math.floor(Math.random() * nodes.length)];
            
            if (source !== target) {
                edges.push({
                    id: `edge${i}`,
                    source: source.id,
                    target: target.id,
                    label: ['knows', 'works_with', 'lives_in'][Math.floor(Math.random() * 3)],
                    properties: {
                        weight: Math.random(),
                        since: new Date(Date.now() - Math.random() * 365 * 24 * 60 * 60 * 1000)
                    }
                });
            }
        }
        
        return { nodes, edges };
    }
    
    /**
     * 生成组织结构图
     * @returns {Object} 图数据
     */
    static generateOrgChart() {
        const nodes = [
            { id: 'CEO', label: 'CEO', type: 'Person' },
            { id: 'CTO', label: 'CTO', type: 'Person' },
            { id: 'CFO', label: 'CFO', type: 'Person' },
            { id: 'Dev1', label: 'Developer 1', type: 'Person' },
            { id: 'Dev2', label: 'Developer 2', type: 'Person' },
            { id: 'Dev3', label: 'Developer 3', type: 'Person' },
            { id: 'PM1', label: 'Project Manager 1', type: 'Person' },
            { id: 'PM2', label: 'Project Manager 2', type: 'Person' },
            { id: 'ACC1', label: 'Accountant 1', type: 'Person' },
            { id: 'ACC2', label: 'Accountant 2', type: 'Person' }
        ];
        
        const edges = [
            { id: 'e1', source: 'CEO', target: 'CTO', label: 'manages' },
            { id: 'e2', source: 'CEO', target: 'CFO', label: 'manages' },
            { id: 'e3', source: 'CTO', target: 'PM1', label: 'manages' },
            { id: 'e4', source: 'CTO', target: 'PM2', label: 'manages' },
            { id: 'e5', source: 'PM1', target: 'Dev1', label: 'manages' },
            { id: 'e6', source: 'PM1', target: 'Dev2', label: 'manages' },
            { id: 'e7', source: 'PM2', target: 'Dev3', label: 'manages' },
            { id: 'e8', source: 'CFO', target: 'ACC1', label: 'manages' },
            { id: 'e9', source: 'CFO', target: 'ACC2', label: 'manages' }
        ];
        
        return { nodes, edges };
    }
    
    /**
     * 生成社交网络图
     * @param {number} userCount 用户数量
     * @returns {Object} 图数据
     */
    static generateSocialNetwork(userCount = 20) {
        const nodes = [];
        const edges = [];
        
        // 生成用户节点
        for (let i = 0; i < userCount; i++) {
            nodes.push({
                id: `user${i}`,
                label: `User ${i}`,
                type: 'Person',
                properties: {
                    age: 20 + Math.floor(Math.random() * 40),
                    gender: Math.random() > 0.5 ? 'male' : 'female',
                    joinDate: new Date(Date.now() - Math.random() * 365 * 24 * 60 * 60 * 1000)
                }
            });
        }
        
        // 生成好友关系
        nodes.forEach(user => {
            const friendCount = Math.floor(Math.random() * 5) + 1;
            for (let i = 0; i < friendCount; i++) {
                const friend = nodes[Math.floor(Math.random() * nodes.length)];
                if (friend !== user) {
                    edges.push({
                        id: `friendship_${user.id}_${friend.id}`,
                        source: user.id,
                        target: friend.id,
                        label: 'friends',
                        properties: {
                            since: new Date(Date.now() - Math.random() * 365 * 24 * 60 * 60 * 1000)
                        }
                    });
                }
            }
        });
        
        return { nodes, edges };
    }
    
    /**
     * 生成知识图谱
     * @returns {Object} 图数据
     */
    static generateKnowledgeGraph() {
        const nodes = [
            { id: 'AI', label: 'Artificial Intelligence', type: 'Concept' },
            { id: 'ML', label: 'Machine Learning', type: 'Concept' },
            { id: 'DL', label: 'Deep Learning', type: 'Concept' },
            { id: 'NN', label: 'Neural Network', type: 'Concept' },
            { id: 'CNN', label: 'Convolutional Neural Network', type: 'Concept' },
            { id: 'RNN', label: 'Recurrent Neural Network', type: 'Concept' },
            { id: 'SVM', label: 'Support Vector Machine', type: 'Concept' },
            { id: 'NLP', label: 'Natural Language Processing', type: 'Concept' },
            { id: 'CV', label: 'Computer Vision', type: 'Concept' },
            { id: 'RL', label: 'Reinforcement Learning', type: 'Concept' }
        ];
        
        const edges = [
            { id: 'e1', source: 'AI', target: 'ML', label: 'includes' },
            { id: 'e2', source: 'ML', target: 'DL', label: 'includes' },
            { id: 'e3', source: 'DL', target: 'NN', label: 'uses' },
            { id: 'e4', source: 'NN', target: 'CNN', label: 'type_of' },
            { id: 'e5', source: 'NN', target: 'RNN', label: 'type_of' },
            { id: 'e6', source: 'ML', target: 'SVM', label: 'includes' },
            { id: 'e7', source: 'AI', target: 'NLP', label: 'includes' },
            { id: 'e8', source: 'AI', target: 'CV', label: 'includes' },
            { id: 'e9', source: 'AI', target: 'RL', label: 'includes' },
            { id: 'e10', source: 'DL', target: 'CV', label: 'used_in' },
            { id: 'e11', source: 'DL', target: 'NLP', label: 'used_in' },
            { id: 'e12', source: 'CNN', target: 'CV', label: 'used_in' },
            { id: 'e13', source: 'RNN', target: 'NLP', label: 'used_in' }
        ];
        
        return { nodes, edges };
    }
}

// 导出数据生成器
window.DemoDataGenerator = DemoDataGenerator;
