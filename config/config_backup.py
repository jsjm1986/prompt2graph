"""
配置备份模块 - 管理配置文件的备份和恢复
"""
import os
import shutil
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, List

class ConfigBackup:
    """配置备份管理器"""
    
    def __init__(self, backup_dir: str = 'config/backups'):
        """初始化配置备份管理器
        
        Args:
            backup_dir (str): 备份目录路径
        """
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # 配置日志
        self.logger = logging.getLogger(__name__)
        handler = logging.FileHandler('config/backup.log')
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        ))
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
        
    def create_backup(self, env: str) -> Optional[str]:
        """创建配置备份
        
        Args:
            env (str): 环境名称
            
        Returns:
            Optional[str]: 备份文件路径，如果失败则返回None
        """
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"{env}_{timestamp}"
            backup_path = self.backup_dir / backup_name
            
            # 创建备份目录
            backup_path.mkdir(exist_ok=True)
            
            # 备份环境配置文件
            env_file = Path(f'config/environments/{env}.env')
            if env_file.exists():
                shutil.copy2(env_file, backup_path / f'{env}.env')
                
            # 备份密钥文件
            secrets_file = Path(f'config/secrets/{env}.json')
            if secrets_file.exists():
                shutil.copy2(secrets_file, backup_path / f'{env}.json')
                
            # 创建备份元数据
            metadata = {
                'timestamp': timestamp,
                'environment': env,
                'files': [f.name for f in backup_path.glob('*')]
            }
            
            with open(backup_path / 'metadata.json', 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
                
            self.logger.info(f"Created backup: {backup_name}")
            return str(backup_path)
            
        except Exception as e:
            self.logger.error(f"Backup failed: {str(e)}")
            return None
            
    def restore_backup(self, backup_name: str) -> bool:
        """从备份恢复配置
        
        Args:
            backup_name (str): 备份名称
            
        Returns:
            bool: 恢复是否成功
        """
        try:
            backup_path = self.backup_dir / backup_name
            
            if not backup_path.exists():
                self.logger.error(f"Backup not found: {backup_name}")
                return False
                
            # 读取元数据
            with open(backup_path / 'metadata.json', 'r', encoding='utf-8') as f:
                metadata = json.load(f)
                
            env = metadata['environment']
            
            # 恢复环境配置文件
            env_backup = backup_path / f'{env}.env'
            if env_backup.exists():
                shutil.copy2(env_backup, f'config/environments/{env}.env')
                
            # 恢复密钥文件
            secrets_backup = backup_path / f'{env}.json'
            if secrets_backup.exists():
                shutil.copy2(secrets_backup, f'config/secrets/{env}.json')
                
            self.logger.info(f"Restored backup: {backup_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Restore failed: {str(e)}")
            return False
            
    def list_backups(self) -> List[dict]:
        """列出所有备份
        
        Returns:
            List[dict]: 备份信息列表
        """
        backups = []
        
        for backup_dir in self.backup_dir.glob('*'):
            if backup_dir.is_dir():
                metadata_file = backup_dir / 'metadata.json'
                if metadata_file.exists():
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                        backups.append({
                            'name': backup_dir.name,
                            'timestamp': metadata['timestamp'],
                            'environment': metadata['environment'],
                            'files': metadata['files']
                        })
                        
        return sorted(backups, key=lambda x: x['timestamp'], reverse=True)
        
    def cleanup_old_backups(self, max_backups: int = 10):
        """清理旧的备份
        
        Args:
            max_backups (int): 保留的最大备份数量
        """
        backups = self.list_backups()
        
        if len(backups) > max_backups:
            for backup in backups[max_backups:]:
                backup_path = self.backup_dir / backup['name']
                try:
                    shutil.rmtree(backup_path)
                    self.logger.info(f"Removed old backup: {backup['name']}")
                except Exception as e:
                    self.logger.error(f"Failed to remove backup {backup['name']}: {str(e)}")
                    
    def verify_backup(self, backup_name: str) -> bool:
        """验证备份的完整性
        
        Args:
            backup_name (str): 备份名称
            
        Returns:
            bool: 备份是否完整
        """
        try:
            backup_path = self.backup_dir / backup_name
            
            if not backup_path.exists():
                return False
                
            # 检查元数据文件
            metadata_file = backup_path / 'metadata.json'
            if not metadata_file.exists():
                return False
                
            # 读取并验证元数据
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
                
            # 验证所有文件是否存在
            for filename in metadata['files']:
                if not (backup_path / filename).exists():
                    return False
                    
            return True
            
        except Exception:
            return False
