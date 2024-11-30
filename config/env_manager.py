"""
环境变量管理模块
"""
import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv

class EnvManager:
    """环境变量管理器"""
    
    def __init__(self, env: str = None):
        """初始化环境变量管理器
        
        Args:
            env (str, optional): 环境名称. 默认为 None，将从 APP_ENV 环境变量读取
        """
        self.env = env or os.getenv('APP_ENV', 'development')
        self.env_file = self._get_env_file()
        self.secrets_file = self._get_secrets_file()
        self._load_env_files()
        
    def _get_env_file(self) -> Path:
        """获取环境配置文件路径"""
        config_dir = Path(__file__).parent
        return config_dir / 'environments' / f'{self.env}.env'
        
    def _get_secrets_file(self) -> Path:
        """获取密钥配置文件路径"""
        config_dir = Path(__file__).parent
        return config_dir / 'secrets' / f'{self.env}.json'
        
    def _load_env_files(self):
        """加载环境变量文件"""
        # 加载 .env 文件
        if self.env_file.exists():
            load_dotenv(self.env_file)
            
        # 加载密钥文件
        if self.secrets_file.exists():
            with open(self.secrets_file, 'r', encoding='utf-8') as f:
                secrets = json.load(f)
                for key, value in secrets.items():
                    os.environ[key] = str(value)
                    
    def get(self, key: str, default: Any = None) -> Any:
        """获取环境变量值
        
        Args:
            key (str): 环境变量名
            default (Any, optional): 默认值. 默认为 None
            
        Returns:
            Any: 环境变量值
        """
        return os.getenv(key, default)
        
    def get_int(self, key: str, default: Optional[int] = None) -> Optional[int]:
        """获取整数类型的环境变量值
        
        Args:
            key (str): 环境变量名
            default (int, optional): 默认值. 默认为 None
            
        Returns:
            Optional[int]: 环境变量值
        """
        value = self.get(key)
        if value is None:
            return default
        return int(value)
        
    def get_float(self, key: str, default: Optional[float] = None) -> Optional[float]:
        """获取浮点数类型的环境变量值
        
        Args:
            key (str): 环境变量名
            default (float, optional): 默认值. 默认为 None
            
        Returns:
            Optional[float]: 环境变量值
        """
        value = self.get(key)
        if value is None:
            return default
        return float(value)
        
    def get_bool(self, key: str, default: Optional[bool] = None) -> Optional[bool]:
        """获取布尔类型的环境变量值
        
        Args:
            key (str): 环境变量名
            default (bool, optional): 默认值. 默认为 None
            
        Returns:
            Optional[bool]: 环境变量值
        """
        value = self.get(key)
        if value is None:
            return default
        return value.lower() in ('true', '1', 'yes', 'on')
        
    def get_list(self, key: str, separator: str = ',', default: Optional[list] = None) -> Optional[list]:
        """获取列表类型的环境变量值
        
        Args:
            key (str): 环境变量名
            separator (str, optional): 分隔符. 默认为 ','
            default (list, optional): 默认值. 默认为 None
            
        Returns:
            Optional[list]: 环境变量值
        """
        value = self.get(key)
        if value is None:
            return default
        return [item.strip() for item in value.split(separator)]
        
    def get_dict(self, key: str, default: Optional[Dict] = None) -> Optional[Dict]:
        """获取字典类型的环境变量值
        
        Args:
            key (str): 环境变量名
            default (Dict, optional): 默认值. 默认为 None
            
        Returns:
            Optional[Dict]: 环境变量值
        """
        value = self.get(key)
        if value is None:
            return default
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return default
            
    def set(self, key: str, value: Any):
        """设置环境变量值
        
        Args:
            key (str): 环境变量名
            value (Any): 环境变量值
        """
        os.environ[key] = str(value)
        
    def is_production(self) -> bool:
        """检查是否为生产环境
        
        Returns:
            bool: 是否为生产环境
        """
        return self.env == 'production'
        
    def is_staging(self) -> bool:
        """检查是否为测试环境
        
        Returns:
            bool: 是否为测试环境
        """
        return self.env == 'staging'
        
    def is_development(self) -> bool:
        """检查是否为开发环境
        
        Returns:
            bool: 是否为开发环境
        """
        return self.env == 'development'
        
    def get_database_url(self) -> str:
        """获取数据库连接URL
        
        Returns:
            str: 数据库连接URL
        """
        host = self.get('DB_HOST', 'localhost')
        port = self.get('DB_PORT', '5432')
        name = self.get('DB_NAME', 'knowledge_graph')
        user = self.get('DB_USER', 'postgres')
        password = self.get('DB_PASSWORD', '')
        
        return f"postgresql://{user}:{password}@{host}:{port}/{name}"
        
    def get_redis_url(self) -> str:
        """获取Redis连接URL
        
        Returns:
            str: Redis连接URL
        """
        host = self.get('REDIS_HOST', 'localhost')
        port = self.get('REDIS_PORT', '6379')
        db = self.get('REDIS_DB', '0')
        password = self.get('REDIS_PASSWORD', '')
        
        if password:
            return f"redis://:{password}@{host}:{port}/{db}"
        return f"redis://{host}:{port}/{db}"
        
    def get_storage_config(self) -> Dict[str, str]:
        """获取存储配置
        
        Returns:
            Dict[str, str]: 存储配置
        """
        return {
            'type': self.get('STORAGE_TYPE', 'local'),
            'bucket': self.get('STORAGE_BUCKET', ''),
            'region': self.get('STORAGE_REGION', ''),
            'access_key': self.get('STORAGE_ACCESS_KEY', ''),
            'secret_key': self.get('STORAGE_SECRET_KEY', '')
        }
        
    def get_monitor_config(self) -> Dict[str, Any]:
        """获取监控配置
        
        Returns:
            Dict[str, Any]: 监控配置
        """
        return {
            'enabled': self.get_bool('MONITOR_ENABLED', False),
            'endpoint': self.get('MONITOR_ENDPOINT', ''),
            'api_key': self.get('MONITOR_API_KEY', ''),
            'interval': self.get_int('MONITOR_INTERVAL', 60)
        }
        
    def get_notification_config(self) -> Dict[str, Any]:
        """获取通知配置
        
        Returns:
            Dict[str, Any]: 通知配置
        """
        return {
            'slack_webhook': self.get('SLACK_WEBHOOK_URL', ''),
            'email_recipients': self.get_list('EMAIL_NOTIFICATIONS', []),
            'enabled': self.get_bool('NOTIFICATIONS_ENABLED', True)
        }

# 创建全局环境变量管理器实例
env_manager = EnvManager()
