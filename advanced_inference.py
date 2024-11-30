from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass
import networkx as nx
from datetime import datetime
import numpy as np
from relation_extraction import Relation, Entity

@dataclass
class TemporalRelation:
    """时序关系"""
    relation: Relation
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[float] = None  # 持续时间（秒）

@dataclass
class ProbabilisticRelation:
    """概率关系"""
    relation: Relation
    probability: float
    evidence: List[str]
    confidence_scores: Dict[str, float]

class AdvancedInferenceEngine:
    """高级推理引擎"""
    
    def __init__(self):
        self.temporal_graph = nx.DiGraph()
        self.probabilistic_graph = nx.DiGraph()
        self.knowledge_graph = nx.DiGraph()
        
        # 时序推理配置
        self.temporal_patterns = {
            'precedes': {'inverse': 'follows', 'transitive': True},
            'during': {'inverse': 'contains', 'transitive': False},
            'overlaps': {'inverse': 'overlapped_by', 'transitive': False},
            'starts': {'inverse': 'started_by', 'transitive': False},
            'finishes': {'inverse': 'finished_by', 'transitive': False}
        }
        
        # 概率推理配置
        self.probability_threshold = 0.6
        self.min_confidence = 0.3
        
        # 多跳推理配置
        self.max_path_length = 5
        self.min_path_confidence = 0.2
    
    def add_temporal_relation(self, relation: Relation, start_time: datetime,
                            end_time: Optional[datetime] = None,
                            duration: Optional[float] = None) -> TemporalRelation:
        """添加时序关系"""
        temporal_rel = TemporalRelation(
            relation=relation,
            start_time=start_time,
            end_time=end_time,
            duration=duration
        )
        
        # 添加到时序图
        self.temporal_graph.add_edge(
            relation.source.id,
            relation.target.id,
            relation=temporal_rel
        )
        
        return temporal_rel
    
    def add_probabilistic_relation(self, relation: Relation, probability: float,
                                 evidence: List[str]) -> ProbabilisticRelation:
        """添加概率关系"""
        prob_rel = ProbabilisticRelation(
            relation=relation,
            probability=probability,
            evidence=evidence,
            confidence_scores={ev: 1.0 for ev in evidence}
        )
        
        # 添加到概率图
        self.probabilistic_graph.add_edge(
            relation.source.id,
            relation.target.id,
            relation=prob_rel
        )
        
        return prob_rel
    
    def temporal_inference(self, start_entity: Entity, end_entity: Entity,
                         relation_type: str) -> List[TemporalRelation]:
        """时序推理
        
        基于时序逻辑进行推理，支持：
        1. 时间区间重叠检测
        2. 时序关系传递
        3. 时间约束推理
        """
        inferred_relations = []
        
        # 获取所有可能的路径
        paths = list(nx.all_simple_paths(
            self.temporal_graph,
            start_entity.id,
            end_entity.id,
            cutoff=self.max_path_length
        ))
        
        for path in paths:
            # 收集路径上的时序关系
            path_relations = []
            valid_path = True
            
            for i in range(len(path) - 1):
                edge_data = self.temporal_graph.get_edge_data(path[i], path[i + 1])
                if edge_data:
                    temporal_rel = edge_data['relation']
                    path_relations.append(temporal_rel)
                else:
                    valid_path = False
                    break
            
            if not valid_path:
                continue
            
            # 时序关系推理
            if self._validate_temporal_sequence(path_relations):
                # 计算综合时间区间
                start_time = min(rel.start_time for rel in path_relations)
                end_times = [rel.end_time for rel in path_relations if rel.end_time]
                end_time = max(end_times) if end_times else None
                
                # 创建推理关系
                inferred_relation = Relation(
                    source=start_entity,
                    target=end_entity,
                    relation_type=relation_type,
                    confidence=self._calculate_temporal_confidence(path_relations),
                    properties={'inferred': True, 'path_length': len(path)}
                )
                
                inferred_relations.append(TemporalRelation(
                    relation=inferred_relation,
                    start_time=start_time,
                    end_time=end_time
                ))
        
        return inferred_relations
    
    def probabilistic_inference(self, start_entity: Entity, end_entity: Entity,
                              relation_type: str) -> List[ProbabilisticRelation]:
        """概率推理
        
        基于贝叶斯网络进行推理，支持：
        1. 条件概率计算
        2. 证据链组合
        3. 不确定性传播
        """
        inferred_relations = []
        
        # 获取所有可能的路径
        paths = list(nx.all_simple_paths(
            self.probabilistic_graph,
            start_entity.id,
            end_entity.id,
            cutoff=self.max_path_length
        ))
        
        for path in paths:
            # 收集路径上的概率关系
            path_relations = []
            valid_path = True
            
            for i in range(len(path) - 1):
                edge_data = self.probabilistic_graph.get_edge_data(path[i], path[i + 1])
                if edge_data:
                    prob_rel = edge_data['relation']
                    path_relations.append(prob_rel)
                else:
                    valid_path = False
                    break
            
            if not valid_path:
                continue
            
            # 计算组合概率
            combined_probability = self._combine_probabilities(path_relations)
            if combined_probability >= self.probability_threshold:
                # 合并证据
                combined_evidence = self._merge_evidence(path_relations)
                
                # 创建推理关系
                inferred_relation = Relation(
                    source=start_entity,
                    target=end_entity,
                    relation_type=relation_type,
                    confidence=combined_probability,
                    properties={'inferred': True, 'path_length': len(path)}
                )
                
                inferred_relations.append(ProbabilisticRelation(
                    relation=inferred_relation,
                    probability=combined_probability,
                    evidence=combined_evidence,
                    confidence_scores=self._calculate_evidence_scores(path_relations)
                ))
        
        return inferred_relations
    
    def multi_hop_inference(self, start_entity: Entity, max_hops: int = 3,
                          min_confidence: float = 0.5) -> List[Relation]:
        """多跳推理
        
        基于图遍历进行多跳推理，支持：
        1. 路径发现
        2. 关系组合
        3. 循环检测
        """
        inferred_relations = []
        visited = set()
        
        def dfs(current_entity: Entity, current_path: List[Relation], depth: int):
            if depth >= max_hops:
                return
            
            visited.add(current_entity.id)
            
            # 获取所有出边
            for _, target_id, edge_data in self.knowledge_graph.out_edges(current_entity.id, data=True):
                if target_id in visited:
                    continue
                
                relation = edge_data['relation']
                new_path = current_path + [relation]
                
                # 计算路径置信度
                path_confidence = self._calculate_path_confidence(new_path)
                
                if path_confidence >= min_confidence:
                    # 创建推理关系
                    target_entity = relation.target
                    inferred_relation = Relation(
                        source=start_entity,
                        target=target_entity,
                        relation_type=self._infer_relation_type(new_path),
                        confidence=path_confidence,
                        properties={
                            'inferred': True,
                            'path_length': len(new_path),
                            'intermediate_nodes': [rel.target.id for rel in new_path[:-1]]
                        }
                    )
                    inferred_relations.append(inferred_relation)
                
                # 继续搜索
                dfs(relation.target, new_path, depth + 1)
            
            visited.remove(current_entity.id)
        
        # 开始搜索
        dfs(start_entity, [], 0)
        return inferred_relations
    
    def _validate_temporal_sequence(self, relations: List[TemporalRelation]) -> bool:
        """验证时序序列的有效性"""
        for i in range(len(relations) - 1):
            curr_rel = relations[i]
            next_rel = relations[i + 1]
            
            # 检查时间顺序
            if curr_rel.end_time and next_rel.start_time:
                if curr_rel.end_time > next_rel.start_time:
                    return False
        
        return True
    
    def _calculate_temporal_confidence(self, relations: List[TemporalRelation]) -> float:
        """计算时序推理的置信度"""
        confidences = [rel.relation.confidence for rel in relations]
        return np.prod(confidences) ** (1.0 / len(confidences))
    
    def _combine_probabilities(self, relations: List[ProbabilisticRelation]) -> float:
        """组合多个概率关系"""
        probabilities = [rel.probability for rel in relations]
        return np.prod(probabilities)
    
    def _merge_evidence(self, relations: List[ProbabilisticRelation]) -> List[str]:
        """合并多个关系的证据"""
        all_evidence = set()
        for rel in relations:
            all_evidence.update(rel.evidence)
        return list(all_evidence)
    
    def _calculate_evidence_scores(self, relations: List[ProbabilisticRelation]) -> Dict[str, float]:
        """计算证据的置信度分数"""
        evidence_scores = {}
        for rel in relations:
            for evidence, score in rel.confidence_scores.items():
                if evidence in evidence_scores:
                    evidence_scores[evidence] = max(evidence_scores[evidence], score)
                else:
                    evidence_scores[evidence] = score
        return evidence_scores
    
    def _calculate_path_confidence(self, path: List[Relation]) -> float:
        """计算路径的整体置信度"""
        confidences = [rel.confidence for rel in path]
        return np.prod(confidences) ** (1.0 / len(confidences))
    
    def _infer_relation_type(self, path: List[Relation]) -> str:
        """推断多跳路径的关系类型"""
        # 简单策略：使用最后一个关系的类型
        return path[-1].relation_type

class CompositeInferenceEngine:
    """组合推理引擎"""
    
    def __init__(self):
        self.engine = AdvancedInferenceEngine()
    
    def infer_all(self, start_entity: Entity, end_entity: Entity,
                  relation_type: str) -> Dict[str, List[Relation]]:
        """执行所有类型的推理"""
        results = {
            'temporal': [],
            'probabilistic': [],
            'multi_hop': []
        }
        
        # 时序推理
        temporal_relations = self.engine.temporal_inference(
            start_entity, end_entity, relation_type
        )
        results['temporal'] = [rel.relation for rel in temporal_relations]
        
        # 概率推理
        probabilistic_relations = self.engine.probabilistic_inference(
            start_entity, end_entity, relation_type
        )
        results['probabilistic'] = [rel.relation for rel in probabilistic_relations]
        
        # 多跳推理
        multi_hop_relations = self.engine.multi_hop_inference(
            start_entity
        )
        results['multi_hop'] = multi_hop_relations
        
        return results
    
    def explain_inference(self, results: Dict[str, List[Relation]]) -> Dict[str, List[str]]:
        """解释推理结果"""
        explanations = {
            'temporal': [],
            'probabilistic': [],
            'multi_hop': []
        }
        
        # 解释时序推理
        for relation in results['temporal']:
            explanation = (
                f"通过时序推理发现：{relation.source.name} 与 {relation.target.name} "
                f"之间存在 {relation.relation_type} 关系（置信度：{relation.confidence:.2f}）"
            )
            explanations['temporal'].append(explanation)
        
        # 解释概率推理
        for relation in results['probabilistic']:
            explanation = (
                f"通过概率推理发现：{relation.source.name} 与 {relation.target.name} "
                f"之间存在 {relation.relation_type} 关系（置信度：{relation.confidence:.2f}）"
            )
            explanations['probabilistic'].append(explanation)
        
        # 解释多跳推理
        for relation in results['multi_hop']:
            path_length = relation.properties.get('path_length', 0)
            explanation = (
                f"通过{path_length}跳推理发现：{relation.source.name} 与 {relation.target.name} "
                f"之间存在 {relation.relation_type} 关系（置信度：{relation.confidence:.2f}）"
            )
            explanations['multi_hop'].append(explanation)
        
        return explanations
