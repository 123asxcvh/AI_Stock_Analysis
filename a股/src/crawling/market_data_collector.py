#!/usr/bin/env python

"""
异步市场数据收集器
- 使用异步方式收集市场数据
- 检查文件存在性，避免重复收集
- 参考 stock_data_collector.py 的异步模式
"""

import asyncio
import sys
import warnings
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List
import pandas as pd

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from config import config
warnings.filterwarnings("ignore")


import akshare as ak


class AsyncMarketDataCollector:
    """异步市场数据收集器"""

    def __init__(self, data_root_dir: str = None):
        """初始化异步收集器"""
        self.project_root = config.project_root
        
        # 基本配置设置
        self.request_delay = 1.0
        
        # 数据目录设置
        if data_root_dir is None:
            data_root_dir = config.market_data_dir
        self.data_root_dir = Path(data_root_dir)
        
        # 数据目录
        self.data_root_dir.mkdir(parents=True, exist_ok=True)
        

    def _is_file_exists(self, filename: str) -> bool:
        """检查数据文件是否存在"""
        file_path = self.data_root_dir / filename
        return file_path.exists()

    def _save_data(self, df: pd.DataFrame, filename: str) -> bool:
        """保存数据到文件"""
        if df is None or df.empty:
            return False
        
        file_path = self.data_root_dir / filename
        df.to_csv(file_path, index=False, encoding="utf-8-sig")
        return True

    async def _collect_sector_fund_flow(self) -> bool:
        """异步收集板块资金流"""
        # 注释：板块资金流数据收集网络连接不稳定，暂时注释
        return True
        # if self._is_file_exists("sector_fund_flow.csv"):
        #     return True
        #
        # df = ak.stock_sector_fund_flow_rank(indicator="今日")
        # return self._save_data(df, "sector_fund_flow.csv")

    async def _collect_fund_flow_industry(self) -> bool:
        if self._is_file_exists("fund_flow_industry.csv"):
            return True

        df = ak.stock_fund_flow_industry(symbol="3日排行")
        return self._save_data(df, "fund_flow_industry.csv")

    async def _collect_fund_flow_concept(self) -> bool:
        """异步收集概念资金流数据"""
        if self._is_file_exists("fund_flow_concept.csv"):
            return True

        df = ak.stock_fund_flow_concept(symbol="3日排行")
        await asyncio.sleep(self.request_delay)
        return self._save_data(df, "fund_flow_concept.csv")

    async def _collect_fund_flow_individual(self) -> bool:
        """异步收集个股资金流数据"""
        if self._is_file_exists("fund_flow_individual.csv"):
            return True

        df = ak.stock_fund_flow_individual(symbol="3日排行")
        await asyncio.sleep(self.request_delay)
        return self._save_data(df, "fund_flow_individual.csv")

    async def _collect_zt_pool(self) -> bool:
        """异步收集涨停股池数据"""
        if self._is_file_exists("zt_pool.csv"):
            return True
        
        df = ak.stock_zt_pool_em(date=datetime.now().strftime("%Y%m%d"))
        await asyncio.sleep(self.request_delay)
        return self._save_data(df, "zt_pool.csv")

    async def _collect_lhb_detail(self) -> bool:
        """异步收集龙虎榜详情数据"""
        if self._is_file_exists("lhb_detail.csv"):
            return True
        
        # 获取最近15天的龙虎榜数据
        end_date = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=15)).strftime("%Y%m%d")
        df = ak.stock_lhb_detail_em(start_date=start_date, end_date=end_date)
        await asyncio.sleep(self.request_delay)
        return self._save_data(df, "lhb_detail.csv")

    async def _collect_realtime_quotes(self) -> bool:
        """异步收集实时行情数据"""
        # 注释：实时行情数据收集网络连接不稳定，暂时注释
        return True
        # if self._is_file_exists("realtime_quotes.csv"):
        #     return True
        #
        # df = ak.stock_zh_a_spot_em()
        # await asyncio.sleep(self.request_delay)
        # return self._save_data(df, "realtime_quotes.csv")

    async def _collect_stock_hot_follow_xq(self) -> bool:
        """异步收集股票热度-雪球关注排行榜数据"""
        # 注释：雪球热度数据已存在，无需重复爬取
        return True
        # if self._is_file_exists("stock_hot_follow_xq.csv"):
        #     return True
        #
        # # 采集"最热门"关注排行榜
        # df = ak.stock_hot_follow_xq(symbol="最热门")
        # await asyncio.sleep(self.request_delay)
        # return self._save_data(df, "stock_hot_follow_xq.csv")

    async def _collect_index_daily_tx(self, symbol: str) -> bool:
        """异步收集指数日线数据"""
        # 注释：指数数据已存在，无需重复爬取
        return True
        # filename = f"index_{symbol.lower()}.csv"
        # if self._is_file_exists(filename):
        #     return True
        #
        # df = ak.stock_zh_index_daily_tx(symbol=symbol)
        # await asyncio.sleep(self.request_delay)
        # return self._save_data(df, filename)

    async def _collect_market_activity_legu(self) -> bool:
        """异步收集乐股市场活跃度数据"""
        if self._is_file_exists("market_activity_legu.csv"):
            return True

        try:
            df = ak.stock_market_activity_legu()

            if df is None or df.empty:
                return False

            # 数据清洗和重命名
            df = df.dropna(how='all')  # 删除全空行
            df = df.reset_index(drop=True)  # 重置索引

            # 重命名列名为中文
            column_mapping = {
                'item': '指标',
                'value': '数值'
            }
            df = df.rename(columns=column_mapping)

            # 保存数据
            self._save_data(df, "market_activity_legu.csv")
            return True

        except Exception as e:
            print(f"⚠️ 乐股市场活跃度数据收集失败: {str(e)[:50]}")
            return False

    async def _collect_news_main_cx(self) -> bool:
        """异步收集财联社主要新闻数据"""
        if self._is_file_exists("news_main_cx.csv"):
            return True

        try:
            df = ak.stock_news_main_cx()

            if df is None or df.empty:
                return False

            # 数据清洗和重命名
            df = df.dropna(how='all')  # 删除全空行
            df = df.reset_index(drop=True)  # 重置索引

            # 重命名列名为中文
            column_mapping = {
                'tag': '标签',
                'summary': '摘要',
                'interval_time': '时间间隔',
                'pub_time': '发布时间',
                'url': '链接'
            }
            df = df.rename(columns=column_mapping)

            # 保存数据
            self._save_data(df, "news_main_cx.csv")
            return True

        except Exception as e:
            print(f"⚠️ 财联社主要新闻数据收集失败: {str(e)[:50]}")
            return False

    async def collect_all_market_data(self, indices: List[str] = None, max_concurrent: int = 3) -> Dict[str, bool]:
        """异步收集所有市场数据（并发执行，限流）"""
        semaphore = asyncio.Semaphore(max_concurrent)

        async def run_task(name: str, coro) -> tuple:
            async with semaphore:
                result = await coro
                return name, bool(result)

        # 定义所有收集任务
        coroutines = [
            ("sector_fund_flow", self._collect_sector_fund_flow()),
            ("fund_flow_industry", self._collect_fund_flow_industry()),
            ("fund_flow_concept", self._collect_fund_flow_concept()),
            ("fund_flow_individual", self._collect_fund_flow_individual()),
            ("zt_pool", self._collect_zt_pool()),
            ("lhb_detail", self._collect_lhb_detail()),
            ("realtime_quotes", self._collect_realtime_quotes()),
            ("stock_hot_follow_xq", self._collect_stock_hot_follow_xq()),
            ("market_activity_legu", self._collect_market_activity_legu()),
            ("news_main_cx", self._collect_news_main_cx()),
        ]
        coroutines.extend([(f"index_{symbol}", self._collect_index_daily_tx(symbol)) for symbol in indices or []])

        # 并发执行
        tasks = [run_task(name, coro) for name, coro in coroutines]
        results_list = await asyncio.gather(*tasks, return_exceptions=False)

        # 汇总结果
        results: Dict[str, bool] = {}
        for name, ok in results_list:
            results[name] = ok
        return results

    async def collect_batch_indices(self, indices: List[str], max_concurrent: int = 3) -> Dict[str, bool]:
        """异步批量收集指数数据"""
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def _collect_with_semaphore(symbol: str) -> tuple:
            async with semaphore:
                return symbol, await self._collect_index_daily_tx(symbol)
        
        # 创建所有任务
        tasks = [_collect_with_semaphore(symbol) for symbol in indices]
        
        # 并发执行
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理结果
        return {result[0]: result[1] for result in results if not isinstance(result, Exception)}


async def main():
    """主函数 - 异步市场数据收集入口"""
    import argparse

    parser = argparse.ArgumentParser(description="异步市场数据收集工具")
    parser.add_argument(
        "--indices",
        type=str,
        help="逗号分隔的指数代码列表，如 sh000001,sz399001,sh000300",
    )
    parser.add_argument("--concurrent", type=int, default=3, help="最大并发数")

    args = parser.parse_args()

    # 初始化异步收集器
    collector = AsyncMarketDataCollector()

    # 处理指数参数
    indices = [s.strip() for s in args.indices.split(",") if s.strip()] if args.indices else []

    # 收集所有市场数据
    results = await collector.collect_all_market_data(indices)
    print("市场数据收集完成!")
    for name, success in results.items():
        status = "✅ 成功" if success else "❌ 失败"
        print(f"  {name}: {status}")


if __name__ == "__main__":
    asyncio.run(main())
