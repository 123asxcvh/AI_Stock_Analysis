#!/usr/bin/env python3

"""
统一技术指标计算器
提供所有常用技术指标的标准化计算 - NumPy优化版本
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from numba import jit


class IndicatorCalculator:
    """统一的技术指标计算器 - NumPy优化版本"""

    def __init__(self):
        """初始化计算器"""
        pass

    @staticmethod
    def _validate_series(series: pd.Series) -> np.ndarray:
        """验证并转换系列为NumPy数组"""
        if len(series) == 0:
            raise ValueError("时间序列不能为空")
        return series.values

    def calculate_macd(self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, pd.Series]:
        """计算MACD指标 - NumPy优化版本"""
        values = self._validate_series(prices)

        # 使用NumPy计算EMA - 更高效的实现
        alpha_fast = 2.0 / (fast + 1)
        alpha_slow = 2.0 / (slow + 1)
        alpha_signal = 2.0 / (signal + 1)

        ema_fast = self._ema_numpy(values, alpha_fast)
        ema_slow = self._ema_numpy(values, alpha_slow)

        dif = ema_fast - ema_slow
        dea = self._ema_numpy(dif, alpha_signal)
        macd_hist = (dif - dea) * 2

        return {
            "MACD_DIF": pd.Series(dif, index=prices.index),
            "MACD_DEA": pd.Series(dea, index=prices.index),
            "MACD_HIST": pd.Series(macd_hist, index=prices.index)
        }

    @staticmethod
    def _ema_numpy(data: np.ndarray, alpha: float) -> np.ndarray:
        """使用NumPy计算EMA - 向量化实现"""
        ema = np.empty_like(data)
        ema[0] = data[0]

        for i in range(1, len(data)):
            ema[i] = alpha * data[i] + (1 - alpha) * ema[i-1]

        return ema

    def calculate_kdj(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 9) -> Dict[str, pd.Series]:
        """计算KDJ指标"""
        lowest_low = low.rolling(window=period).min()
        highest_high = high.rolling(window=period).max()
        rsv = (close - lowest_low) / (highest_high - lowest_low) * 100
        rsv = rsv.ffill().fillna(50)

        # 使用标准KDJ计算公式
        k = rsv.ewm(alpha=1/3, adjust=False).mean()
        d = k.ewm(alpha=1/3, adjust=False).mean()
        j = 3 * k - 2 * d

        # 限制J值在合理范围内
        j = j.clip(lower=-50, upper=150)

        return {
            "DAILY_KDJ_K": k,
            "DAILY_KDJ_D": d,
            "DAILY_KDJ_J": j
        }

    
    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """计算RSI指标"""
        delta = prices.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()

        rs = avg_gain / avg_loss.replace(0, np.inf)
        rsi = 100 - (100 / (1 + rs))

        return rsi

    def calculate_cci(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 20) -> pd.Series:
        """计算CCI指标"""
        typical_price = (high + low + close) / 3
        sma_tp = typical_price.rolling(window=period).mean()

        # 计算平均绝对偏差 (MAD)
        mad = typical_price.rolling(window=period).apply(lambda x: abs(x - x.mean()).mean())

        # CCI = (TP - SMA(TP)) / (0.015 * MAD)
        cci = (typical_price - sma_tp) / (0.015 * mad)

        return cci

    def calculate_bollinger_bands(self, prices: pd.Series, period: int = 20, std_dev: float = 2) -> Dict[str, pd.Series]:
        """计算布林带"""
        sma = self.calculate_sma(prices, period)
        std = prices.rolling(window=period, min_periods=1).std()

        upper = sma + (std * std_dev)
        lower = sma - (std * std_dev)

        return {
            "BOLL_UPPER": upper,
            "BOLL_MIDDLE": sma,
            "BOLL_LOWER": lower
        }

    def calculate_bbi(self, prices: pd.Series) -> pd.Series:
        """计算BBI多空指标"""
        ma3 = self.calculate_sma(prices, 3)
        ma6 = self.calculate_sma(prices, 6)
        ma12 = self.calculate_sma(prices, 12)
        ma24 = self.calculate_sma(prices, 24)

        bbi = (ma3 + ma6 + ma12 + ma24) / 4
        return bbi

    def calculate_sma(self, data: pd.Series, period: int) -> pd.Series:
        """计算简单移动平均线"""
        return data.rolling(window=period).mean()

    def calculate_ema(self, data: pd.Series, period: int) -> pd.Series:
        """计算指数移动平均线"""
        return data.ewm(span=period, adjust=False).mean()

    def calculate_atr(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """计算ATR平均真实波幅"""
        high_low = high - low
        high_close = np.abs(high - close.shift())
        low_close = np.abs(low - close.shift())

        true_range = np.maximum(high_low, np.maximum(high_close, low_close))
        return true_range.rolling(window=period).mean()

    def validate_indicators(self, df: pd.DataFrame, required_indicators: List[str]) -> bool:
        """验证指标数据是否完整"""
        missing_indicators = [ind for ind in required_indicators if ind not in df.columns]
        if missing_indicators:
            return False

        # 检查空值比例
        for ind in required_indicators:
            if df[ind].isnull().sum() / len(df) > 0.1:
                return False

        return True

    def calculate_williams_r(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """计算威廉指标 (Williams %R)"""
        highest_high = high.rolling(window=period).max()
        lowest_low = low.rolling(window=period).min()

        # 威廉指标公式: (最高价 - 收盘价) / (最高价 - 最低价) * -100
        wr = (highest_high - close) / (highest_high - lowest_low) * -100
        return wr

    def calculate_mtm(self, close: pd.Series, period: int = 12) -> pd.Series:
        """计算动量指标 (Momentum)"""
        # 动量指标公式: 当前价 - N日前收盘价
        mtm = close - close.shift(period)
        return mtm

    def calculate_obv(self, close: pd.Series, volume: pd.Series) -> pd.Series:
        """计算能量潮指标 (On-Balance Volume)"""
        # OBV计算基于价格变化方向
        price_change = close.diff()

        # 当价格上涨时，OBV增加成交量；当价格下跌时，OBV减少成交量
        obv = (price_change > 0).astype(int) * volume - (price_change < 0).astype(int) * volume
        return obv.cumsum()


# 全局指标计算器实例
indicator_calculator = IndicatorCalculator()