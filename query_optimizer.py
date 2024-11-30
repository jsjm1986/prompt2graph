import networkx as nx
from typing import List, Dict, Any, Optional, Set, Tuple
import logging
from dataclasses import dataclass
from datetime import datetime
import numpy as np
from collections import defaultdict
from cache_manager import GraphCacheManager
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class QueryPlan:
    """查询执行计划"""
    steps: List[Dict[str, Any]]
    estimated_cost: float
    cache_hits: int
    optimization_time: float

@dataclass
class QuerySuggestion:
    """查询建议"""
    original_query: str
    suggested_query: str
    confidence: float
    explanation: str
    example_results: Optional[Dict[str, Any]] = None

class QueryOptimizer:
    """查询优化器"""
    
    def __init__(self):
        self.graph = None
        self.cache_manager = GraphCacheManager()
        self.query_patterns = self._load_query_patterns()
        self.query_history: List[Dict[str, Any]] = []
        self.vectorizer = TfidfVectorizer(
            token_pattern=r'[^,，。！？\s]+',
            stop_words=['的', '是', '在', '与', '和', '及']
        )
    
    def _load_query_patterns(self) -> Dict[str, Dict[str, Any]]:
        """加载查询模式"""
        return {
            "path_query": {
                "patterns": ["路径", "关系", "联系", "之间"],
                "template": "查找 {entity1} 和 {entity2} 之间的关系",
                "cost_factors": {
                    "node_count": 0.4,
                    "path_length": 0.3,
                    "cache_hit": -0.5
                }
            },
            "neighbor_query": {
                "patterns": ["相关", "相似", "类似", "周围"],
                "template": "查找与 {entity} 相关的 {relation_type}",
                "cost_factors": {
                    "neighbor_count": 0.3,
                    "depth": 0.4,
                    "cache_hit": -0.5
                }
            },
            "subgraph_query": {
                "patterns": ["子图", "区域", "领域", "范围"],
                "template": "提取关于 {topic} 的知识子图",
                "cost_factors": {
                    "node_count": 0.5,
                    "edge_density": 0.3,
                    "cache_hit": -0.4
                }
            }
        }
    
    def set_graph(self, graph: nx.DiGraph):
        """设置图数据"""
        self.graph = graph
    
    def optimize_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> QueryPlan:
        """优化查询"""
        start_time = datetime.now()
        
        # 1. 分析查询类型和模式
        query_type, entities = self._analyze_query(query)
        
        # 2. 检查缓存
        cache_key = f"query_{hash(query)}"
        cache_hits = 1 if self.cache_manager.get(cache_key) else 0
        
        # 3. 估算查询成本
        base_cost = self._estimate_base_cost(query_type, entities)
        cache_benefit = cache_hits * self.query_patterns[query_type]["cost_factors"]["cache_hit"]
        final_cost = max(0.1, base_cost + cache_benefit)
        
        # 4. 生成执行计划
        steps = self._generate_execution_steps(query_type, entities, context)
        
        # 5. 记录查询历史
        self.query_history.append({
            "query": query,
            "type": query_type,
            "entities": entities,
            "cost": final_cost,
            "timestamp": datetime.now().isoformat()
        })
        
        return QueryPlan(
            steps=steps,
            estimated_cost=final_cost,
            cache_hits=cache_hits,
            optimization_time=(datetime.now() - start_time).total_seconds()
        )
    
    def suggest_queries(self, query: str, max_suggestions: int = 3) -> List[QuerySuggestion]:
        """生成查询建议"""
        suggestions = []
        
        # 1. 基于历史查询的建议
        if self.query_history:
            historical_queries = [h["query"] for h in self.query_history]
            historical_queries.append(query)
            
            # 计算查询之间的相似度
            try:
                tfidf_matrix = self.vectorizer.fit_transform(historical_queries)
                similarities = cosine_similarity(
                    tfidf_matrix[-1:], tfidf_matrix[:-1]
                )[0]
                
                # 获取最相似的查询
                for idx in np.argsort(similarities)[-max_suggestions:]:
                    if similarities[idx] > 0.3:  # 相似度阈值
                        similar_query = historical_queries[idx]
                        suggestions.append(
                            QuerySuggestion(
                                original_query=query,
                                suggested_query=similar_query,
                                confidence=float(similarities[idx]),
                                explanation="基于历史查询模式"
                            )
                        )
            except Exception as e:
                logger.warning(f"计算查询相似度时出错: {str(e)}")
        
        # 2. 基于查询模式的建议
        query_type, entities = self._analyze_query(query)
        if query_type in self.query_patterns:
            pattern = self.query_patterns[query_type]
            
            # 生成模板化建议
            if entities:
                template = pattern["template"]
                if len(entities) >= 2:
                    suggested_query = template.format(
                        entity1=entities[0],
                        entity2=entities[1]
                    )
                else:
                    suggested_query = template.format(
                        entity=entities[0],
                        topic=entities[0],
                        relation_type="概念"
                    )
                
                suggestions.append(
                    QuerySuggestion(
                        original_query=query,
                        suggested_query=suggested_query,
                        confidence=0.8,
                        explanation="基于查询模板优化"
                    )
                )
        
        # 3. 基于图结构的建议
        if self.graph and entities:
            for entity in entities:
                # 查找重要相关节点
                related_nodes = self._find_important_related_nodes(entity)
                if related_nodes:
                    node_names = [self.graph.nodes[n].get("name", n) 
                                for n in related_nodes[:2]]
                    suggested_query = f"分析 {entity} 与 {', '.join(node_names)} 的关系"
                    
                    suggestions.append(
                        QuerySuggestion(
                            original_query=query,
                            suggested_query=suggested_query,
                            confidence=0.7,
                            explanation="基于知识图谱结构"
                        )
                    )
        
        return sorted(suggestions, key=lambda x: x.confidence, reverse=True)[:max_suggestions]
    
    def _analyze_query(self, query: str) -> Tuple[str, List[str]]:
        """分析查询类型和实体"""
        query_type = "general"
        entities = []
        
        # 识别查询类型
        for qtype, pattern in self.query_patterns.items():
            if any(p in query for p in pattern["patterns"]):
                query_type = qtype
                break
        
        # 提取实体（这里可以集成更复杂的NER系统）
        words = query.split()
        entities = [w for w in words if w not in ["的", "和", "与", "在", "是"]]
        
        return query_type, entities
    
    def _estimate_base_cost(self, query_type: str, entities: List[str]) -> float:
        """估算基础查询成本"""
        if not self.graph:
            return 1.0
        
        cost = 0.0
        pattern = self.query_patterns.get(query_type, {})
        cost_factors = pattern.get("cost_factors", {})
        
        if query_type == "path_query":
            # 路径查询成本与节点数和路径长度相关
            cost = (self.graph.number_of_nodes() * cost_factors.get("node_count", 0.4) +
                   len(entities) * cost_factors.get("path_length", 0.3))
        
        elif query_type == "neighbor_query":
            # 邻居查询成本与邻居数量和深度相关
            avg_degree = self.graph.number_of_edges() / self.graph.number_of_nodes()
            cost = (avg_degree * cost_factors.get("neighbor_count", 0.3) +
                   2 * cost_factors.get("depth", 0.4))  # 默认深度为2
        
        elif query_type == "subgraph_query":
            # 子图查询成本与节点数和边密度相关
            density = nx.density(self.graph)
            cost = (self.graph.number_of_nodes() * cost_factors.get("node_count", 0.5) +
                   density * cost_factors.get("edge_density", 0.3))
        
        else:
            # 通用查询的默认成本
            cost = 1.0
        
        return cost
    
    def _generate_execution_steps(self, query_type: str, entities: List[str],
                                context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """生成执行步骤"""
        steps = []
        
        # 1. 缓存检查步骤
        steps.append({
            "type": "cache_check",
            "description": "检查查询缓存",
            "estimated_cost": 0.1
        })
        
        # 2. 实体验证步骤
        steps.append({
            "type": "entity_validation",
            "description": "验证查询实体",
            "entities": entities,
            "estimated_cost": 0.2
        })
        
        # 3. 根据查询类型生成特定步骤
        if query_type == "path_query":
            steps.extend([
                {
                    "type": "path_search",
                    "description": "搜索实体间路径",
                    "max_length": 3,
                    "estimated_cost": 0.5
                },
                {
                    "type": "path_ranking",
                    "description": "对路径进行排序",
                    "estimated_cost": 0.2
                }
            ])
        
        elif query_type == "neighbor_query":
            steps.extend([
                {
                    "type": "neighbor_expansion",
                    "description": "扩展邻居节点",
                    "max_depth": 2,
                    "estimated_cost": 0.4
                },
                {
                    "type": "neighbor_filtering",
                    "description": "过滤相关邻居",
                    "estimated_cost": 0.2
                }
            ])
        
        elif query_type == "subgraph_query":
            steps.extend([
                {
                    "type": "subgraph_extraction",
                    "description": "提取相关子图",
                    "estimated_cost": 0.6
                },
                {
                    "type": "subgraph_optimization",
                    "description": "优化子图结构",
                    "estimated_cost": 0.3
                }
            ])
        
        # 4. 结果处理步骤
        steps.append({
            "type": "result_processing",
            "description": "处理查询结果",
            "estimated_cost": 0.2
        })
        
        # 5. 缓存更新步骤
        steps.append({
            "type": "cache_update",
            "description": "更新查询缓存",
            "estimated_cost": 0.1
        })
        
        return steps
    
    def _find_important_related_nodes(self, entity: str, limit: int = 3) -> List[str]:
        """查找重要的相关节点"""
        if not self.graph:
            return []
        
        related_nodes = []
        
        # 查找匹配的节点
        matching_nodes = set()
        for node, data in self.graph.nodes(data=True):
            if entity.lower() in str(node).lower() or \
               entity.lower() in str(data.get("name", "")).lower():
                matching_nodes.add(node)
        
        # 对于每个匹配的节点，找到重要的相关节点
        for node in matching_nodes:
            # 获取邻居节点
            neighbors = set(self.graph.predecessors(node)) | set(self.graph.successors(node))
            
            # 计算节点重要性（使用度中心性）
            importance = nx.degree_centrality(self.graph)
            
            # 选择最重要的邻居节点
            important_neighbors = sorted(
                neighbors,
                key=lambda x: importance.get(x, 0),
                reverse=True
            )
            
            related_nodes.extend(important_neighbors)
        
        # 返回最重要的不重复节点
        return list(dict.fromkeys(related_nodes))[:limit]
