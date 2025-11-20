#!/usr/bin/env python

"""
增强版港股数据采集器 - 完全异步实现
支持多种港股数据类型，包括个股、指数、板块、资金流向等
使用 asyncio 和线程池实现高效的并发爬取
"""

import asyncio
import json
import logging
import os
import random
import sys
import time
from collections.abc import Iterable
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# 路径设置
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    import akshare as ak
    import pandas as pd
    from src.utils.common.hk_normalization import normalize_hk_ohlcv
except ImportError as e:
    print(f"依赖导入失败: {e}")
    sys.exit(1)

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - [%(funcName)s] - %(message)s",
)
logger = logging.getLogger(__name__)


class EnhancedHKDataCollector:
    """
    增强版港股数据采集器
    
    特性：
    - 完全异步实现，支持高并发爬取
    - 多种数据类型：个股、指数、板块、资金流向、新闻等
    - 智能重试机制和错误处理
    - 数据标准化和缓存支持
    - 批量处理优化
    """

    def __init__(self, data_root_dir: str = "data", max_workers: int = None):
        """
        初始化港股数据采集器
        
        Args:
            data_root_dir: 数据存储根目录
            max_workers: 最大工作线程数，默认使用CPU核心数
        """
        self.data_root_dir = Path(data_root_dir)
        self.max_workers = max_workers or min(os.cpu_count() or 4, 8)
        self._executor = ThreadPoolExecutor(max_workers=self.max_workers)
        
        # 创建必要的目录结构
        self._init_directories()
        
        # 配置参数
        self.request_delay = 0.5  # 请求间隔
        self.max_retries = 3      # 最大重试次数
        self.retry_base_delay = 1.0  # 重试基础延迟
        
        logger.info(f"初始化港股数据采集器 - 工作线程: {self.max_workers}")
        logger.info(f"数据存储目录: {self.data_root_dir}")

    def _init_directories(self):
        """初始化目录结构"""
        directories = [
            self.data_root_dir / "cleaned_stocks" / "hk" / "equities",
            self.data_root_dir / "cleaned_stocks" / "hk" / "indexes",
            self.data_root_dir / "cleaned_stocks" / "hk" / "sectors",
            self.data_root_dir / "cleaned_stocks" / "hk" / "fund_flow",
            self.data_root_dir / "cleaned_stocks" / "hk" / "news",
            self.data_root_dir / "cleaned_stocks" / "hk" / "financials",
            self.data_root_dir / "cache" / "hk",
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    async def _run_sync(self, fn, *args, **kwargs) -> Any:
        """
        在线程池中异步运行同步函数
        
        Args:
            fn: 要执行的同步函数
            *args: 函数参数
            **kwargs: 函数关键字参数
            
        Returns:
            函数执行结果
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self._executor, lambda: fn(*args, **kwargs))

    async def _retry_async(self, coro_fn, max_retries: int = None, 
                          base_delay: float = None) -> Any:
        """
        异步重试机制
        
        Args:
            coro_fn: 要重试的协程函数
            max_retries: 最大重试次数
            base_delay: 基础延迟时间
            
        Returns:
            成功执行的结果
            
        Raises:
            Exception: 重试失败后的异常
        """
        max_retries = max_retries or self.max_retries
        base_delay = base_delay or self.retry_base_delay
        
        last_exc: Optional[Exception] = None
        
        for attempt in range(max_retries):
            try:
                return await coro_fn()
            except Exception as e:
                last_exc = e
                if attempt < max_retries - 1:
                    wait_time = base_delay * (2 ** attempt) + random.uniform(0, 0.5)
                    logger.warning(f"港股数据获取失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                    logger.info(f"等待 {wait_time:.2f} 秒后重试...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"港股数据获取最终失败: {e}")
        
        if last_exc:
            raise last_exc

    async def _add_delay(self):
        """添加请求延迟，避免频率限制"""
        await asyncio.sleep(self.request_delay)

    # ==================== 个股数据爬取 ====================
    
    async def fetch_equity_daily(self, symbol: str, start_date: str = "20200101", 
                                end_date: str = None) -> pd.DataFrame:
        """
        获取个股日线数据（后复权）
        
        Args:
            symbol: 港股代码（如：00700）
            start_date: 开始日期，格式：YYYYMMDD
            end_date: 结束日期，格式：YYYYMMDD，默认为当前日期
            
        Returns:
            标准化的OHLCV数据
        """
        if end_date is None:
            end_date = time.strftime("%Y%m%d")
            
        async def _call():
            await self._add_delay()
            df = await self._run_sync(
                ak.stock_hk_hist, symbol, "daily", start_date, end_date, "hfq"
            )
            return normalize_hk_ohlcv(df)

        return await self._retry_async(_call)

    async def fetch_equity_minute(self, symbol: str, period: str = "1") -> pd.DataFrame:
        """
        获取个股分钟级数据
        
        Args:
            symbol: 港股代码
            period: 周期，1=1分钟，5=5分钟，15=15分钟，30=30分钟，60=60分钟
            
        Returns:
            分钟级OHLCV数据
        """
        async def _call():
            await self._add_delay()
            df = await self._run_sync(ak.stock_hk_min, symbol, period)
            return normalize_hk_ohlcv(df)

        return await self._retry_async(_call)

    async def fetch_equity_realtime(self, symbol: str) -> pd.DataFrame:
        """
        获取个股实时行情
        
        Args:
            symbol: 港股代码
            
        Returns:
            实时行情数据
        """
        async def _call():
            await self._add_delay()
            return await self._run_sync(ak.stock_hk_spot_em, symbol)

        return await self._retry_async(_call)

    # ==================== 指数数据爬取 ====================
    
    async def fetch_index_daily(self, symbol: str) -> pd.DataFrame:
        """
        获取指数日线数据
        
        Args:
            symbol: 指数代码（如：HSI）
            
        Returns:
            标准化的指数OHLCV数据
        """
        async def _call():
            await self._add_delay()
            df = await self._run_sync(ak.stock_hk_index_daily_sina, symbol)
            return normalize_hk_ohlcv(df)

        return await self._retry_async(_call)

    async def fetch_index_realtime(self, symbol: str) -> pd.DataFrame:
        """
        获取指数实时数据
        
        Args:
            symbol: 指数代码
            
        Returns:
            指数实时数据
        """
        async def _call():
            await self._add_delay()
            return await self._run_sync(ak.stock_hk_index_spot, symbol)

        return await self._retry_async(_call)

    # ==================== 板块和行业数据 ====================
    
    async def fetch_sector_list(self) -> pd.DataFrame:
        """
        获取港股板块列表
        
        Returns:
            板块列表数据
        """
        async def _call():
            await self._add_delay()
            return await self._run_sync(ak.stock_board_industry_name_em)

        return await self._retry_async(_call)

    async def fetch_sector_stocks(self, sector_name: str) -> pd.DataFrame:
        """
        获取指定板块的股票列表
        
        Args:
            sector_name: 板块名称
            
        Returns:
            板块股票列表
        """
        async def _call():
            await self._add_delay()
            return await self._run_sync(ak.stock_board_industry_cons_em, sector_name)

        return await self._retry_async(_call)

    async def fetch_sector_fund_flow(self, sector_name: str) -> pd.DataFrame:
        """
        获取板块资金流向
        
        Args:
            sector_name: 板块名称
            
        Returns:
            板块资金流向数据
        """
        async def _call():
            await self._add_delay()
            return await self._run_sync(ak.stock_board_industry_fund_flow_rank, sector_name)

        return await self._retry_async(_call)

    # ==================== 资金流向数据 ====================
    
    async def fetch_market_fund_flow(self) -> pd.DataFrame:
        """
        获取港股市场资金流向
        
        Returns:
            市场资金流向数据
        """
        async def _call():
            await self._add_delay()
            return await self._run_sync(ak.stock_hk_fund_flow_individual)

        return await self._retry_async(_call)

    async def fetch_stock_fund_flow(self, symbol: str) -> pd.DataFrame:
        """
        获取个股资金流向
        
        Args:
            symbol: 港股代码
            
        Returns:
            个股资金流向数据
        """
        async def _call():
            await self._add_delay()
            return await self._run_sync(ak.stock_individual_fund_flow_rank, symbol)

        return await self._retry_async(_call)

    # ==================== 财务数据 ====================
    
    async def fetch_financial_statement(self, symbol: str, statement_type: str = "资产负债表") -> pd.DataFrame:
        """
        获取财务报表数据
        
        Args:
            symbol: 港股代码
            statement_type: 报表类型（资产负债表、利润表、现金流量表）
            
        Returns:
            财务报表数据
        """
        async def _call():
            await self._add_delay()
            return await self._run_sync(ak.stock_financial_report_sina, symbol, statement_type)

        return await self._retry_async(_call)

    async def fetch_financial_indicators(self, symbol: str) -> pd.DataFrame:
        """
        获取财务指标数据
        
        Args:
            symbol: 港股代码
            
        Returns:
            财务指标数据
        """
        async def _call():
            await self._add_delay()
            return await self._run_sync(ak.stock_financial_analysis_indicator, symbol)

        return await self._retry_async(_call)

    # ==================== 新闻和公告数据 ====================
    
    async def fetch_news_data(self, symbol: str = None) -> pd.DataFrame:
        """
        获取港股新闻数据
        
        Args:
            symbol: 港股代码，如果为None则获取市场新闻
            
        Returns:
            新闻数据
        """
        async def _call():
            await self._add_delay()
            if symbol:
                return await self._run_sync(ak.stock_news_em, symbol)
            else:
                return await self._run_sync(ak.stock_news_em)

        return await self._retry_async(_call)

    async def fetch_announcements(self, symbol: str) -> pd.DataFrame:
        """
        获取公司公告
        
        Args:
            symbol: 港股代码
            
        Returns:
            公告数据
        """
        async def _call():
            await self._add_delay()
            return await self._run_sync(ak.stock_notice_report, symbol)

        return await self._retry_async(_call)

    # ==================== 批量处理 ====================
    
    async def fetch_equities_batch(self, symbols: Iterable[str], 
                                  data_types: List[str] = None,
                                  start_date: str = "20200101") -> Dict[str, Dict[str, pd.DataFrame]]:
        """
        批量获取多个股票的数据
        
        Args:
            symbols: 股票代码列表
            data_types: 数据类型列表，默认为所有类型
            start_date: 开始日期
            
        Returns:
            按股票代码和数据类型组织的数据字典
        """
        if data_types is None:
            data_types = ["daily", "realtime", "fund_flow"]
            
        results = {}
        
        for symbol in symbols:
            logger.info(f"开始处理股票 {symbol}")
            symbol_data = {}
            
            try:
                # 并发获取该股票的所有数据类型
                tasks = []
                if "daily" in data_types:
                    tasks.append(("daily", self.fetch_equity_daily(symbol, start_date)))
                if "realtime" in data_types:
                    tasks.append(("realtime", self.fetch_equity_realtime(symbol)))
                if "fund_flow" in data_types:
                    tasks.append(("fund_flow", self.fetch_stock_fund_flow(symbol)))
                
                # 并发执行
                for data_type, task in tasks:
                    try:
                        symbol_data[data_type] = await task
                        logger.info(f"股票 {symbol} {data_type} 数据获取成功")
                    except Exception as e:
                        logger.error(f"股票 {symbol} {data_type} 数据获取失败: {e}")
                        symbol_data[data_type] = pd.DataFrame()
                
                results[symbol] = symbol_data
                
            except Exception as e:
                logger.error(f"股票 {symbol} 处理失败: {e}")
                results[symbol] = {}
            
            # 添加延迟避免频率限制
            await asyncio.sleep(self.request_delay)
        
        return results

    async def fetch_indexes_batch(self, index_symbols: Iterable[str]) -> Dict[str, pd.DataFrame]:
        """
        批量获取指数数据
        
        Args:
            index_symbols: 指数代码列表
            
        Returns:
            指数数据字典
        """
        tasks = [self.fetch_index_daily(symbol) for symbol in index_symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        out = {}
        for symbol, result in zip(index_symbols, results):
            if isinstance(result, Exception):
                logger.error(f"指数 {symbol} 获取失败: {result}")
                out[symbol] = pd.DataFrame()
            else:
                out[symbol] = result
                logger.info(f"指数 {symbol} 数据获取成功")
        
        return out

    # ==================== 数据保存 ====================
    
    def _make_path(self, data_type: str, name: str, sub_type: str = None) -> Path:
        """
        生成文件保存路径
        
        Args:
            data_type: 数据类型（equities, indexes, sectors等）
            name: 股票/指数名称
            sub_type: 子类型（如daily, realtime等）
            
        Returns:
            文件路径
        """
        if sub_type:
            base = self.data_root_dir / "cleaned_stocks" / "hk" / data_type / sub_type
        else:
            base = self.data_root_dir / "cleaned_stocks" / "hk" / data_type
        
        base.mkdir(parents=True, exist_ok=True)
        return base / f"{name}.csv"

    async def save_data(self, data: pd.DataFrame, data_type: str, name: str, 
                       sub_type: str = None) -> str:
        """
        保存数据到CSV文件
        
        Args:
            data: 要保存的数据
            data_type: 数据类型
            name: 名称
            sub_type: 子类型
            
        Returns:
            保存的文件路径
        """
        if data is None or data.empty:
            logger.warning(f"数据为空，跳过保存: {data_type}/{name}")
            return ""
            
        path = self._make_path(data_type, name, sub_type)
        
        try:
            data.to_csv(path, index=False, encoding='utf-8-sig')
            logger.info(f"数据保存成功: {path}")
            return str(path)
        except Exception as e:
            logger.error(f"数据保存失败 {path}: {e}")
            return ""

    async def save_batch_data(self, batch_results: Dict[str, Any], 
                             data_type: str = "equities") -> List[str]:
        """
        批量保存数据
        
        Args:
            batch_results: 批量获取的结果
            data_type: 数据类型
            
        Returns:
            保存的文件路径列表
        """
        saved_paths = []
        
        for name, data in batch_results.items():
            if isinstance(data, dict):
                # 多类型数据
                for sub_type, sub_data in data.items():
                    if not sub_data.empty:
                        path = await self.save_data(sub_data, data_type, name, sub_type)
                        if path:
                            saved_paths.append(path)
            else:
                # 单类型数据
                if not data.empty:
                    path = await self.save_data(data, data_type, name)
                    if path:
                        saved_paths.append(path)
        
        logger.info(f"批量保存完成，共保存 {len(saved_paths)} 个文件")
        return saved_paths

    # ==================== 主流程方法 ====================
    
    async def collect_comprehensive_hk_data(self, symbols: List[str], 
                                          indexes: List[str] = None,
                                          include_sectors: bool = True) -> Dict[str, Any]:
        """
        综合收集港股数据的主流程
        
        Args:
            symbols: 股票代码列表
            indexes: 指数代码列表
            include_sectors: 是否包含板块数据
            
        Returns:
            收集结果统计
        """
        start_time = time.time()
        logger.info(f"开始综合收集港股数据，股票数量: {len(symbols)}")
        
        results = {
            "stocks": {},
            "indexes": {},
            "sectors": {},
            "summary": {}
        }
        
        try:
            # 1. 收集股票数据
            logger.info("开始收集股票数据...")
            stock_results = await self.fetch_equities_batch(symbols)
            results["stocks"] = stock_results
            
            # 2. 收集指数数据
            if indexes:
                logger.info("开始收集指数数据...")
                index_results = await self.fetch_indexes_batch(indexes)
                results["indexes"] = index_results
            
            # 3. 收集板块数据
            if include_sectors:
                logger.info("开始收集板块数据...")
                try:
                    sector_list = await self.fetch_sector_list()
                    results["sectors"]["sector_list"] = sector_list
                    
                    # 获取前几个主要板块的股票列表
                    top_sectors = sector_list.head(5)["板块名称"].tolist()
                    for sector in top_sectors:
                        try:
                            sector_stocks = await self.fetch_sector_stocks(sector)
                            results["sectors"][sector] = sector_stocks
                        except Exception as e:
                            logger.error(f"板块 {sector} 数据获取失败: {e}")
                            
                except Exception as e:
                    logger.error(f"板块数据收集失败: {e}")
            
            # 4. 保存数据
            logger.info("开始保存数据...")
            saved_paths = []
            
            # 保存股票数据
            stock_paths = await self.save_batch_data(stock_results, "equities")
            saved_paths.extend(stock_paths)
            
            # 保存指数数据
            if indexes:
                for name, data in results["indexes"].items():
                    if not data.empty:
                        path = await self.save_data(data, "indexes", name)
                        if path:
                            saved_paths.append(path)
            
            # 保存板块数据
            if include_sectors and "sectors" in results:
                for name, data in results["sectors"].items():
                    if isinstance(data, pd.DataFrame) and not data.empty:
                        path = await self.save_data(data, "sectors", name)
                        if path:
                            saved_paths.append(path)
            
            # 5. 生成统计信息
            duration = time.time() - start_time
            success_stocks = sum(1 for data in stock_results.values() if data)
            total_stocks = len(symbols)
            
            results["summary"] = {
                "total_stocks": total_stocks,
                "success_stocks": success_stocks,
                "success_rate": (success_stocks / total_stocks * 100) if total_stocks > 0 else 0,
                "total_indexes": len(indexes) if indexes else 0,
                "saved_files": len(saved_paths),
                "duration": duration,
                "status": "success"
            }
            
            logger.info(f"港股数据收集完成！成功率: {results['summary']['success_rate']:.1f}%")
            logger.info(f"共保存 {len(saved_paths)} 个文件，耗时 {duration:.2f} 秒")
            
        except Exception as e:
            logger.error(f"港股数据收集失败: {e}")
            results["summary"] = {
                "status": "failed",
                "error": str(e),
                "duration": time.time() - start_time
            }
        
        return results

    async def close(self):
        """关闭采集器，释放资源"""
        if self._executor:
            self._executor.shutdown(wait=True)
            logger.info("港股数据采集器已关闭")

    # ==================== 新增缺失接口 ====================
    
    async def fetch_company_profile(self, symbol: str) -> pd.DataFrame:
        """
        获取港股公司资料
        
        Args:
            symbol: 港股代码
            
        Returns:
            公司资料数据
        """
        try:
            logger.info(f"获取港股 {symbol} 公司资料...")
            
            # 使用 akshare 获取公司资料
            data = await self._run_sync(
                ak.stock_hk_company_profile_em, 
                symbol=symbol
            )
            
            if data is not None and not data.empty:
                # 标准化数据
                data = data.copy()
                data['symbol'] = symbol
                data['fetch_time'] = pd.Timestamp.now()
                
                logger.info(f"成功获取港股 {symbol} 公司资料，共 {len(data)} 条记录")
                return data
            else:
                logger.warning(f"港股 {symbol} 公司资料为空")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"获取港股 {symbol} 公司资料失败: {e}")
            return pd.DataFrame()

    async def fetch_profit_forecast(self, symbol: str) -> pd.DataFrame:
        """
        获取港股盈利预测数据
        
        Args:
            symbol: 港股代码
            
        Returns:
            盈利预测数据
        """
        try:
            logger.info(f"获取港股 {symbol} 盈利预测数据...")
            
            # 使用 akshare 获取盈利预测概览
            data = await self._run_sync(
                ak.stock_hk_profit_forecast_et,
                symbol=symbol,
                indicator="盈利预测概览"
            )
            
            if data is not None and not data.empty:
                # 标准化数据
                data = data.copy()
                data['symbol'] = symbol
                data['fetch_time'] = pd.Timestamp.now()
                
                logger.info(f"成功获取港股 {symbol} 盈利预测数据，共 {len(data)} 条记录")
                return data
            else:
                logger.warning(f"港股 {symbol} 盈利预测数据为空")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"获取港股 {symbol} 盈利预测数据失败: {e}")
            return pd.DataFrame()

    async def fetch_valuation_indicators(self, symbol: str) -> pd.DataFrame:
        """
        获取港股估值指标数据
        
        Args:
            symbol: 港股代码
            
        Returns:
            估值指标数据
        """
        try:
            logger.info(f"获取港股 {symbol} 估值指标数据...")
            
            # 获取多种估值指标
            indicators = ["总市值", "市盈率(TTM)", "市净率", "市销率TTM", "净资产收益率TTM"]
            all_data = []
            
            for indicator in indicators:
                try:
                    data = await self._run_sync(
                        ak.stock_hk_valuation_baidu,
                        symbol=symbol,
                        indicator=indicator,
                        period="近一年"
                    )
                    
                    if data is not None and not data.empty:
                        data = data.copy()
                        data['indicator'] = indicator
                        data['symbol'] = symbol
                        all_data.append(data)
                        
                except Exception as e:
                    logger.warning(f"获取港股 {symbol} {indicator} 数据失败: {e}")
                    continue
            
            if all_data:
                # 合并所有指标数据
                combined_data = pd.concat(all_data, ignore_index=True)
                combined_data['fetch_time'] = pd.Timestamp.now()
                
                logger.info(f"成功获取港股 {symbol} 估值指标数据，共 {len(combined_data)} 条记录")
                return combined_data
            else:
                logger.warning(f"港股 {symbol} 估值指标数据为空")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"获取港股 {symbol} 估值指标数据失败: {e}")
            return pd.DataFrame()

    async def fetch_hot_rank_data(self) -> pd.DataFrame:
        """
        获取港股人气榜数据
        
        Returns:
            人气榜数据
        """
        try:
            logger.info("获取港股人气榜数据...")
            
            # 使用 akshare 获取人气榜数据
            data = await self._run_sync(ak.stock_hk_hot_rank_em)
            
            if data is not None and not data.empty:
                # 标准化数据
                data = data.copy()
                data['fetch_time'] = pd.Timestamp.now()
                
                logger.info(f"成功获取港股人气榜数据，共 {len(data)} 条记录")
                return data
            else:
                logger.warning("港股人气榜数据为空")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"获取港股人气榜数据失败: {e}")
            return pd.DataFrame()

    async def fetch_famous_stocks(self) -> pd.DataFrame:
        """
        获取知名港股数据
        
        Returns:
            知名港股数据
        """
        try:
            logger.info("获取知名港股数据...")
            
            # 使用 akshare 获取知名港股数据
            data = await self._run_sync(ak.stock_hk_famous_spot_em)
            
            if data is not None and not data.empty:
                # 标准化数据
                data = data.copy()
                data['fetch_time'] = pd.Timestamp.now()
                
                logger.info(f"成功获取知名港股数据，共 {len(data)} 条记录")
                return data
            else:
                logger.warning("知名港股数据为空")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"获取知名港股数据失败: {e}")
            return pd.DataFrame()

    async def fetch_main_board_stocks(self) -> pd.DataFrame:
        """
        获取港股主板实时行情数据
        
        Returns:
            港股主板数据
        """
        try:
            logger.info("获取港股主板实时行情数据...")
            
            # 使用 akshare 获取港股主板数据
            data = await self._run_sync(ak.stock_hk_main_board_spot_em)
            
            if data is not None and not data.empty:
                # 标准化数据
                data = data.copy()
                data['fetch_time'] = pd.Timestamp.now()
                
                logger.info(f"成功获取港股主板数据，共 {len(data)} 条记录")
                return data
            else:
                logger.warning("港股主板数据为空")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"获取港股主板数据失败: {e}")
            return pd.DataFrame()

    async def fetch_ggt_components(self) -> pd.DataFrame:
        """
        获取港股通成份股数据
        
        Returns:
            港股通成份股数据
        """
        try:
            logger.info("获取港股通成份股数据...")
            
            # 使用 akshare 获取港股通成份股数据
            data = await self._run_sync(ak.stock_hk_ggt_components_em)
            
            if data is not None and not data.empty:
                # 标准化数据
                data = data.copy()
                data['fetch_time'] = pd.Timestamp.now()
                
                logger.info(f"成功获取港股通成份股数据，共 {len(data)} 条记录")
                return data
            else:
                logger.warning("港股通成份股数据为空")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"获取港股通成份股数据失败: {e}")
            return pd.DataFrame()

    async def fetch_individual_indicators(self, symbol: str) -> pd.DataFrame:
        """
        获取港股个股指标数据
        
        Args:
            symbol: 港股代码
            
        Returns:
            个股指标数据
        """
        try:
            logger.info(f"获取港股 {symbol} 个股指标数据...")
            
            # 获取多种指标
            indicators = ["港股", "市盈率", "市净率", "股息率", "ROE", "市值"]
            all_data = []
            
            for indicator in indicators:
                try:
                    data = await self._run_sync(
                        ak.stock_hk_indicator_eniu,
                        symbol=f"hk{symbol}",
                        indicator=indicator
                    )
                    
                    if data is not None and not data.empty:
                        data = data.copy()
                        data['indicator'] = indicator
                        data['symbol'] = symbol
                        all_data.append(data)
                        
                except Exception as e:
                    logger.warning(f"获取港股 {symbol} {indicator} 指标数据失败: {e}")
                    continue
            
            if all_data:
                # 合并所有指标数据
                combined_data = pd.concat(all_data, ignore_index=True)
                combined_data['fetch_time'] = pd.Timestamp.now()
                
                logger.info(f"成功获取港股 {symbol} 个股指标数据，共 {len(combined_data)} 条记录")
                return combined_data
            else:
                logger.warning(f"港股 {symbol} 个股指标数据为空")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"获取港股 {symbol} 个股指标数据失败: {e}")
            return pd.DataFrame()

    async def fetch_individual_basic_info(self, symbol: str) -> pd.DataFrame:
        """
        获取港股个股基本信息
        
        Args:
            symbol: 港股代码
            
        Returns:
            个股基本信息数据
        """
        try:
            logger.info(f"获取港股 {symbol} 个股基本信息...")
            
            # 使用 akshare 获取个股基本信息
            data = await self._run_sync(
                ak.stock_individual_basic_info_hk_xq,
                symbol=symbol
            )
            
            if data is not None and not data.empty:
                # 标准化数据
                data = data.copy()
                data['symbol'] = symbol
                data['fetch_time'] = pd.Timestamp.now()
                
                logger.info(f"成功获取港股 {symbol} 个股基本信息，共 {len(data)} 条记录")
                return data
            else:
                logger.warning(f"港股 {symbol} 个股基本信息为空")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"获取港股 {symbol} 个股基本信息失败: {e}")
            return pd.DataFrame()

    async def fetch_sina_daily_data(self, symbol: str) -> pd.DataFrame:
        """
        获取港股新浪历史行情数据
        
        Args:
            symbol: 港股代码
            
        Returns:
            历史行情数据
        """
        try:
            logger.info(f"获取港股 {symbol} 新浪历史行情数据...")
            
            # 使用 akshare 获取新浪历史行情数据
            data = await self._run_sync(
                ak.stock_hk_daily,
                symbol=symbol,
                adjust="hfq"  # 后复权数据
            )
            
            if data is not None and not data.empty:
                # 标准化数据
                data = data.copy()
                data['symbol'] = symbol
                data['fetch_time'] = pd.Timestamp.now()
                
                logger.info(f"成功获取港股 {symbol} 新浪历史行情数据，共 {len(data)} 条记录")
                return data
            else:
                logger.warning(f"港股 {symbol} 新浪历史行情数据为空")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"获取港股 {symbol} 新浪历史行情数据失败: {e}")
            return pd.DataFrame()

    # ==================== 沪深港通接口 ====================
    
    async def fetch_hsgt_hold_stock(self) -> pd.DataFrame:
        """
        获取沪深港通持股-个股排行数据
        
        Returns:
            沪深港通持股数据
        """
        try:
            logger.info("获取沪深港通持股-个股排行数据...")
            
            # 使用 akshare 获取沪深港通持股数据
            data = await self._run_sync(ak.stock_hsgt_hold_stock_em)
            
            if data is not None and not data.empty:
                # 标准化数据
                data = data.copy()
                data['fetch_time'] = pd.Timestamp.now()
                
                logger.info(f"成功获取沪深港通持股数据，共 {len(data)} 条记录")
                return data
            else:
                logger.warning("沪深港通持股数据为空")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"获取沪深港通持股数据失败: {e}")
            return pd.DataFrame()

    async def fetch_hsgt_stock_statistics(self) -> pd.DataFrame:
        """
        获取沪深港通持股-每日个股统计数据
        
        Returns:
            沪深港通个股统计数据
        """
        try:
            logger.info("获取沪深港通持股-每日个股统计数据...")
            
            # 使用 akshare 获取沪深港通个股统计数据
            data = await self._run_sync(ak.stock_hsgt_stock_statistics_em)
            
            if data is not None and not data.empty:
                # 标准化数据
                data = data.copy()
                data['fetch_time'] = pd.Timestamp.now()
                
                logger.info(f"成功获取沪深港通个股统计数据，共 {len(data)} 条记录")
                return data
            else:
                logger.warning("沪深港通个股统计数据为空")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"获取沪深港通个股统计数据失败: {e}")
            return pd.DataFrame()

    async def fetch_hsgt_institution_statistics(self) -> pd.DataFrame:
        """
        获取沪深港通持股-每日机构统计数据
        
        Returns:
            沪深港通机构统计数据
        """
        try:
            logger.info("获取沪深港通持股-每日机构统计数据...")
            
            # 使用 akshare 获取沪深港通机构统计数据
            data = await self._run_sync(ak.stock_hsgt_institution_statistics_em)
            
            if data is not None and not data.empty:
                # 标准化数据
                data = data.copy()
                data['fetch_time'] = pd.Timestamp.now()
                
                logger.info(f"成功获取沪深港通机构统计数据，共 {len(data)} 条记录")
                return data
            else:
                logger.warning("沪深港通机构统计数据为空")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"获取沪深港通机构统计数据失败: {e}")
            return pd.DataFrame()

    async def fetch_hsgt_history(self, symbol: str = None) -> pd.DataFrame:
        """
        获取沪深港通历史数据
        
        Args:
            symbol: 股票代码，可选
            
        Returns:
            沪深港通历史数据
        """
        try:
            logger.info("获取沪深港通历史数据...")
            
            # 使用 akshare 获取沪深港通历史数据
            data = await self._run_sync(ak.stock_hsgt_hist_em, symbol=symbol)
            
            if data is not None and not data.empty:
                # 标准化数据
                data = data.copy()
                if symbol:
                    data['symbol'] = symbol
                data['fetch_time'] = pd.Timestamp.now()
                
                logger.info(f"成功获取沪深港通历史数据，共 {len(data)} 条记录")
                return data
            else:
                logger.warning("沪深港通历史数据为空")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"获取沪深港通历史数据失败: {e}")
            return pd.DataFrame()

    async def fetch_hsgt_board_rank(self) -> pd.DataFrame:
        """
        获取沪深港通板块排行数据
        
        Returns:
            沪深港通板块排行数据
        """
        try:
            logger.info("获取沪深港通板块排行数据...")
            
            # 使用 akshare 获取沪深港通板块排行数据
            data = await self._run_sync(ak.stock_hsgt_board_rank_em)
            
            if data is not None and not data.empty:
                # 标准化数据
                data = data.copy()
                data['fetch_time'] = pd.Timestamp.now()
                
                logger.info(f"成功获取沪深港通板块排行数据，共 {len(data)} 条记录")
                return data
            else:
                logger.warning("沪深港通板块排行数据为空")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"获取沪深港通板块排行数据失败: {e}")
            return pd.DataFrame()

    async def fetch_hsgt_fund_flow_summary(self) -> pd.DataFrame:
        """
        获取沪深港通资金流向数据
        
        Returns:
            沪深港通资金流向数据
        """
        try:
            logger.info("获取沪深港通资金流向数据...")
            
            # 使用 akshare 获取沪深港通资金流向数据
            data = await self._run_sync(ak.stock_hsgt_fund_flow_summary_em)
            
            if data is not None and not data.empty:
                # 标准化数据
                data = data.copy()
                data['fetch_time'] = pd.Timestamp.now()
                
                logger.info(f"成功获取沪深港通资金流向数据，共 {len(data)} 条记录")
                return data
            else:
                logger.warning("沪深港通资金流向数据为空")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"获取沪深港通资金流向数据失败: {e}")
            return pd.DataFrame()

    async def fetch_hsgt_individual(self, symbol: str) -> pd.DataFrame:
        """
        获取沪深港通持股-具体股票数据
        
        Args:
            symbol: 股票代码
            
        Returns:
            沪深港通具体股票数据
        """
        try:
            logger.info(f"获取沪深港通持股-具体股票 {symbol} 数据...")
            
            # 使用 akshare 获取沪深港通具体股票数据
            data = await self._run_sync(ak.stock_hsgt_individual_em, symbol=symbol)
            
            if data is not None and not data.empty:
                # 标准化数据
                data = data.copy()
                data['symbol'] = symbol
                data['fetch_time'] = pd.Timestamp.now()
                
                logger.info(f"成功获取沪深港通具体股票 {symbol} 数据，共 {len(data)} 条记录")
                return data
            else:
                logger.warning(f"沪深港通具体股票 {symbol} 数据为空")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"获取沪深港通具体股票 {symbol} 数据失败: {e}")
            return pd.DataFrame()

    async def fetch_hsgt_individual_detail(self, symbol: str) -> pd.DataFrame:
        """
        获取沪深港通持股-具体股票-详情数据
        
        Args:
            symbol: 股票代码
            
        Returns:
            沪深港通具体股票详情数据
        """
        try:
            logger.info(f"获取沪深港通持股-具体股票 {symbol} 详情数据...")
            
            # 使用 akshare 获取沪深港通具体股票详情数据
            data = await self._run_sync(ak.stock_hsgt_individual_detail_em, symbol=symbol)
            
            if data is not None and not data.empty:
                # 标准化数据
                data = data.copy()
                data['symbol'] = symbol
                data['fetch_time'] = pd.Timestamp.now()
                
                logger.info(f"成功获取沪深港通具体股票 {symbol} 详情数据，共 {len(data)} 条记录")
                return data
            else:
                logger.warning(f"沪深港通具体股票 {symbol} 详情数据为空")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"获取沪深港通具体股票 {symbol} 详情数据失败: {e}")
            return pd.DataFrame()

    # ==================== 综合数据收集方法 ====================
    
    async def collect_all_hk_data(self, symbols: List[str] = None) -> Dict[str, Any]:
        """
        收集所有类型的港股数据
        
        Args:
            symbols: 港股代码列表，如果为None则使用默认列表
            
        Returns:
            包含所有类型数据的字典
        """
        if symbols is None:
            symbols = ["00700", "09988", "03690", "02318", "02020"]  # 默认港股代码
        
        start_time = time.time()
        results = {
            "equities": {},
            "indexes": {},
            "sectors": {},
            "fund_flow": {},
            "news": {},
            "financials": {},
            "company_profiles": {},
            "profit_forecasts": {},
            "valuation_indicators": {},
            "hot_rank": None,
            "famous_stocks": None,
            "main_board_stocks": None,
            "ggt_components": None,
            "individual_indicators": {},
            "individual_basic_info": {},
            "sina_daily_data": {},
            "hsgt_data": {},
            "summary": {}
        }
        
        try:
            logger.info("开始收集所有类型的港股数据...")
            
            # 1. 收集基础数据
            logger.info("1. 收集基础数据...")
            
            # 个股数据
            stock_results = await self.fetch_equities_batch(symbols)
            results["equities"] = stock_results
            
            # 指数数据
            index_results = await self.fetch_indexes_batch(["HSI", "HSCEI", "HSCCI"])
            results["indexes"] = index_results
            
            # 板块数据
            sector_list = await self.fetch_sector_list()
            results["sectors"]["sector_list"] = sector_list
            
            # 2. 收集扩展数据
            logger.info("2. 收集扩展数据...")
            
            # 公司资料
            for symbol in symbols:
                profile_data = await self.fetch_company_profile(symbol)
                if not profile_data.empty:
                    results["company_profiles"][symbol] = profile_data
            
            # 盈利预测
            for symbol in symbols:
                forecast_data = await self.fetch_profit_forecast(symbol)
                if not forecast_data.empty:
                    results["profit_forecasts"][symbol] = forecast_data
            
            # 估值指标
            for symbol in symbols:
                valuation_data = await self.fetch_valuation_indicators(symbol)
                if not valuation_data.empty:
                    results["valuation_indicators"][symbol] = valuation_data
            
            # 个股指标
            for symbol in symbols:
                indicator_data = await self.fetch_individual_indicators(symbol)
                if not indicator_data.empty:
                    results["individual_indicators"][symbol] = indicator_data
            
            # 个股基本信息
            for symbol in symbols:
                basic_info_data = await self.fetch_individual_basic_info(symbol)
                if not basic_info_data.empty:
                    results["individual_basic_info"][symbol] = basic_info_data
            
            # 新浪历史数据
            for symbol in symbols:
                sina_data = await self.fetch_sina_daily_data(symbol)
                if not sina_data.empty:
                    results["sina_daily_data"][symbol] = sina_data
            
            # 3. 收集市场数据
            logger.info("3. 收集市场数据...")
            
            # 人气榜
            hot_rank_data = await self.fetch_hot_rank_data()
            results["hot_rank"] = hot_rank_data
            
            # 知名港股
            famous_stocks_data = await self.fetch_famous_stocks()
            results["famous_stocks"] = famous_stocks_data
            
            # 港股主板
            main_board_data = await self.fetch_main_board_stocks()
            results["main_board_stocks"] = main_board_data
            
            # 港股通成份股
            ggt_data = await self.fetch_ggt_components()
            results["ggt_components"] = ggt_data
            
            # 4. 收集沪深港通数据
            logger.info("4. 收集沪深港通数据...")
            
            # 沪深港通基础数据
            hsgt_hold_data = await self.fetch_hsgt_hold_stock()
            hsgt_stock_stats = await self.fetch_hsgt_stock_statistics()
            hsgt_institution_stats = await self.fetch_hsgt_institution_statistics()
            hsgt_board_rank = await self.fetch_hsgt_board_rank()
            hsgt_fund_flow = await self.fetch_hsgt_fund_flow_summary()
            
            results["hsgt_data"] = {
                "hold_stock": hsgt_hold_data,
                "stock_statistics": hsgt_stock_stats,
                "institution_statistics": hsgt_institution_stats,
                "board_rank": hsgt_board_rank,
                "fund_flow_summary": hsgt_fund_flow
            }
            
            # 沪深港通个股数据
            for symbol in symbols:
                hsgt_individual = await self.fetch_hsgt_individual(symbol)
                hsgt_individual_detail = await self.fetch_hsgt_individual_detail(symbol)
                
                if not hsgt_individual.empty or not hsgt_individual_detail.empty:
                    results["hsgt_data"][f"individual_{symbol}"] = {
                        "basic": hsgt_individual,
                        "detail": hsgt_individual_detail
                    }
            
            # 5. 保存数据
            logger.info("5. 保存数据...")
            saved_paths = []
            
            # 保存所有类型的数据
            for data_type, data_dict in results.items():
                if isinstance(data_dict, dict) and data_dict:
                    for name, data in data_dict.items():
                        if isinstance(data, pd.DataFrame) and not data.empty:
                            path = await self.save_data(data, data_type, name)
                            if path:
                                saved_paths.append(path)
                elif isinstance(data_dict, pd.DataFrame) and not data_dict.empty:
                    path = await self.save_data(data_dict, data_type, "data")
                    if path:
                        saved_paths.append(path)
            
            # 6. 生成统计信息
            duration = time.time() - start_time
            success_stocks = sum(1 for data in stock_results.values() if data)
            total_stocks = len(symbols)
            
            results["summary"] = {
                "total_stocks": total_stocks,
                "success_stocks": success_stocks,
                "success_rate": (success_stocks / total_stocks * 100) if total_stocks > 0 else 0,
                "total_data_types": len([k for k, v in results.items() if isinstance(v, (dict, pd.DataFrame)) and v]),
                "saved_files": len(saved_paths),
                "duration": duration,
                "status": "success"
            }
            
            logger.info(f"所有类型港股数据收集完成！成功率: {results['summary']['success_rate']:.1f}%")
            logger.info(f"共保存 {len(saved_paths)} 个文件，耗时 {duration:.2f} 秒")
            
        except Exception as e:
            logger.error(f"所有类型港股数据收集失败: {e}")
            results["summary"] = {
                "status": "failed",
                "error": str(e),
                "duration": time.time() - start_time
            }
        
        return results


# ==================== 使用示例 ====================

async def main():
    """主函数示例"""
    # 港股代码示例
    hk_stocks = ["00700", "09988", "03690", "02318", "02020"]  # 腾讯、阿里巴巴、美团、中国平安、安踏
    hk_indexes = ["HSI", "HSCEI", "HSCCI"]  # 恒生指数、国企指数、红筹指数
    
    collector = EnhancedHKDataCollector()
    
    try:
        print("=== 港股数据收集器功能演示 ===")
        
        # 1. 基础数据收集
        print("\n1. 收集基础港股数据...")
        basic_results = await collector.collect_comprehensive_hk_data(
            symbols=hk_stocks,
            indexes=hk_indexes,
            include_sectors=True
        )
        
        # 2. 收集所有类型数据（新增功能）
        print("\n2. 收集所有类型港股数据...")
        all_results = await collector.collect_all_hk_data(hk_stocks)
        
        # 3. 单独测试新功能
        print("\n3. 测试新增功能...")
        
        # 公司资料
        print("   - 获取公司资料...")
        company_profile = await collector.fetch_company_profile("00700")
        if not company_profile.empty:
            print(f"     腾讯公司资料: {len(company_profile)} 条记录")
        
        # 盈利预测
        print("   - 获取盈利预测...")
        profit_forecast = await collector.fetch_profit_forecast("00700")
        if not profit_forecast.empty:
            print(f"     腾讯盈利预测: {len(profit_forecast)} 条记录")
        
        # 估值指标
        print("   - 获取估值指标...")
        valuation = await collector.fetch_valuation_indicators("00700")
        if not valuation.empty:
            print(f"     腾讯估值指标: {len(valuation)} 条记录")
        
        # 人气榜
        print("   - 获取人气榜...")
        hot_rank = await collector.fetch_hot_rank_data()
        if not hot_rank.empty:
            print(f"     港股人气榜: {len(hot_rank)} 条记录")
        
        # 知名港股
        print("   - 获取知名港股...")
        famous_stocks = await collector.fetch_famous_stocks()
        if not famous_stocks.empty:
            print(f"     知名港股: {len(famous_stocks)} 条记录")
        
        # 港股通成份股
        print("   - 获取港股通成份股...")
        ggt_components = await collector.fetch_ggt_components()
        if not ggt_components.empty:
            print(f"     港股通成份股: {len(ggt_components)} 条记录")
        
        # 沪深港通数据
        print("   - 获取沪深港通数据...")
        hsgt_hold = await collector.fetch_hsgt_hold_stock()
        if not hsgt_hold.empty:
            print(f"     沪深港通持股: {len(hsgt_hold)} 条记录")
        
        # 打印结果摘要
        print("\n=== 港股数据收集结果摘要 ===")
        print(f"基础数据收集状态: {basic_results['summary']['status']}")
        if basic_results['summary']['status'] == 'success':
            print(f"基础数据股票成功率: {basic_results['summary']['success_rate']:.1f}%")
            print(f"基础数据保存文件数: {basic_results['summary']['saved_files']}")
            print(f"基础数据总耗时: {basic_results['summary']['duration']:.2f} 秒")
        
        print(f"\n所有类型数据收集状态: {all_results['summary']['status']}")
        if all_results['summary']['status'] == 'success':
            print(f"所有类型数据股票成功率: {all_results['summary']['success_rate']:.1f}%")
            print(f"所有类型数据保存文件数: {all_results['summary']['saved_files']}")
            print(f"所有类型数据总耗时: {all_results['summary']['duration']:.2f} 秒")
        
    except Exception as e:
        logger.error(f"主程序执行失败: {e}")
    
    finally:
        await collector.close()


if __name__ == "__main__":
    asyncio.run(main())
