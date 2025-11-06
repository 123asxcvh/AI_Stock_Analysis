"""
配置模块 - 极简版
统一管理所有配置参数
"""

from .config import (
    config, Config,
    get_web_port, get_api_key, get_target_stocks,
    get_project_root, get_data_dir,
    strategy_configs, StrategyConfigs,
    CacheManager, cache_manager,
    AsyncAIAnalyzerBase, DataProcessor,
    MODEL_NAME, MAX_CONCURRENCY,
    GEMINI_API_KEYS, APIKeyRotator
)


# 导出
__all__ = [
    'config', 'Config',
    'get_web_port', 'get_api_key', 'get_target_stocks',
    'get_project_root', 'get_data_dir',
    'strategy_configs', 'StrategyConfigs',
    'CacheManager', 'cache_manager',
    'AsyncAIAnalyzerBase', 'DataProcessor',
    'MODEL_NAME', 'MAX_CONCURRENCY',
    'GEMINI_API_KEYS', 'APIKeyRotator'
]