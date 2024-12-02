import logging
import requests
from functools import wraps
from flask import current_app
import time
import hashlib
import json
from datetime import datetime, timedelta

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
    """DeepSeek API 封装 - 使用模拟数据"""
    def __init__(self, api_key=None):
        self.logger = logging.getLogger(__name__)
    
    def extract_entities(self, text):
        """从文本中提取实体和关系（使用模拟数据）"""
        if not text:
            return {'entities': [], 'relations': []}

        try:
            # 生成模拟数据
            words = [word for word in text.split() if len(word) > 1][:5]  # 取前5个非空词作为实体
            entities = []
            relations = []
            
            # 生成实体
            for i, word in enumerate(words, 1):
                entity = {
                    'id': i,
                    'name': word,
                    'type': '概念',
                    'properties': {'description': f'从文本中提取的第{i}个实体'}
                }
                entities.append(entity)
            
            # 生成关系
            for i in range(len(entities)-1):
                relation = {
                    'source_id': entities[i]['id'],
                    'target_id': entities[i+1]['id'],
                    'relation_type': '关联',  
                    'properties': {'strength': 'strong'},
                    'confidence': 0.9
                }
                relations.append(relation)
            
            return {
                'entities': entities,
                'relations': relations
            }
            
        except Exception as e:
            self.logger.error(f"Entity extraction failed: {str(e)}")
            return {'entities': [], 'relations': []}

class DataCleaner:
    """数据清理工具"""
    @staticmethod
    def clean_text(text):
        """清理输入文本"""
        # 移除特殊字符
        # 标准化空白字符
        # 移除HTML标签等
        return text.strip()
    
    @staticmethod
    def validate_entity(entity):
        """验证实体数据"""
        required_fields = ['id', 'name', 'type']
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
        ext = file_path.split('.')[-1].lower()
        if ext == 'txt':
            return self._extract_from_txt(file_path)
        elif ext == 'pdf':
            return self._extract_from_pdf(file_path)
        elif ext in ['doc', 'docx']:
            return self._extract_from_word(file_path)
        else:
            raise ValueError(f"Unsupported file type: {ext}")
    
    def _extract_from_txt(self, file_path):
        """从txt文件提取文本"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def _extract_from_pdf(self, file_path):
        """从PDF文件提取文本"""
        # TODO: 实现PDF文本提取
        pass
    
    def _extract_from_word(self, file_path):
        """从Word文件提取文本"""
        # TODO: 实现Word文本提取
        pass
