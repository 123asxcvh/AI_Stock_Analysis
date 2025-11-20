#!/usr/bin/env python3
from __future__ import annotations

"""
港股 个股级 TA-Lib 技术指标分析器（精简核心指标）
输入：h股/data/stocks/{symbol}/historical_quotes.csv
输出：h股/data/stocks/{symbol}/historical_quotes_talib.csv（附加指标列，已去NaN）
"""

import os
import logging
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

try:
    import talib  # type: ignore

    TALIB_AVAILABLE = True
except Exception:
    TALIB_AVAILABLE = False


class HKCoreTALibAnalyzer:
    def __init__(self, data_root_dir: str) -> None:
        self.data_root_dir = data_root_dir
        if not TALIB_AVAILABLE:
            raise ImportError("TA-Lib 未安装，无法进行技术指标计算")

    def _load_stock_df(self, symbol: str) -> Optional[pd.DataFrame]:
        path = os.path.join(self.data_root_dir, "stocks", symbol, "historical_quotes.csv")
        if not os.path.exists(path):
            logger.error(f"未找到原始行情: {path}")
            return None
        df = pd.read_csv(path)
        required = ["日期", "开盘", "最高", "最低", "收盘", "成交量"]
        missing = [c for c in required if c not in df.columns]
        if missing:
            logger.error(f"缺少列: {missing}")
            return None
        df["日期"] = pd.to_datetime(df["日期"], errors="coerce")
        for c in ["开盘", "最高", "最低", "收盘", "成交量"]:
            df[c] = pd.to_numeric(df[c], errors="coerce")
        df = (
            df.dropna(subset=["日期"]).sort_values("日期").drop_duplicates("日期").reset_index(drop=True)
        )
        return df

    def _calc_trend(self, df: pd.DataFrame) -> pd.DataFrame:
        close = df["收盘"].astype(np.float64).values
        df["trend_sma_20"] = talib.SMA(close, timeperiod=20)
        df["trend_sma_50"] = talib.SMA(close, timeperiod=50)
        df["trend_ema_12"] = talib.EMA(close, timeperiod=12)
        df["trend_ema_26"] = talib.EMA(close, timeperiod=26)
        macd, macd_signal, macd_hist = talib.MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)
        df["trend_macd"] = macd
        df["trend_macd_signal"] = macd_signal
        df["trend_macd_hist"] = macd_hist
        return df

    def _calc_momentum(self, df: pd.DataFrame) -> pd.DataFrame:
        close = df["收盘"].astype(np.float64).values
        high = df["最高"].astype(np.float64).values
        low = df["最低"].astype(np.float64).values
        df["momentum_rsi_14"] = talib.RSI(close, timeperiod=14)
        k, d = talib.STOCH(high, low, close, fastk_period=14, slowk_period=3, slowd_period=3)
        df["momentum_stoch_k"] = k
        df["momentum_stoch_d"] = d
        df["momentum_stoch_j"] = 3 * k - 2 * d
        return df

    def _calc_volatility(self, df: pd.DataFrame) -> pd.DataFrame:
        close = df["收盘"].astype(np.float64).values
        high = df["最高"].astype(np.float64).values
        low = df["最低"].astype(np.float64).values
        up, mid, lowb = talib.BBANDS(close, timeperiod=20, nbdevup=2, nbdevdn=2, matype=0)
        df["volatility_bbands_upper"] = up
        df["volatility_bbands_middle"] = mid
        df["volatility_bbands_lower"] = lowb
        df["volatility_atr_14"] = talib.ATR(high, low, close, timeperiod=14)
        return df

    def _calc_volume(self, df: pd.DataFrame) -> pd.DataFrame:
        close = df["收盘"].astype(np.float64).values
        high = df["最高"].astype(np.float64).values
        low = df["最低"].astype(np.float64).values
        vol = df["成交量"].astype(np.float64).values
        df["volume_obv"] = talib.OBV(close, vol)
        df["volume_ad"] = talib.AD(high, low, close, vol)
        df["volume_vwap"] = (df["成交量"] * (df["最高"] + df["最低"] + df["收盘"]) / 3).cumsum() / df["成交量"].cumsum()
        return df

    def analyze_stock(self, symbol: str) -> Dict[str, Any]:
        df = self._load_stock_df(symbol)
        if df is None or df.empty:
            return {"status": "Fail", "message": "原始数据缺失或为空"}
        n0 = len(df)
        df = self._calc_trend(df)
        df = self._calc_momentum(df)
        df = self._calc_volatility(df)
        df = self._calc_volume(df)
        df = df.dropna()
        out_dir = os.path.join(self.data_root_dir, "stocks", symbol)
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, "historical_quotes_talib.csv")
        df.to_csv(out_path, index=False, encoding="utf-8-sig")
        ind_cols = [c for c in df.columns if c.startswith(("trend_", "momentum_", "volatility_", "volume_"))]
        return {
            "status": "Success",
            "rows_in": n0,
            "rows_out": len(df),
            "indicators": ind_cols,
            "output_path": out_path,
        }



