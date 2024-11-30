from typing import List, Dict, Any, Optional, Set
from datetime import datetime
import json
import re
import requests
from prompt_manager import PromptManager
from graph_models import Entity, Relation

class RelationValidator:
    """关系验证器"""
    def __init__(self):
        # 扩展有效关系类型
        self.valid_relation_types: Set[str] = {
            # 基础关系类型
            'is_a', 'part_of', 'belongs_to',
            'creates', 'uses', 'affects', 'controls',
            'has_property', 'has_value', 'has_state',
            'happens_before', 'happens_after', 'happens_at',
            'located_in', 'near_to', 'far_from',
            'causes', 'results_in', 'depends_on',
            'works_for', 'collaborates_with', 'competes_with',
            
            # 技术领域关系
            'compatible_with', 'implements', 'extends',
            'calls', 'imports', 'exports',
            'configures', 'deploys', 'monitors',
            
            # 业务领域关系
            'reports_to', 'responsible_for', 'manages',
            'approves', 'processes', 'coordinates',
            'owns', 'supports', 'delivers',
            
            # 学术领域关系
            'cites', 'proves', 'disproves',
            'based_on', 'contributes_to', 'analyzes',
            'validates', 'compares', 'synthesizes',
            
            # 医疗领域关系
            'diagnoses', 'treats', 'prevents',
            'indicates', 'contraindicates', 'interacts_with',
            'administers', 'prescribes', 'monitors',
            
            # 法律领域关系
            'applies_to', 'references', 'obligates',
            'permits', 'prohibits', 'regulates',
            'enforces', 'supersedes', 'amends'
        }
    
    def validate_relation(self, relation: Relation) -> bool:
        """验证关系的有效性"""
        # 验证关系类型
        if relation.relation_type not in self.valid_relation_types:
            return False
        
        # 验证置信度
        if not (0 <= relation.confidence <= 1):
            return False
        
        # 验证实体
        if not self._validate_entity(relation.source) or not self._validate_entity(relation.target):
            return False
        
        return True
    
    def _validate_entity(self, entity: Entity) -> bool:
        """验证实体的有效性"""
        return bool(entity.id and entity.name and entity.type)

class HybridRelationExtractor:
    """混合关系提取器"""
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.api_url = "https://api.deepseek.com/v1/chat/completions"
        self.prompt_manager = PromptManager()
        self.validator = RelationValidator()
        self.inference_engine = None  # 延迟初始化
        self.batch_processor = None   # 延迟初始化
    
    def _init_inference(self):
        """延迟初始化推理引擎"""
        if self.inference_engine is None:
            from relation_inference import RelationInferenceEngine, BatchProcessor
            self.inference_engine = RelationInferenceEngine()
            self.batch_processor = BatchProcessor(self, self.inference_engine)
    
    def extract_relations(self, text: str, template_id: Optional[str] = None) -> List[Relation]:
        """提取关系"""
        # 生成提示词
        prompt = self.prompt_manager.generate_prompt(text, template_id)
        
        try:
            # 调用DeepSeek API
            response = self._call_api(prompt)
            
            # 解析响应
            relations = self._parse_response(response)
            
            # 验证关系
            valid_relations = [
                relation for relation in relations
                if self.validator.validate_relation(relation)
            ]
            
            # 执行关系推理
            if self.inference_engine is None:
                self._init_inference()
            inferred_relations = self.inference_engine.infer_relations(valid_relations)
            
            # 合并结果
            all_relations = valid_relations + inferred_relations
            
            # 去重和冲突解决
            return self._resolve_conflicts(all_relations)
            
        except Exception as e:
            print(f"提取关系时出错: {str(e)}")
            return []
    
    def extract_batch(self, texts: List[str], template_id: Optional[str] = None) -> List[Relation]:
        """批量提取关系"""
        if self.batch_processor is None:
            self._init_inference()
        return self.batch_processor.process_batch(texts, template_id)
    
    def _call_api(self, prompt: str) -> Dict[str, Any]:
        """调用DeepSeek API"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            self.api_url,
            headers=headers,
            json={
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": prompt}]
            }
        )
        
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        return json.loads(content)
    
    def _parse_response(self, response: Dict[str, Any]) -> List[Relation]:
        """解析API响应"""
        relations = []
        entities = {}
        
        # 创建实体字典
        for entity_data in response["entities"]:
            entity = Entity(
                id=entity_data["id"],
                name=entity_data["name"],
                type=entity_data["type"],
                properties=entity_data.get("properties", {})
            )
            entities[entity.id] = entity
        
        # 创建关系列表
        for relation_data in response["relations"]:
            source = entities.get(relation_data["source"])
            target = entities.get(relation_data["target"])
            
            if source and target:
                relation = Relation(
                    source=source,
                    target=target,
                    relation_type=relation_data["relation_type"],
                    confidence=relation_data.get("confidence", 1.0),
                    properties=relation_data.get("properties", {})
                )
                relations.append(relation)
        
        return relations
    
    def _resolve_conflicts(self, relations: List[Relation]) -> List[Relation]:
        """解决冲突关系"""
        resolved_relations = []
        seen_pairs = set()
        
        # 按置信度排序
        sorted_relations = sorted(relations, key=lambda r: r.confidence, reverse=True)
        
        for relation in sorted_relations:
            pair_key = (relation.source.id, relation.target.id, relation.relation_type)
            
            if pair_key not in seen_pairs:
                resolved_relations.append(relation)
                seen_pairs.add(pair_key)
        
        return resolved_relations

class DeepSeekRelationExtractor:
    """使用DeepSeek的关系提取器"""
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.relation_patterns = self._compile_relation_patterns()
        self.prompt_manager = PromptManager()
        self.inference_engine = None  # 延迟初始化
        self.batch_processor = None   # 延迟初始化
    
    def _init_inference(self):
        """延迟初始化推理引擎"""
        if self.inference_engine is None:
            from relation_inference import RelationInferenceEngine, BatchProcessor
            self.inference_engine = RelationInferenceEngine()
            self.batch_processor = BatchProcessor(self, self.inference_engine)
    
    def _compile_relation_patterns(self) -> Dict[str, List[str]]:
        """编译关系模式"""
        return {
            'is_a': [
                r"是一种",
                r"是一个",
                r"属于",
                r"被归类为"
            ],
            'part_of': [
                r"是.*的一部分",
                r"包含",
                r"组成部分包括",
                r"由.*组成"
            ],
            'creates': [
                r"创建",
                r"生产",
                r"制造",
                r"产生"
            ],
            # ... 其他关系模式
        }
    
    def extract_relations(self, text: str) -> List[Relation]:
        """
        从文本中提取实体关系
        1. 使用DeepSeek API进行初步关系提取
        2. 使用规则和模式进行补充提取
        3. 合并结果并去重
        """
        # 构建提示模板
        prompt = self.prompt_manager.generate_prompt(text)
        
        try:
            # 调用DeepSeek API
            response = self._call_api(prompt)
            
            # 解析响应
            relations = self._parse_response(response)
            
            # 使用规则和模式进行补充提取
            rule_based_relations = self._extract_by_rules(text)
            
            # 合并结果
            all_relations = relations + rule_based_relations
            
            # 去重和冲突解决
            return self._resolve_conflicts(all_relations)
        
        except Exception as e:
            print(f"提取关系时出错: {str(e)}")
            return []
    
    def extract_batch(self, texts: List[str]) -> List[Relation]:
        """批量提取关系"""
        if self.batch_processor is None:
            self._init_inference()
        return self.batch_processor.process_batch(texts)
    
    def _call_api(self, prompt: str) -> Dict[str, Any]:
        """调用DeepSeek API"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            self.api_url,
            headers=headers,
            json={
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": prompt}]
            }
        )
        
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        return json.loads(content)
    
    def _parse_response(self, response: Dict[str, Any]) -> List[Relation]:
        """解析API响应"""
        relations = []
        entities = {}
        
        # 创建实体字典
        for entity_data in response["entities"]:
            entity = Entity(
                id=entity_data["id"],
                name=entity_data["name"],
                type=entity_data["type"],
                properties=entity_data.get("properties", {})
            )
            entities[entity.id] = entity
        
        # 创建关系列表
        for relation_data in response["relations"]:
            source = entities.get(relation_data["source"])
            target = entities.get(relation_data["target"])
            
            if source and target:
                relation = Relation(
                    source=source,
                    target=target,
                    relation_type=relation_data["relation_type"],
                    confidence=relation_data.get("confidence", 1.0),
                    properties=relation_data.get("properties", {})
                )
                relations.append(relation)
        
        return relations
    
    def _extract_by_rules(self, text: str) -> List[Relation]:
        """使用规则和模式进行关系提取"""
        relations = []
        for relation_type, patterns in self.relation_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text)
                for match in matches:
                    source = Entity(
                        id=f"E{len(relations)*2+1}",
                        name=match.group(1),
                        type="Unknown"
                    )
                    target = Entity(
                        id=f"E{len(relations)*2+2}",
                        name=match.group(2),
                        type="Unknown"
                    )
                    relations.append(Relation(
                        source=source,
                        target=target,
                        relation_type=relation_type,
                        confidence=1.0,
                        properties={}
                    ))
        return relations
    
    def _resolve_conflicts(self, relations: List[Relation]) -> List[Relation]:
        """解决冲突关系"""
        resolved_relations = []
        seen_pairs = set()
        
        # 按置信度排序
        sorted_relations = sorted(relations, key=lambda r: r.confidence, reverse=True)
        
        for relation in sorted_relations:
            pair_key = (relation.source.id, relation.target.id, relation.relation_type)
            
            if pair_key not in seen_pairs:
                resolved_relations.append(relation)
                seen_pairs.add(pair_key)
        
        return resolved_relations

class RuleBasedRelationExtractor:
    """基于规则的关系提取器"""
    def __init__(self):
        self.patterns = {
            'is_a': [
                r"(\w+)是一种(\w+)",
                r"(\w+)是一个(\w+)",
                r"(\w+)属于(\w+)"
            ],
            'part_of': [
                r"(\w+)是(\w+)的一部分",
                r"(\w+)包含(\w+)",
                r"(\w+)由(\w+)组成"
            ],
            # ... 其他关系模式
        }
    
    def extract_relations(self, text: str) -> List[Relation]:
        relations = []
        for relation_type, patterns in self.patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text)
                for match in matches:
                    source = Entity(
                        id=f"E{len(relations)*2+1}",
                        name=match.group(1),
                        type="Unknown"
                    )
                    target = Entity(
                        id=f"E{len(relations)*2+2}",
                        name=match.group(2),
                        type="Unknown"
                    )
                    relations.append(Relation(
                        source=source,
                        target=target,
                        relation_type=relation_type,
                        confidence=1.0,
                        properties={}
                    ))
        return relations

class RelationExtractor:
    """关系提取器基类"""
    def extract_relations(self, text: str) -> List[Relation]:
        raise NotImplementedError
