import logging
import requests
from functools import wraps
from flask import current_app
import time
import hashlib
import json
from datetime import datetime, timedelta
from graph_algorithms import KnowledgeGraphAlgorithms
import re

class SimpleCache:
    """简单的内存缓存实现"""
    def __init__(self, default_timeout=300):
        self.cache = {}
        self.default_timeout = default_timeout

    def get(self, key):
        if key in self.cache:
            item = self.cache[key]
            if item['expiry'] > datetime.now():
                return item['value']
            else:
                del self.cache[key]
        return None

    def set(self, key, value, timeout=None):
        if timeout is None:
            timeout = self.default_timeout
        expiry = datetime.now() + timedelta(seconds=timeout)
        self.cache[key] = {
            'value': value,
            'expiry': expiry
        }

# 创建全局缓存实例
cache = SimpleCache()

def setup_logging():
    """配置日志"""
    logging.basicConfig(
        level=current_app.config['LOG_LEVEL'],
        format=current_app.config['LOG_FORMAT'],
        filename=current_app.config['LOG_FILE']
    )
    return logging.getLogger(__name__)

class APIRateLimiter:
    """API调用频率限制器"""
    def __init__(self, calls_limit, time_window):
        self.calls_limit = calls_limit
        self.time_window = time_window
        self.calls = []
    
    def can_call(self):
        """检查是否可以进行API调用"""
        now = time.time()
        self.calls = [call for call in self.calls if now - call < self.time_window]
        if len(self.calls) < self.calls_limit:
            self.calls.append(now)
            return True
        return False

class DeepSeekAPI:
    """DeepSeek API 封装 - 使用改进的模拟数据生成"""
    def __init__(self, api_key=None):
        self.logger = logging.getLogger(__name__)
        
        # 预定义实体类型
        self.entity_types = {
            '技术': ['人工智能', '深度学习', '机器学习', '神经网络', '计算机科学', '自然语言处理', '计算机视觉'],
            '概念': ['分支', '技术', '核心', '方法', '理论', '架构', '模型'],
            '工具': ['框架', '平台', '系统', '工具', '库', '接口'],
            '领域': ['领域', '方向', '学科', '研究', '应用']
        }
        
        # 预定义关系类型
        self.relation_types = {
            '是': '表示类别或定义关系',
            '包含': '表示整体与部分的关系',
            '使用': '表示工具或方法的使用关系',
            '基于': '表示依赖或基础关系',
            '实现': '表示实现或完成的关系'
        }
    
    def _identify_entity_type(self, entity):
        """识别实体类型"""
        for type_name, keywords in self.entity_types.items():
            if any(keyword in entity for keyword in keywords):
                return type_name
        return '概念'  # 默认类型
    
    def _extract_entities_from_text(self, text):
        """从文本中提取实体"""
        entities = []
        entity_id = 1
        
        # 使用预定义的关键词作为实体识别的基础
        all_keywords = []
        for keywords in self.entity_types.values():
            all_keywords.extend(keywords)
        
        # 查找文本中的实体
        found_entities = set()
        for keyword in all_keywords:
            if keyword in text:
                found_entities.add(keyword)
        
        # 添加额外的名词短语作为实体
        # 使用简单的规则：2-6个字的连续汉字
        additional_entities = re.findall(r'[\u4e00-\u9fa5]{2,6}', text)
        for entity in additional_entities:
            if entity not in found_entities:
                found_entities.add(entity)
        
        # 创建实体对象
        for entity in found_entities:
            entity_type = self._identify_entity_type(entity)
            entities.append({
                'id': entity_id,
                'name': entity,
                'type': entity_type,
                'properties': {
                    'source': 'text_extraction',
                    'confidence': 0.9
                }
            })
            entity_id += 1
        
        return entities
    
    def _extract_relations(self, text, entities):
        """提取实体间的关系"""
        relations = []
        relation_id = 1
        
        # 为实体创建查找字典
        entity_dict = {entity['name']: entity for entity in entities}
        
        # 在实体对之间寻找关系
        for i, entity1 in enumerate(entities):
            for j, entity2 in enumerate(entities[i+1:], i+1):
                # 在文本中查找这两个实体之间的文本
                try:
                    start_idx = text.index(entity1['name'])
                    end_idx = text.index(entity2['name'])
                    between_text = text[start_idx:end_idx]
                    
                    # 检查关系类型
                    for relation_type, description in self.relation_types.items():
                        if relation_type in between_text:
                            relations.append({
                                'id': relation_id,
                                'source_id': entity1['id'],
                                'target_id': entity2['id'],
                                'relation_type': relation_type,
                                'properties': {
                                    'description': description,
                                    'confidence': 0.8
                                }
                            })
                            relation_id += 1
                except ValueError:
                    continue
        
        return relations
    
    def extract_entities(self, text):
        """从文本中提取实体和关系（改进的实现）"""
        if not text:
            return {'entities': [], 'relations': []}

        try:
            # 提取实体
            entities = self._extract_entities_from_text(text)
            
            # 提取关系
            relations = self._extract_relations(text, entities)
            
            return {
                'entities': entities,
                'relations': relations
            }
            
        except Exception as e:
            self.logger.error(f"Error in entity extraction: {str(e)}")
            return {'entities': [], 'relations': []}

class DataCleaner:
    """数据清理工具"""
    @staticmethod
    def clean_text(text):
        """清理输入文本"""
        if not text:
            return ""
        # 移除多余的空白字符
        text = re.sub(r'\s+', ' ', text.strip())
        # 统一标点符号
        text = text.replace('；', '。').replace('！', '。').replace('？', '。')
        return text

    @staticmethod
    def validate_entity(entity):
        """验证实体数据"""
        required_fields = ['name', 'type']
        return all(field in entity for field in required_fields)

    @staticmethod
    def validate_relation(relation):
        """验证关系数据"""
        required_fields = ['source_id', 'target_id', 'relation_type']
        return all(field in relation for field in required_fields)

class FileHandler:
    """文件处理工具"""
    def __init__(self, allowed_extensions):
        self.allowed_extensions = allowed_extensions

    def allowed_file(self, filename):
        """检查文件类型是否允许"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in self.allowed_extensions

    def extract_text(self, file_path):
        """从不同类型的文件中提取文本"""
        if not file_path:
            return ""
            
        ext = file_path.rsplit('.', 1)[1].lower()
        if ext == 'txt':
            return self._extract_from_txt(file_path)
        elif ext == 'pdf':
            return self._extract_from_pdf(file_path)
        elif ext in ['doc', 'docx']:
            return self._extract_from_word(file_path)
        return ""

    def _extract_from_txt(self, file_path):
        """从txt文件提取文本"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            current_app.logger.error(f"Error reading txt file: {str(e)}")
            return ""

    def _extract_from_pdf(self, file_path):
        """从PDF文件提取文本"""
        try:
            # 这里需要实现PDF文本提取
            return ""
        except Exception as e:
            current_app.logger.error(f"Error reading PDF file: {str(e)}")
            return ""

    def _extract_from_word(self, file_path):
        """从Word文件提取文本"""
        try:
            # 这里需要实现Word文本提取
            return ""
        except Exception as e:
            current_app.logger.error(f"Error reading Word file: {str(e)}")
            return ""

def process_knowledge_graph(entities, relations):
    """处理知识图谱数据，计算各种指标和分析结果"""
    # 创建算法实例
    kg_algo = KnowledgeGraphAlgorithms(entities, relations)
    
    # 计算节点中心性指标
    centrality_metrics = kg_algo.calculate_centrality_metrics()
    
    # 检测社区
    communities = kg_algo.detect_communities()
    
    # 分析关系模式
    relation_patterns = kg_algo.analyze_relation_patterns()
    
    # 计算图的整体指标
    graph_metrics = kg_algo.calculate_graph_metrics()
    
    # 查找重要子图
    important_subgraphs = kg_algo.find_important_subgraphs()
    
    # 推荐新的关系
    recommended_relations = kg_algo.recommend_relations()
    
    # 整合分析结果
    analysis_results = {
        'centrality_metrics': centrality_metrics,
        'communities': communities,
        'relation_patterns': relation_patterns,
        'graph_metrics': graph_metrics,
        'important_subgraphs': [list(sg) for sg in important_subgraphs],
        'recommended_relations': recommended_relations
    }
    
    return analysis_results

def enrich_graph_data(entities, relations):
    """使用算法分析结果丰富图数据"""
    analysis_results = process_knowledge_graph(entities, relations)
    
    # 为实体添加中心性指标
    for entity in entities:
        entity_id = entity['id']
        if entity_id in analysis_results['centrality_metrics']:
            entity['metrics'] = analysis_results['centrality_metrics'][entity_id]
        if entity_id in analysis_results['communities']:
            entity['community'] = analysis_results['communities'][entity_id]
    
    # 为关系添加模式信息
    for relation in relations:
        relation_type = relation['relation_type']
        if relation_type in analysis_results['relation_patterns']:
            relation['patterns'] = analysis_results['relation_patterns'][relation_type]
    
    return {
        'entities': entities,
        'relations': relations,
        'analysis': analysis_results
    }
