from typing import Dict, Any, Optional, List
import json
import os
import logging
from dataclasses import dataclass
from threading import Lock

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ThemeColors:
    """主题颜色配置"""
    primary: str
    secondary: str
    background: str
    text: str
    border: str
    hover: str
    shadow: str

@dataclass
class ThemeConfig:
    """主题配置"""
    id: str
    name: str
    description: str
    colors: ThemeColors
    dark_mode: bool

class ThemeManager:
    """主题管理器"""
    
    def __init__(self, themes_dir: str = "static/themes",
                 default_theme: str = "light"):
        self.themes_dir = themes_dir
        self.default_theme = default_theme
        self.current_theme = default_theme
        self.themes: Dict[str, ThemeConfig] = {}
        self.lock = Lock()
        
        # 加载内置主题
        self._load_built_in_themes()
        
        # 加载自定义主题
        self._load_custom_themes()
    
    def _load_built_in_themes(self):
        """加载内置主题"""
        built_in_themes = {
            "light": ThemeConfig(
                id="light",
                name="Light Theme",
                description="Default light theme",
                colors=ThemeColors(
                    primary="#4a90e2",
                    secondary="#67c23a",
                    background="#ffffff",
                    text="#2c3e50",
                    border="#dcdfe6",
                    hover="#ecf5ff",
                    shadow="rgba(0, 0, 0, 0.1)"
                ),
                dark_mode=False
            ),
            "dark": ThemeConfig(
                id="dark",
                name="Dark Theme",
                description="Default dark theme",
                colors=ThemeColors(
                    primary="#409eff",
                    secondary="#67c23a",
                    background="#1a1a1a",
                    text="#ffffff",
                    border="#4c4c4c",
                    hover="#363636",
                    shadow="rgba(255, 255, 255, 0.1)"
                ),
                dark_mode=True
            ),
            "blue": ThemeConfig(
                id="blue",
                name="Blue Theme",
                description="Professional blue theme",
                colors=ThemeColors(
                    primary="#1976d2",
                    secondary="#42a5f5",
                    background="#f5f5f5",
                    text="#263238",
                    border="#e0e0e0",
                    hover="#bbdefb",
                    shadow="rgba(25, 118, 210, 0.1)"
                ),
                dark_mode=False
            ),
            "green": ThemeConfig(
                id="green",
                name="Green Theme",
                description="Nature-inspired green theme",
                colors=ThemeColors(
                    primary="#2e7d32",
                    secondary="#66bb6a",
                    background="#f1f8e9",
                    text="#1b5e20",
                    border="#c8e6c9",
                    hover="#dcedc8",
                    shadow="rgba(46, 125, 50, 0.1)"
                ),
                dark_mode=False
            )
        }
        
        self.themes.update(built_in_themes)
        logger.info(f"已加载 {len(built_in_themes)} 个内置主题")
    
    def _load_custom_themes(self):
        """加载自定义主题"""
        try:
            if not os.path.exists(self.themes_dir):
                os.makedirs(self.themes_dir)
                return
            
            for file_name in os.listdir(self.themes_dir):
                if file_name.endswith('.json'):
                    theme_path = os.path.join(self.themes_dir, file_name)
                    try:
                        with open(theme_path, 'r', encoding='utf-8') as f:
                            theme_data = json.load(f)
                            theme_id = file_name[:-5]  # 移除.json后缀
                            
                            # 创建主题配置
                            self.themes[theme_id] = ThemeConfig(
                                id=theme_id,
                                name=theme_data.get('name', theme_id),
                                description=theme_data.get('description', ''),
                                colors=ThemeColors(**theme_data.get('colors', {})),
                                dark_mode=theme_data.get('dark_mode', False)
                            )
                    
                    except Exception as e:
                        logger.error(f"加载主题文件失败 {theme_path}: {str(e)}")
            
            logger.info(f"已加载 {len(self.themes)} 个主题")
        
        except Exception as e:
            logger.error(f"加载自定义主题失败: {str(e)}")
    
    def set_theme(self, theme_id: str) -> bool:
        """设置当前主题"""
        with self.lock:
            if theme_id not in self.themes:
                logger.error(f"未找到主题: {theme_id}")
                return False
            
            self.current_theme = theme_id
            logger.info(f"当前主题已设置为: {self.themes[theme_id].name}")
            return True
    
    def get_theme(self, theme_id: Optional[str] = None) -> Optional[ThemeConfig]:
        """获取主题配置"""
        target_theme = theme_id or self.current_theme
        return self.themes.get(target_theme)
    
    def get_available_themes(self) -> Dict[str, str]:
        """获取所有可用的主题"""
        return {theme_id: theme.name for theme_id, theme in self.themes.items()}
    
    def create_theme(self, theme_data: Dict[str, Any]) -> bool:
        """创建新主题"""
        with self.lock:
            try:
                theme_id = theme_data.get('id')
                if not theme_id:
                    logger.error("主题ID不能为空")
                    return False
                
                if theme_id in self.themes:
                    logger.error(f"主题已存在: {theme_id}")
                    return False
                
                # 创建主题配置
                self.themes[theme_id] = ThemeConfig(
                    id=theme_id,
                    name=theme_data.get('name', theme_id),
                    description=theme_data.get('description', ''),
                    colors=ThemeColors(**theme_data.get('colors', {})),
                    dark_mode=theme_data.get('dark_mode', False)
                )
                
                # 保存到文件
                theme_path = os.path.join(self.themes_dir, f"{theme_id}.json")
                with open(theme_path, 'w', encoding='utf-8') as f:
                    json.dump(theme_data, f, ensure_ascii=False, indent=2)
                
                logger.info(f"已创建新主题: {theme_id}")
                return True
            
            except Exception as e:
                logger.error(f"创建主题失败: {str(e)}")
                return False
    
    def update_theme(self, theme_id: str, theme_data: Dict[str, Any]) -> bool:
        """更新主题"""
        with self.lock:
            if theme_id not in self.themes:
                logger.error(f"未找到主题: {theme_id}")
                return False
            
            try:
                # 更新主题配置
                self.themes[theme_id] = ThemeConfig(
                    id=theme_id,
                    name=theme_data.get('name', theme_id),
                    description=theme_data.get('description', ''),
                    colors=ThemeColors(**theme_data.get('colors', {})),
                    dark_mode=theme_data.get('dark_mode', False)
                )
                
                # 如果是自定义主题，更新文件
                theme_path = os.path.join(self.themes_dir, f"{theme_id}.json")
                if os.path.exists(theme_path):
                    with open(theme_path, 'w', encoding='utf-8') as f:
                        json.dump(theme_data, f, ensure_ascii=False, indent=2)
                
                logger.info(f"已更新主题: {theme_id}")
                return True
            
            except Exception as e:
                logger.error(f"更新主题失败: {str(e)}")
                return False
    
    def delete_theme(self, theme_id: str) -> bool:
        """删除主题"""
        with self.lock:
            if theme_id not in self.themes:
                logger.error(f"未找到主题: {theme_id}")
                return False
            
            # 不能删除内置主题
            if theme_id in ["light", "dark", "blue", "green"]:
                logger.error("不能删除内置主题")
                return False
            
            try:
                # 删除主题配置
                del self.themes[theme_id]
                
                # 删除主题文件
                theme_path = os.path.join(self.themes_dir, f"{theme_id}.json")
                if os.path.exists(theme_path):
                    os.remove(theme_path)
                
                # 如果删除的是当前主题，切换到默认主题
                if theme_id == self.current_theme:
                    self.current_theme = self.default_theme
                
                logger.info(f"已删除主题: {theme_id}")
                return True
            
            except Exception as e:
                logger.error(f"删除主题失败: {str(e)}")
                return False
    
    def get_css_variables(self, theme_id: Optional[str] = None) -> Dict[str, str]:
        """获取CSS变量"""
        theme = self.get_theme(theme_id)
        if not theme:
            return {}
        
        return {
            "--primary-color": theme.colors.primary,
            "--secondary-color": theme.colors.secondary,
            "--background-color": theme.colors.background,
            "--text-color": theme.colors.text,
            "--border-color": theme.colors.border,
            "--hover-color": theme.colors.hover,
            "--shadow-color": theme.colors.shadow
        }
    
    def apply_theme_to_element(self, element_id: str, theme_id: Optional[str] = None) -> str:
        """生成应用主题的CSS"""
        variables = self.get_css_variables(theme_id)
        css = f"#{element_id} {{\n"
        for var_name, value in variables.items():
            css += f"    {var_name}: {value};\n"
        css += "}"
        return css
