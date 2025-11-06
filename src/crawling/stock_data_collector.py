#!/usr/bin/env python

"""
完全异步的股票数据收集器
与 unified_stock_collector.py 保持一致的9类数据爬取
"""

import asyncio
import sys
import warnings
from pathlib import Path
from typing import Dict, List

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from config import config

warnings.filterwarnings("ignore")

# 统一路径：直接使用配置提供的常量
DATA_ROOT = Path(config.data_dir)

try:
    import akshare as ak
except ImportError:
    print("请安装 akshare: pip install akshare")
    sys.exit(1)


class AsyncStockCollector:
    """完全异步的股票数据收集器，与 unified_stock_collector.py 保持一致"""

    def __init__(self, data_root_dir: str = None):
        """初始化异步收集器"""
        self.project_root = config.project_root

        # 基本配置设置
        self.request_delay = 1.0
        self.historical_start_date = "20210101"

        # 数据目录设置
        if data_root_dir is None:
            data_root_dir = DATA_ROOT  # 不要额外添加 /stocks
        self.data_root_dir = Path(data_root_dir)

        # 数据目录
        self.data_root_dir.mkdir(parents=True, exist_ok=True)

    def get_stock_prefix_em(self, code: str) -> str:
        """获取东方财富格式的股票代码"""
        if code.startswith("6"):
            return f"SH{code}"
        elif code.startswith("0") or code.startswith("3"):
            return f"SZ{code}"
        elif code.startswith("8") or code.startswith("4"):
            return f"BJ{code}"
        else:
            return code

    def _get_symbol_data_dir(self, symbol: str) -> Path:
        """返回某只股票的数据目录路径"""
        symbol_data_dir = self.data_root_dir / "stocks" / symbol
        symbol_data_dir.mkdir(parents=True, exist_ok=True)
        return symbol_data_dir

    def _is_file_exists(self, symbol: str, filename: str) -> bool:
        """检查数据文件是否存在"""
        file_path = self._get_symbol_data_dir(symbol) / filename
        return file_path.exists()

    async def _collect_financial_statements(self, symbol: str) -> bool:
        """异步收集财务报表数据 - 同花顺 (与 unified_stock_collector.py 保持一致)"""
        stock_dir = self._get_symbol_data_dir(symbol)
        reports_collected = 0

        # 1. 资产负债表 - 按报告期
        if not self._is_file_exists(symbol, "balance_sheet.csv"):
            balance_sheet_df = ak.stock_financial_debt_ths(
                symbol=symbol, indicator="按报告期"
            )
            if not balance_sheet_df.empty:
                balance_file = stock_dir / "balance_sheet.csv"
                balance_sheet_df.to_csv(
                    balance_file, index=False, encoding="utf-8-sig"
                )
                reports_collected += 1
        await asyncio.sleep(self.request_delay)

        # 2. 利润表 - 按报告期
        if not self._is_file_exists(symbol, "income_statement.csv"):
            income_df = ak.stock_financial_benefit_ths(
                symbol=symbol, indicator="按报告期"
            )
            if not income_df.empty:
                income_file = stock_dir / "income_statement.csv"
                income_df.to_csv(
                    income_file, index=False, encoding="utf-8-sig"
                )
                reports_collected += 1
        await asyncio.sleep(self.request_delay)

        # 3. 现金流量表 - 按报告期
        if not self._is_file_exists(symbol, "cash_flow_statement.csv"):
            cash_flow_df = ak.stock_financial_cash_ths(
                symbol=symbol, indicator="按报告期"
            )
            if not cash_flow_df.empty:
                cash_file = stock_dir / "cash_flow_statement.csv"
                cash_flow_df.to_csv(
                    cash_file, index=False, encoding="utf-8-sig"
                )
                reports_collected += 1
        await asyncio.sleep(self.request_delay)

        return reports_collected > 0

    async def _collect_main_business(self, symbol: str) -> bool:
        """异步收集主营业务构成数据 - 东方财富 (与 unified_stock_collector.py 保持一致)"""
        stock_dir = self._get_symbol_data_dir(symbol)

        # 需要转换股票代码格式为东方财富格式
        em_symbol = self.get_stock_prefix_em(symbol)

        # 获取主营业务构成 - 东方财富
        if self._is_file_exists(symbol, "main_business_composition.csv"):
            return True

        business_df = ak.stock_zygc_em(symbol=em_symbol)

        if business_df.empty:
            return False

        business_file = stock_dir / "main_business_composition.csv"
        business_df.to_csv(business_file, index=False, encoding="utf-8-sig")

        await asyncio.sleep(self.request_delay)
        return True

    async def _collect_financial_indicators(self, symbol: str) -> bool:
        """异步收集详细财务指标 - 同花顺 (与 unified_stock_collector.py 保持一致)"""
        stock_dir = self._get_symbol_data_dir(symbol)

        if self._is_file_exists(symbol, "financial_indicators.csv"):
            return True

        # 获取财务指标 - 使用同花顺接口
        indicators_df = ak.stock_financial_abstract_ths(
            symbol=symbol, indicator="按报告期"
        )

        if indicators_df.empty:
            return False

        indicators_file = stock_dir / "financial_indicators.csv"
        indicators_df.to_csv(indicators_file, index=False, encoding="utf-8-sig")

        await asyncio.sleep(self.request_delay)
        return True

    async def _collect_stock_valuation(self, symbol: str) -> bool:
        """异步收集个股估值数据 (与 unified_stock_collector.py 保持一致)"""
        stock_dir = self._get_symbol_data_dir(symbol)

        # 获取个股估值
        valuation_df = ak.stock_value_em(symbol=symbol)

        if valuation_df.empty:
            return False

        valuation_file = stock_dir / "stock_valuation.csv"
        valuation_df.to_csv(valuation_file, index=False, encoding="utf-8-sig")

        await asyncio.sleep(self.request_delay)
        return True

    async def _collect_news_data(self, symbol: str) -> bool:
        """异步收集新闻数据 (与 unified_stock_collector.py 保持一致)"""
        stock_dir = self._get_symbol_data_dir(symbol)

        # 获取新闻数据
        news_df = ak.stock_news_em(symbol=symbol)

        if news_df.empty:
            return False

        news_file = stock_dir / "news_data.csv"
        news_df.to_csv(news_file, index=False, encoding="utf-8-sig")

        await asyncio.sleep(self.request_delay)
        return True

    async def _collect_historical_quotes(self, symbol: str) -> bool:
        """异步收集历史行情数据 - 东方财富 (与 unified_stock_collector.py 保持一致)"""
        stock_dir = self._get_symbol_data_dir(symbol)

        # 历史行情数据 - 东方财富 (为技术指标计算提供足够历史数据)
        from datetime import datetime

        end_date = datetime.now().strftime("%Y%m%d")

        # 使用不复权数据 - 获取真实价格（重要：技术指标计算需要真实价格）
        # adjust="" 表示不复权，"qfq"为前复权，"hfq"为后复权
        # 不复权数据能准确反映历史真实价格，便于技术指标计算
        historical_df = ak.stock_zh_a_hist(
            symbol=symbol,
            period="daily",
            start_date=self.historical_start_date,
            end_date=end_date,
            adjust="",
        )
        if historical_df.empty:
            return False

        file_path = stock_dir / "historical_quotes.csv"
        historical_df.to_csv(file_path, index=False, encoding="utf-8-sig")
        await asyncio.sleep(self.request_delay)
        return True

    async def _collect_intraday_data(self, symbol: str) -> bool:
        """异步收集分时数据 - 东方财富 (与 unified_stock_collector.py 保持一致)"""
        stock_dir = self._get_symbol_data_dir(symbol)

        # 获取分时数据 - 使用5分钟K线数据，支持复权
        from datetime import datetime, timedelta

        # 获取最近5个交易日的数据
        end_date = datetime.now()
        start_date = end_date - timedelta(days=10)  # 多取几天确保有5个交易日

        start_date_str = start_date.strftime("%Y-%m-%d 09:30:00")
        end_date_str = end_date.strftime("%Y-%m-%d 15:00:00")

        # 使用5分钟数据，不复权（与日线数据保持一致）
        # adjust="" 表示不复权，确保分时数据与日线数据的复权方式一致
        intraday_df = ak.stock_zh_a_hist_min_em(
            symbol=symbol,
            start_date=start_date_str,
            end_date=end_date_str,
            period="5",
            adjust="",
        )

        if intraday_df.empty:
            return False

        intraday_file = stock_dir / "intraday_data.csv"
        intraday_df.to_csv(intraday_file, index=False, encoding="utf-8-sig")

        await asyncio.sleep(self.request_delay)
        return True

    async def _collect_company_profile_cninfo(self, symbol: str) -> bool:
        """异步收集公司概况数据 - 巨潮资讯 (与 unified_stock_collector.py 保持一致)"""
        stock_dir = self._get_symbol_data_dir(symbol)

        # 文件存在性检查
        if self._is_file_exists(symbol, "company_profile.csv"):
            return True

        # 使用巨潮资讯的公司概况接口
        profile_df = ak.stock_profile_cninfo(symbol=symbol)

        if profile_df.empty:
            return False

        # 保存为 company_profile.csv，因为其格式更接近原始版本
        file_path = stock_dir / "company_profile.csv"
        profile_df.to_csv(file_path, index=False, encoding="utf-8-sig")
        await asyncio.sleep(self.request_delay)
        return True

    async def _collect_bid_ask(self, symbol: str) -> bool:
        """异步采集东方财富盘口行情（买卖五档、最新价、涨跌幅等）"""
        stock_dir = self._get_symbol_data_dir(symbol)
        df = ak.stock_bid_ask_em(symbol=symbol)

        if df.empty:
            return False

        df.to_csv(stock_dir / "bid_ask.csv", index=False, encoding="utf-8-sig")
        await asyncio.sleep(self.request_delay)
        return True

    async def _collect_peer_comparison(self, symbol: str) -> bool:
        """异步收集同行比较数据 - 东方财富"""
        # 转换股票代码格式 (例如: 000895 -> SZ000895)
        if symbol.startswith('0') or symbol.startswith('3'):
            ak_symbol = f"SZ{symbol}"
        else:
            ak_symbol = f"SH{symbol}"
        
        # 1. 成长性比较
        growth_df = ak.stock_zh_growth_comparison_em(symbol=ak_symbol)
        if not growth_df.empty:
            stock_dir = self._get_symbol_data_dir(symbol)
            growth_path = stock_dir / "peer_growth_comparison.csv"
            growth_path.parent.mkdir(parents=True, exist_ok=True)
            growth_df.to_csv(growth_path, index=False, encoding='utf-8-sig')

        # 2. 估值比较
        valuation_df = ak.stock_zh_valuation_comparison_em(symbol=ak_symbol)
        if not valuation_df.empty:
            stock_dir = self._get_symbol_data_dir(symbol)
            valuation_path = stock_dir / "peer_valuation_comparison.csv"
            valuation_path.parent.mkdir(parents=True, exist_ok=True)
            valuation_df.to_csv(valuation_path, index=False, encoding='utf-8-sig')

        # 3. 杜邦分析比较
        dupont_df = ak.stock_zh_dupont_comparison_em(symbol=ak_symbol)
        if not dupont_df.empty:
            stock_dir = self._get_symbol_data_dir(symbol)
            dupont_path = stock_dir / "peer_dupont_comparison.csv"
            dupont_path.parent.mkdir(parents=True, exist_ok=True)
            dupont_df.to_csv(dupont_path, index=False, encoding='utf-8-sig')

        # 4. 公司规模比较
        scale_df = ak.stock_zh_scale_comparison_em(symbol=ak_symbol)
        if not scale_df.empty:
            stock_dir = self._get_symbol_data_dir(symbol)
            scale_path = stock_dir / "peer_scale_comparison.csv"
            scale_path.parent.mkdir(parents=True, exist_ok=True)
            scale_df.to_csv(scale_path, index=False, encoding='utf-8-sig')
        
        return True

    async def collect_all_stock_data(self, symbol: str) -> Dict[str, bool]:
        """异步收集单个股票的所有数据 (10类数据，包含同行比较)"""
        results = {}

        # 1. 财务报表 (同花顺)
        results["财务报表"] = await self._collect_financial_statements(symbol)

        # 2. 主营业务构成 (东方财富)
        results["主营构成"] = await self._collect_main_business(symbol)

        # 3. 财务指标详细
        results["财务指标"] = await self._collect_financial_indicators(symbol)

        # 4. 个股估值
        results["个股估值"] = await self._collect_stock_valuation(symbol)

        # 5. 新闻数据
        results["新闻数据"] = await self._collect_news_data(symbol)

        # 6. 历史行情数据 (用于技术指标计算)
        results["历史行情"] = await self._collect_historical_quotes(symbol)

        # 7. 分时数据
        results["分时数据"] = await self._collect_intraday_data(symbol)

        # 8. 公司概况数据 (巨潮资讯)
        results["公司概况"] = await self._collect_company_profile_cninfo(symbol)

        # 9. 盘口行情数据 (东方财富)
        results["盘口行情"] = await self._collect_bid_ask(symbol)

        # 10. 同行比较数据 (东方财富)
        results["同行比较"] = await self._collect_peer_comparison(symbol)

        return results

    async def collect_batch_stocks(self, symbols: List[str], max_concurrent: int = 5) -> Dict[str, Dict[str, bool]]:
        """异步批量收集多个股票的数据"""
        # 创建信号量控制并发数
        semaphore = asyncio.Semaphore(max_concurrent)

        async def _collect_with_semaphore(symbol: str) -> tuple:
            """带信号量控制的单个股票收集"""
            async with semaphore:
                results = await self.collect_all_stock_data(symbol)
                return symbol, results

        # 并发执行所有股票的数据收集
        tasks = [_collect_with_semaphore(symbol) for symbol in symbols]
        all_results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理结果
        return {result[0]: result[1] for result in all_results if not isinstance(result, Exception)}



async def main():
    """主函数 - 异步数据收集入口"""
    import argparse

    parser = argparse.ArgumentParser(description="异步股票数据收集工具")
    parser.add_argument("--symbols", nargs="*", help="要收集的股票代码")
    parser.add_argument("--concurrent", type=int, default=5, help="最大并发数")

    args = parser.parse_args()

    # 初始化异步收集器
    collector = AsyncStockCollector()

    # 确定要收集的股票列表
    if not args.symbols:
        print("请指定股票代码")
        return

    results = await collector.collect_batch_stocks(args.symbols, args.concurrent)

    # 显示结果摘要
    if not results:
        print("没有收集到任何数据")
        return

    print("数据收集完成!")
    for symbol, symbol_results in results.items():
        success_count = sum(1 for success in symbol_results.values() if success)
        total_count = len(symbol_results)
        success_rate = success_count / total_count * 100 if total_count > 0 else 0
        print(f"股票 {symbol}: {success_count}/{total_count} ({success_rate:.1f}%)")


if __name__ == "__main__":
    asyncio.run(main())