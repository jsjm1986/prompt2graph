import networkx as nx
import numpy as np
from collections import defaultdict
from typing import List, Dict, Tuple, Set, Optional
import community  # python-louvain
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
import concurrent.futures
from functools import lru_cache
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KnowledgeGraphAlgorithms:
    def __init__(self, entities: List[Dict], relations: List[Dict]):
        """初始化知识图谱算法类
        
        Args:
            entities: 实体列表，每个实体是一个字典，包含id、name、type等信息
            relations: 关系列表，每个关系是一个字典，包含source_id、target_id、type等信息
        """
        self.entities = entities
        self.relations = relations
        self.graph = self._build_networkx_graph()
        self._entity_text_cache = {}
        
    def _build_networkx_graph(self) -> nx.DiGraph:
        """构建NetworkX有向图，使用批量操作优化性能"""
        logger.info("Building NetworkX graph...")
        G = nx.DiGraph()
        
        # 批量添加节点
        nodes_data = [
            (entity['id'], {
                'name': entity['name'],
                'type': entity['type'],
                'properties': entity.get('properties', {})
            })
            for entity in self.entities
        ]
        G.add_nodes_from(nodes_data)
        
        # 批量添加边
        edges_data = [
            (relation['source_id'], 
             relation['target_id'], 
             {
                 'type': relation['relation_type'],
                 'weight': relation.get('confidence', 1.0),
                 'properties': relation.get('properties', {})
             })
            for relation in self.relations
        ]
        G.add_edges_from(edges_data)
        
        logger.info(f"Graph built with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")
        return G
    
    @lru_cache(maxsize=1024)
    def _get_entity_text(self, node_id: int) -> str:
        """获取实体的文本表示，使用缓存优化性能"""
        if node_id not in self._entity_text_cache:
            node = self.graph.nodes[node_id]
            text = f"{node['name']} {node['type']} {' '.join(str(v) for v in node['properties'].values())}"
            self._entity_text_cache[node_id] = text
        return self._entity_text_cache[node_id]
    
    def calculate_centrality_metrics(self) -> Dict[int, Dict[str, float]]:
        """并行计算节点的中心性指标"""
        logger.info("Calculating centrality metrics...")
        metrics = {}
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # 并行计算各种中心性指标
            future_degree = executor.submit(nx.degree_centrality, self.graph)
            future_between = executor.submit(nx.betweenness_centrality, self.graph)
            future_close = executor.submit(nx.closeness_centrality, self.graph)
            future_eigen = executor.submit(nx.eigenvector_centrality, self.graph, max_iter=1000)
            
            degree_cent = future_degree.result()
            between_cent = future_between.result()
            close_cent = future_close.result()
            eigen_cent = future_eigen.result()
        
        for node in self.graph.nodes():
            metrics[node] = {
                'degree': degree_cent[node],
                'betweenness': between_cent[node],
                'closeness': close_cent[node],
                'eigenvector': eigen_cent[node]
            }
        
        logger.info("Centrality metrics calculated")
        return metrics
    
    def detect_communities(self) -> Dict[int, int]:
        """使用Louvain算法检测社区，针对大规模图优化"""
        logger.info("Detecting communities...")
        
        # 转换为无向图并移除自环
        undirected_graph = self.graph.to_undirected()
        undirected_graph.remove_edges_from(nx.selfloop_edges(undirected_graph))
        
        # 使用Louvain算法检测社区
        communities = community.best_partition(undirected_graph)
        
        logger.info(f"Detected {len(set(communities.values()))} communities")
        return communities
    
    def find_shortest_path(self, source_id: int, target_id: int) -> Optional[List[int]]:
        """使用双向搜索优化最短路径查找"""
        logger.info(f"Finding shortest path between {source_id} and {target_id}...")
        try:
            path = nx.bidirectional_shortest_path(self.graph, source_id, target_id)
            return path
        except nx.NetworkXNoPath:
            return None
    
    def calculate_semantic_similarity(self, node1_id: int, node2_id: int) -> float:
        """使用缓存优化语义相似度计算"""
        text1 = self._get_entity_text(node1_id)
        text2 = self._get_entity_text(node2_id)
        
        vectorizer = TfidfVectorizer()
        try:
            tfidf_matrix = vectorizer.fit_transform([text1, text2])
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            return float(similarity)
        except:
            logger.warning(f"Failed to calculate similarity between {node1_id} and {node2_id}")
            return 0.0
    
    def find_important_subgraphs(self, min_size: int = 3) -> List[Set[int]]:
        """使用并行处理优化子图识别"""
        logger.info("Finding important subgraphs...")
        
        # 使用k-核分解找到密集连接的子图
        k_core = nx.k_core(self.graph.to_undirected())
        
        def process_component(comp):
            if len(comp) >= min_size:
                return comp
            return None
        
        # 并行处理连通分量
        with concurrent.futures.ThreadPoolExecutor() as executor:
            components = list(nx.connected_components(k_core))
            future_to_comp = {executor.submit(process_component, comp): comp 
                            for comp in components}
            
            important_subgraphs = []
            for future in concurrent.futures.as_completed(future_to_comp):
                result = future.result()
                if result is not None:
                    important_subgraphs.append(result)
        
        logger.info(f"Found {len(important_subgraphs)} important subgraphs")
        return important_subgraphs
    
    def recommend_relations(self, threshold: float = 0.5) -> List[Tuple[int, int, float]]:
        """使用并行处理和剪枝优化关系推荐"""
        logger.info("Generating relation recommendations...")
        recommendations = []
        nodes = list(self.graph.nodes())
        
        def process_node_pair(i, j):
            node1_id = nodes[i]
            node2_id = nodes[j]
            
            # 如果两个节点之间已经存在边，跳过
            if self.graph.has_edge(node1_id, node2_id) or \
               self.graph.has_edge(node2_id, node1_id):
                return None
            
            # 计算节点相似度
            similarity = self.calculate_semantic_similarity(node1_id, node2_id)
            
            if similarity > threshold:
                return (node1_id, node2_id, similarity)
            return None
        
        # 并行处理节点对
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_to_pair = {
                executor.submit(process_node_pair, i, j): (i, j)
                for i in range(len(nodes))
                for j in range(i + 1, len(nodes))
            }
            
            for future in concurrent.futures.as_completed(future_to_pair):
                result = future.result()
                if result is not None:
                    recommendations.append(result)
        
        # 按相似度降序排序
        recommendations.sort(key=lambda x: x[2], reverse=True)
        logger.info(f"Generated {len(recommendations)} recommendations")
        return recommendations
    
    def analyze_relation_patterns(self) -> Dict[str, List[Tuple[str, str]]]:
        """优化关系模式分析"""
        logger.info("Analyzing relation patterns...")
        patterns = defaultdict(set)  # 使用set避免重复模式
        
        for edge in self.graph.edges(data=True):
            source_id, target_id = edge[0], edge[1]
            relation_type = edge[2]['type']
            source_type = self.graph.nodes[source_id]['type']
            target_type = self.graph.nodes[target_id]['type']
            
            patterns[relation_type].add((source_type, target_type))
        
        # 转换回列表格式
        return {k: list(v) for k, v in patterns.items()}
    
    def calculate_graph_metrics(self) -> Dict[str, float]:
        """并行计算图的整体指标"""
        logger.info("Calculating graph metrics...")
        metrics = {}
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # 并行计算基本指标
            future_density = executor.submit(nx.density, self.graph)
            future_clustering = executor.submit(
                nx.average_clustering, self.graph.to_undirected())
            future_reciprocity = executor.submit(nx.reciprocity, self.graph)
            
            metrics['density'] = future_density.result()
            metrics['average_clustering'] = future_clustering.result()
            metrics['reciprocity'] = future_reciprocity.result()
        
        # 添加基本统计信息
        metrics['number_of_nodes'] = self.graph.number_of_nodes()
        metrics['number_of_edges'] = self.graph.number_of_edges()
        
        # 计算最大连通分量的指标
        largest_cc = max(nx.weakly_connected_components(self.graph), key=len)
        subgraph = self.graph.subgraph(largest_cc)
        
        try:
            metrics['average_shortest_path_length'] = nx.average_shortest_path_length(subgraph)
            metrics['diameter'] = nx.diameter(subgraph)
        except nx.NetworkXError:
            metrics['average_shortest_path_length'] = float('inf')
            metrics['diameter'] = float('inf')
            logger.warning("Graph is not strongly connected, some metrics are set to infinity")
        
        logger.info("Graph metrics calculated")
        return metrics
