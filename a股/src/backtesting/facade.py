#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一导入管理器
提供干净的导入接口，避免重复导入和路径问题
作者：AI Assistant
创建时间：2025年11月
"""

# 核心模块导入
from .config import BacktestConfig, STRATEGY_PARAM_GRIDS, OPTIMIZATION_CONFIG
from .engine import BacktestEngine
from .data_manager import DataManager
from .visualizer import BacktestVisualizer
from .evaluator import StrategyEvaluator
from .optimizer import ParameterOptimizer
from .indicators import IndicatorCalculator, indicator_calculator

# 统一工具模块导入
from .tools import (
    get_data_manager,
    clear_caches,
    read_optimized_parameters,
    generate_total_trades_csv_unified,
    create_strategy_comparison_csv,
    ensure_output_directory,
    format_strategy_results_display,
    validate_performance_data,
    format_performance_metrics,
    calculate_strategy_rating,
    parse_param_string,
    normalize_params,
    apply_strategy_params,
    load_stock_data_with_validation,
    extract_date_series,
    format_params_for_storage,
    validate_symbol_list,
    parse_strategy_list,
)

# 策略导入
from .strategies import (
    BaseStrategy,
    StrategyRegistry,
    strategy_registry,
    # 基础策略
    DualMAStrategy,
    MACDStrategy,
    RSIStrategy,
    KDJStrategy,
    # 进阶策略
    BollingerStrategy,
    VolumeBreakoutStrategy,
    # 修正后的复合策略
    BollingerRSIReversalStrategy,
)


def get_available_strategies():
    """
    获取所有可用策略名称

    Returns:
        策略名称列表
    """
    return list(strategy_registry._strategies.keys())


def create_strategy_by_name(strategy_name: str, params: dict = None):
    """
    根据名称创建策略实例

    Args:
        strategy_name: 策略名称
        params: 策略参数

    Returns:
        策略实例
    """
    # 获取策略实例模板（已经通过Registry.get()创建新实例）
    strategy_template = strategy_registry.get(strategy_name)
    if not strategy_template:
        raise ValueError(f"未知策略: {strategy_name}. 可用策略: {get_available_strategies()}")

    # 安全地创建策略实例，传入参数
    try:
        # 直接通过构造函数创建新实例
        strategy = strategy_template.__class__(name=strategy_name, params=params or {})
    except TypeError:
        # 如果构造函数不支持参数，则创建实例后设置参数
        strategy = strategy_template.__class__()
        strategy.name = strategy_name
        if params:
            if hasattr(strategy, 'set_params'):
                strategy.set_params(params)
            else:
                # 兼容性处理：直接设置params属性
                strategy.params.update(params)
                for key, value in params.items():
                    object.__setattr__(strategy, key, value)

    return strategy


def get_indicator_calculator():
    """
    获取指标计算器实例

    Returns:
        IndicatorCalculator实例
    """
    return indicator_calculator


def run_backtest(symbol: str, strategy_name: str, config=None):
    """
    运行单个策略回测（便捷函数）

    Args:
        symbol: 股票代码
        strategy_name: 策略名称
        config: 回测配置

    Returns:
        回测结果
    """
    engine = BacktestEngine(config or BacktestConfig())

    # 获取股票数据（不重新计算技术指标，避免覆盖已有数据）
    data_manager = get_data_manager()
    data = data_manager.load_stock_data(symbol, required_indicators=[])

    if data is None or data.empty:
        raise ValueError(f"无法加载股票 {symbol} 的数据")

    # 创建策略
    strategy = create_strategy_by_name(strategy_name)

    # 运行回测
    return engine.run(data, strategy)


def compare_strategies(symbol: str, strategy_names: list, config=None, save_results: bool = True):
    """
    比较多个策略表现（便捷函数）

    Args:
        symbol: 股票代码
        strategy_names: 策略名称列表
        config: 回测配置
        save_results: 是否保存结果

    Returns:
        策略比较结果
    """
    evaluator = StrategyEvaluator(config or BacktestConfig())
    return evaluator.compare_strategies(symbol, strategy_names, save_results=save_results)


def optimize_strategy(symbol: str, strategy_name: str, max_evaluations: int = 100, method: str = "bayesian", objective: str = "sharpe_ratio"):
    """
    优化策略参数（便捷函数）

    Args:
        symbol: 股票代码
        strategy_name: 策略名称
        max_evaluations: 最大评估次数
        method: 优化方法
        objective: 优化目标

    Returns:
        优化结果
    """
    optimizer = ParameterOptimizer()
    return optimizer.optimize(symbol, strategy_name, method=method, max_evaluations=max_evaluations, objective=objective)


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

    # 工具模块
    'get_data_manager',
    'get_indicator_calculator',
    'clear_caches',
    'read_optimized_parameters',
    'generate_total_trades_csv_unified',
    'create_strategy_comparison_csv',
    'ensure_output_directory',
    'format_strategy_results_display',
    'validate_performance_data',
    'format_performance_metrics',
    'calculate_strategy_rating',
    'parse_param_string',
    'normalize_params',
    'apply_strategy_params',
    'load_stock_data_with_validation',
    'extract_date_series',
    'format_params_for_storage',
    'validate_symbol_list',
    'parse_strategy_list',

    # 策略
    'BaseStrategy',
    'StrategyRegistry',
    'strategy_registry',
    'get_available_strategies',
    'create_strategy_by_name',
    'run_backtest',
    'compare_strategies',
    'optimize_strategy',

    # 具体策略类
    'DualMAStrategy',
    'MACDStrategy',
    'RSIStrategy',
    'KDJStrategy',
    'BollingerStrategy',
    'VolumeBreakoutStrategy',
]