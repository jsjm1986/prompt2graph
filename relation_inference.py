from typing import List, Dict, Set, Tuple, Optional
import networkx as nx
from datetime import datetime
from graph_models import Entity, Relation, InferenceRule

class RelationInferenceEngine:
    """关系推理引擎"""
    def __init__(self):
        self.rules: List[InferenceRule] = []
        self.initialize_default_rules()
    
    def initialize_default_rules(self):
        """初始化默认推理规则"""
        # 传递性规则
        self.rules.extend([
            InferenceRule(
                id="transitive-is-a",
                name="IS-A传递性",
                description="如果A是B，B是C，则A是C",
                premise_relations=["is_a", "is_a"],
                conclusion_relation="is_a",
                confidence_factor=0.9,
                created_at=datetime.now(),
                updated_at=datetime.now()
            ),
            InferenceRule(
                id="transitive-part-of",
                name="PART-OF传递性",
                description="如果A是B的一部分，B是C的一部分，则A是C的一部分",
                premise_relations=["part_of", "part_of"],
                conclusion_relation="part_of",
                confidence_factor=0.9,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        ])
        
        # 组合规则
        self.rules.extend([
            InferenceRule(
                id="cause-effect-chain",
                name="因果链",
                description="如果A导致B，B导致C，则A导致C",
                premise_relations=["causes", "causes"],
                conclusion_relation="causes",
                confidence_factor=0.8,
                created_at=datetime.now(),
                updated_at=datetime.now()
            ),
            InferenceRule(
                id="dependency-chain",
                name="依赖链",
                description="如果A依赖B，B依赖C，则A依赖C",
                premise_relations=["depends_on", "depends_on"],
                conclusion_relation="depends_on",
                confidence_factor=0.8,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        ])
        
        # 复合规则
        self.rules.extend([
            InferenceRule(
                id="location-containment",
                name="位置包含",
                description="如果A位于B，B包含C，则A位于C",
                premise_relations=["located_in", "contains"],
                conclusion_relation="located_in",
                confidence_factor=0.85,
                created_at=datetime.now(),
                updated_at=datetime.now()
            ),
            InferenceRule(
                id="temporal-sequence",
                name="时序关系",
                description="如果A发生在B之前，B发生在C之前，则A发生在C之前",
                premise_relations=["happens_before", "happens_before"],
                conclusion_relation="happens_before",
                confidence_factor=0.9,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        ])
    
    def add_rule(self, rule: InferenceRule):
        """添加新的推理规则"""
        self.rules.append(rule)
    
    def remove_rule(self, rule_id: str):
        """移除推理规则"""
        self.rules = [r for r in self.rules if r.id != rule_id]
    
    def infer_relations(self, relations: List[Relation]) -> List[Relation]:
        """执行关系推理"""
        # 构建关系图
        graph = nx.DiGraph()
        
        # 添加现有关系
        for relation in relations:
            graph.add_edge(
                relation.source.id,
                relation.target.id,
                relation_type=relation.relation_type,
                confidence=relation.confidence,
                properties=relation.properties
            )
        
        # 应用推理规则
        inferred_relations = []
        for rule in self.rules:
            if len(rule.premise_relations) == 2:  # 目前只处理双前提规则
                # 找到符合前提关系类型的所有路径
                paths = self._find_matching_paths(graph, rule.premise_relations)
                
                # 对每个路径应用规则
                for path in paths:
                    inferred_relation = self._apply_rule(rule, path, relations)
                    if inferred_relation:
                        inferred_relations.append(inferred_relation)
        
        return inferred_relations
    
    def _find_matching_paths(self, graph: nx.DiGraph, relation_types: List[str]) -> List[List[str]]:
        """找到符合关系类型序列的路径"""
        matching_paths = []
        for source in graph.nodes():
            for target in graph.nodes():
                if source != target:
                    # 使用简单路径查找算法
                    for path in nx.all_simple_paths(graph, source, target, cutoff=len(relation_types)):
                        if len(path) - 1 == len(relation_types):
                            # 检查路径上的关系类型是否匹配
                            path_relations = []
                            for i in range(len(path) - 1):
                                edge_data = graph[path[i]][path[i + 1]]
                                path_relations.append(edge_data['relation_type'])
                            
                            if path_relations == relation_types:
                                matching_paths.append(path)
        
        return matching_paths
    
    def _apply_rule(self, rule: InferenceRule, path: List[str], 
                   existing_relations: List[Relation]) -> Optional[Relation]:
        """应用推理规则生成新关系"""
        # 获取路径的起点和终点实体
        source_id = path[0]
        target_id = path[-1]
        
        # 从现有关系中找到对应的实体对象
        source_entity = None
        target_entity = None
        for relation in existing_relations:
            if relation.source.id == source_id:
                source_entity = relation.source
            if relation.target.id == target_id:
                target_entity = relation.target
            if source_entity and target_entity:
                break
        
        if not (source_entity and target_entity):
            return None
        
        # 计算新关系的置信度
        # 使用路径上所有关系的置信度和规则的置信度因子
        path_confidence = 1.0
        for i in range(len(path) - 1):
            relation = next(
                r for r in existing_relations
                if r.source.id == path[i] and r.target.id == path[i + 1]
            )
            path_confidence *= relation.confidence
        
        final_confidence = path_confidence * rule.confidence_factor
        
        # 创建新的推理关系
        return Relation(
            source=source_entity,
            target=target_entity,
            relation_type=rule.conclusion_relation,
            confidence=final_confidence,
            properties={"inferred": True, "rule_id": rule.id}
        )

class BatchProcessor:
    """批量处理器"""
    def __init__(self, extractor, inference_engine):
        self.extractor = extractor
        self.inference_engine = inference_engine
    
    def process_batch(self, texts: List[str], template_id: Optional[str] = None) -> List[Relation]:
        """批量处理文本"""
        all_relations = []
        
        # 1. 提取关系
        for text in texts:
            relations = self.extractor.extract_relations(text, template_id)
            all_relations.extend(relations)
        
        # 2. 执行推理
        inferred_relations = self.inference_engine.infer_relations(all_relations)
        
        # 3. 合并结果
        all_relations.extend(inferred_relations)
        
        # 4. 去重和冲突解决
        return self._resolve_conflicts(all_relations)
    
    def _resolve_conflicts(self, relations: List[Relation]) -> List[Relation]:
        """解决冲突关系"""
        resolved_relations = []
        seen_pairs = set()  # 用于跟踪已处理的实体对
        
        for relation in sorted(relations, key=lambda r: r.confidence, reverse=True):
            pair_key = (relation.source.id, relation.target.id, relation.relation_type)
            
            if pair_key not in seen_pairs:
                resolved_relations.append(relation)
                seen_pairs.add(pair_key)
        
        return resolved_relations
