import networkx as nx
from typing import List, Dict, Any, Optional, Set, Tuple
import logging
from dataclasses import dataclass
from datetime import datetime
from collections import defaultdict
import re
from cache_manager import GraphCacheManager
from performance_monitor import PerformanceMonitor

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class QueryResult:
    """查询结果数据类"""
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    paths: List[List[str]]
    confidence: float
    execution_time: float
    query_type: str
    timestamp: str

class QueryEngine:
    """知识图谱查询引擎"""
    
    def __init__(self):
        self.graph = None
        self.cache_manager = GraphCacheManager()
        self.performance_monitor = PerformanceMonitor()
        self.relation_patterns = self._load_relation_patterns()
    
    def _load_relation_patterns(self) -> Dict[str, List[str]]:
        """加载关系模式"""
        return {
            "is_a": ["是", "属于", "类型是", "分类为"],
            "part_of": ["包含", "组成部分", "属于", "构成"],
            "related_to": ["相关", "关联", "连接", "链接"],
            "causes": ["导致", "引起", "造成", "产生"],
            "used_for": ["用于", "用途是", "应用于", "服务于"],
            "located_in": ["位于", "在", "处于", "坐落于"],
            "time_of": ["发生于", "时间是", "日期是", "期间"],
            "has_property": ["特征是", "属性是", "特点是", "性质是"]
        }
    
    def set_graph(self, graph: nx.DiGraph):
        """设置查询图"""
        self.graph = graph
    
    def natural_language_query(self, query: str, use_cache: bool = True) -> QueryResult:
        """自然语言查询接口"""
        with self.performance_monitor.track_operation("natural_language_query"):
            # 检查缓存
            if use_cache:
                cache_key = f"nlq_{hash(query)}"
                cached_result = self.cache_manager.get(cache_key)
                if cached_result:
                    logger.info("使用缓存的查询结果")
                    return cached_result
            
            # 解析查询类型和关键实体
            query_type, entities, relations = self._parse_query(query)
            
            # 根据查询类型执行相应的查询
            if query_type == "path":
                result = self._find_paths(entities[0], entities[1])
            elif query_type == "neighbors":
                result = self._find_neighbors(entities[0], relations)
            elif query_type == "subgraph":
                result = self._extract_subgraph(entities, relations)
            else:
                result = self._general_search(entities, relations)
            
            # 缓存结果
            if use_cache:
                self.cache_manager.set(cache_key, result)
            
            return result
    
    def _parse_query(self, query: str) -> Tuple[str, List[str], List[str]]:
        """解析自然语言查询"""
        # 识别查询类型
        path_patterns = ["路径", "关系", "联系", "如何联系"]
        neighbor_patterns = ["相关", "相邻", "周围", "附近"]
        subgraph_patterns = ["子图", "局部", "区域", "范围"]
        
        query_type = "general"
        for pattern in path_patterns:
            if pattern in query:
                query_type = "path"
                break
        for pattern in neighbor_patterns:
            if pattern in query:
                query_type = "neighbors"
                break
        for pattern in subgraph_patterns:
            if pattern in query:
                query_type = "subgraph"
                break
        
        # 提取实体和关系
        entities = []
        relations = []
        
        # 使用预定义的关系模式匹配
        for relation_type, patterns in self.relation_patterns.items():
            for pattern in patterns:
                if pattern in query:
                    relations.append(relation_type)
                    # 分割查询以提取实体
                    parts = query.split(pattern)
                    if len(parts) >= 2:
                        entities.extend([p.strip() for p in parts if p.strip()])
        
        # 如果没有找到关系，尝试提取命名实体
        if not relations:
            # 这里可以集成更复杂的NER系统
            words = query.split()
            entities = [w for w in words if w not in ["的", "和", "与", "在", "是"]]
        
        return query_type, list(set(entities)), list(set(relations))
    
    def _find_paths(self, source: str, target: str, max_length: int = 3) -> QueryResult:
        """查找两个实体之间的路径"""
        start_time = datetime.now()
        
        # 查找源节点和目标节点的实际ID
        source_nodes = self._find_matching_nodes(source)
        target_nodes = self._find_matching_nodes(target)
        
        if not source_nodes or not target_nodes:
            return self._create_empty_result("path")
        
        paths = []
        nodes = set()
        edges = []
        
        # 对每对源节点和目标节点寻找路径
        for s in source_nodes:
            for t in target_nodes:
                try:
                    # 使用NetworkX的所有简单路径算法
                    for path in nx.all_simple_paths(self.graph, s, t, cutoff=max_length):
                        paths.append(path)
                        # 收集路径上的节点和边
                        nodes.update(path)
                        for i in range(len(path) - 1):
                            edges.append((path[i], path[i + 1]))
                except nx.NetworkXNoPath:
                    continue
        
        # 构建结果
        node_data = [
            {
                'id': node,
                'properties': self.graph.nodes[node]
            }
            for node in nodes
        ]
        
        edge_data = [
            {
                'source': source,
                'target': target,
                'properties': self.graph.edges[source, target]
            }
            for source, target in edges
        ]
        
        # 计算置信度
        confidence = min(1.0, len(paths) / 5.0) if paths else 0.0
        
        return QueryResult(
            nodes=node_data,
            edges=edge_data,
            paths=paths,
            confidence=confidence,
            execution_time=(datetime.now() - start_time).total_seconds(),
            query_type="path",
            timestamp=datetime.now().isoformat()
        )
    
    def _find_neighbors(self, entity: str, relations: List[str], max_depth: int = 2) -> QueryResult:
        """查找实体的邻居"""
        start_time = datetime.now()
        
        # 查找匹配的节点
        source_nodes = self._find_matching_nodes(entity)
        
        if not source_nodes:
            return self._create_empty_result("neighbors")
        
        nodes = set()
        edges = set()
        
        # 对每个源节点进行广度优先搜索
        for source in source_nodes:
            current_depth = 0
            current_layer = {source}
            visited = {source}
            
            while current_depth < max_depth and current_layer:
                next_layer = set()
                
                for node in current_layer:
                    # 获取所有相邻节点
                    neighbors = set(self.graph.predecessors(node)) | set(self.graph.successors(node))
                    
                    for neighbor in neighbors:
                        if neighbor not in visited:
                            # 检查关系类型是否匹配
                            edge_data = self.graph.get_edge_data(node, neighbor) or \
                                      self.graph.get_edge_data(neighbor, node)
                            
                            if not relations or any(r in str(edge_data) for r in relations):
                                next_layer.add(neighbor)
                                visited.add(neighbor)
                                edges.add((node, neighbor))
                
                nodes.update(next_layer)
                current_layer = next_layer
                current_depth += 1
        
        # 构建结果
        node_data = [
            {
                'id': node,
                'properties': self.graph.nodes[node]
            }
            for node in nodes
        ]
        
        edge_data = [
            {
                'source': source,
                'target': target,
                'properties': self.graph.edges[source, target]
                if self.graph.has_edge(source, target)
                else self.graph.edges[target, source]
            }
            for source, target in edges
        ]
        
        # 计算置信度
        confidence = min(1.0, len(nodes) / (10.0 * max_depth)) if nodes else 0.0
        
        return QueryResult(
            nodes=node_data,
            edges=edge_data,
            paths=[],  # 邻居查询不返回路径
            confidence=confidence,
            execution_time=(datetime.now() - start_time).total_seconds(),
            query_type="neighbors",
            timestamp=datetime.now().isoformat()
        )
    
    def _extract_subgraph(self, entities: List[str], relations: List[str]) -> QueryResult:
        """提取子图"""
        start_time = datetime.now()
        
        nodes = set()
        edges = set()
        
        # 为每个实体找到匹配的节点
        for entity in entities:
            matching_nodes = self._find_matching_nodes(entity)
            nodes.update(matching_nodes)
        
        # 构建节点之间的所有可能路径
        node_list = list(nodes)
        for i in range(len(node_list)):
            for j in range(i + 1, len(node_list)):
                try:
                    paths = list(nx.all_simple_paths(
                        self.graph, node_list[i], node_list[j], cutoff=2
                    ))
                    for path in paths:
                        nodes.update(path)
                        for k in range(len(path) - 1):
                            edges.add((path[k], path[k + 1]))
                except (nx.NetworkXNoPath, nx.NodeNotFound):
                    continue
        
        # 构建结果
        node_data = [
            {
                'id': node,
                'properties': self.graph.nodes[node]
            }
            for node in nodes
        ]
        
        edge_data = [
            {
                'source': source,
                'target': target,
                'properties': self.graph.edges[source, target]
            }
            for source, target in edges
        ]
        
        # 计算置信度
        coverage = len(nodes) / len(entities) if entities else 0
        density = len(edges) / (len(nodes) * (len(nodes) - 1)) if len(nodes) > 1 else 0
        confidence = (coverage + density) / 2
        
        return QueryResult(
            nodes=node_data,
            edges=edge_data,
            paths=[],  # 子图查询不返回路径
            confidence=confidence,
            execution_time=(datetime.now() - start_time).total_seconds(),
            query_type="subgraph",
            timestamp=datetime.now().isoformat()
        )
    
    def _general_search(self, entities: List[str], relations: List[str]) -> QueryResult:
        """通用搜索"""
        start_time = datetime.now()
        
        nodes = set()
        edges = set()
        
        # 查找所有匹配的节点
        for entity in entities:
            matching_nodes = self._find_matching_nodes(entity)
            nodes.update(matching_nodes)
        
        # 扩展到相关节点
        expanded_nodes = set()
        for node in nodes:
            # 获取直接相连的节点
            neighbors = set(self.graph.predecessors(node)) | set(self.graph.successors(node))
            for neighbor in neighbors:
                edge_data = self.graph.get_edge_data(node, neighbor) or \
                           self.graph.get_edge_data(neighbor, node)
                
                # 检查关系是否匹配
                if not relations or any(r in str(edge_data) for r in relations):
                    expanded_nodes.add(neighbor)
                    edges.add((node, neighbor))
        
        nodes.update(expanded_nodes)
        
        # 构建结果
        node_data = [
            {
                'id': node,
                'properties': self.graph.nodes[node]
            }
            for node in nodes
        ]
        
        edge_data = [
            {
                'source': source,
                'target': target,
                'properties': self.graph.edges[source, target]
            }
            for source, target in edges
        ]
        
        # 计算置信度
        entity_coverage = len(nodes) / len(entities) if entities else 0
        relation_coverage = len(edges) / len(relations) if relations else 0
        confidence = (entity_coverage + relation_coverage) / 2 if entities or relations else 0
        
        return QueryResult(
            nodes=node_data,
            edges=edge_data,
            paths=[],  # 通用搜索不返回路径
            confidence=confidence,
            execution_time=(datetime.now() - start_time).total_seconds(),
            query_type="general",
            timestamp=datetime.now().isoformat()
        )
    
    def _find_matching_nodes(self, entity: str) -> Set[str]:
        """查找匹配的节点"""
        matching_nodes = set()
        
        for node, data in self.graph.nodes(data=True):
            # 检查节点ID
            if entity.lower() in str(node).lower():
                matching_nodes.add(node)
                continue
            
            # 检查节点属性
            for value in data.values():
                if entity.lower() in str(value).lower():
                    matching_nodes.add(node)
                    break
        
        return matching_nodes
    
    def _create_empty_result(self, query_type: str) -> QueryResult:
        """创建空结果"""
        return QueryResult(
            nodes=[],
            edges=[],
            paths=[],
            confidence=0.0,
            execution_time=0.0,
            query_type=query_type,
            timestamp=datetime.now().isoformat()
        )
