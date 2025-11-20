#!/usr/bin/env python

"""
完全异步的股票数据收集器
与 unified_stock_collector.py 保持一致的9类数据爬取
"""

import asyncio
import sys
import warnings
import os
import time
import random
from pathlib import Path
from typing import Dict, List

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from config import config

# 统一路径：直接使用配置提供的常量
DATA_ROOT = Path(config.data_dir)

import akshare as ak
import pandas as pd
import efinance



class AsyncStockCollector:
    """完全异步的股票数据收集器，与 unified_stock_collector.py 保持一致"""

    def __init__(self, data_root_dir: str = None):
        """初始化异步收集器"""
        self.project_root = config.project_root

        # 基本配置设置
        self.request_delay = 1.0
        self.historical_start_date = "20210101"

        # 随机延迟配置（秒）
        self.min_delay = 0.5
        self.max_delay = 2.0

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

    async def _random_delay(self, extra_delay: float = 0):
        """随机延迟方法"""
        delay = random.uniform(self.min_delay, self.max_delay) + extra_delay
        await asyncio.sleep(delay)

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
        await self._random_delay()

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
        await self._random_delay()

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
        await self._random_delay()

        return reports_collected > 0

    async def _collect_main_business(self, symbol: str) -> bool:
        """异步收集主营业务构成数据 - 东方财富 (与 unified_stock_collector.py 保持一致)"""
        stock_dir = self._get_symbol_data_dir(symbol)

        try:
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

            await self._random_delay()
            return True
        except Exception as e:
            print(f"⚠️ 主营业务数据收集失败 {symbol}: {str(e)[:50]}")
            return False

    async def _collect_financial_indicators(self, symbol: str) -> bool:
        """异步收集详细财务指标 - 同花顺 (与 unified_stock_collector.py 保持一致)"""
        stock_dir = self._get_symbol_data_dir(symbol)

        try:
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

            await self._random_delay()
            return True
        except Exception as e:
            print(f"⚠️ 财务指标数据收集失败 {symbol}: {str(e)[:50]}")
            return False

    async def _collect_stock_valuation(self, symbol: str) -> bool:
        """异步收集个股估值数据 - 东方财富 (与 unified_stock_collector.py 保持一致)"""
        stock_dir = self._get_symbol_data_dir(symbol)

        try:
            # 获取个股估值 - 东方财富接口
            valuation_df = ak.stock_value_em(symbol=symbol)

            if valuation_df.empty:
                return False

            valuation_file = stock_dir / "stock_valuation.csv"
            valuation_df.to_csv(valuation_file, index=False, encoding="utf-8-sig")

            await self._random_delay()
            return True
        except Exception as e:
            print(f"⚠️ 个股估值数据收集失败 {symbol}: {str(e)[:50]}")
            return False

    
    async def _collect_historical_quotes(self, symbol: str) -> bool:
        """异步收集历史行情数据 - 东方财富优化版 (与 unified_stock_collector.py 保持一致)"""
        stock_dir = self._get_symbol_data_dir(symbol)

        # 历史行情数据 - 东方财富 (为技术指标计算提供足够历史数据)
        from datetime import datetime

        end_date = datetime.now().strftime("%Y%m%d")

        # 设置akshare优化参数
        try:
            ak.set_option('request_interval', 0.5)  # 设置请求间隔为0.5秒
        except:
            pass  # 如果akshare版本不支持，忽略错误

        try:
            # 直接使用腾讯接口获取历史行情数据
            if symbol.startswith('6'):
                tx_symbol = f"sh{symbol}"
            else:
                tx_symbol = f"sz{symbol}"

            historical_df = ak.stock_zh_a_hist_tx(
                symbol=tx_symbol,
                start_date=self.historical_start_date,
                end_date=end_date,
                adjust=""
            )
            print(f"✅ 腾讯接口成功获取历史数据")
        except Exception as e:
            print(f"⚠️ 历史行情数据收集失败 {symbol}: {str(e)[:50]}")
            return False
        if historical_df.empty:
            return False

        file_path = stock_dir / "historical_quotes.csv"

        # 转换列名格式，适配backtesting系统
        column_mapping = {
            'date': '日期',
            'open': '开盘',
            'high': '最高',
            'low': '最低',
            'close': '收盘',
            'amount': '成交量'
        }

        # 重命名列名
        historical_df = historical_df.rename(columns=column_mapping)

        # 确保日期格式正确
        if '日期' in historical_df.columns:
            historical_df['日期'] = pd.to_datetime(historical_df['日期']).dt.strftime('%Y-%m-%d')

        historical_df.to_csv(file_path, index=False, encoding="utf-8-sig")
        await self._random_delay()
        return True

    async def _collect_intraday_data(self, symbol: str) -> bool:
        """异步收集分时数据 - 参考try.py使用baostock接口（仅当天数据）"""
        stock_dir = self._get_symbol_data_dir(symbol)

        try:
            import baostock as bs
            from datetime import datetime, timedelta
            import pandas as pd

            # 计算当天的日期范围
            end_date = datetime.now()
            start_date = end_date  # 当天开始
            start_date_str = start_date.strftime("%Y-%m-%d")
            end_date_str = end_date.strftime("%Y-%m-%d")

            # 登陆baostock系统
            lg = bs.login()
            if lg.error_code != '0':
                print(f"⚠️ baostock登录失败: {lg.error_msg}")
                return False

            # 根据symbol构建baostock格式的代码
            if symbol.startswith('6'):
                baostock_symbol = f"sh.{symbol}"
            else:
                baostock_symbol = f"sz.{symbol}"

            # 获取5分钟K线数据（最近7天）
            rs = bs.query_history_k_data_plus(
                baostock_symbol,
                "date,time,code,open,high,low,close,volume,amount,adjustflag",
                start_date=start_date_str,
                end_date=end_date_str,
                frequency="5",
                adjustflag="3"
            )

            if rs.error_code != '0':
                print(f"⚠️ baostock数据获取失败: {rs.error_msg}")
                bs.logout()
                return False

            # 获取数据
            data_list = []
            while (rs.error_code == '0') & rs.next():
                data_list.append(rs.get_row_data())

            # 登出系统
            bs.logout()

            if not data_list:
                print(f"⚠️ {symbol} 分时数据为空")
                return False

            # 转换为DataFrame
            intraday_df = pd.DataFrame(data_list, columns=rs.fields)

            if intraday_df.empty:
                return False

            intraday_file = stock_dir / "intraday_data.csv"
            intraday_df.to_csv(intraday_file, index=False, encoding="utf-8-sig")

            await self._random_delay()
            return True
        except Exception as e:
            print(f"⚠️ 分时数据收集失败 {symbol}: {str(e)[:50]}")
            return False

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
        await self._random_delay()
        return True

    async def _collect_bid_ask(self, symbol: str) -> bool:
        """异步采集东方财富盘口行情（买卖五档、最新价、涨跌幅等）"""
        stock_dir = self._get_symbol_data_dir(symbol)

        try:
            df = ak.stock_bid_ask_em(symbol=symbol)

            if df.empty:
                return False

            df.to_csv(stock_dir / "bid_ask.csv", index=False, encoding="utf-8-sig")
            await self._random_delay()
            return True
        except Exception as e:
            print(f"⚠️ 盘口行情数据收集失败 {symbol}: {str(e)[:50]}")
            return False

    async def _collect_peer_comparison(self, symbol: str) -> bool:
        """异步收集同行比较数据 - 东方财富"""
        try:
            # 转换股票代码格式 (例如: 000895 -> SZ000895)
            if symbol.startswith('0') or symbol.startswith('3'):
                ak_symbol = f"SZ{symbol}"
            else:
                ak_symbol = f"SH{symbol}"

            success_count = 0

            # 1. 成长性比较
            try:
                growth_df = ak.stock_zh_growth_comparison_em(symbol=ak_symbol)
                if not growth_df.empty:
                    stock_dir = self._get_symbol_data_dir(symbol)
                    growth_path = stock_dir / "peer_growth_comparison.csv"
                    growth_path.parent.mkdir(parents=True, exist_ok=True)
                    growth_df.to_csv(growth_path, index=False, encoding='utf-8-sig')
                    success_count += 1
                await self._random_delay(0.2)  # 每个子接口之间也加小延迟
            except Exception as e:
                print(f"⚠️ 成长性比较数据收集失败 {symbol}: {str(e)[:50]}")

            # 2. 估值比较
            try:
                valuation_df = ak.stock_zh_valuation_comparison_em(symbol=ak_symbol)
                if not valuation_df.empty:
                    stock_dir = self._get_symbol_data_dir(symbol)
                    valuation_path = stock_dir / "peer_valuation_comparison.csv"
                    valuation_path.parent.mkdir(parents=True, exist_ok=True)
                    valuation_df.to_csv(valuation_path, index=False, encoding='utf-8-sig')
                    success_count += 1
                await self._random_delay(0.2)
            except Exception as e:
                print(f"⚠️ 估值比较数据收集失败 {symbol}: {str(e)[:50]}")

            # 3. 杜邦分析比较
            try:
                dupont_df = ak.stock_zh_dupont_comparison_em(symbol=ak_symbol)
                if not dupont_df.empty:
                    stock_dir = self._get_symbol_data_dir(symbol)
                    dupont_path = stock_dir / "peer_dupont_comparison.csv"
                    dupont_path.parent.mkdir(parents=True, exist_ok=True)
                    dupont_df.to_csv(dupont_path, index=False, encoding='utf-8-sig')
                    success_count += 1
                await self._random_delay(0.2)
            except Exception as e:
                print(f"⚠️ 杜邦分析比较数据收集失败 {symbol}: {str(e)[:50]}")

            # 4. 公司规模比较
            try:
                scale_df = ak.stock_zh_scale_comparison_em(symbol=ak_symbol)
                if not scale_df.empty:
                    stock_dir = self._get_symbol_data_dir(symbol)
                    scale_path = stock_dir / "peer_scale_comparison.csv"
                    scale_path.parent.mkdir(parents=True, exist_ok=True)
                    scale_df.to_csv(scale_path, index=False, encoding='utf-8-sig')
                    success_count += 1
                await self._random_delay(0.2)
            except Exception as e:
                print(f"⚠️ 公司规模比较数据收集失败 {symbol}: {str(e)[:50]}")

            return success_count > 0  # 至少成功一个就算成功
        except Exception as e:
            print(f"⚠️ 同行比较数据收集总体失败 {symbol}: {str(e)[:50]}")
            return False

    async def _collect_stock_belong_boards(self, symbol: str) -> bool:
        """异步收集股票所属版块数据 - efinance"""
        stock_dir = self._get_symbol_data_dir(symbol)

        try:
            # 检查文件是否已存在
            if self._is_file_exists(symbol, "stock_belong_boards.csv"):
                return True

            # 使用efinance获取股票所属版块
            belong_boards_df = efinance.stock.get_belong_board(symbol)

            if belong_boards_df is None or belong_boards_df.empty:
                return False

            # 数据清洗和处理
            belong_boards_df = belong_boards_df.dropna(how='all')  # 删除全空行
            belong_boards_df = belong_boards_df.reset_index(drop=True)  # 重置索引

            # 保存数据
            belong_boards_file = stock_dir / "stock_belong_boards.csv"
            belong_boards_df.to_csv(belong_boards_file, index=False, encoding="utf-8-sig")

            await self._random_delay()
            return True
        except Exception as e:
            print(f"⚠️ 股票所属版块数据收集失败 {symbol}: {str(e)[:50]}")
            return False

    async def collect_all_stock_data(self, symbol: str) -> Dict[str, bool]:
        """异步收集单个股票的所有数据 (11类数据，包含所属版块)"""
        results = {}

        # 1. 财务报表 (同花顺)
        results["财务报表"] = await self._collect_financial_statements(symbol)

        # 2. 主营业务构成 (东方财富)
        results["主营构成"] = await self._collect_main_business(symbol)

        # 3. 财务指标详细
        results["财务指标"] = await self._collect_financial_indicators(symbol)

        # 4. 个股估值
        results["个股估值"] = await self._collect_stock_valuation(symbol)

        
        # 5. 历史行情数据 (用于技术指标计算)
        results["历史行情"] = await self._collect_historical_quotes(symbol)

        # 6. 分时数据
        results["分时数据"] = await self._collect_intraday_data(symbol)

        # 7. 公司概况数据 (巨潮资讯)
        results["公司概况"] = await self._collect_company_profile_cninfo(symbol)

        # 8. 盘口行情数据 (东方财富)
        results["盘口行情"] = await self._collect_bid_ask(symbol)

        # 9. 同行比较数据 (东方财富)
        results["同行比较"] = await self._collect_peer_comparison(symbol)

        # 10. 所属版块数据 (efinance)
        results["所属版块"] = await self._collect_stock_belong_boards(symbol)

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