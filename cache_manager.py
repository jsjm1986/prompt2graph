import os
import json
import hashlib
import pickle
from typing import Any, Dict, Optional, List
from datetime import datetime, timedelta
import logging
from threading import Lock
import networkx as nx
from dataclasses import dataclass, asdict
import time

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CacheMetadata:
    """缓存元数据"""
    key: str
    created_at: str
    expires_at: str
    size_bytes: int
    data_type: str
    access_count: int
    last_accessed: str

class CacheManager:
    """缓存管理器"""
    
    def __init__(self, cache_dir: str = "cache", max_size_mb: int = 500,
                 default_ttl_hours: int = 24):
        self.cache_dir = cache_dir
        self.max_size_bytes = max_size_mb * 1024 * 1024  # 转换为字节
        self.default_ttl = timedelta(hours=default_ttl_hours)
        self.metadata_file = os.path.join(cache_dir, "cache_metadata.json")
        self.lock = Lock()
        self.metadata: Dict[str, CacheMetadata] = {}
        
        # 确保缓存目录存在
        os.makedirs(cache_dir, exist_ok=True)
        
        # 加载元数据
        self._load_metadata()
        
        # 清理过期缓存
        self._cleanup()
    
    def _generate_key(self, data: Any, prefix: str = "") -> str:
        """生成缓存键"""
        if isinstance(data, (str, bytes)):
            content = data if isinstance(data, bytes) else data.encode()
        else:
            content = pickle.dumps(data)
        
        hash_value = hashlib.sha256(content).hexdigest()
        return f"{prefix}_{hash_value}" if prefix else hash_value
    
    def _get_cache_path(self, key: str) -> str:
        """获取缓存文件路径"""
        return os.path.join(self.cache_dir, f"{key}.cache")
    
    def _load_metadata(self):
        """加载缓存元数据"""
        try:
            if os.path.exists(self.metadata_file):
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.metadata = {
                        k: CacheMetadata(**v) for k, v in data.items()
                    }
        except Exception as e:
            logger.error(f"加载缓存元数据失败: {str(e)}")
            self.metadata = {}
    
    def _save_metadata(self):
        """保存缓存元数据"""
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump({k: asdict(v) for k, v in self.metadata.items()},
                         f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存缓存元数据失败: {str(e)}")
    
    def _cleanup(self):
        """清理过期和超大的缓存"""
        with self.lock:
            current_time = datetime.now()
            total_size = 0
            items_to_remove = []
            
            # 检查过期和计算总大小
            for key, meta in self.metadata.items():
                if datetime.fromisoformat(meta.expires_at) < current_time:
                    items_to_remove.append(key)
                else:
                    total_size += meta.size_bytes
            
            # 如果总大小超过限制，删除最少访问的缓存
            if total_size > self.max_size_bytes:
                sorted_items = sorted(
                    self.metadata.items(),
                    key=lambda x: (x[1].access_count, x[1].last_accessed)
                )
                
                while total_size > self.max_size_bytes and sorted_items:
                    key, meta = sorted_items.pop(0)
                    total_size -= meta.size_bytes
                    items_to_remove.append(key)
            
            # 删除缓存文件和元数据
            for key in items_to_remove:
                self._remove_cache(key)
    
    def _remove_cache(self, key: str):
        """删除指定的缓存"""
        cache_path = self._get_cache_path(key)
        try:
            if os.path.exists(cache_path):
                os.remove(cache_path)
            if key in self.metadata:
                del self.metadata[key]
        except Exception as e:
            logger.error(f"删除缓存失败 {key}: {str(e)}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取缓存数据"""
        with self.lock:
            if key not in self.metadata:
                return default
            
            meta = self.metadata[key]
            
            # 检查是否过期
            if datetime.fromisoformat(meta.expires_at) < datetime.now():
                self._remove_cache(key)
                return default
            
            try:
                cache_path = self._get_cache_path(key)
                with open(cache_path, 'rb') as f:
                    data = pickle.load(f)
                
                # 更新访问信息
                meta.access_count += 1
                meta.last_accessed = datetime.now().isoformat()
                self._save_metadata()
                
                return data
            
            except Exception as e:
                logger.error(f"读取缓存失败 {key}: {str(e)}")
                return default
    
    def set(self, key: str, data: Any, ttl_hours: Optional[int] = None,
            data_type: str = "general") -> bool:
        """设置缓存数据"""
        with self.lock:
            try:
                # 序列化数据
                cache_path = self._get_cache_path(key)
                with open(cache_path, 'wb') as f:
                    pickle.dump(data, f)
                
                # 获取文件大小
                size_bytes = os.path.getsize(cache_path)
                
                # 创建元数据
                created_at = datetime.now()
                expires_at = created_at + (
                    timedelta(hours=ttl_hours) if ttl_hours else self.default_ttl
                )
                
                self.metadata[key] = CacheMetadata(
                    key=key,
                    created_at=created_at.isoformat(),
                    expires_at=expires_at.isoformat(),
                    size_bytes=size_bytes,
                    data_type=data_type,
                    access_count=0,
                    last_accessed=created_at.isoformat()
                )
                
                self._save_metadata()
                self._cleanup()  # 检查是否需要清理
                
                return True
            
            except Exception as e:
                logger.error(f"设置缓存失败 {key}: {str(e)}")
                return False
    
    def clear(self):
        """清空所有缓存"""
        with self.lock:
            try:
                # 删除所有缓存文件
                for key in list(self.metadata.keys()):
                    self._remove_cache(key)
                
                # 清空元数据
                self.metadata = {}
                self._save_metadata()
                
                logger.info("缓存已清空")
                return True
            
            except Exception as e:
                logger.error(f"清空缓存失败: {str(e)}")
                return False
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        with self.lock:
            total_size = sum(meta.size_bytes for meta in self.metadata.values())
            total_items = len(self.metadata)
            
            # 按数据类型统计
            type_stats = {}
            for meta in self.metadata.values():
                if meta.data_type not in type_stats:
                    type_stats[meta.data_type] = {
                        'count': 0,
                        'total_size': 0,
                        'total_access': 0
                    }
                
                stats = type_stats[meta.data_type]
                stats['count'] += 1
                stats['total_size'] += meta.size_bytes
                stats['total_access'] += meta.access_count
            
            return {
                'total_items': total_items,
                'total_size_bytes': total_size,
                'max_size_bytes': self.max_size_bytes,
                'usage_percent': (total_size / self.max_size_bytes) * 100 if self.max_size_bytes > 0 else 0,
                'type_statistics': type_stats,
                'timestamp': datetime.now().isoformat()
            }

class GraphCacheManager(CacheManager):
    """图数据专用缓存管理器"""
    
    def __init__(self, cache_dir: str = "cache/graphs", max_size_mb: int = 200,
                 default_ttl_hours: int = 12):
        super().__init__(cache_dir, max_size_mb, default_ttl_hours)
    
    def cache_graph(self, graph: nx.Graph, key: str) -> bool:
        """缓存图数据"""
        return self.set(key, graph, data_type="graph")
    
    def get_graph(self, key: str) -> Optional[nx.Graph]:
        """获取缓存的图数据"""
        return self.get(key)
    
    def cache_analysis_results(self, key: str, results: Dict[str, Any],
                             ttl_hours: int = 24) -> bool:
        """缓存分析结果"""
        return self.set(f"analysis_{key}", results, ttl_hours, data_type="analysis")
    
    def get_analysis_results(self, key: str) -> Optional[Dict[str, Any]]:
        """获取缓存的分析结果"""
        return self.get(f"analysis_{key}")
    
    def cache_visualization(self, key: str, html_content: str,
                          ttl_hours: int = 24) -> bool:
        """缓存可视化结果"""
        return self.set(f"viz_{key}", html_content, ttl_hours, data_type="visualization")
    
    def get_visualization(self, key: str) -> Optional[str]:
        """获取缓存的可视化结果"""
        return self.get(f"viz_{key}")
