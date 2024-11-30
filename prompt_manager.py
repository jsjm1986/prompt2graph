from typing import Dict, List, Optional
import json
import os
from dataclasses import dataclass
from datetime import datetime

@dataclass
class PromptTemplate:
    """提示词模板"""
    id: str
    name: str
    description: str
    template: str
    relation_types: List[str]
    created_at: datetime
    updated_at: datetime
    is_active: bool = True
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'PromptTemplate':
        return cls(
            id=data['id'],
            name=data['name'],
            description=data['description'],
            template=data['template'],
            relation_types=data['relation_types'],
            created_at=datetime.fromisoformat(data['created_at']),
            updated_at=datetime.fromisoformat(data['updated_at']),
            is_active=data.get('is_active', True)
        )
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'template': self.template,
            'relation_types': self.relation_types,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'is_active': self.is_active
        }

class PromptManager:
    """提示词管理器"""
    def __init__(self, templates_file: str = 'templates/prompt_templates.json'):
        self.templates_file = templates_file
        self.templates: Dict[str, PromptTemplate] = {}
        self.load_templates()
        
        # 默认模板
        self.default_template = """
分析以下文本，提取所有可能的实体和关系。对于每个关系，提供置信度评分。

文本内容：
{text}

请提取以下类型的关系：
{relation_types}

对于每个关系，考虑以下方面：
1. 实体的完整性和准确性
2. 关系的方向性和类型
3. 关系的置信度（0-1之间的数值）
4. 任何额外的属性或上下文信息

返回格式：
{
    "entities": [
        {
            "id": "E1",
            "name": "实体名称",
            "type": "实体类型",
            "properties": {
                "属性1": "值1",
                "属性2": "值2"
            }
        }
    ],
    "relations": [
        {
            "source": "E1",
            "target": "E2",
            "relation_type": "关系类型",
            "confidence": 0.95,
            "properties": {
                "属性1": "值1",
                "属性2": "值2"
            }
        }
    ]
}

请尽可能详细地提取关系，包括隐含的和间接的关系。对于每个关系，请提供具体的证据或理由。
"""
    
    def load_templates(self) -> None:
        """加载提示词模板"""
        if not os.path.exists(self.templates_file):
            os.makedirs(os.path.dirname(self.templates_file), exist_ok=True)
            self.save_templates()
            return
        
        with open(self.templates_file, 'r', encoding='utf-8') as f:
            templates_data = json.load(f)
            self.templates = {
                template_id: PromptTemplate.from_dict(data)
                for template_id, data in templates_data.items()
            }
    
    def save_templates(self) -> None:
        """保存提示词模板"""
        templates_data = {
            template_id: template.to_dict()
            for template_id, template in self.templates.items()
        }
        os.makedirs(os.path.dirname(self.templates_file), exist_ok=True)
        with open(self.templates_file, 'w', encoding='utf-8') as f:
            json.dump(templates_data, f, indent=2, ensure_ascii=False)
    
    def add_template(self, template: PromptTemplate) -> None:
        """添加新模板"""
        self.templates[template.id] = template
        self.save_templates()
    
    def update_template(self, template_id: str, updates: Dict) -> None:
        """更新模板"""
        if template_id not in self.templates:
            raise ValueError(f"Template {template_id} not found")
        
        template = self.templates[template_id]
        for key, value in updates.items():
            if hasattr(template, key):
                setattr(template, key, value)
        
        template.updated_at = datetime.now()
        self.save_templates()
    
    def delete_template(self, template_id: str) -> None:
        """删除模板"""
        if template_id in self.templates:
            del self.templates[template_id]
            self.save_templates()
    
    def get_template(self, template_id: str) -> Optional[PromptTemplate]:
        """获取模板"""
        return self.templates.get(template_id)
    
    def list_templates(self) -> List[PromptTemplate]:
        """列出所有模板"""
        return list(self.templates.values())
    
    def generate_prompt(self, text: str, template_id: Optional[str] = None) -> str:
        """生成提示词"""
        template = self.templates.get(template_id) if template_id else None
        template_text = template.template if template else self.default_template
        
        # 获取所有关系类型的描述
        relation_types_desc = self._generate_relation_types_description(
            template.relation_types if template else None
        )
        
        return template_text.format(
            text=text,
            relation_types=relation_types_desc
        )
    
    def _generate_relation_types_description(self, relation_types: Optional[List[str]] = None) -> str:
        """生成关系类型描述"""
        all_types = {
            "层次关系": [
                "is_a (是一个): 表示类别归属关系",
                "part_of (部分-整体): 表示组成关系",
                "belongs_to (从属): 表示归属关系"
            ],
            "动作关系": [
                "creates (创建): 表示创建或生产关系",
                "uses (使用): 表示使用或应用关系",
                "affects (影响): 表示影响或作用关系",
                "controls (控制): 表示控制或管理关系"
            ],
            "属性关系": [
                "has_property (具有属性): 表示特征属性",
                "has_value (具有值): 表示数值属性",
                "has_state (具有状态): 表示状态属性"
            ],
            "时间关系": [
                "happens_before (发生在...之前): 表示时间先后顺序",
                "happens_after (发生在...之后): 表示时间后续关系",
                "happens_at (发生于): 表示时间点关系"
            ],
            "空间关系": [
                "located_in (位于): 表示位置关系",
                "near_to (靠近): 表示proximity关系",
                "far_from (远离): 表示距离关系"
            ],
            "逻辑关系": [
                "causes (导致): 表示因果关系",
                "results_in (结果是): 表示结果关系",
                "depends_on (依赖于): 表示依赖关系"
            ],
            "社会关系": [
                "works_for (工作于): 表示工作关系",
                "collaborates_with (合作): 表示合作关系",
                "competes_with (竞争): 表示竞争关系"
            ]
        }
        
        if relation_types:
            # 只包含指定的关系类型
            filtered_types = {}
            for category, types in all_types.items():
                filtered = [t for t in types if any(rt in t for rt in relation_types)]
                if filtered:
                    filtered_types[category] = filtered
            types_to_use = filtered_types
        else:
            types_to_use = all_types
        
        # 生成描述文本
        description = []
        for category, types in types_to_use.items():
            description.append(f"\n{category}:")
            description.extend(f"- {t}" for t in types)
        
        return "\n".join(description)
