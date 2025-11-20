from __future__ import annotations

import asyncio
import logging
import os
import random
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, Iterable, List, Optional

import akshare as ak
import pandas as pd

from src.utils.common.hk_normalization import normalize_hk_ohlcv


logger = logging.getLogger(__name__)


class HKDataCollector:
    """港股数据采集器（支持异步并发调度）

    - 将 AkShare 同步接口包装为在线程池中执行，配合 asyncio 实现并发
    - 输出 DataFrame 统一标准列，便于后续清洗与可视化
    """

    def __init__(self, data_root_dir: str = "data") -> None:
        self.data_root_dir = data_root_dir
        self._executor = ThreadPoolExecutor(max_workers=os.cpu_count() or 4)

    # ---------------------- A股式 per-symbol 目录 ----------------------
    def get_stock_dir(self, symbol: str) -> str:
        stock_dir = os.path.join(self.data_root_dir, "stocks", symbol)
        os.makedirs(stock_dir, exist_ok=True)
        return stock_dir

    # ---------------------- 内部通用 ----------------------
    async def _run_sync(self, fn, *args, **kwargs):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self._executor, lambda: fn(*args, **kwargs))

    async def _retry_async(self, coro_fn, max_retries: int = 3, base: float = 0.8):
        last_exc: Optional[Exception] = None
        for i in range(max_retries):
            try:
                return await coro_fn()
            except Exception as e:  # noqa: BLE001
                last_exc = e
                wait = base * (2**i) + random.uniform(0, 0.3)
                logger.warning(f"HK fetch failed: {e}; retry in {wait:.2f}s")
                await asyncio.sleep(wait)
        if last_exc:
            raise last_exc

    # ---------------------- 个股与指数抓取 ----------------------
    async def fetch_equity_daily(self, symbol: str, start_date: str = "20150101", end_date: str = "22220101") -> pd.DataFrame:
        """个股日线（不复权）"""

        async def _call():
            df = await self._run_sync(
                ak.stock_hk_hist, symbol, "daily", start_date, end_date, ""
            )
            return normalize_hk_ohlcv(df)

        return await self._retry_async(_call)

    async def fetch_index_daily(self, symbol: str) -> pd.DataFrame:
        """指数日线（新浪）"""

        async def _call():
            df = await self._run_sync(ak.stock_hk_index_daily_sina, symbol)
            return normalize_hk_ohlcv(df)

        return await self._retry_async(_call)

    async def fetch_intraday_15m(self, symbol: str, start_dt: str | None = None, end_dt: str | None = None) -> pd.DataFrame:
        """个股15分钟分时数据（不复权，默认仅最近7个交易日）。
        - 数据源：ak.stock_hk_hist_min_em(period='15', adjust='')
        - 当未提供 start_dt/end_dt 时，将在获取后按日期过滤，仅保留最近7个交易日的数据。
        """

        async def _call():
            kwargs = {
                "symbol": symbol,
                "period": "15",
                "adjust": "",  # 不复权
            }
            if start_dt:
                kwargs["start_date"] = start_dt
            if end_dt:
                kwargs["end_date"] = end_dt
            df = await self._run_sync(ak.stock_hk_hist_min_em, **kwargs)
            df = normalize_hk_ohlcv(df)
            # 若未指定时间范围，则只保留最近7个交易日
            if start_dt is None and end_dt is None and isinstance(df, pd.DataFrame) and not df.empty:
                if "日期" in df.columns:
                    dates = pd.to_datetime(df["日期"]).dt.date
                    unique_days = pd.Series(dates.unique()).sort_values()
                    last_7_days = set(unique_days.iloc[-7:]) if len(unique_days) > 7 else set(unique_days)
                    df = df[dates.isin(last_7_days)].copy()
            return df

        return await self._retry_async(_call)

    async def fetch_daily_sina(self, symbol: str, adjust: str = "") -> pd.DataFrame:
        """个股历史行情（新浪接口）。adjust: "", "qfq", "hfq", "qfq-factor", "hfq-factor""" 
        async def _call():
            df = await self._run_sync(ak.stock_hk_daily, symbol, adjust)
            return normalize_hk_ohlcv(df)
        return await self._retry_async(_call)

    async def fetch_spot_single(self, symbol: str) -> pd.DataFrame:
        """从新浪实时接口获取全市场后按代码过滤单只。"""
        async def _call():
            df = await self._run_sync(ak.stock_hk_spot)
            if df is None or df.empty:
                return df
            # 列名参照文档：代码
            sub = df[df.get("代码").astype(str) == str(symbol)].copy()
            # 规范部分列
            if "日期时间" in sub.columns:
                sub.rename(columns={"日期时间": "日期"}, inplace=True)
            return normalize_hk_ohlcv(sub)
        return await self._retry_async(_call)

    async def fetch_company_profile_em(self, symbol: str) -> pd.DataFrame:
        async def _call():
            return await self._run_sync(ak.stock_hk_company_profile_em, symbol)
        return await self._retry_async(_call)

    async def fetch_financial_report_em(self, stock: str, table: str, indicator: str = "报告期") -> pd.DataFrame:
        """table in {资产负债表, 利润表, 现金流量表}; indicator {年度, 报告期}"""
        async def _call():
            return await self._run_sync(ak.stock_financial_hk_report_em, stock, table, indicator)
        return await self._retry_async(_call)

    async def fetch_financial_analysis_indicator_em(self, symbol: str, indicator: str = "年度") -> pd.DataFrame:
        async def _call():
            return await self._run_sync(ak.stock_financial_hk_analysis_indicator_em, symbol, indicator)
        return await self._retry_async(_call)

    async def fetch_indicator_eniu(self, symbol: str, indicator: str) -> pd.DataFrame:
        async def _call():
            return await self._run_sync(ak.stock_hk_indicator_eniu, symbol, indicator)
        return await self._retry_async(_call)

    async def fetch_profit_forecast_et(self, symbol: str, indicator: str) -> pd.DataFrame:
        """indicator in {评级总览, 去年度业绩表现, 综合盈利预测, 盈利预测概览}"""
        async def _call():
            return await self._run_sync(ak.stock_hk_profit_forecast_et, symbol, indicator)
        return await self._retry_async(_call)

    async def fetch_valuation_baidu(self, symbol: str, indicator: str, period: str = "近一年") -> pd.DataFrame:
        async def _call():
            return await self._run_sync(ak.stock_hk_valuation_baidu, symbol, indicator, period)
        return await self._retry_async(_call)

    # ---------------------- 市场/全量接口 ----------------------
    async def fetch_spot_em_all(self) -> pd.DataFrame:
        async def _call():
            return await self._run_sync(ak.stock_hk_spot_em)
        return await self._retry_async(_call)

    async def fetch_spot_sina_all(self) -> pd.DataFrame:
        """全市场实时行情（Sina 源）。"""
        async def _call():
            return await self._run_sync(ak.stock_hk_spot)
        return await self._retry_async(_call)

    async def fetch_main_board_spot_em_all(self) -> pd.DataFrame:
        async def _call():
            return await self._run_sync(ak.stock_hk_main_board_spot_em)
        return await self._retry_async(_call)

    async def fetch_ggt_components_em_all(self) -> pd.DataFrame:
        async def _call():
            return await self._run_sync(ak.stock_hk_ggt_components_em)
        return await self._retry_async(_call)

    async def fetch_index_spot_sina_all(self) -> pd.DataFrame:
        async def _call():
            return await self._run_sync(ak.stock_hk_index_spot_sina)
        return await self._retry_async(_call)

    async def fetch_index_spot_em_all(self) -> pd.DataFrame:
        async def _call():
            return await self._run_sync(ak.stock_hk_index_spot_em)
        return await self._retry_async(_call)

    async def fetch_index_daily_em(self, symbol: str) -> pd.DataFrame:
        async def _call():
            return await self._run_sync(ak.stock_hk_index_daily_em, symbol)
        return await self._retry_async(_call)

    async def fetch_famous_spot_em_all(self) -> pd.DataFrame:
        async def _call():
            return await self._run_sync(ak.stock_hk_famous_spot_em)
        return await self._retry_async(_call)

    async def fetch_hot_rank_em_all(self) -> pd.DataFrame:
        """港股热度榜（Eastmoney）"""
        async def _call():
            return await self._run_sync(ak.stock_hk_hot_rank_em)
        return await self._retry_async(_call)

    # ---------------------- 批量并发 ----------------------
    async def fetch_equities_daily_batch(self, symbols: Iterable[str], start_date: str = "20150101", end_date: str = "22220101") -> Dict[str, pd.DataFrame]:
        tasks = [self.fetch_equity_daily(s, start_date, end_date) for s in symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        out: Dict[str, pd.DataFrame] = {}
        for s, r in zip(symbols, results):
            if isinstance(r, Exception):
                logger.error(f"❌ 个股失败 {s}: {r}")
            else:
                out[s] = r
        return out

    async def fetch_indexes_daily_batch(self, index_symbols: Iterable[str]) -> Dict[str, pd.DataFrame]:
        tasks = [self.fetch_index_daily(s) for s in index_symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        out: Dict[str, pd.DataFrame] = {}
        for s, r in zip(index_symbols, results):
            if isinstance(r, Exception):
                logger.error(f"❌ 指数失败 {s}: {r}")
            else:
                out[s] = r
        return out

    async def fetch_intraday_15m_batch(self, symbols: Iterable[str], start_dt: str | None = None, end_dt: str | None = None) -> Dict[str, pd.DataFrame]:
        tasks = [self.fetch_intraday_15m(s, start_dt, end_dt) for s in symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        out: Dict[str, pd.DataFrame] = {}
        for s, r in zip(symbols, results):
            if isinstance(r, Exception):
                logger.error(f"❌ 分时失败 {s}: {r}")
            else:
                out[s] = r
        return out

    # ---------------------- 落盘 ----------------------
    def _market_path(self, name: str) -> str:
        base = os.path.join(self.data_root_dir, "market")
        os.makedirs(base, exist_ok=True)
        return os.path.join(base, f"{name}.csv")

    async def save_equity_csv(self, symbol: str, df: pd.DataFrame) -> str:
        # 统一存入 data/stocks/{symbol}/historical_quotes.csv
        return await self.save_equity_to_stocks(symbol, df)

    async def save_index_csv(self, symbol: str, df: pd.DataFrame) -> str:
        # 指数归为市场数据
        path = self._market_path(f"index_{symbol}")
        df.to_csv(path, index=False)
        return path

    async def save_intraday15m_csv(self, symbol: str, df: pd.DataFrame) -> str:
        # 统一存入 data/stocks/{symbol}/intraday_data.csv
        return await self.save_intraday_to_stocks(symbol, df)

    async def save_df(self, subdir: str, name: str, df: pd.DataFrame) -> str:
        # 市场级统一写入 data/market/{name}.csv（忽略 subdir 层次）
        path = self._market_path(name)
        df.to_csv(path, index=False)
        return path

    async def save_financial_report_csv(self, symbol: str, table: str, df: pd.DataFrame) -> str:
        # 统一存入 data/stocks/{symbol}/
        return await self.save_financial_report_to_stocks(symbol, table, df)

    # ---------------------- 保存到 data/stocks/{symbol} 下（与A股一致） ----------------------
    async def save_equity_to_stocks(self, symbol: str, df: pd.DataFrame) -> str:
        stock_dir = self.get_stock_dir(symbol)
        path = os.path.join(stock_dir, "historical_quotes.csv")
        df.to_csv(path, index=False)
        return path

    async def save_intraday_to_stocks(self, symbol: str, df: pd.DataFrame) -> str:
        stock_dir = self.get_stock_dir(symbol)
        path = os.path.join(stock_dir, "intraday_data.csv")
        df.to_csv(path, index=False)
        return path

    async def save_financial_report_to_stocks(self, symbol: str, table: str, df: pd.DataFrame) -> str:
        table_map = {
            "资产负债表": "balance_sheet.csv",
            "利润表": "income_statement.csv",
            "现金流量表": "cash_flow_statement.csv",
        }
        stock_dir = self.get_stock_dir(symbol)
        filename = table_map.get(table, f"{table}.csv")
        path = os.path.join(stock_dir, filename)
        df.to_csv(path, index=False)
        return path

    async def save_financial_indicators_to_stocks(self, symbol: str, df: pd.DataFrame) -> str:
        stock_dir = self.get_stock_dir(symbol)
        path = os.path.join(stock_dir, "financial_indicators.csv")
        df.to_csv(path, index=False)
        return path

    async def save_company_profile_to_stocks(self, symbol: str, df: pd.DataFrame) -> str:
        stock_dir = self.get_stock_dir(symbol)
        path = os.path.join(stock_dir, "company_profile.csv")
        df.to_csv(path, index=False)
        return path

    async def save_stock_valuation_to_stocks(self, symbol: str, df: pd.DataFrame) -> str:
        stock_dir = self.get_stock_dir(symbol)
        path = os.path.join(stock_dir, "stock_valuation.csv")
        df.to_csv(path, index=False)
        return path

    # ---- 估值指标分别落盘 ----
    @staticmethod
    def _indicator_key(indicator: str) -> str:
        mapping = {
            "总市值": "total_market_cap",
            "市盈率(TTM)": "pe_ttm",
            "市盈率(静)": "pe_static",
            "市净率": "pb",
            "市现率": "pcf",
        }
        return mapping.get(indicator, indicator)

    async def save_stock_valuation_indicator_to_stocks(self, symbol: str, indicator: str, df: pd.DataFrame) -> str:
        key = self._indicator_key(indicator)
        stock_dir = self.get_stock_dir(symbol)
        filename = f"valuation_{key}.csv"
        path = os.path.join(stock_dir, filename)
        df.to_csv(path, index=False)
        return path

    # ---- 盈利预测拆分保存（清洗目录） ----
    @staticmethod
    def _profit_indicator_key(indicator: str) -> str:
        mapping = {
            "评级总览": "rating_overview",
            "去年度业绩表现": "last_year_performance",
            "综合盈利预测": "comprehensive",
            "盈利预测概览": "overview",
        }
        return mapping.get(indicator, indicator)

    async def save_profit_forecast_indicator(self, symbol: str, indicator: str, df: pd.DataFrame) -> str:
        # 统一存入 data/stocks/{symbol}/
        key = self._profit_indicator_key(indicator)
        stock_dir = self.get_stock_dir(symbol)
        path = os.path.join(stock_dir, f"profit_forecast_{key}.csv")
        df.to_csv(path, index=False)
        return path


