#!/usr/bin/env python

"""
数据爬取模块
提供股票数据的爬取功能
"""

from src.crawling.market_data_collector import AsyncMarketDataCollector
from src.crawling.stock_data_collector import AsyncStockCollector
from src.crawling.index_stocks_collector import collect_index_stocks_batch_async

__all__ = [
    "AsyncMarketDataCollector",
    "AsyncStockCollector", 
    "collect_index_stocks_batch_async",
]

__version__ = "2.0.0"
__author__ = "Stock Data Team"
__description__ = "股票数据爬取模块"
