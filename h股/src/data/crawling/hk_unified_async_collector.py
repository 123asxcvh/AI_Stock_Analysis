from __future__ import annotations

import asyncio
from typing import Dict

from src.data.crawling.hk_data_collector import HKDataCollector


class HKUnifiedAsyncCollector:
    """港股 统一个股数据采集器（异步）

    复刻 A股 的“单只统一并发采集”逻辑：
    - 并发抓取：日线、分时、三大报表、财务指标、公司资料、盈利预测、估值、（可选）亿牛指标
    - 各自独立落盘，失败不阻塞其它项
    - 返回各项成功/失败布尔值
    """

    def __init__(self, data_root_dir: str) -> None:
        self.collector = HKDataCollector(data_root_dir=data_root_dir)

    async def collect_all_stock_data(self, symbol: str) -> Dict[str, bool]:
        results: Dict[str, bool] = {}

        async def wrap(name: str, coro, save_coro=None):
            try:
                df = await coro
                if save_coro:
                    await save_coro(df)
                results[name] = True
            except Exception:
                results[name] = False

        tasks = [
            # 日线（后复权）
            wrap(
                "equity_daily",
                self.collector.fetch_equity_daily(symbol, start_date="20100101", end_date="22220101"),
                lambda df, s=symbol: self.collector.save_equity_to_stocks(s, df),
            ),
            # 15 分钟分时
            wrap(
                "intraday_15m",
                self.collector.fetch_intraday_15m(symbol),
                lambda df, s=symbol: self.collector.save_intraday_to_stocks(s, df),
            ),
            # 三大报表（报告期）
            wrap(
                "balance_sheet",
                self.collector.fetch_financial_report_em(symbol, "资产负债表", indicator="报告期"),
                lambda df, s=symbol: self.collector.save_financial_report_to_stocks(s, "资产负债表", df),
            ),
            wrap(
                "income_statement",
                self.collector.fetch_financial_report_em(symbol, "利润表", indicator="报告期"),
                lambda df, s=symbol: self.collector.save_financial_report_to_stocks(s, "利润表", df),
            ),
            wrap(
                "cashflow_statement",
                self.collector.fetch_financial_report_em(symbol, "现金流量表", indicator="报告期"),
                lambda df, s=symbol: self.collector.save_financial_report_to_stocks(s, "现金流量表", df),
            ),
            # 财务指标（年度）
            wrap(
                "financial_analysis_indicator",
                self.collector.fetch_financial_analysis_indicator_em(symbol, indicator="年度"),
                lambda df, s=symbol: self.collector.save_financial_indicators_to_stocks(s, df),
            ),
            # 公司资料（东财）
            wrap(
                "company_profile",
                self.collector.fetch_company_profile_em(symbol),
                lambda df, s=symbol: self.collector.save_company_profile_to_stocks(s, df),
            ),
            # 盈利预测（经济通，概览）
            wrap(
                "profit_forecast_overview",
                self.collector.fetch_profit_forecast_et(symbol, indicator="盈利预测概览"),
                lambda df, s=symbol: self.collector.save_profit_forecast_indicator(s, "盈利预测概览", df),
            ),
            wrap(
                "profit_forecast_rating_overview",
                self.collector.fetch_profit_forecast_et(symbol, indicator="评级总览"),
                lambda df, s=symbol: self.collector.save_profit_forecast_indicator(s, "评级总览", df),
            ),
            wrap(
                "profit_forecast_last_year_performance",
                self.collector.fetch_profit_forecast_et(symbol, indicator="去年度业绩表现"),
                lambda df, s=symbol: self.collector.save_profit_forecast_indicator(s, "去年度业绩表现", df),
            ),
            wrap(
                "profit_forecast_comprehensive",
                self.collector.fetch_profit_forecast_et(symbol, indicator="综合盈利预测"),
                lambda df, s=symbol: self.collector.save_profit_forecast_indicator(s, "综合盈利预测", df),
            ),
            # 估值（百度，拆分多指标，近一年）
            wrap(
                "valuation_total_market_cap",
                self.collector.fetch_valuation_baidu(symbol, indicator="总市值", period="近一年"),
                lambda df, s=symbol: self.collector.save_stock_valuation_indicator_to_stocks(s, "总市值", df),
            ),
            wrap(
                "valuation_pe_ttm",
                self.collector.fetch_valuation_baidu(symbol, indicator="市盈率(TTM)", period="近一年"),
                lambda df, s=symbol: self.collector.save_stock_valuation_indicator_to_stocks(s, "市盈率(TTM)", df),
            ),
            wrap(
                "valuation_pe_static",
                self.collector.fetch_valuation_baidu(symbol, indicator="市盈率(静)", period="近一年"),
                lambda df, s=symbol: self.collector.save_stock_valuation_indicator_to_stocks(s, "市盈率(静)", df),
            ),
            wrap(
                "valuation_pb",
                self.collector.fetch_valuation_baidu(symbol, indicator="市净率", period="近一年"),
                lambda df, s=symbol: self.collector.save_stock_valuation_indicator_to_stocks(s, "市净率", df),
            ),
            wrap(
                "valuation_pcf",
                self.collector.fetch_valuation_baidu(symbol, indicator="市现率", period="近一年"),
                lambda df, s=symbol: self.collector.save_stock_valuation_indicator_to_stocks(s, "市现率", df),
            ),
        ]

        await asyncio.gather(*tasks, return_exceptions=True)
        return results


