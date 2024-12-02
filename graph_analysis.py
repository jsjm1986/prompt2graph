import networkx as nx
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
import logging
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class GraphMetrics:
    """图分析指标数据类"""
    timestamp: str
    node_count: int
    edge_count: int
    density: float
    avg_degree: float
    clustering_coefficient: float
    components_count: int
    avg_path_length: Optional[float]
    diameter: Optional[int]
    top_nodes: List[Tuple[str, float]]
    communities: List[List[str]]

class GraphAnalyzer:
    """知识图谱分析器"""
    
    def __init__(self):
        self.graph = None
        self.metrics = None
    
    def build_graph(self, relations: List[Any]) -> nx.DiGraph:
        """构建NetworkX图"""
        self.graph = nx.DiGraph()
        
        # 添加节点和边
        for relation in relations:
            # 添加节点
            self.graph.add_node(relation.source.id, 
                              name=relation.source.name,
                              type=relation.source.type,
                              properties=relation.source.properties)
            
            self.graph.add_node(relation.target.id,
                              name=relation.target.name,
                              type=relation.target.type,
                              properties=relation.target.properties)
            
            # 添加边
            self.graph.add_edge(relation.source.id, relation.target.id,
                              type=relation.relation_type,
                              confidence=getattr(relation, 'confidence', 1.0),
                              properties=relation.properties)
        
        return self.graph
    
    def analyze(self, relations: List[Any]) -> GraphMetrics:
        """执行全面的图分析"""
        if not self.graph:
            self.build_graph(relations)
        
        try:
            # 基础指标
            node_count = self.graph.number_of_nodes()
            edge_count = self.graph.number_of_edges()
            density = nx.density(self.graph)
            avg_degree = edge_count / node_count if node_count > 0 else 0
            
            # 聚类系数
            clustering_coefficient = nx.average_clustering(self.graph.to_undirected())
            
            # 连通性分析
            undirected = self.graph.to_undirected()
            components = list(nx.connected_components(undirected))
            components_count = len(components)
            
            # 路径分析
            largest_component = max(components, key=len)
            subgraph = undirected.subgraph(largest_component)
            
            try:
                avg_path_length = nx.average_shortest_path_length(subgraph)
                diameter = nx.diameter(subgraph)
            except nx.NetworkXError:
                avg_path_length = None
                diameter = None
            
            # 中心性分析
            pagerank = nx.pagerank(self.graph)
            top_nodes = sorted(pagerank.items(), key=lambda x: x[1], reverse=True)[:10]
            
            # 社区发现
            communities = list(nx.community.greedy_modularity_communities(undirected))
            community_lists = [[node for node in community] for community in communities]
            
            # 创建指标对象
            self.metrics = GraphMetrics(
                timestamp=datetime.now().isoformat(),
                node_count=node_count,
                edge_count=edge_count,
                density=density,
                avg_degree=avg_degree,
                clustering_coefficient=clustering_coefficient,
                components_count=components_count,
                avg_path_length=avg_path_length,
                diameter=diameter,
                top_nodes=top_nodes,
                communities=community_lists
            )
            
            return self.metrics
        
        except Exception as e:
            logger.error(f"图分析过程中发生错误: {str(e)}")
            raise
    
    def find_shortest_path(self, source_id: str, target_id: str) -> Optional[List[str]]:
        """查找最短路径"""
        try:
            path = nx.shortest_path(self.graph, source_id, target_id)
            return path
        except nx.NetworkXNoPath:
            return None
    
    def find_all_paths(self, source_id: str, target_id: str, cutoff: int = 3) -> List[List[str]]:
        """查找所有路径（限制长度）"""
        try:
            paths = list(nx.all_simple_paths(self.graph, source_id, target_id, cutoff=cutoff))
            return paths
        except nx.NetworkXNoPath:
            return []
    
    def get_node_importance(self, node_id: str) -> Dict[str, float]:
        """计算节点重要性指标"""
        if not self.graph:
            return {}
        
        metrics = {
            'degree_centrality': nx.degree_centrality(self.graph)[node_id],
            'in_degree_centrality': nx.in_degree_centrality(self.graph)[node_id],
            'out_degree_centrality': nx.out_degree_centrality(self.graph)[node_id],
            'pagerank': nx.pagerank(self.graph)[node_id],
            'betweenness_centrality': nx.betweenness_centrality(self.graph)[node_id]
        }
        
        return metrics
    
    def find_similar_nodes(self, node_id: str, top_k: int = 5) -> List[Tuple[str, float]]:
        """查找相似节点"""
        if not self.graph or node_id not in self.graph:
            return []
        
        # 基于共同邻居的相似度
        neighbors = set(self.graph.predecessors(node_id)) | set(self.graph.successors(node_id))
        similarity_scores = []
        
        for other_node in self.graph.nodes():
            if other_node != node_id:
                other_neighbors = set(self.graph.predecessors(other_node)) | \
                                set(self.graph.successors(other_node))
                
                # Jaccard相似度
                similarity = len(neighbors & other_neighbors) / len(neighbors | other_neighbors) \
                           if len(neighbors | other_neighbors) > 0 else 0
                
                similarity_scores.append((other_node, similarity))
        
        # 返回top-k个相似节点
        return sorted(similarity_scores, key=lambda x: x[1], reverse=True)[:top_k]
    
    def get_subgraph(self, node_ids: List[str], depth: int = 1) -> nx.DiGraph:
        """获取子图"""
        if not self.graph:
            return nx.DiGraph()
        
        subgraph_nodes = set(node_ids)
        
        # 按深度扩展
        for _ in range(depth):
            new_nodes = set()
            for node in subgraph_nodes:
                new_nodes.update(self.graph.predecessors(node))
                new_nodes.update(self.graph.successors(node))
            subgraph_nodes.update(new_nodes)
        
        return self.graph.subgraph(subgraph_nodes)
    
    def get_graph_summary(self) -> Dict[str, Any]:
        """获取图摘要"""
        if not self.metrics:
            return {}
        
        return {
            'basic_info': {
                'node_count': self.metrics.node_count,
                'edge_count': self.metrics.edge_count,
                'density': self.metrics.density,
                'avg_degree': self.metrics.avg_degree,
                'clustering_coefficient': self.metrics.clustering_coefficient,
                'components_count': self.metrics.components_count
            },
            'path_analysis': {
                'avg_path_length': self.metrics.avg_path_length,
                'diameter': self.metrics.diameter
            },
            'top_nodes': self.metrics.top_nodes,
            'community_sizes': [len(comm) for comm in self.metrics.communities]
        }

    def analyze_temporal_patterns(self, time_window: int = 7) -> Dict[str, Any]:
        """分析时序模式
        
        Args:
            time_window: 时间窗口大小（天）
            
        Returns:
            Dict: 包含时序分析结果
        """
        if not self.graph:
            return {}
            
        try:
            # 获取边的时间戳
            edge_times = nx.get_edge_attributes(self.graph, 'timestamp')
            if not edge_times:
                return {}
                
            # 转换时间戳
            from datetime import datetime, timedelta
            current_time = datetime.now()
            window_start = current_time - timedelta(days=time_window)
            
            # 统计时间窗口内的活动
            activity_count = defaultdict(int)
            relation_count = defaultdict(int)
            
            for edge, timestamp in edge_times.items():
                if isinstance(timestamp, str):
                    timestamp = datetime.fromisoformat(timestamp)
                if timestamp >= window_start:
                    day = timestamp.date()
                    activity_count[day] += 1
                    relation_count[self.graph.edges[edge]['type']] += 1
            
            return {
                'daily_activity': dict(activity_count),
                'relation_distribution': dict(relation_count),
                'total_activity': sum(activity_count.values())
            }
        except Exception as e:
            logger.error(f"时序分析错误: {str(e)}")
            return {}

    def detect_anomalies(self) -> List[Dict[str, Any]]:
        """检测图中的异常模式"""
        anomalies = []
        
        try:
            # 检测度数异常
            degrees = dict(self.graph.degree())
            mean_degree = np.mean(list(degrees.values()))
            std_degree = np.std(list(degrees.values()))
            threshold = mean_degree + 2 * std_degree
            
            for node, degree in degrees.items():
                if degree > threshold:
                    anomalies.append({
                        'type': 'high_degree',
                        'node_id': node,
                        'value': degree,
                        'threshold': threshold
                    })
            
            # 检测聚类系数异常
            clustering = nx.clustering(self.graph)
            mean_clustering = np.mean(list(clustering.values()))
            std_clustering = np.std(list(clustering.values()))
            
            for node, coef in clustering.items():
                if coef > mean_clustering + 2 * std_clustering:
                    anomalies.append({
                        'type': 'high_clustering',
                        'node_id': node,
                        'value': coef,
                        'threshold': mean_clustering + 2 * std_clustering
                    })
            
            # 检测孤立节点
            for node in self.graph.nodes():
                if self.graph.degree(node) == 0:
                    anomalies.append({
                        'type': 'isolated_node',
                        'node_id': node
                    })
            
            return anomalies
        except Exception as e:
            logger.error(f"异常检测错误: {str(e)}")
            return []

    def analyze_relation_patterns(self) -> Dict[str, Any]:
        """分析关系模式"""
        if not self.graph:
            return {}
            
        try:
            patterns = {
                'type_distribution': defaultdict(int),
                'bidirectional_relations': [],
                'cycles': [],
                'hubs': [],
                'authorities': []
            }
            
            # 统计关系类型分布
            for _, _, data in self.graph.edges(data=True):
                patterns['type_distribution'][data.get('type', 'unknown')] += 1
            
            # 查找双向关系
            for u, v in self.graph.edges():
                if self.graph.has_edge(v, u):
                    patterns['bidirectional_relations'].append((u, v))
            
            # 查找环路
            try:
                cycles = list(nx.simple_cycles(self.graph))
                patterns['cycles'] = [cycle for cycle in cycles if len(cycle) <= 5]
            except:
                pass
            
            # 识别中心节点
            in_degrees = self.graph.in_degree()
            out_degrees = self.graph.out_degree()
            
            # 查找枢纽节点（高出度）
            patterns['hubs'] = sorted(
                [(node, d) for node, d in out_degrees if d > np.mean(list(dict(out_degrees).values()))],
                key=lambda x: x[1],
                reverse=True
            )[:5]
            
            # 查找权威节点（高入度）
            patterns['authorities'] = sorted(
                [(node, d) for node, d in in_degrees if d > np.mean(list(dict(in_degrees).values()))],
                key=lambda x: x[1],
                reverse=True
            )[:5]
            
            return patterns
        except Exception as e:
            logger.error(f"关系模式分析错误: {str(e)}")
            return {}

    def predict_missing_relations(self, min_confidence: float = 0.5) -> List[Dict[str, Any]]:
        """预测可能存在的关系"""
        predictions = []
        
        try:
            # 基于共同邻居的链接预测
            for u in self.graph.nodes():
                for v in self.graph.nodes():
                    if u != v and not self.graph.has_edge(u, v):
                        # 获取共同邻居
                        u_neighbors = set(self.graph.neighbors(u))
                        v_neighbors = set(self.graph.neighbors(v))
                        common_neighbors = u_neighbors & v_neighbors
                        
                        if len(common_neighbors) > 0:
                            # 计算Jaccard系数
                            similarity = len(common_neighbors) / len(u_neighbors | v_neighbors)
                            
                            if similarity >= min_confidence:
                                # 推测最可能的关系类型
                                relation_types = defaultdict(int)
                                for n in common_neighbors:
                                    edge_type = self.graph.edges[u, n].get('type', '')
                                    relation_types[edge_type] += 1
                                
                                most_likely_type = max(relation_types.items(), key=lambda x: x[1])[0]
                                
                                predictions.append({
                                    'source': u,
                                    'target': v,
                                    'confidence': similarity,
                                    'predicted_type': most_likely_type,
                                    'common_neighbors': list(common_neighbors)
                                })
            
            # 按置信度排序
            predictions.sort(key=lambda x: x['confidence'], reverse=True)
            return predictions
        except Exception as e:
            logger.error(f"关系预测错误: {str(e)}")
            return []

    def get_node_influence(self, node_id: str) -> Dict[str, float]:
        """计算节点影响力指标"""
        if not self.graph or node_id not in self.graph:
            return {}
            
        try:
            metrics = {}
            
            # PageRank分数
            pagerank = nx.pagerank(self.graph)
            metrics['pagerank'] = pagerank[node_id]
            
            # HITS分数
            hits = nx.hits(self.graph)
            metrics['hub_score'] = hits[0][node_id]
            metrics['authority_score'] = hits[1][node_id]
            
            # 介数中心性
            metrics['betweenness'] = nx.betweenness_centrality(self.graph)[node_id]
            
            # 接近中心性
            metrics['closeness'] = nx.closeness_centrality(self.graph)[node_id]
            
            # 特征向量中心性
            metrics['eigenvector'] = nx.eigenvector_centrality(self.graph)[node_id]
            
            return metrics
        except Exception as e:
            logger.error(f"节点影响力计算错误: {str(e)}")
            return {}
