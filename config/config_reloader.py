"""
配置热重载模块 - 实现配置的动态重载功能
"""
import os
import time
import json
import logging
import threading
from typing import Dict, Callable, Set
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class ConfigChangeHandler(FileSystemEventHandler):
    """配置文件变更处理器"""
    
    def __init__(self, callback: Callable[[str], None]):
        """初始化变更处理器
        
        Args:
            callback (Callable[[str], None]): 配置变更回调函数
        """
        self.callback = callback
        self.last_modified: Dict[str, float] = {}
        
    def on_modified(self, event):
        if event.is_directory:
            return
            
        # 获取文件路径
        file_path = event.src_path
        
        # 检查是否是配置文件
        if not (file_path.endswith('.env') or file_path.endswith('.json')):
            return
            
        # 防止重复触发
        current_time = time.time()
        last_modified = self.last_modified.get(file_path, 0)
        if current_time - last_modified < 1:  # 1秒内的修改忽略
            return
            
        self.last_modified[file_path] = current_time
        self.callback(file_path)

class ConfigReloader:
    """配置热重载管理器"""
    
    def __init__(self, env_manager):
        """初始化配置热重载管理器
        
        Args:
            env_manager: 环境变量管理器实例
        """
        self.env_manager = env_manager
        self.observer = Observer()
        self.handler = ConfigChangeHandler(self._handle_config_change)
        self.watch_paths = set()
        self.callbacks: Dict[str, Set[Callable]] = {}
        self.lock = threading.Lock()
        
        # 配置日志
        self.logger = logging.getLogger(__name__)
        handler = logging.FileHandler('config/reload.log')
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        ))
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
        
    def start(self):
        """启动配置监控"""
        try:
            # 监控环境配置目录
            env_path = Path('config/environments')
            if env_path.exists():
                self.observer.schedule(self.handler, str(env_path), recursive=False)
                self.watch_paths.add(str(env_path))
                
            # 监控密钥配置目录
            secrets_path = Path('config/secrets')
            if secrets_path.exists():
                self.observer.schedule(self.handler, str(secrets_path), recursive=False)
                self.watch_paths.add(str(secrets_path))
                
            self.observer.start()
            self.logger.info("Config reloader started")
            
        except Exception as e:
            self.logger.error(f"Failed to start config reloader: {str(e)}")
            
    def stop(self):
        """停止配置监控"""
        try:
            self.observer.stop()
            self.observer.join()
            self.logger.info("Config reloader stopped")
        except Exception as e:
            self.logger.error(f"Failed to stop config reloader: {str(e)}")
            
    def register_callback(self, config_key: str, callback: Callable):
        """注册配置变更回调函数
        
        Args:
            config_key (str): 配置键
            callback (Callable): 回调函数
        """
        with self.lock:
            if config_key not in self.callbacks:
                self.callbacks[config_key] = set()
            self.callbacks[config_key].add(callback)
            
    def unregister_callback(self, config_key: str, callback: Callable):
        """注销配置变更回调函数
        
        Args:
            config_key (str): 配置键
            callback (Callable): 回调函数
        """
        with self.lock:
            if config_key in self.callbacks:
                self.callbacks[config_key].discard(callback)
                
    def _handle_config_change(self, file_path: str):
        """处理配置文件变更
        
        Args:
            file_path (str): 变更的文件路径
        """
        try:
            # 重新加载环境变量
            self.env_manager._load_env_files()
            
            # 获取变更的配置键
            changed_keys = self._get_changed_keys(file_path)
            
            # 触发回调
            for key in changed_keys:
                if key in self.callbacks:
                    for callback in self.callbacks[key]:
                        try:
                            callback()
                        except Exception as e:
                            self.logger.error(f"Callback failed for {key}: {str(e)}")
                            
            self.logger.info(f"Config reloaded: {file_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to handle config change: {str(e)}")
            
    def _get_changed_keys(self, file_path: str) -> Set[str]:
        """获取变更的配置键
        
        Args:
            file_path (str): 变更的文件路径
            
        Returns:
            Set[str]: 变更的配置键集合
        """
        changed_keys = set()
        
        try:
            if file_path.endswith('.env'):
                # 解析.env文件
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            key = line.split('=')[0].strip()
                            changed_keys.add(key)
                            
            elif file_path.endswith('.json'):
                # 解析JSON文件
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    changed_keys.update(data.keys())
                    
        except Exception as e:
            self.logger.error(f"Failed to parse config file {file_path}: {str(e)}")
            
        return changed_keys
        
    def add_watch_path(self, path: str):
        """添加监控路径
        
        Args:
            path (str): 要监控的路径
        """
        if path not in self.watch_paths:
            try:
                self.observer.schedule(self.handler, path, recursive=False)
                self.watch_paths.add(path)
                self.logger.info(f"Added watch path: {path}")
            except Exception as e:
                self.logger.error(f"Failed to add watch path {path}: {str(e)}")
                
    def remove_watch_path(self, path: str):
        """移除监控路径
        
        Args:
            path (str): 要移除的监控路径
        """
        if path in self.watch_paths:
            try:
                for watch in self.observer._watches:
                    if watch.path == path:
                        self.observer.unschedule(watch)
                        break
                self.watch_paths.remove(path)
                self.logger.info(f"Removed watch path: {path}")
            except Exception as e:
                self.logger.error(f"Failed to remove watch path {path}: {str(e)}")
                
    def get_watch_paths(self) -> Set[str]:
        """获取所有监控路径
        
        Returns:
            Set[str]: 监控路径集合
        """
        return self.watch_paths.copy()
