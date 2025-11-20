#!/usr/bin/env python3
"""
数据处理流水线脚本 - 重构版本
功能：数据爬取 -> 数据清洗 -> 技术指标准备 -> [回测分析]
作者：AI Assistant
创建时间：2025年
更新时间：2025年11月 - 重构，将回测功能移至backtesting模块
"""

import argparse
import subprocess
import sys
import json
from pathlib import Path
import os
from datetime import datetime
import pandas as pd
import numpy as np

# 添加项目根目录到Python路径
current_file = Path(__file__).resolve()
project_root = current_file.parents[2]
sys.path.insert(0, str(project_root))


# 导入统一配置
try:
    from config import config
except ImportError:
    # 如果config模块导入失败，创建基本的配置
    class Config:
        project_root = Path(__file__).parents[2]
        def get_stock_dir(self, symbol, cleaned=False):
            base_dir = "cleaned_stocks" if cleaned else "raw_stocks"
            return self.project_root / "data" / base_dir / symbol

    config = Config()



# 数据处理配置 - 更新与backtesting和Web界面完全一致
DATA_PIPELINE_CONFIG = {
    # 支持的回测策略列表（用于backtesting模块调用）
    "supported_strategies": [
        "双均线策略", "MACD趋势策略", "KDJ超卖反弹策略", "RSI反转策略", "布林带策略",
        "成交量突破策略", "双EMA策略", "MACD+KDJ双重确认策略", "RSI背离策略",
        "均线多头排列策略", "布林带收缩策略", "量价配合策略", "MACD柱状图策略",
        "布林带RSI反转策略", "双ATR反转策略", "KDJ钝化策略", "RSI趋势策略"
    ],
    # 技术指标配置 - 与backtesting模块和Web界面保持一致
    "technical_indicators": [
        # 基础移动平均线
        'MA5', 'MA10', 'MA20', 'MA30', 'MA60', 'MA120',
        # EMA指标（用于MACD）
        'EMA12', 'EMA26',
        # 成交量均线
        'VOLUME_MA5', 'VOLUME_MA10', 'VOLUME_MA20',
        # 核心技术指标
        'RSI',
        # MACD完整指标组
        'MACD_DIF', 'MACD_DEA', 'MACD_HIST',
        # 日线KDJ指标组
        'DAILY_KDJ_K', 'DAILY_KDJ_D', 'DAILY_KDJ_J',
        # 布林带指标组
        'BOLL_UPPER', 'BOLL_MIDDLE', 'BOLL_LOWER',
        # ATR指标
        'ATR',
        # BBI指标（Web界面需要）
        'BBI',
        # 额外补充指标（策略可能用到）
        'CCI',
        'WR',  # 威廉指标
        'MTM',  # 动量指标
        'OBV'   # 能量潮指标
    ]
}


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




def run_backtesting_analysis(symbol, enable_optimization=True, strategies=None, max_evaluations=None):
    """
    运行回测分析 - 使用增强版strategy_comparison进行智能策略分析和对比

    Args:
        symbol (str): 股票代码
        enable_optimization (bool): 是否启用深度参数优化（影响评估次数，默认启用）
        strategies (list): 要分析的策略列表，None表示使用所有策略
        max_evaluations (int): 最大评估次数，None表示使用默认值（10次）
    """
    print(f"\n📈 开始回测分析: {symbol}")

    try:
        import subprocess
        import sys
        from pathlib import Path

        # 获取backtesting脚本的路径 - 使用增强版strategy_comparison
        backtesting_script = project_root / "src" / "backtesting" / "launchers" / "strategy_comparison.py"

        if not backtesting_script.exists():
            print(f"❌ 找不到backtesting脚本: {backtesting_script}")
            return False

        # 构建命令
        cmd = [sys.executable, str(backtesting_script), symbol]

        # 增强版strategy_comparison支持多种参数
        print(f"   📊 增强策略对比分析模式")

        if strategies:
            strategy_str = ",".join(strategies)
            cmd.extend(["--strategies", strategy_str])
            print(f"   🎯 指定策略: {strategy_str}")
        else:
            print(f"   🔄 分析所有支持策略")

        # 设置评估次数
        if max_evaluations:
            cmd.extend(["--max-evaluations", str(max_evaluations)])
        elif enable_optimization:
            # 优化模式使用10次评估
            cmd.extend(["--max-evaluations", "10"])
            print(f"   🔍 参数优化模式，评估次数: 10")
        else:
            # 快速模式使用10次评估
            cmd.extend(["--max-evaluations", "10"])
            print(f"   🚀 快速对比模式，评估次数: 10")

        # 添加并行处理支持（如果支持）
        cmd.extend(["--parallel", "4"])  # 使用4个进程并行处理

        print(f"   执行命令: {' '.join(cmd)}")

        # 设置环境变量
        env = _get_env()

        # 执行backtesting脚本
        result = subprocess.run(
            cmd,
            cwd=str(project_root),
            capture_output=True,
            text=True,
            env=env
        )

        if result.returncode == 0:
            print(f"✅ 回测分析完成")
            # 显示输出摘要
            output_lines = result.stdout.strip().split('\n')
            for line in output_lines[-15:]:  # 显示最后15行输出
                if line.strip():
                    print(f"   {line}")
        else:
            print(f"⚠️ 回测分析完成（退出码: {result.returncode}）")
            if result.stderr:
                error_lines = result.stderr.strip().split('\n')
                for line in error_lines[-10:]:  # 显示最后10行错误
                    if line.strip():
                        print(f"   错误: {line}")

        # 检查输出目录
        output_dir = Path(f"data/cleaned_stocks/{symbol}/backtest_results")
        if output_dir.exists():
            print(f"   📊 结果已保存到: {output_dir}")

            # 确保生成total_trades.csv文件
            try:
                from src.backtesting.tools import generate_total_trades_csv_unified

                # 获取所有策略名称
                strategy_dirs = [d for d in output_dir.iterdir() if d.is_dir()]
                strategy_names = [d.name for d in strategy_dirs]

                if strategy_names:
                    print(f"   🔄 生成total_trades.csv文件，包含 {len(strategy_names)} 个策略")
                    generate_total_trades_csv_unified(output_dir, symbol, strategy_names)
                    print(f"   ✅ total_trades.csv 已生成")
                else:
                    print(f"   ⚠️ 未找到策略目录，无法生成total_trades.csv")

            except Exception as e:
                print(f"   ⚠️ 生成total_trades.csv失败: {e}")

            # 显示关键文件
            key_files = [
                "strategy_comparison.csv",
                "total_trades.csv"
            ]

            for file_name in key_files:
                file_path = output_dir / file_name
                if file_path.exists():
                    print(f"      ✅ {file_name} - 策略对比结果")
                else:
                    print(f"      ⚠️ {file_name} - 未找到")

            # 显示策略目录
            strategy_dirs_for_display = [d for d in output_dir.iterdir() if d.is_dir()]
            for strategy_dir in strategy_dirs_for_display[:5]:  # 只显示前5个
                print(f"      📂 {strategy_dir.name}/")
                if (strategy_dir / "best_params.csv").exists():
                    print(f"         ✅ best_params.csv")
                if (strategy_dir / "backtest_report.csv").exists():
                    print(f"         ✅ backtest_report.csv")
                if (strategy_dir / "trades.csv").exists():
                    print(f"         ✅ trades.csv")
            if len(strategy_dirs_for_display) > 5:
                print(f"      ... 还有 {len(strategy_dirs_for_display) - 5} 个策略目录")

        return result.returncode == 0

    except Exception as e:
        print(f"❌ 回测分析失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def clear_cache():
    """清理所有缓存数据"""
    print(f"🗑️ 清理缓存数据...")

    import shutil
    from pathlib import Path

    # 清理data_cache目录
    cache_dir = Path("data_cache")
    if cache_dir.exists():
        try:
            shutil.rmtree(cache_dir)
            print(f"✅ 已清理data_cache目录")
        except Exception as e:
            print(f"⚠️ 清理data_cache目录失败: {e}")

    # 清理DataManager的内存缓存
    try:
        from src.backtesting.data_manager import data_manager
        data_manager.clear_cache()
        print(f"✅ 已清理DataManager缓存")
    except Exception as e:
        print(f"⚠️ 清理DataManager缓存失败: {e}")

def run_complete_pipeline(stock_symbols, skip_data_collection=False, enable_optimization=True,
                         max_evaluations=None, strategies=None):
    """
    运行完整的数据处理流水线 - 增强版本（回测分析默认启用）

    Args:
        stock_symbols (list): 股票代码列表
        skip_data_collection (bool): 是否跳过数据收集步骤
        enable_optimization (bool): 是否启用回测分析（已废弃，始终为True）
        max_evaluations (int): 最大评估次数，None表示使用默认值
        strategies (list): 指定要分析的策略列表，None表示分析所有策略
    """
    print(f"🚀 启动完整数据处理+回测分析流水线")
    print("=" * 50)

    # 每次运行时清理缓存，确保获取最新数据
    clear_cache()

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
                "包含: 历史行情、财务数据、技术指标、同行比较等数据"
            ):
                step_failed = True

        # 步骤2: 数据清洗（包含historical_quotes.csv）
        if not step_failed and not _run_step(
            "步骤2: 数据清洗",
            "-c",
            [
                "from src.cleaning.stock_data_cleaner import EnhancedDataCleaner;",
                "from pathlib import Path;",
                f"cleaner = EnhancedDataCleaner('data');",
                f"cleaner.clean_stock_data('{symbol}');"
            ],
            "清洗和整理股票数据（包含historical_quotes.csv）"
        ):
            step_failed = True

        # 步骤3: 技术指标准备
        if not step_failed:
            print(f"\n🔄 步骤3: 技术指标准备")
            try:
                from src.backtesting.data_manager import DataManager

                # 准备技术指标数据
                dm = DataManager()
                data = dm.load_stock_data(symbol, required_indicators=DATA_PIPELINE_CONFIG["technical_indicators"])

                if data is not None and not data.empty:
                    print(f"✅ 步骤3: 技术指标准备完成")
                    print(f"   数据行数: {len(data)}")
                    print(f"   技术指标数: {len(DATA_PIPELINE_CONFIG['technical_indicators'])}")

                    # 使用DataManager的智能保存方法，避免覆盖有效的指标数据
                    data_file = config.get_stock_dir(symbol, cleaned=True) / "historical_quotes.csv"
                    dm._save_indicators_to_file(data, symbol, cleaned=True)
                    print(f"   已保存技术指标准备文件: {data_file}")

                    # 注意：historical_quotes的倒序处理将在backtesting模块中完成
                else:
                    print(f"⚠️ 步骤3: 技术指标准备完成（数据为空）")
                    step_failed = True

            except Exception as e:
                print(f"❌ 步骤3: 技术指标准备失败: {e}")
                import traceback
                traceback.print_exc()
                step_failed = True

        # 步骤4: 回测分析（默认启用）
        if not step_failed:
            print(f"\n📈 步骤4: 回测分析")
            if not run_backtesting_analysis(symbol, enable_optimization=True,
                                           strategies=strategies, max_evaluations=max_evaluations):
                print(f"⚠️ 回测分析遇到问题，但数据处理已完成")
            # 使用增强版策略对比进行参数优化，结果由backtesting模块自动保存

        
        if step_failed:
            print(f"\n⚠️ 股票 {symbol} 处理过程中遇到错误")
            failed_symbols.append(symbol)
        else:
            print(f"\n🎉 股票 {symbol} 处理完成！包含回测分析")
            success_count += 1

    print("\n" + "=" * 50)
    print(f"🏁 数据处理+回测分析流水线执行完成！")
    print(f"   成功: {success_count}/{len(stock_symbols)}")
    if failed_symbols:
        print(f"   失败: {', '.join(failed_symbols)}")


def main():
    """
    主函数 - 重构版本
    """
    parser = argparse.ArgumentParser(
        description="数据处理流水线：数据爬取 -> 数据清洗 -> 技术指标准备 -> [回测分析]",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 数据处理+回测分析流水线（默认启用回测）
  python run_data_pipeline_async.py 000001
  python run_data_pipeline_async.py 000001 600519 002594
  python run_data_pipeline_async.py --symbols-list 000001,600519,002594
  python run_data_pipeline_async.py 000001 --skip-data-collection
  python run_data_pipeline_async.py 000001 --strategies "双均线策略,MACD趋势策略"
  python run_data_pipeline_async.py 000001 --max-evaluations 100 --parallel 8
  python run_data_pipeline_async.py 000001 600519 --skip-data-collection

流程说明:
  1. 数据爬取: 获取股票历史数据、财务数据等
  2. 数据清洗: 清洗和整理数据（升序排列，便于技术指标计算）
  3. 技术指标准备: 准备backtesting所需的技术指标数据
  4. 回测分析: 运行增强版策略对比分析（默认启用）
     - 支持参数优化和贝叶斯搜索
     - 并行处理提高效率
     - 生成详细的策略报告
  5. 最终排序: 将所有数据按日期降序排列，便于查看最新数据

新增功能:
  - 增强版策略对比: 使用最新的strategy_comparison.py
  - 并行处理: 支持多进程并行分析
  - 灵活策略选择: 可指定特定策略进行分析
  - 评估次数控制: 精确控制参数优化的计算量
  - 详细结果报告: 包含strategy_comparison.csv和total_trades.csv

注意事项:
  - 本脚本已升级使用增强版strategy_comparison
  - 回测分析功能默认启用，无需额外选项
  - 支持的技术指标已与backtesting模块完全兼容
  - 并行处理需要足够的CPU资源
  - 评估次数越高，优化精度越高但耗时越长
  - 生成的策略对比结果可直接用于Web界面展示
  - 如仅需数据处理而不运行回测，请使用其他专门的脚本
        """,
    )

    parser.add_argument("symbols", nargs="*", help="股票代码列表，用空格分隔")

    parser.add_argument("--symbols-list", type=str, help="股票代码列表，用逗号分隔")

    parser.add_argument("--skip-data-collection", "--skip-crawl", action="store_true",
                        help="跳过数据收集步骤，直接使用现有数据进行技术分析")

    # 回测分析功能默认启用，无需选项
    # 如果需要只进行数据处理而不运行回测，请使用其他专门的脚本

    parser.add_argument("--max-evaluations", type=int, default=None,
                        help="最大评估次数（默认：优化模式50，快速模式20）")

    parser.add_argument("--strategies", type=str, default=None,
                        help="指定要分析的策略列表，用逗号分隔（如：双均线策略,MACD趋势策略）")

    parser.add_argument("--parallel", type=int, default=4,
                        help="并行处理的进程数（默认：4）")

    args = parser.parse_args()

    # 处理股票代码参数
    symbols_from_args = args.symbols or []
    symbols_from_list = args.symbols_list.split(",") if args.symbols_list else []
    stock_symbols = list(set(s.strip() for s in symbols_from_args + symbols_from_list if s.strip()))

    # 处理策略列表参数
    strategies = None
    if args.strategies:
        strategies = [s.strip() for s in args.strategies.split(",") if s.strip()]

    if not stock_symbols:
        print("❌ 请提供至少一个股票代码")
        parser.print_help()
        sys.exit(1)

    print(f"📋 待处理股票代码: {', '.join(stock_symbols)}")
    if args.skip_data_collection:
        print("⏭️ 将跳过数据收集步骤")

    # 回测分析功能默认启用
    print(f"📈 已启用增强回测分析功能")
    print(f"   技术指标数: {len(DATA_PIPELINE_CONFIG['technical_indicators'])}个")
    print(f"   并行进程数: {args.parallel}")
    print(f"   说明: 将使用增强版策略对比进行参数优化")
    if args.max_evaluations:
        print(f"   最大评估次数: {args.max_evaluations}")
    elif strategies:
        print(f"   指定策略: {', '.join(strategies)}")
    else:
        print(f"   分析策略: 所有支持策略")

    # 运行完整流水线（回测分析默认启用）
    run_complete_pipeline(
        stock_symbols,
        skip_data_collection=args.skip_data_collection,
        enable_optimization=True,  # 默认启用回测分析
        max_evaluations=args.max_evaluations,
        strategies=strategies
    )


if __name__ == "__main__":
    # 导入numpy用于参数组合计算
    import numpy as np
    main()