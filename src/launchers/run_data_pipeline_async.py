#!/usr/bin/env python3
"""
完整数据处理流水线脚本
功能：数据爬取 -> TA-Lib技术指标计算 -> 数据清洗 -> 回测分析（仅Single策略）
包含：数据收集（含同行比较）、技术指标计算、数据清洗、策略回测（仅单指标策略，含图表生成）
作者：AI Assistant
创建时间：2025年
"""

import argparse
import subprocess
import sys
from pathlib import Path
import os

# 添加项目根目录到Python路径
current_file = Path(__file__).resolve()
project_root = current_file.parents[2]
sys.path.insert(0, str(project_root))

from config import config

# 使用config的项目根目录（更可靠）
project_root = config.project_root


def _get_env():
    """获取环境变量配置"""
    env = os.environ.copy()
    existing_path = env.get('PYTHONPATH', '')
    env['PYTHONPATH'] = f"{project_root}:{existing_path}" if existing_path else str(project_root)
    return env

def _run_step(step_name, script_path, args=None, description=""):
    """运行单个步骤"""
    print(f"\n🔄 {step_name}")
    cmd = [sys.executable]

    # 处理 -m 模块参数
    if script_path == "-m":
        cmd.append("-m")
        if args:
            if isinstance(args, list):
                cmd.extend(args)
            else:
                cmd.append(str(args))
    # 处理 -c 命令参数
    elif script_path == "-c":
        cmd.append("-c")
        if args:
            if isinstance(args, list):
                # 将代码列表合并为单个字符串
                code_str = " ".join(args) if isinstance(args, list) else str(args)
                cmd.append(code_str)
            else:
                cmd.append(str(args))
    else:
        cmd.append(script_path)
        if args:
            if isinstance(args, list):
                cmd.extend(args)
            else:
                cmd.append(str(args))

    result = subprocess.run(
        cmd,
        cwd=str(project_root),
        capture_output=True,
        text=True,
        env=_get_env()
    )

    if result.returncode == 0:
        print(f"✅ {step_name}完成")
    else:
        print(f"⚠️ {step_name}完成（退出码: {result.returncode}）")
        if result.stderr:
            print(f"   错误信息: {result.stderr[:200]}")

    if description:
        print(f"   {description}")

    return result.returncode == 0

def run_complete_pipeline(stock_symbols, skip_data_collection=False):
    """
    运行完整的数据处理流水线

    Args:
        stock_symbols (list): 股票代码列表
        skip_data_collection (bool): 是否跳过数据收集步骤
    """
    print("🚀 启动完整数据处理流水线")
    print("=" * 50)

    success_count = 0
    failed_symbols = []

    for symbol in stock_symbols:
        print(f"\n📊 开始处理股票: {symbol}")
        print("-" * 30)

        step_failed = False

        # 步骤1: 数据爬取
        if not skip_data_collection:
            if not _run_step(
                "步骤1: 异步数据爬取",
                "src/crawling/stock_data_collector.py",
                ["--symbols", symbol],
                "包含: 历史行情、财务数据、技术指标、同行比较等10类数据"
            ):
                step_failed = True

        # 步骤2: 数据清洗
        if not step_failed and not _run_step(
            "步骤2: 数据清洗",
            "-c",
            [
                "from src.cleaning.stock_data_cleaner import EnhancedDataCleaner;",
                f"cleaner = EnhancedDataCleaner('data');",
                f"cleaner.clean_stock_data('{symbol}');"
            ],
            "清洗和整理股票数据（升序排列，便于技术指标计算）"
        ):
            step_failed = True

        # 步骤3: 技术指标计算 (使用backtesting模块的统一技术指标计算器)
        if not step_failed and not _run_step(
            "步骤3: 技术指标计算",
            "-m",
            ["src.talib_analysis.calculator", symbol],
            "使用backtesting模块的指标计算器"
        ):
            step_failed = True

        # 步骤4: 回测分析
        if not step_failed and not _run_step(
            "步骤4: 回测分析",
            "-m",
            ["src.backtesting.core.tester", symbol, "--all-strategies", "--output-dir", f"data/cleaned_stocks/{symbol}/results"],
            "包含: 单指标策略、交易记录、图表生成"
        ):
            step_failed = True

        # 步骤5: 最终数据排序（降序排列，便于查看最新数据）
        if not step_failed and not _run_step(
            "步骤5: 最终数据排序",
            "-c",
            [
                "from src.cleaning.stock_data_cleaner import EnhancedDataCleaner;",
                "from pathlib import Path;",
                f"cleaner = EnhancedDataCleaner('data');",
                f"cleaner.sort_symbol_data_descending('{symbol}');"
            ],
            "将所有数据文件按日期降序排列"
        ):
            step_failed = True

        if step_failed:
            print(f"\n⚠️ 股票 {symbol} 处理过程中遇到错误")
            failed_symbols.append(symbol)
        else:
            print(f"\n🎉 股票 {symbol} 处理完成！")
            success_count += 1

    print("\n" + "=" * 50)
    print(f"🏁 完整数据处理流水线执行完成！")
    print(f"   成功: {success_count}/{len(stock_symbols)}")
    if failed_symbols:
        print(f"   失败: {', '.join(failed_symbols)}")


def main():
    """
    主函数
    """
    parser = argparse.ArgumentParser(
        description="完整数据处理流水线：数据爬取 -> 数据清洗 -> TA-Lib技术指标 -> 回测分析 -> 最终排序",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python run_data_pipeline_async.py 002594
  python run_data_pipeline_async.py 002594 600519 000001
  python run_data_pipeline_async.py --symbols-list 002594,600519,000001
  python run_data_pipeline_async.py 002594 --skip-data-collection
  python run_data_pipeline_async.py 002594 --skip-crawl

流程说明:
  1. 数据爬取: 获取股票历史数据（含同行比较数据）
  2. 数据清洗: 清洗和整理数据（升序排列，便于技术指标计算）
  3. TA-Lib计算: 计算技术指标（MACD、KDJ、BBI等）
  4. 回测分析: 运行单指标策略（7种策略），生成交易记录和图表
  5. 最终排序: 将所有数据按日期降序排列，便于查看最新数据
        """,
    )

    parser.add_argument("symbols", nargs="*", help="股票代码列表，用空格分隔")

    parser.add_argument("--symbols-list", type=str, help="股票代码列表，用逗号分隔")

    parser.add_argument("--skip-data-collection", "--skip-crawl", action="store_true",
                        help="跳过数据收集步骤，直接使用现有数据进行技术分析")

    args = parser.parse_args()

    # 处理股票代码参数
    symbols_from_args = args.symbols or []
    symbols_from_list = args.symbols_list.split(",") if args.symbols_list else []
    stock_symbols = list(set(s.strip() for s in symbols_from_args + symbols_from_list if s.strip()))
    
    if not stock_symbols:
        print("❌ 请提供至少一个股票代码")
        parser.print_help()
        sys.exit(1)

    print(f"📋 待处理股票代码: {', '.join(stock_symbols)}")
    if args.skip_data_collection:
        print("⏭️ 将跳过数据收集步骤")
    
    # 运行完整流水线
    run_complete_pipeline(stock_symbols, skip_data_collection=args.skip_data_collection)


if __name__ == "__main__":
    main()
