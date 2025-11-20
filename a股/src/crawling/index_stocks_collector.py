#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
成份股数据收集器
功能：收集东方财富的行业板块和概念板块成份股数据
作者：AI Assistant
创建时间：2025年
"""

import argparse
import os
import sys
import time
import asyncio
import pandas as pd
import akshare as ak
from pathlib import Path
from typing import Dict, List, Optional

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from config import config

# 数据保存路径（延迟初始化，避免在导入时创建目录）
def _get_index_stocks_dir():
    """获取指数股票目录（仅在需要时创建）"""
    dir_path = config.get_index_stocks_dir()
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path

def _get_concept_stocks_dir():
    """获取概念股票目录（仅在需要时创建）"""
    dir_path = config.get_concept_stocks_dir()
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path

def _get_industry_stocks_dir():
    """获取行业股票目录（仅在需要时创建）"""
    dir_path = config.get_industry_stocks_dir()
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


async def collect_industry_cons_stocks_async(symbol: str = "小金属", force: bool = False) -> Optional[pd.DataFrame]:
    """
    异步收集行业板块成份股数据
    
    Args:
        symbol: 板块名称或代码，如"小金属"或"BK1027"
        force: 是否强制重新收集，忽略已存在的文件
    
    Returns:
        成份股数据DataFrame
    """
    # 检查文件是否已存在
    filename = f"{symbol}.csv"
    filepath = _get_industry_stocks_dir() / filename
    
    if not force and filepath.exists():
        return pd.read_csv(filepath)
    
    start_time = time.time()
    
    try:
        # 调用东方财富接口获取行业板块成份股
        df = ak.stock_board_industry_cons_em(symbol=symbol)
        
        if df is None or df.empty:
            return None
        
        # 数据清洗
        df = df.dropna(how='all')  # 删除全空行
        df = df.reset_index(drop=True)  # 重置索引
        
        # 保存数据到行业目录
        df.to_csv(filepath, index=False, encoding='utf-8-sig')
        
        # 添加延迟避免请求过于频繁
        await asyncio.sleep(1)
        
        return df
        
    except Exception as e:
        return None


async def collect_concept_cons_stocks_async(symbol: str = "融资融券", force: bool = False) -> Optional[pd.DataFrame]:
    """
    异步收集概念板块成份股数据
    
    Args:
        symbol: 板块名称或代码，如"融资融券"或"BK0655"
        force: 是否强制重新收集，忽略已存在的文件
    
    Returns:
        成份股数据DataFrame
    """
    # 检查文件是否已存在
    filename = f"{symbol}.csv"
    filepath = _get_concept_stocks_dir() / filename
    
    if not force and filepath.exists():
        return pd.read_csv(filepath)
    
    start_time = time.time()
    
    try:
        # 调用东方财富接口获取概念板块成份股
        df = ak.stock_board_concept_cons_em(symbol=symbol)
        
        if df is None or df.empty:
            return None
        
        # 数据清洗
        df = df.dropna(how='all')  # 删除全空行
        df = df.reset_index(drop=True)  # 重置索引
        
        # 保存数据到概念目录
        df.to_csv(filepath, index=False, encoding='utf-8-sig')
        
        # 添加延迟避免请求过于频繁
        await asyncio.sleep(1)
        
        return df
        
    except Exception as e:
        return None


def get_industry_board_names() -> Optional[pd.DataFrame]:
    """
    获取所有行业板块名称和代码
    
    Returns:
        行业板块信息DataFrame
    """
    df = ak.stock_board_industry_name_em()
    
    if df is None or df.empty:
        return None
    
    # 保存行业板块名称列表
    filepath = _get_index_stocks_dir() / "industry_board_names.csv"
    df.to_csv(filepath, index=False, encoding='utf-8-sig')
    
    return df


def get_concept_board_names() -> Optional[pd.DataFrame]:
    """
    获取所有概念板块名称和代码
    
    Returns:
        概念板块信息DataFrame
    """
    df = ak.stock_board_concept_name_em()
    
    if df is None or df.empty:
        return None
    
    # 保存概念板块名称列表
    filepath = _get_index_stocks_dir() / "concept_board_names.csv"
    df.to_csv(filepath, index=False, encoding='utf-8-sig')
    
    return df




async def collect_index_stocks_batch_async(symbols: List[str], collection_type: str, max_concurrent: int = 3, force: bool = False) -> Dict[str, Dict[str, bool]]:
    """
    异步批量收集指数成份股数据
    
    Args:
        symbols: 板块名称列表
        collection_type: 收集类型 ("概念板块" 或 "行业板块")
        max_concurrent: 最大并发数
        force: 是否强制重新收集，忽略已存在的文件
    
    Returns:
        收集结果字典
    """
    # 创建信号量控制并发数
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def _collect_with_semaphore(symbol: str) -> tuple:
        """带信号量控制的单个板块收集"""
        async with semaphore:
            if collection_type == "概念板块" or collection_type == "concept":
                df = await collect_concept_cons_stocks_async(symbol, force=force)
            else:
                df = await collect_industry_cons_stocks_async(symbol, force=force)
            
            return symbol, {
                'success': df is not None and not df.empty
            }
    
    # 并发执行所有板块的数据收集
    tasks = [_collect_with_semaphore(symbol) for symbol in symbols]
    all_results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # 处理结果
    return {result[0]: result[1] for result in all_results if not isinstance(result, Exception)}




async def main_async():
    """异步主函数"""
    # 创建数据目录（仅在需要时）
    _get_index_stocks_dir()
    
    # 获取板块名称列表
    industry_names_df = get_industry_board_names()
    concept_names_df = get_concept_board_names()
    
    industry_symbols = industry_names_df['板块名称'].dropna().tolist()[:5] if industry_names_df is not None and not industry_names_df.empty else []
    concept_symbols = concept_names_df['板块名称'].dropna().tolist()[:5] if concept_names_df is not None and not concept_names_df.empty else []
    
    # 异步收集行业板块成份股数据
    industry_results = await collect_index_stocks_batch_async(industry_symbols, "行业板块", max_concurrent=3) if industry_symbols else {}
    
    # 异步收集概念板块成份股数据
    concept_results = await collect_index_stocks_batch_async(concept_symbols, "概念板块", max_concurrent=3) if concept_symbols else {}
    
    # 输出总结
    industry_success = sum(1 for result in industry_results.values() if result['success'])
    industry_total = len(industry_results)
    concept_success = sum(1 for result in concept_results.values() if result['success'])
    concept_total = len(concept_results)
    

def main():
    """主函数 - 支持命令行参数"""
    parser = argparse.ArgumentParser(
        description="指数成份股数据收集器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python src/crawling/index_stocks_collector.py "人工智能"
  python src/crawling/index_stocks_collector.py "人工智能,5G概念" --type concept
  python src/crawling/index_stocks_collector.py "半导体,银行" --type industry
  python src/crawling/index_stocks_collector.py "人工智能" --force
  python src/crawling/index_stocks_collector.py --all
        """
    )
    
    parser.add_argument(
        "symbols",
        nargs="?",
        help="要收集的板块名称，多个用逗号分隔，如：人工智能,5G概念"
    )
    
    parser.add_argument(
        "--type",
        choices=["concept", "industry"],
        default="concept",
        help="板块类型：concept(概念板块) 或 industry(行业板块)，默认为concept"
    )
    
    parser.add_argument(
        "--all",
        action="store_true",
        help="收集所有板块数据"
    )
    
    parser.add_argument(
        "--max-concurrent",
        type=int,
        default=3,
        help="最大并发数，默认为3"
    )
    
    parser.add_argument(
        "--force",
        action="store_true",
        help="强制重新收集所有数据，忽略已存在的文件"
    )
    
    args = parser.parse_args()
    
    # 如果没有提供任何参数，显示帮助信息
    if not args.symbols and not args.all:
        parser.print_help()
        return
    
    # 运行异步主函数
    asyncio.run(main_async_with_args(args))


async def main_async_with_args(args):
    """带参数的异步主函数"""
    if args.all:
        # 收集所有板块数据
        await main_async()
        return

    # 收集指定板块数据
    symbols = [s.strip() for s in args.symbols.split(',') if s.strip()]
    collection_type = args.type
    max_concurrent = args.max_concurrent
    
    # 调用批量收集函数
    results = await collect_index_stocks_batch_async(
        symbols=symbols,
        collection_type=collection_type,
        max_concurrent=max_concurrent,
        force=args.force
    )
    
    # 显示结果
    success_count = sum(1 for result in results.values() if result['success'])
    total_count = len(results)

    print(f"\n🎉 成份股数据收集完成！")
    print(f"成功: {success_count}/{total_count} 个板块")

    # 显示详细的收集结果
    for symbol, result in results.items():
        status = "✅ 成功" if result['success'] else "❌ 失败"
        print(f"  {symbol}: {status}")
        if not result['success'] and 'error' in result:
            print(f"    错误: {result['error']}")


if __name__ == "__main__":
    main()