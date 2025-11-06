"""
Core Module
核心回测模块 - 整合引擎、策略、指标和测试功能
"""

from .engine import BacktestEngine, BacktestConfig, run_backtest_single
from .strategies import (
    Strategy, IndicatorStrategy, CrossOverStrategy, CombinedStrategy,
    strategy_registry,
    MACDStrategy, MACDCrossStrategy, KDJStrategy, WeeklyKDJStrategy,
    RSIStrategy, BBIStrategy, BollingerStrategy, WeeklyKDJBBI,
    DailyKDJMACD, VolumeBreakout
)
from .indicators import (
    IndicatorCalculator, indicator_calculator,
    calculate_all_indicators, validate_indicators_data
)
from .plotter import BacktestPlotter, plotter, plot_backtest_result, plot_strategy_comparison
from .tester import BacktestTester

__all__ = [
    # 核心引擎
    "BacktestEngine",
    "BacktestConfig",
    "run_backtest_single",

    # 策略系统
    "Strategy",
    "IndicatorStrategy",
    "CrossOverStrategy",
    "CombinedStrategy",
    "strategy_registry",

    # 内置策略
    "MACDStrategy",
    "MACDCrossStrategy",
    "KDJStrategy",
    "WeeklyKDJStrategy",
    "RSIStrategy",
    "BBIStrategy",
    "BollingerStrategy",
    "WeeklyKDJBBI",
    "DailyKDJMACD",
    "VolumeBreakout",

    # 技术指标
    "IndicatorCalculator",
    "indicator_calculator",
    "calculate_all_indicators",
    "validate_indicators_data",

    # 可视化工具
    "BacktestPlotter",
    "plotter",
    "plot_backtest_result",
    "plot_strategy_comparison",

    # 测试工具
    "BacktestTester"
]