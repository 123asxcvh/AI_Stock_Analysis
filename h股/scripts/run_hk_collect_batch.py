#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def ensure_sys_path() -> None:
    root = project_root()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))


async def collect_one(symbol: str, data_dir: str) -> tuple[str, dict]:
    from src.data.crawling.hk_unified_async_collector import HKUnifiedAsyncCollector
    from src.analysis.talib_analysis.hk_core_talib_analyzer import HKCoreTALibAnalyzer
    from src.data.cleaning.hk_stock_cleaner import clean_stock_folder

    # 1) 数据爬取
    c = HKUnifiedAsyncCollector(data_root_dir=data_dir)
    res = await c.collect_all_stock_data(symbol)

    # 2) TA-Lib 核心指标
    talib_status = False
    talib_output = None
    try:
        analyzer = HKCoreTALibAnalyzer(data_root_dir=data_dir)
        ana_res = analyzer.analyze_stock(symbol)
        talib_status = (ana_res.get("status") == "Success")
        talib_output = ana_res.get("output_path")
    except Exception as e:
        talib_status = False

    # 3) 数据清洗（个股目录）
    cleaned_map = {}
    try:
        cleaned_map = clean_stock_folder(os.path.join(data_dir, "stocks"), symbol)
    except Exception:
        cleaned_map = {}

    # 汇总
    res_summary = dict(res)
    res_summary["talib"] = talib_status
    res_summary["talib_output"] = talib_output
    res_summary["cleaned_files"] = len(cleaned_map)
    return symbol, res_summary


async def main_async(symbols: list[str], list_file: str | None, batch: int) -> None:
    from src.data.crawling.hk_unified_async_collector import HKUnifiedAsyncCollector  # noqa: F401

    data_dir = str(project_root() / "data")

    # 从文件读取追加代码
    if list_file:
        p = Path(list_file)
        if p.exists():
            extra = [line.strip() for line in p.read_text(encoding="utf-8").splitlines() if line.strip()]
            symbols.extend(extra)
    # 去重
    symbols = sorted({s.strip() for s in symbols if s.strip()})

    total = len(symbols)
    print(f"Total symbols: {total}")
    for i in range(0, total, batch):
        chunk = symbols[i : i + batch]
        print(f"Batch {i//batch+1}/{(total-1)//batch+1}: {', '.join(chunk)}")
        tasks = [collect_one(s, data_dir) for s in chunk]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for r in results:
            if isinstance(r, Exception):
                print("ERROR:", r)
                continue
            sym, res = r
            ok = [k for k, v in res.items() if isinstance(v, bool) and v]
            fail = [k for k, v in res.items() if isinstance(v, bool) and not v]
            extra = f" | talib={'ok' if res.get('talib') else 'fail'} | cleaned={res.get('cleaned_files',0)}"
            print(f"{sym} | OK: {','.join(ok)} | FAIL: {','.join(fail)}{extra}")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Collect HK stocks in batch (unified async)")
    p.add_argument("--symbols", type=str, default="", help="逗号分隔，如 01810,00700")
    p.add_argument("--list-file", type=str, default=None, help="每行一个代码的文件路径")
    p.add_argument("--batch", type=int, default=10, help="并发批大小")
    return p.parse_args()


def main() -> None:
    ensure_sys_path()
    args = parse_args()
    symbols = [s.strip() for s in args.symbols.split(",") if s.strip()]
    asyncio.run(main_async(symbols, args.list_file, args.batch))


if __name__ == "__main__":
    main()


