#!/usr/bin/env python3

"""
统一技术指标计算器
提供所有常用技术指标的标准化计算
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List


class IndicatorCalculator:
    """统一的技术指标计算器"""

    def __init__(self):
        self.cache = {}

    def calculate_all(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算所有常用技术指标

        Args:
            df: OHLCV数据

        Returns:
            包含所有指标的DataFrame
        """
        result = df.copy()

        # MACD指标
        macd_data = self.calculate_macd(result["收盘"])
        for key, values in macd_data.items():
            result[key] = values

        # KDJ指标（日线和周线）
        kdj_daily = self.calculate_kdj(result["最高"], result["最低"], result["收盘"])
        for key, values in kdj_daily.items():
            result[f"DAILY_{key}"] = values

        # 计算周线KDJ（如果数据有日期列）
        weekly_kdj = self.calculate_weekly_kdj(result)
        for key, values in weekly_kdj.items():
            result[f"WEEKLY_{key}"] = values

        # RSI指标
        result["RSI"] = self.calculate_rsi(result["收盘"])

        # 布林带
        boll_data = self.calculate_bollinger_bands(result["收盘"])
        for key, values in boll_data.items():
            result[key] = values

        # BBI指标
        result["BBI"] = self.calculate_bbi(result["收盘"])

        # 成交量指标
        result["VOLUME_MA5"] = self.calculate_sma(result["成交量"], 5)
        result["VOLUME_MA10"] = self.calculate_sma(result["成交量"], 10)

        # ATR指标
        result["ATR"] = self.calculate_atr(result["最高"], result["最低"], result["收盘"])

        return result

    def calculate_macd(self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, pd.Series]:
        """计算MACD指标"""
        ema_fast = self.calculate_ema(prices, fast)
        ema_slow = self.calculate_ema(prices, slow)

        dif = ema_fast - ema_slow
        dea = self.calculate_ema(dif, signal)
        macd_hist = (dif - dea) * 2

        return {
            "MACD_DIF": dif,
            "MACD_DEA": dea,
            "MACD_HIST": macd_hist
        }

    def calculate_kdj(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 9) -> Dict[str, pd.Series]:
        """计算KDJ指标"""
        lowest_low = low.rolling(window=period, min_periods=1).min()
        highest_high = high.rolling(window=period, min_periods=1).max()

        rsv = (close - lowest_low) / (highest_high - lowest_low) * 100
        rsv = rsv.fillna(50)  # 避免除零错误

        k = rsv.ewm(alpha=1/3, adjust=False).mean()
        d = k.ewm(alpha=1/3, adjust=False).mean()
        j = 3 * k - 2 * d

        return {
            "KDJ_K": k,
            "KDJ_D": d,
            "KDJ_J": j
        }

    def calculate_weekly_kdj(self, df: pd.DataFrame) -> Dict[str, pd.Series]:
        """计算周线KDJ指标"""
        # 检查是否有日期列
        if '日期' not in df.columns:
            # 如果没有日期列，返回空字典
            print("⚠️ 警告: 数据中缺少日期列，跳过周KDJ计算")
            return {}

        df_weekly = df.copy()
        df_weekly['日期'] = pd.to_datetime(df_weekly['日期'])
        df_weekly.set_index('日期', inplace=True)

        # 重采样为周线数据
        weekly_data = df_weekly.resample('W').agg({
            '开盘': 'first',
            '最高': 'max',
            '最低': 'min',
            '收盘': 'last',
            '成交量': 'sum'
        }).dropna()

        # 计算周KDJ
        weekly_kdj = self.calculate_kdj(weekly_data['最高'], weekly_data['最低'], weekly_data['收盘'])
        weekly_kdj_df = pd.DataFrame(weekly_kdj, index=weekly_data.index)

        # 将周KDJ数据映射回日线
        weekly_kdj_df.reset_index(inplace=True)
        weekly_kdj_df.rename(columns={'日期': 'weekly_date'}, inplace=True)

        # 使用merge_asof将最近的周KDJ值匹配到每日数据
        df_daily = df.copy()
        df_daily['weekly_date'] = pd.to_datetime(df_daily['日期'])
        merged = pd.merge_asof(df_daily.sort_values('weekly_date'),
                             weekly_kdj_df.sort_values('weekly_date'),
                             left_on='weekly_date', right_on='weekly_date',
                             direction='backward')

        return {
            "KDJ_K": merged["KDJ_K"],
            "KDJ_D": merged["KDJ_D"],
            "KDJ_J": merged["KDJ_J"]
        }

    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """计算RSI指标"""
        delta = prices.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        avg_gain = gain.rolling(window=period, min_periods=1).mean()
        avg_loss = loss.rolling(window=period, min_periods=1).mean()

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return rsi.fillna(50)

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
        return data.rolling(window=period, min_periods=1).mean()

    def calculate_ema(self, data: pd.Series, period: int) -> pd.Series:
        """计算指数移动平均线"""
        return data.ewm(span=period, adjust=False).mean()

    def calculate_atr(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """计算ATR平均真实波幅"""
        high_low = high - low
        high_close = np.abs(high - close.shift())
        low_close = np.abs(low - close.shift())

        true_range = np.maximum(high_low, np.maximum(high_close, low_close))
        atr = true_range.rolling(window=period, min_periods=1).mean()

        return atr

    def validate_indicators(self, df: pd.DataFrame, required_indicators: List[str]) -> bool:
        """验证指标数据是否完整"""
        missing_indicators = [ind for ind in required_indicators if ind not in df.columns]

        if missing_indicators:
            print(f"缺少指标: {missing_indicators}")
            return False

        # 检查空值
        for ind in required_indicators:
            null_ratio = df[ind].isnull().sum() / len(df)
            if null_ratio > 0.1:
                print(f"指标 {ind} 空值过多: {null_ratio:.2%}")
                return False

        return True


# 全局指标计算器实例
indicator_calculator = IndicatorCalculator()


# 便捷函数
def calculate_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """便捷函数：计算所有技术指标"""
    return indicator_calculator.calculate_all(df)


def validate_indicators_data(df: pd.DataFrame, required_indicators: List[str]) -> bool:
    """便捷函数：验证指标数据"""
    return indicator_calculator.validate_indicators(df, required_indicators)