#!/usr/bin/env python3

"""
统一策略管理器
包含所有内置策略的定义和管理
"""

import pandas as pd
import numpy as np
from typing import Tuple, Dict, Any, List
from abc import ABC, abstractmethod


class Strategy(ABC):
    """统一策略基类"""

    def __init__(self, name: str, **params):
        self.name = name
        self.params = params

    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> Tuple[pd.Series, pd.Series]:
        """生成交易信号"""
        pass

    def validate_data(self, data: pd.DataFrame) -> bool:
        """验证数据是否满足策略要求"""
        required_cols = ["日期", "开盘", "最高", "最低", "收盘", "成交量"]
        return all(col in data.columns for col in required_cols)

    def get_required_indicators(self) -> List[str]:
        """获取策略所需的技术指标"""
        return []

    def __str__(self):
        return f"{self.__class__.__name__}(name='{self.name}')"


class IndicatorStrategy(Strategy):
    """基于单一指标的策略模板"""

    def __init__(self, name: str, indicator: str, buy_condition=None, sell_condition=None, **params):
        super().__init__(name, **params)
        self.indicator = indicator
        self.buy_condition = buy_condition or (lambda x: x > 0)
        self.sell_condition = sell_condition or (lambda x: x < 0)

    def generate_signals(self, data: pd.DataFrame) -> Tuple[pd.Series, pd.Series]:
        if self.indicator not in data.columns:
            raise ValueError(f"数据中缺少指标: {self.indicator}")

        indicator_values = data[self.indicator]

        # 生成信号
        buy_signals = self.buy_condition(indicator_values)
        sell_signals = self.sell_condition(indicator_values)

        return buy_signals, sell_signals

    def get_required_indicators(self) -> List[str]:
        return [self.indicator]


class CrossOverStrategy(Strategy):
    """交叉策略模板"""

    def __init__(self, name: str, fast_line: str, slow_line: str, **params):
        super().__init__(name, **params)
        self.fast_line = fast_line
        self.slow_line = slow_line

    def generate_signals(self, data: pd.DataFrame) -> Tuple[pd.Series, pd.Series]:
        for line in [self.fast_line, self.slow_line]:
            if line not in data.columns:
                raise ValueError(f"数据中缺少指标: {line}")

        fast_values = data[self.fast_line]
        slow_values = data[self.slow_line]

        # 金叉买入
        buy_signals = (fast_values > slow_values) & (fast_values.shift(1) <= slow_values.shift(1))

        # 死叉卖出
        sell_signals = (fast_values < slow_values) & (fast_values.shift(1) >= slow_values.shift(1))

        return buy_signals, sell_signals

    def get_required_indicators(self) -> List[str]:
        return [self.fast_line, self.slow_line]


class CombinedStrategy(Strategy):
    """组合策略模板"""

    def __init__(self, name: str, conditions: List[Dict], **params):
        super().__init__(name, **params)
        self.conditions = conditions

    def generate_signals(self, data: pd.DataFrame) -> Tuple[pd.Series, pd.Series]:
        buy_signals = pd.Series(False, index=data.index)
        sell_signals = pd.Series(False, index=data.index)

        for condition in self.conditions:
            if condition["type"] == "buy":
                signals = self._evaluate_condition(data, condition)
                buy_signals = buy_signals | signals
            elif condition["type"] == "sell":
                signals = self._evaluate_condition(data, condition)
                sell_signals = sell_signals | signals

        return buy_signals, sell_signals

    def _evaluate_condition(self, data: pd.DataFrame, condition: Dict) -> pd.Series:
        """评估单个条件"""
        if "indicator" in condition:
            # 单指标条件
            indicator = condition["indicator"]
            operator = condition.get("operator", ">")
            value = condition["value"]

            if indicator not in data.columns:
                raise ValueError(f"数据中缺少指标: {indicator}")

            indicator_values = data[indicator]

            if operator == ">":
                return indicator_values > value
            elif operator == "<":
                return indicator_values < value
            elif operator == ">=":
                return indicator_values >= value
            elif operator == "<=":
                return indicator_values <= value
            elif operator == "==":
                return indicator_values == value
            else:
                raise ValueError(f"不支持的运算符: {operator}")

        elif "crossover" in condition:
            # 交叉条件
            fast_line = condition["crossover"]["fast"]
            slow_line = condition["crossover"]["slow"]

            if fast_line not in data.columns or slow_line not in data.columns:
                raise ValueError(f"数据中缺少交叉指标: {fast_line}, {slow_line}")

            fast_values = data[fast_line]
            slow_values = data[slow_line]

            if condition.get("direction", "golden") == "golden":
                # 金叉
                return (fast_values > slow_values) & (fast_values.shift(1) <= slow_values.shift(1))
            else:
                # 死叉
                return (fast_values < slow_values) & (fast_values.shift(1) >= slow_values.shift(1))

        else:
            raise ValueError(f"不支持的条件类型: {condition}")

    def get_required_indicators(self) -> List[str]:
        indicators = []
        for condition in self.conditions:
            if "indicator" in condition:
                indicators.append(condition["indicator"])
            elif "crossover" in condition:
                indicators.extend([condition["crossover"]["fast"], condition["crossover"]["slow"]])
        return list(set(indicators))


# ==================== 内置策略定义 ====================

class MACDStrategy(IndicatorStrategy):
    """MACD策略"""

    def __init__(self):
        super().__init__(
            name="MACD策略",
            indicator="MACD_DIF",
            buy_condition=lambda x: (x > 0) & (x.shift(1) <= 0),  # 上穿0轴
            sell_condition=lambda x: (x < 0) & (x.shift(1) >= 0)  # 下穿0轴
        )


class MACDCrossStrategy(CrossOverStrategy):
    """MACD金叉死叉策略"""

    def __init__(self):
        super().__init__(
            name="MACD金叉死叉策略",
            fast_line="MACD_DIF",
            slow_line="MACD_DEA"
        )


class KDJStrategy(IndicatorStrategy):
    """KDJ策略"""

    def __init__(self, buy_threshold=20, sell_threshold=80):
        super().__init__(
            name="KDJ策略",
            indicator="DAILY_KDJ_J",
            buy_condition=lambda x: x < buy_threshold,
            sell_condition=lambda x: x > sell_threshold
        )
        self.buy_threshold = buy_threshold
        self.sell_threshold = sell_threshold


class WeeklyKDJStrategy(IndicatorStrategy):
    """周KDJ策略"""

    def __init__(self, buy_threshold=20, sell_threshold=80):
        super().__init__(
            name="周KDJ策略",
            indicator="WEEKLY_KDJ_J",
            buy_condition=lambda x: x < buy_threshold,
            sell_condition=lambda x: x > sell_threshold
        )
        self.buy_threshold = buy_threshold
        self.sell_threshold = sell_threshold


class RSIStrategy(IndicatorStrategy):
    """RSI策略"""

    def __init__(self, buy_threshold=30, sell_threshold=70):
        super().__init__(
            name="RSI策略",
            indicator="RSI",
            buy_condition=lambda x: x < buy_threshold,
            sell_condition=lambda x: x > sell_threshold
        )
        self.buy_threshold = buy_threshold
        self.sell_threshold = sell_threshold


class BBIStrategy(Strategy):
    """BBI策略"""

    def __init__(self):
        super().__init__(name="BBI策略")

    def generate_signals(self, data: pd.DataFrame) -> Tuple[pd.Series, pd.Series]:
        price = data["收盘"]
        bbi = data["BBI"]

        # 价格上穿BBI买入
        buy_signals = (price > bbi) & (price.shift(1) <= bbi.shift(1))

        # 价格下穿BBI卖出
        sell_signals = (price < bbi) & (price.shift(1) >= bbi.shift(1))

        return buy_signals, sell_signals

    def get_required_indicators(self) -> List[str]:
        return ["BBI"]


class BollingerStrategy(Strategy):
    """布林带策略"""

    def __init__(self):
        super().__init__(name="布林带策略")

    def generate_signals(self, data: pd.DataFrame) -> Tuple[pd.Series, pd.Series]:
        price = data["收盘"]
        upper = data["BOLL_UPPER"]
        lower = data["BOLL_LOWER"]

        # 价格突破下轨买入
        buy_signals = (price > lower) & (price.shift(1) <= lower.shift(1))

        # 价格突破上轨卖出
        sell_signals = (price < upper) & (price.shift(1) >= upper.shift(1))

        return buy_signals, sell_signals

    def get_required_indicators(self) -> List[str]:
        return ["BOLL_UPPER", "BOLL_LOWER"]


class WeeklyKDJBBI(CombinedStrategy):
    """周KDJ + BBI组合策略"""

    def __init__(self):
        conditions = [
            {
                "type": "buy",
                "indicator": "WEEKLY_KDJ_J",
                "operator": "<",
                "value": 20
            },
            {
                "type": "buy",
                "crossover": {
                    "fast": "收盘",
                    "slow": "BBI",
                    "direction": "golden"
                }
            },
            {
                "type": "sell",
                "indicator": "WEEKLY_KDJ_J",
                "operator": ">",
                "value": 80
            }
        ]
        super().__init__("周KDJ+BBI策略", conditions)


class DailyKDJMACD(CombinedStrategy):
    """日KDJ + MACD组合策略"""

    def __init__(self):
        conditions = [
            {
                "type": "buy",
                "indicator": "DAILY_KDJ_J",
                "operator": "<",
                "value": 20
            },
            {
                "type": "buy",
                "crossover": {
                    "fast": "MACD_DIF",
                    "slow": "MACD_DEA",
                    "direction": "golden"
                }
            },
            {
                "type": "sell",
                "indicator": "DAILY_KDJ_J",
                "operator": ">",
                "value": 80
            }
        ]
        super().__init__("日KDJ+MACD策略", conditions)


class VolumeBreakout(Strategy):
    """成交量突破策略"""

    def __init__(self, volume_multiplier=1.5):
        super().__init__(name="成交量突破策略")
        self.volume_multiplier = volume_multiplier

    def generate_signals(self, data: pd.DataFrame) -> Tuple[pd.Series, pd.Series]:
        price = data["收盘"]
        volume = data["成交量"]
        volume_ma = data["VOLUME_MA5"]

        # 成交量突破 + 价格上涨
        volume_breakout = volume > volume_ma * self.volume_multiplier
        price_up = price > price.shift(1)

        buy_signals = volume_breakout & price_up

        # 简单的卖出条件：价格跌破5日均线
        ma5 = price.rolling(window=5).mean()
        sell_signals = price < ma5

        return buy_signals, sell_signals

    def get_required_indicators(self) -> List[str]:
        return ["VOLUME_MA5"]


# ==================== 策略注册器 ====================

class StrategyRegistry:
    """策略注册器"""

    def __init__(self):
        self._strategies = {}

    def register(self, strategy_class):
        """注册策略"""
        strategy_instance = strategy_class()
        self._strategies[strategy_instance.name] = strategy_instance

    def get(self, name: str) -> Strategy:
        """获取策略实例"""
        return self._strategies.get(name)

    def list_all(self) -> List[str]:
        """列出所有策略"""
        return list(self._strategies.keys())

    def create_summary(self) -> str:
        """创建策略汇总"""
        lines = ["可用策略:", "=" * 50]
        for name, strategy in self._strategies.items():
            required_indicators = strategy.get_required_indicators()
            lines.append(f"• {name}")
            lines.append(f"  所需指标: {', '.join(required_indicators) if required_indicators else '无'}")
            lines.append("")
        return "\n".join(lines)


# 全局策略注册器
strategy_registry = StrategyRegistry()

# 注册所有内置策略
_builtin_strategies = [
    MACDStrategy,
    MACDCrossStrategy,
    KDJStrategy,
    WeeklyKDJStrategy,
    RSIStrategy,
    BBIStrategy,
    BollingerStrategy,
    WeeklyKDJBBI,
    DailyKDJMACD,
    VolumeBreakout
]

for strategy_class in _builtin_strategies:
    strategy_registry.register(strategy_class)