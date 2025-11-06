"""
Backtesting Module
回测模块 - 简化的策略回测框架 v3.0

统一的回测解决方案，整合引擎、策略、指标和测试功能

使用示例:
    from src.backtesting import BacktestEngine, BacktestConfig, strategy_registry, indicator_calculator

    # 加载数据
    from config import config
    import pandas as pd
    data_file = config.get_stock_file_path("000001", "historical_quotes", cleaned=True)
    data = pd.read_csv(data_file)
    data = indicator_calculator.calculate_all(data)

    # 获取策略
    strategy = strategy_registry.get("MACD策略")

    # 运行回测
    config = BacktestConfig(initial_capital=100000)
    engine = BacktestEngine(config)
    result = engine.run(data, strategy, output_dir="./results")

    # 或使用统一测试器
    from src.backtesting import BacktestTester
    tester = BacktestTester()
    tester.test_single_strategy("000001", "MACD策略")
"""

# 核心功能
from .core import (
    BacktestEngine, BacktestConfig,
    strategy_registry,
    indicator_calculator,
    BacktestTester,
    BacktestPlotter
)

# 便捷函数
from .core.indicators import calculate_all_indicators, validate_indicators_data

__version__ = "3.0.0"
__author__ = "AI Assistant"

__all__ = [
    # 核心组件
    "BacktestEngine",
    "BacktestConfig",
    "BacktestTester",
    "BacktestPlotter",

    # 策略和指标
    "strategy_registry",
    "indicator_calculator",

    # 便捷函数
    "calculate_all_indicators",
    "validate_indicators_data"
]
