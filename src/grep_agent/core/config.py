"""
配置管理模块
"""
import os
from pathlib import Path
from typing import Optional
import yaml
from dotenv import load_dotenv

from .models import (
    AppConfig,
    SystemConfig,
    LLMConfig,
    APIConfig,
    StrategyConfig,
    GrepOptions,
    StrategyMode,
    StrategyType,
)
from .exceptions import ConfigurationError


class ConfigManager:
    """配置管理器"""
    
    _instance: Optional['ConfigManager'] = None
    _config: Optional[AppConfig] = None
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def load_config(self, config_path: Optional[str] = None) -> AppConfig:
        """
        加载配置文件
        
        Args:
            config_path: 配置文件路径，默认为./config/config.yaml
            
        Returns:
            AppConfig: 应用配置对象
            
        Raises:
            ConfigurationError: 配置加载或验证失败
        """
        # 加载环境变量
        load_dotenv()
        
        # 确定配置文件路径
        if config_path is None:
            config_path = os.getenv("CONFIG_PATH", "./config/config.yaml")
        
        config_file = Path(config_path)
        
        if not config_file.exists():
            raise ConfigurationError(f"配置文件不存在: {config_path}")
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
        except Exception as e:
            raise ConfigurationError(f"配置文件解析失败: {e}")
        
        try:
            # 解析系统配置
            system_config = SystemConfig(**config_data.get('system', {}))
            
            # 解析LLM配置
            llm_data = config_data.get('llm', {})
            # API密钥优先从环境变量获取
            llm_data['api_key'] = os.getenv('OPENAI_API_KEY', llm_data.get('api_key'))
            # API端点也可以从环境变量获取
            llm_data['api_endpoint'] = os.getenv('OPENAI_API_ENDPOINT', llm_data.get('api_endpoint'))
            llm_config = LLMConfig(**llm_data)
            
            # 解析API配置
            api_config = APIConfig(**config_data.get('api', {}))
            
            # 解析策略配置
            strategy_data = config_data.get('strategy', {})
            
            # 转换策略类型
            predefined_sequence = [
                StrategyType(s) for s in strategy_data.get('predefined_sequence', [])
            ]
            
            # 解析grep基础选项
            grep_base_data = strategy_data.get('grep_base_options', {})
            grep_base_options = GrepOptions(**grep_base_data)
            
            strategy_config = StrategyConfig(
                strategy_name="default",
                strategy_mode=StrategyMode(strategy_data.get('strategy_mode', 'hybrid')),
                predefined_sequence=predefined_sequence,
                hybrid_rules=strategy_data.get('hybrid_rules', {}),
                grep_base_options=grep_base_options,
                file_include_patterns=strategy_data.get('file_include_patterns', []),
                file_exclude_patterns=strategy_data.get('file_exclude_patterns', []),
                max_result_size=strategy_data.get('max_result_size', 10485760),
            )
            
            # 创建总配置
            self._config = AppConfig(
                system=system_config,
                llm=llm_config,
                api=api_config,
                strategy=strategy_config,
            )
            
            return self._config
            
        except Exception as e:
            raise ConfigurationError(f"配置验证失败: {e}")
    
    def get_config(self) -> AppConfig:
        """
        获取配置对象
        
        Returns:
            AppConfig: 应用配置对象
            
        Raises:
            ConfigurationError: 配置未加载
        """
        if self._config is None:
            raise ConfigurationError("配置未加载，请先调用load_config()")
        return self._config
    
    def reload_config(self, config_path: Optional[str] = None) -> AppConfig:
        """
        重新加载配置
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            AppConfig: 应用配置对象
        """
        return self.load_config(config_path)


# 全局配置管理器实例
config_manager = ConfigManager()
