import logging
import requests
from functools import wraps
from flask_caching import Cache
from flask import current_app
import time
import hashlib
import json

# 初始化缓存
cache = Cache()

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
    """DeepSeek API 封装"""
    def __init__(self, api_key):
        self.api_key = api_key
        self.rate_limiter = APIRateLimiter(calls_limit=100, time_window=3600)
        self.logger = logging.getLogger(__name__)
    
    @cache.memoize(timeout=300)
    def extract_entities(self, text):
        """从文本中提取实体，带缓存"""
        cache_key = hashlib.md5(text.encode()).hexdigest()
        
        if not self.rate_limiter.can_call():
            raise Exception("API rate limit exceeded")
        
        try:
            response = self._make_api_call(text)
            return self._process_response(response)
        except Exception as e:
            self.logger.error(f"API调用失败: {str(e)}")
            raise
    
    def _make_api_call(self, text, max_retries=3):
        """进行API调用，支持重试"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    "https://api.deepseek.com/v1/extract",
                    headers=headers,
                    json={"text": text}
                )
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    raise
                time.sleep(2 ** attempt)  # 指数退避
    
    def _process_response(self, response):
        """处理API响应"""
        if not response.get("success"):
            raise Exception(response.get("error", "Unknown API error"))
        return response["data"]

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
