#!/usr/bin/env python3
"""
参数优化脚本 - 专门用于策略参数优化
承接从data pipeline移转过来的参数优化功能
作者：AI Assistant
创建时间：2025年11月
"""

import argparse
import sys
from pathlib import Path
import os

# 添加项目根目录到Python路径
current_file = Path(__file__).resolve()
project_root = current_file.parents[3]
sys.path.insert(0, str(project_root))

# 参数优化配置
OPTIMIZATION_CONFIG = {
    # 需要优化的策略列表 - 与strategies.py中的实际策略对应
    "strategies_to_optimize": [
        # 基础策略
        "双均线策略",
        "MACD趋势策略",
        "KDJ超卖反弹策略",
        "RSI反转策略",
        "布林带策略",
        "成交量突破策略"
    ],
    # 优化目标
    "objective": "sharpe_ratio",
    "objective_direction": "maximize",
    # 优化约束
    "min_trades": 5,
    "max_drawdown_limit": 50.0,
    # 优化配置
    "max_combinations": 100,
    "workers": 2,
    "timeout": 60,
    # 对比分析配置
    "enable_comparison": False,  # 修复：避免覆盖最优参数结果
    "comparison_sort_by": "sharpe_ratio",
    "comparison_output_dir": None
}


def run_strategy_optimization(symbol, strategy_name, max_evaluations=100):
    """运行单个策略的参数优化"""
    print(f"\n🔍 开始参数优化: {strategy_name} on {symbol}")

    try:
        from src.backtesting.facade import optimize_strategy

        # 运行优化 - 使用贝叶斯优化（backtesting模块只支持贝叶斯优化）
        optimization_result = optimize_strategy(
            symbol=symbol,
            strategy_name=strategy_name,
            method="bayesian",  # 修正：backtesting只支持贝叶斯优化
            max_evaluations=max_evaluations,
            objective=OPTIMIZATION_CONFIG["objective"]
        )

        if optimization_result and optimization_result.best_score > -10:  # 排除无效结果
            print(f"✅ {strategy_name} 参数优化完成")
            print(f"   最佳夏普比率: {optimization_result.best_score:.3f}")
            print(f"   最佳参数: {optimization_result.best_params}")

            # 运行最优参数回测并保存结果
            run_optimized_backtest(symbol, strategy_name, optimization_result)

            return optimization_result
        else:
            print(f"⚠️ {strategy_name} 优化未找到有效参数")
            return None

    except Exception as e:
        print(f"❌ {strategy_name} 参数优化失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def run_optimized_backtest(symbol, strategy_name, optimization_result):
    """使用最优参数运行回测并保存详细结果"""
    print(f"\n📈 使用最优参数运行回测: {strategy_name} on {symbol}")

    try:
        from src.backtesting.facade import (
            BacktestEngine, create_strategy_by_name, get_data_manager, BacktestVisualizer
        )
        from pathlib import Path
        import pandas as pd

        # 创建输出目录
        output_dir = Path(f"data/cleaned_stocks/{symbol}/backtest_results")
        output_dir.mkdir(parents=True, exist_ok=True)

        # 创建策略特定的输出目录
        strategy_output_dir = output_dir / strategy_name
        strategy_output_dir.mkdir(parents=True, exist_ok=True)

        print(f"   输出目录: {strategy_output_dir}")

        # 安全地创建策略实例，使用最优参数
        strategy = create_strategy_by_name(strategy_name, optimization_result.best_params)
        print(f"   应用最优参数: {optimization_result.best_params}")

        # 直接使用BacktestEngine运行回测，确保使用最优参数
        data_manager = get_data_manager()
        data = data_manager.load_stock_data(symbol, required_indicators=[])

        engine = BacktestEngine()
        result = engine.run(data, strategy, output_dir=str(strategy_output_dir))

        if result and result.get('performance'):
            perf = result['performance']
            print(f"✅ {strategy_name} 最优参数回测完成")
            print(f"   夏普比率: {perf.get('sharpe_ratio', 0):.3f}")
            print(f"   总收益率: {perf.get('total_return', 0):.2f}%")
            print(f"   最大回撤: {perf.get('max_drawdown', 0):.2f}%")
            print(f"   胜率: {perf.get('win_rate', 0):.1f}%")

            # 保存详细的优化结果到CSV
            save_optimization_results(strategy_output_dir, symbol, strategy_name, optimization_result, perf)

            # 生成图表
            try:
                visualizer = BacktestVisualizer()
                # 生成权益曲线和回撤图
                visualizer.plot_equity_with_drawdown(
                    result,
                    output_path=str(strategy_output_dir / "equity_drawdown.png"),
                    show=False
                )
                # 生成交易点和技术指标图
                visualizer.plot_trades_with_indicator(
                    result,
                    strategy_name,
                    output_path=str(strategy_output_dir / "trades_analysis.png"),
                    show=False
                )
                print(f"   📊 图表已保存到: {strategy_output_dir}")

            except Exception as e:
                print(f"   ⚠️ 图表生成失败: {e}")

            return True
        else:
            print(f"❌ {strategy_name} 最优参数回测失败")
            return False

    except Exception as e:
        print(f"❌ {strategy_name} 最优参数回测异常: {e}")
        import traceback
        traceback.print_exc()
        return False


def save_optimization_results(output_dir, symbol, strategy_name, optimization_result, performance):
    """保存详细的优化结果到CSV文件"""
    try:
        import pandas as pd

        # 保存优化结果CSV
        if optimization_result.all_results and len(optimization_result.all_results) > 0:
            # 创建以指标为行，参数组合为列的数据框
            optimization_rows = []

            # 收集所有唯一的参数组合并按夏普比率排序
            unique_results = []
            seen_params = set()
            for result_item in sorted(optimization_result.all_results, key=lambda x: x.get('score', 0), reverse=True):
                params = result_item.get('params', {})
                param_str = "_".join([f"{k}:{v}" for k, v in params.items()])
                if param_str not in seen_params:
                    seen_params.add(param_str)
                    unique_results.append(result_item)

            # 限制显示前10个最优组合
            top_results = unique_results[:10]

            # 创建行数据 - 使用与performance.csv相同的15个指标
            indicators = [
                "总收益率", "年化收益率", "夏普比率", "卡尔玛比率", "最大回撤",
                "年化波动率", "总交易次数", "胜率", "盈亏比",
                "止损次数", "止损率", "初始资金", "最终资金", "总盈利", "总亏损"
            ]

            # 首先添加参数行（放在前面）
            param_names = set()
            for result_item in top_results:
                param_names.update(result_item.get('params', {}).keys())

            for param_name in sorted(list(param_names))[:5]:  # 最多显示5个参数
                row_data = {"指标": f"参数_{param_name}"}
                for i, result_item in enumerate(top_results):
                    params = result_item.get('params', {})
                    param_combo_str = f"组合{i+1}"
                    value = str(params.get(param_name, ''))
                    row_data[param_combo_str] = value
                optimization_rows.append(row_data)

            # 然后添加指标行（放在后面）
            for indicator in indicators:
                row_data = {"指标": indicator}
                for i, result_item in enumerate(top_results):
                    perf_item = result_item.get('performance', {})
                    param_combo_str = f"组合{i+1}"

                    # 根据指标类型获取对应值 - 与performance.csv格式一致
                    if indicator == "总收益率":
                        value = f"{perf_item.get('total_return', 0):.2f}%"
                    elif indicator == "年化收益率":
                        value = f"{perf_item.get('annual_return', 0):.2f}%"
                    elif indicator == "夏普比率":
                        value = f"{result_item.get('score', 0):.3f}"  # 使用score而不是performance中的sharpe_ratio
                    elif indicator == "卡尔玛比率":
                        value = f"{perf_item.get('calmar_ratio', 0):.3f}"
                    elif indicator == "最大回撤":
                        value = f"{perf_item.get('max_drawdown', 0):.2f}%"
                    elif indicator == "年化波动率":
                        value = f"{perf_item.get('volatility', 0):.2f}%"
                    elif indicator == "总交易次数":
                        value = str(perf_item.get('total_trades', 0))
                    elif indicator == "胜率":
                        value = f"{perf_item.get('win_rate', 0):.1f}%"
                    elif indicator == "盈亏比":
                        pl_ratio = perf_item.get('profit_loss_ratio', 0)
                        value = f"{pl_ratio:.2f}" if pl_ratio != float('inf') else "inf"
                    elif indicator == "止损次数":
                        value = str(perf_item.get('stop_loss_count', 0))
                    elif indicator == "止损率":
                        value = f"{perf_item.get('stop_loss_rate', 0):.2f}%"
                    elif indicator == "初始资金":
                        value = f"{int(perf_item.get('initial_capital', 0)):,}"
                    elif indicator == "最终资金":
                        value = f"{int(perf_item.get('final_capital', 0)):,}"
                    elif indicator == "总盈利":
                        value = f"{int(perf_item.get('total_profit', 0)):,}"
                    elif indicator == "总亏损":
                        value = f"{int(perf_item.get('total_loss', 0)):,}"

                    row_data[param_combo_str] = value

                optimization_rows.append(row_data)

            # 创建数据框并保存
            optimization_df = pd.DataFrame(optimization_rows)
            optimization_csv_path = output_dir / "optimization_results.csv"
            optimization_df.to_csv(optimization_csv_path, index=False, encoding='utf-8')

            print(f"   📊 优化结果已保存到: {optimization_csv_path}")
            print(f"💡 共保存 {len(top_results)} 个最优参数组合，按夏普比率排序")

        else:
            # 如果没有all_results，使用基本格式
            optimization_data = [
                {"参数项": "股票代码", "参数值": symbol},
                {"参数项": "策略名称", "参数值": strategy_name}
            ]

            # 添加策略参数
            for param_name, param_value in optimization_result.best_params.items():
                optimization_data.append({"参数项": param_name, "参数值": param_value})

            # 添加优化结果性能指标
            optimization_data.extend([
                {"参数项": "最佳夏普比率", "参数值": f"{performance.get('sharpe_ratio', 0):.3f}"},
                {"参数项": "总收益率", "参数值": f"{performance.get('total_return', 0):.2f}%"},
                {"参数项": "年化收益率", "参数值": f"{performance.get('annual_return', 0):.2f}%"},
                {"参数项": "最大回撤", "参数值": f"{performance.get('max_drawdown', 0):.2f}%"},
                {"参数项": "胜率", "参数值": f"{performance.get('win_rate', 0):.1f}%"},
                {"参数项": "盈亏比", "参数值": f"{performance.get('profit_loss_ratio', 0):.2f}"},
                {"参数项": "总交易次数", "参数值": f"{int(performance.get('total_trades', 0))}"},
                {"参数项": "初始资金", "参数值": f"{int(performance.get('initial_capital', 0)):,}"},
                {"参数项": "最终资金", "参数值": f"{int(performance.get('final_capital', 0)):,}"}
            ])

            # 保存优化结果CSV
            optimization_df = pd.DataFrame(optimization_data)
            optimization_csv_path = output_dir / "optimization_results.csv"
            optimization_df.to_csv(optimization_csv_path, index=False, encoding='utf-8')
            print(f"   📈 参数优化结果已保存: {optimization_csv_path}")

    except Exception as e:
        print(f"   ⚠️ 参数优化CSV保存失败: {e}")


def run_strategy_comparison(symbol, strategy_names=None):
    """运行策略对比分析"""
    print(f"\n📊 开始策略对比分析: {symbol}")

    try:
        from src.backtesting.facade import (
            compare_strategies, get_available_strategies, BacktestConfig
        )
        from pathlib import Path

        # 创建输出目录
        comparison_output_dir = Path(f"data/cleaned_stocks/{symbol}/backtest_results")
        comparison_output_dir.mkdir(parents=True, exist_ok=True)

        # 确定要对比的策略
        if strategy_names is None:
            strategy_names = OPTIMIZATION_CONFIG["strategies_to_optimize"]

        print(f"   对比策略数: {len(strategy_names)}")

        # 运行策略对比
        config = BacktestConfig()
        comparison_results = compare_strategies(
            symbol,
            strategy_names,
            config=config,
            save_results=True,
            output_dir=str(comparison_output_dir)
        )

        if comparison_results:
            print(f"✅ 策略对比分析完成")

            # 显示最佳策略
            sorted_results = sorted(
                comparison_results.items(),
                key=lambda x: x[1].performance.get('sharpe_ratio', 0),
                reverse=True
            )

            print(f"\n🏆 策略对比分析结果:")
            print(f"   对比策略数: {len(sorted_results)}")

            if sorted_results:
                best_strategy, best_result = sorted_results[0]
                best_perf = best_result.performance
                best_sharpe = best_perf.get('sharpe_ratio', 0)
                best_return = best_perf.get('total_return', 0)
                best_win_rate = best_perf.get('win_rate', 0)

                print(f"   最佳策略: {best_strategy}")
                print(f"   夏普比率: {best_sharpe:.3f}")
                print(f"   总收益率: {best_return:.2f}%")
                print(f"   胜率: {best_win_rate:.1f}%")

                # 显示前5名策略
                print(f"\n📈 策略排名 (按夏普比率):")
                for i, (strategy, result) in enumerate(sorted_results[:5], 1):
                    perf = result.performance
                    sharpe = perf.get('sharpe_ratio', 0)
                    total_return = perf.get('total_return', 0)
                    print(f"   {i:2d}. {strategy:20s} 夏普:{sharpe:6.3f} 收益:{total_return:7.2f}%")

        else:
            print(f"⚠️ 策略对比分析未产生结果")

        return comparison_results

    except Exception as e:
        print(f"❌ 策略对比分析失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="策略参数优化脚本：专门的参数优化和回测分析工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 对单个股票进行所有策略优化
  python run_optimization.py 000001

  # 对单个股票进行指定策略优化
  python run_optimization.py 000001 --strategies "双均线策略,MACD趋势策略"

  # 对多个股票进行优化
  python run_optimization.py 000001 600519 002594

  # 只进行策略对比，不进行参数优化
  python run_optimization.py 000001 --comparison-only

  # 限制优化组合数量
  python run_optimization.py 000001 --max-evaluations 50

功能说明:
  - 策略参数优化: 使用网格搜索优化策略参数，以夏普比率为目标
  - 最优参数回测: 使用优化得到的最优参数进行回测验证
  - 策略对比分析: 对比多个策略的表现
  - 结果保存: 自动保存优化结果、回测报告和可视化图表

优化配置:
  - 支持策略: 6种基础策略（双均线、MACD、RSI、布林带、KDJ、成交量突破）
  - 优化目标: 夏普比率最大化（专注风险调整收益）
  - 结果保存: data/cleaned_stocks/{股票代码}/backtest_results/{策略名称}/
        """,
    )

    parser.add_argument("symbol", help="股票代码")

    parser.add_argument("--strategies", type=str,
                        help="要优化的策略列表，用逗号分隔")

    parser.add_argument("--comparison-only", action="store_true",
                        help="只进行策略对比分析，不进行参数优化")

    parser.add_argument("--max-evaluations", type=int, default=100,
                        help="每个策略的最大参数组合评估次数 (默认: 100)")

    args = parser.parse_args()

    # 处理策略参数
    if args.strategies:
        strategy_names = [s.strip() for s in args.strategies.split(",") if s.strip()]
    else:
        strategy_names = OPTIMIZATION_CONFIG["strategies_to_optimize"]

    if args.comparison_only:
        print(f"📊 策略对比模式，策略数: {len(strategy_names)}")
    else:
        print(f"🎯 参数优化模式，策略数: {len(strategy_names)}")
        print(f"   优化目标: {OPTIMIZATION_CONFIG['objective']} ({OPTIMIZATION_CONFIG['objective_direction']})")
        print(f"   最大评估数: {args.max_evaluations}")

    print(f"\n{'='*50}")
    print(f"📊 处理股票: {args.symbol}")
    print(f"{'='*50}")

    try:
        if args.comparison_only:
            # 只进行策略对比分析
            if run_strategy_comparison(args.symbol, strategy_names):
                print(f"\n🎉 股票 {args.symbol} 策略对比完成！")
            else:
                print(f"\n⚠️ 股票 {args.symbol} 策略对比失败")
        else:
            # 进行参数优化
            optimization_count = 0
            for strategy_name in strategy_names:
                result = run_strategy_optimization(args.symbol, strategy_name, args.max_evaluations)
                if result:
                    optimization_count += 1

            if optimization_count > 0:
                print(f"\n🎉 股票 {args.symbol} 参数优化完成！优化策略数: {optimization_count}")

                # 可选：进行策略对比分析
                if OPTIMIZATION_CONFIG.get("enable_comparison", False):
                    run_strategy_comparison(args.symbol)
            else:
                print(f"\n⚠️ 股票 {args.symbol} 所有策略优化均失败")

    except Exception as e:
        print(f"\n❌ 股票 {args.symbol} 处理异常: {e}")

    print(f"\n{'='*50}")
    if args.comparison_only:
        print(f"🏁 策略对比脚本执行完成！")
    else:
        print(f"🏁 参数优化脚本执行完成！")
        print(f"   优化目标: {OPTIMIZATION_CONFIG['objective']} ({OPTIMIZATION_CONFIG['objective_direction']})")


if __name__ == "__main__":
    main()