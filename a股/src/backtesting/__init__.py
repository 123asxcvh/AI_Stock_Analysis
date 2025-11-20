#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化回测系统 v4.1
统一的入口点和便捷函数
消除重复，整合所有模块
"""

# 使用统一导入管理器
from .facade import *  # 导入所有需要的模块和函数

# 导出所有公共接口
__all__ = [
    # 核心模块
    'BacktestConfig',
    'BacktestEngine',
    'DataManager',
    'BacktestVisualizer',
    'StrategyEvaluator',
    'ParameterOptimizer',
    'IndicatorCalculator',
    'STRATEGY_PARAM_GRIDS',
    'OPTIMIZATION_CONFIG',

    # 工具函数
    'get_data_manager',
    'get_indicator_calculator',
    'validate_performance_data',
    'format_performance_metrics',
    'calculate_strategy_rating',
    'clear_caches',

    # 公共函数
    'read_optimized_parameters',
    'generate_total_trades_csv_unified',
    'create_strategy_comparison_csv',
    'ensure_output_directory',
    'format_strategy_results_display',

    # 策略相关
    'get_available_strategies',
    'get_strategy_categories',
    'create_strategy_by_name',
    'run_backtest',
    'compare_strategies',
    'optimize_strategy',

    # 统一策略
    'UNIFIED_STRATEGIES',
    'create_unified_strategy',
    'get_all_unified_strategies',
    'get_unified_strategy_info',
    'create_dual_ma_strategy',
    'create_macd_strategy',
    'create_rsi_strategy',
    'create_kdj_strategy',
    'create_bollinger_strategy',
    'create_volume_breakout_strategy',

    # 原始策略（兼容性）
    'BaseStrategy',
    'StrategyRegistry',
    'strategy_registry',
    'BollingerSqueezeStrategy',
    'MACD_KDJ_Strategy',
    'RSI_DivergenceStrategy',
    'CombinedStrategy',
]