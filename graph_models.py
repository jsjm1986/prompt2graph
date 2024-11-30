from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Entity:
    """实体类"""
    id: str
    name: str
    type: str
    properties: Dict[str, Any]

@dataclass
class Relation:
    """关系类"""
    source: Entity
    target: Entity
    relation_type: str
    confidence: float
    properties: Dict[str, Any]

@dataclass
class InferenceRule:
    """推理规则类"""
    id: str
    name: str
    description: str
    premise_relations: List[str]  # 前提关系类型列表
    conclusion_relation: str      # 结论关系类型
    confidence_factor: float      # 置信度因子
    created_at: datetime
    updated_at: datetime
    is_active: bool = True
