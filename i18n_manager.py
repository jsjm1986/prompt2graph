import json
import os
from typing import Dict, Any, Optional
import logging
from dataclasses import dataclass
from threading import Lock

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class LocaleConfig:
    """区域设置配置"""
    code: str
    name: str
    file_path: str
    fallback: Optional[str] = None

class I18nManager:
    """国际化管理器"""
    
    def __init__(self, locale_dir: str = "static/i18n", default_locale: str = "en-US"):
        self.locale_dir = locale_dir
        self.default_locale = default_locale
        self.current_locale = default_locale
        self.translations: Dict[str, Dict[str, Any]] = {}
        self.locales: Dict[str, LocaleConfig] = {}
        self.lock = Lock()
        
        # 加载所有可用的语言
        self._load_available_locales()
        
        # 加载默认语言
        self._load_locale(default_locale)
    
    def _load_available_locales(self):
        """加载所有可用的语言配置"""
        try:
            # 遍历语言目录
            for file_name in os.listdir(self.locale_dir):
                if file_name.endswith('.json'):
                    locale_code = file_name[:-5]  # 移除.json后缀
                    file_path = os.path.join(self.locale_dir, file_name)
                    
                    # 创建语言配置
                    self.locales[locale_code] = LocaleConfig(
                        code=locale_code,
                        name=self._get_locale_name(locale_code),
                        file_path=file_path,
                        fallback=self.default_locale if locale_code != self.default_locale else None
                    )
            
            logger.info(f"已加载 {len(self.locales)} 个语言配置")
        
        except Exception as e:
            logger.error(f"加载语言配置失败: {str(e)}")
    
    def _get_locale_name(self, locale_code: str) -> str:
        """获取语言名称"""
        locale_names = {
            "en-US": "English (US)",
            "zh-CN": "简体中文",
            "zh-TW": "繁體中文",
            "ja-JP": "日本語",
            "ko-KR": "한국어",
            "fr-FR": "Français",
            "de-DE": "Deutsch",
            "es-ES": "Español",
            "pt-BR": "Português (Brasil)",
            "ru-RU": "Русский"
        }
        return locale_names.get(locale_code, locale_code)
    
    def _load_locale(self, locale_code: str):
        """加载指定语言的翻译"""
        if locale_code not in self.locales:
            logger.error(f"未找到语言配置: {locale_code}")
            return
        
        config = self.locales[locale_code]
        
        try:
            with open(config.file_path, 'r', encoding='utf-8') as f:
                self.translations[locale_code] = json.load(f)
            logger.info(f"已加载语言: {config.name}")
        
        except Exception as e:
            logger.error(f"加载语言文件失败 {config.file_path}: {str(e)}")
            
            # 如果有回退语言，确保它已加载
            if config.fallback and config.fallback not in self.translations:
                self._load_locale(config.fallback)
    
    def set_locale(self, locale_code: str) -> bool:
        """设置当前语言"""
        with self.lock:
            if locale_code not in self.locales:
                logger.error(f"不支持的语言: {locale_code}")
                return False
            
            # 如果语言未加载，先加载
            if locale_code not in self.translations:
                self._load_locale(locale_code)
            
            self.current_locale = locale_code
            logger.info(f"当前语言已设置为: {self.locales[locale_code].name}")
            return True
    
    def get_text(self, key: str, default: str = "", locale: Optional[str] = None) -> str:
        """获取翻译文本"""
        # 使用指定的语言或当前语言
        target_locale = locale or self.current_locale
        
        # 如果目标语言不存在，使用默认语言
        if target_locale not in self.translations:
            target_locale = self.default_locale
        
        # 获取翻译
        translation = self.translations.get(target_locale, {})
        keys = key.split('.')
        
        # 遍历键路径
        for k in keys:
            translation = translation.get(k, {})
        
        # 如果没有找到翻译
        if not translation or isinstance(translation, dict):
            # 如果有回退语言，尝试使用回退语言
            if target_locale != self.default_locale:
                return self.get_text(key, default, self.default_locale)
            return default or key
        
        return translation
    
    def get_available_locales(self) -> Dict[str, str]:
        """获取所有可用的语言"""
        return {code: config.name for code, config in self.locales.items()}
    
    def reload_locale(self, locale_code: str) -> bool:
        """重新加载指定语言"""
        with self.lock:
            if locale_code not in self.locales:
                logger.error(f"未找到语言配置: {locale_code}")
                return False
            
            # 重新加载语言文件
            self._load_locale(locale_code)
            return True
    
    def reload_all(self):
        """重新加载所有语言"""
        with self.lock:
            # 重新加载语言配置
            self._load_available_locales()
            
            # 重新加载所有翻译
            for locale_code in self.locales:
                self._load_locale(locale_code)
    
    def format_text(self, key: str, params: Dict[str, Any] = None,
                   locale: Optional[str] = None) -> str:
        """格式化翻译文本"""
        text = self.get_text(key, "", locale)
        
        if params:
            try:
                return text.format(**params)
            except KeyError as e:
                logger.error(f"格式化文本失败 {key}: {str(e)}")
                return text
        
        return text
