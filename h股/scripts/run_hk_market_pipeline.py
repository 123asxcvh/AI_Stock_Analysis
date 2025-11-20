#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path
import os


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def ensure_sys_path() -> None:
    root = project_root()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))


async def main_async(
    include_spot_sina: bool,
    include_spot_em: bool,
    include_main_board: bool,
    include_ggt_components: bool,
    include_index_spot_sina: bool,
    include_index_spot_em: bool,
    include_hot_rank: bool,
    include_famous: bool,
    include_index_daily_em: bool,
) -> None:
    from src.data.crawling.hk_data_collector import HKDataCollector
    from src.data.cleaning.hk_market_cleaner import clean_market_folder

    base_data_dir = str(project_root() / "data")
    collector = HKDataCollector(data_root_dir=base_data_dir)

    # 全市场实时（Sina）
    if include_spot_sina:
        spot_sina = await collector.fetch_spot_sina_all()
        await collector.save_df("market", "spot_sina_all", spot_sina)

    # 全市场实时（Eastmoney）
    if include_spot_em:
        spot_em = await collector.fetch_spot_em_all()
        await collector.save_df("market", "spot_em_all", spot_em)

    # 主板实时与港股通成份：按需求禁用（不再抓取）

    # 指数现货：按需求禁用（不再抓取）

    # 热度榜（Eastmoney）
    if include_hot_rank:
        hot_rank = await collector.fetch_hot_rank_em_all()
        await collector.save_df("market", "hot_rank_em", hot_rank)

    # 知名港股（Eastmoney）
    if include_famous:
        fam = await collector.fetch_famous_spot_em_all()
        await collector.save_df("market", "famous_spot_em_all", fam)

    # 指数日线（Eastmoney，仅恒生指数）
    if include_index_daily_em:
        default_idx = ["HSI"]
        for sym in default_idx:
            try:
                df = await collector.fetch_index_daily_em(sym)
                await collector.save_df("market", f"index_daily_em_{sym}", df)
            except Exception:
                pass

    # 市场数据清洗
    base_data_dir = str(project_root() / "data")
    market_dir = os.path.join(base_data_dir, "market")
    try:
        outputs = clean_market_folder(market_dir)
        print(f"Cleaned market files: {len(outputs)}")
    except Exception as e:
        print(f"Market clean failed: {e}")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="HK market data pipeline (crawl + clean)")
    p.add_argument("--all", action="store_true", help="采集所有市场级数据（默认）")
    p.add_argument("--spot-sina", action="store_true", help="全市场实时(Sina)")
    p.add_argument("--spot-em", action="store_true", help="全市场实时(EM)")
    # 移除主板实时、港股通成份、指数现货的开关
    p.add_argument("--hot-rank", action="store_true", help="热度榜(EM)")
    p.add_argument("--famous", action="store_true", help="知名港股(EM)")
    p.add_argument("--index-daily-em", action="store_true", help="指数日线(EM) - 抓取常用篮子")
    return p.parse_args()


def main() -> None:
    ensure_sys_path()
    args = parse_args()

    # 默认 --all
    if not any([
        args.spot_sina,
        args.spot_em,
        args.hot_rank,
        args.famous,
        args.index_daily_em,
    ]):
        args.all = True

    include_spot_sina = args.all or args.spot_sina
    include_spot_em = args.all or args.spot_em
    include_main_board = False
    include_ggt_components = False
    include_index_spot_sina = False
    include_index_spot_em = False
    include_hot_rank = args.all or args.hot_rank
    include_famous = args.all or args.famous
    include_index_daily_em = args.all or args.index_daily_em

    asyncio.run(
        main_async(
            include_spot_sina,
            include_spot_em,
            include_main_board,
            include_ggt_components,
            include_index_spot_sina,
            include_index_spot_em,
            include_hot_rank,
            include_famous,
            include_index_daily_em,
        )
    )


if __name__ == "__main__":
    main()



