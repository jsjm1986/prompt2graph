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
                'avg_degree': self.metrics.avg_degree
            },
            'structure_info': {
                'clustering_coefficient': self.metrics.clustering_coefficient,
                'components_count': self.metrics.components_count,
                'avg_path_length': self.metrics.avg_path_length,
                'diameter': self.metrics.diameter
            },
            'top_nodes': [
                {'id': node_id, 'importance': score}
                for node_id, score in self.metrics.top_nodes
            ],
            'communities': [
                {'size': len(community), 'nodes': community}
                for community in self.metrics.communities
            ]
        }
