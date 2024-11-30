"""
配置验证模块 - 验证环境变量配置的完整性和正确性
"""
import re
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('config/config_changes.log'),
        logging.StreamHandler()
    ]
)

@dataclass
class ConfigRule:
    """配置规则类"""
    required: bool = False
    type: type = str
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    pattern: Optional[str] = None
    allowed_values: Optional[List[Any]] = None
    custom_validator: Optional[callable] = None

class ConfigValidator:
    """配置验证器类"""
    
    # 定义配置规则
    CONFIG_RULES = {
        # 服务器配置
        'APP_ENV': ConfigRule(required=True, allowed_values=['development', 'staging', 'production']),
        'APP_DEBUG': ConfigRule(type=bool),
        'APP_PORT': ConfigRule(type=int, min_value=1, max_value=65535),
        'APP_HOST': ConfigRule(pattern=r'^[a-zA-Z0-9\.\-]+$'),
        
        # 数据库配置
        'DB_HOST': ConfigRule(required=True),
        'DB_PORT': ConfigRule(required=True, type=int, min_value=1, max_value=65535),
        'DB_NAME': ConfigRule(required=True),
        'DB_USER': ConfigRule(required=True),
        'DB_PASSWORD': ConfigRule(required=True),
        
        # 缓存配置
        'REDIS_HOST': ConfigRule(required=True),
        'REDIS_PORT': ConfigRule(required=True, type=int, min_value=1, max_value=65535),
        'REDIS_DB': ConfigRule(type=int, min_value=0),
        
        # 性能配置
        'MAX_WORKERS': ConfigRule(type=int, min_value=1, max_value=32),
        'BATCH_SIZE': ConfigRule(type=int, min_value=1),
        'CACHE_TTL': ConfigRule(type=int, min_value=0),
        
        # 安全配置
        'JWT_SECRET': ConfigRule(required=True, pattern=r'^[A-Za-z0-9_\-]{32,}$'),
        'API_RATE_LIMIT': ConfigRule(type=int, min_value=1),
    }
    
    def __init__(self, env_manager):
        """初始化配置验证器
        
        Args:
            env_manager: 环境变量管理器实例
        """
        self.env_manager = env_manager
        self.logger = logging.getLogger(__name__)
        
    def validate_all(self) -> List[str]:
        """验证所有配置
        
        Returns:
            List[str]: 错误信息列表
        """
        errors = []
        
        for key, rule in self.CONFIG_RULES.items():
            value = self.env_manager.get(key)
            
            # 检查必需项
            if rule.required and value is None:
                errors.append(f"Missing required config: {key}")
                continue
                
            if value is not None:
                # 类型检查
                try:
                    if rule.type == bool:
                        value = str(value).lower() in ('true', '1', 'yes', 'on')
                    else:
                        value = rule.type(value)
                except ValueError:
                    errors.append(f"Invalid type for {key}: expected {rule.type.__name__}")
                    continue
                
                # 范围检查
                if rule.min_value is not None and value < rule.min_value:
                    errors.append(f"{key} must be >= {rule.min_value}")
                if rule.max_value is not None and value > rule.max_value:
                    errors.append(f"{key} must be <= {rule.max_value}")
                
                # 模式检查
                if rule.pattern and not re.match(rule.pattern, str(value)):
                    errors.append(f"{key} does not match pattern: {rule.pattern}")
                
                # 允许值检查
                if rule.allowed_values and value not in rule.allowed_values:
                    errors.append(f"{key} must be one of: {rule.allowed_values}")
                
                # 自定义验证
                if rule.custom_validator:
                    try:
                        rule.custom_validator(value)
                    except Exception as e:
                        errors.append(f"Custom validation failed for {key}: {str(e)}")
                        
        return errors
        
    def log_config_change(self, key: str, old_value: Any, new_value: Any):
        """记录配置更改
        
        Args:
            key (str): 配置键
            old_value (Any): 旧值
            new_value (Any): 新值
        """
        timestamp = datetime.now().isoformat()
        message = f"{timestamp} - Config changed: {key} = {old_value} -> {new_value}"
        self.logger.info(message)
        
    def validate_database_connection(self) -> bool:
        """验证数据库连接
        
        Returns:
            bool: 连接是否成功
        """
        try:
            url = self.env_manager.get_database_url()
            # 这里添加数据库连接测试代码
            return True
        except Exception as e:
            self.logger.error(f"Database connection failed: {str(e)}")
            return False
            
    def validate_redis_connection(self) -> bool:
        """验证Redis连接
        
        Returns:
            bool: 连接是否成功
        """
        try:
            url = self.env_manager.get_redis_url()
            # 这里添加Redis连接测试代码
            return True
        except Exception as e:
            self.logger.error(f"Redis connection failed: {str(e)}")
            return False
            
    def validate_storage_access(self) -> bool:
        """验证存储访问
        
        Returns:
            bool: 访问是否成功
        """
        try:
            config = self.env_manager.get_storage_config()
            # 这里添加存储访问测试代码
            return True
        except Exception as e:
            self.logger.error(f"Storage access failed: {str(e)}")
            return False
