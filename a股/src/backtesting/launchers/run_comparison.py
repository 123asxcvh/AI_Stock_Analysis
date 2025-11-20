#!/usr/bin/env python3
"""
策略对比分析脚本 - 专门用于多策略对比分析
从data pipeline移转过来的策略对比功能
作者：AI Assistant
创建时间：2025年11月
"""

import argparse
import sys
from pathlib import Path

# 添加项目根目录到Python路径
current_file = Path(__file__).resolve()
project_root = current_file.parents[3]
sys.path.insert(0, str(project_root))




def run_strategy_comparison(symbol, strategy_names=None, save_results=True):
    """运行策略对比分析"""
    print(f"\n📊 开始策略对比分析: {symbol}")

    try:
        from src.backtesting.facade import get_available_strategies, BacktestConfig, get_data_manager, generate_total_trades_csv_unified
        from src.backtesting.engine import BacktestEngine
        from src.backtesting.strategies import strategy_registry
        from src.backtesting.tools import ensure_output_directory

        # 创建输出目录
        comparison_output_dir = ensure_output_directory(symbol)

        # 确定要对比的策略
        if strategy_names is None:
            strategy_names = get_available_strategies()

        print(f"   对比策略数: {len(strategy_names)}")

        # 读取已有的最优参数
        from src.backtesting.tools import read_optimized_parameters
        optimized_params = read_optimized_parameters(symbol)
        print(f"   发现最优参数的策略数: {len(optimized_params)}")

        # 手动运行每个策略的回测，使用最优参数
        comparison_results = {}
        data_manager = get_data_manager()
        data = data_manager.load_stock_data(symbol, required_indicators=[])

        if data is None or data.empty:
            print(f"❌ 无法加载股票 {symbol} 的数据")
            return None

        for strategy_name in strategy_names:
            print(f"   📈 回测策略: {strategy_name}")

            # 创建策略输出目录
            strategy_dir = comparison_output_dir / strategy_name
            strategy_dir.mkdir(exist_ok=True)

            # 使用最优参数或默认参数安全地创建策略实例
            from src.backtesting.facade import create_strategy_by_name
            from src.backtesting.tools import normalize_params, parse_param_string

            params = optimized_params.get(strategy_name, None)
            if params:
                print(f"      参数: {params}")
                # 将参数转换为字典格式
                if isinstance(params, str):
                    param_list = parse_param_string(params)
                    param_dict = normalize_params(strategy_name, param_list)
                else:
                    param_dict = params

                # 使用安全的方法创建策略实例
                try:
                    strategy = create_strategy_by_name(strategy_name, param_dict)
                except Exception as e:
                    print(f"      ⚠️ 参数设置失败，使用默认参数: {e}")
                    strategy = create_strategy_by_name(strategy_name)
            else:
                strategy = create_strategy_by_name(strategy_name)

            # 运行回测
            config = BacktestConfig()
            engine = BacktestEngine(config)
            result = engine.run(data, strategy, output_dir=str(strategy_dir))

            if result:
                comparison_results[strategy_name] = result
                perf = result["performance"]
                print(f"      ✅ 收益: {perf.get('total_return', 0):.2f}%, 夏普: {perf.get('sharpe_ratio', 0):.3f}")
            else:
                print(f"      ❌ 回测失败")

        if comparison_results:
            print(f"✅ 策略对比分析完成")

            # 显示最佳策略
            sorted_results = sorted(
                comparison_results.items(),
                key=lambda x: x[1]["performance"].get('sharpe_ratio', 0),
                reverse=True
            )

            print(f"\n🏆 策略对比分析结果:")
            print(f"   对比策略数: {len(sorted_results)}")

            if sorted_results:
                best_strategy, best_result = sorted_results[0]
                best_perf = best_result["performance"]
                best_sharpe = best_perf.get('sharpe_ratio', 0)
                best_return = best_perf.get('total_return', 0)
                best_win_rate = best_perf.get('win_rate', 0)

                print(f"   最佳策略: {best_strategy}")
                print(f"   夏普比率: {best_sharpe:.3f}")
                print(f"   总收益率: {best_return:.2f}%")
                print(f"   胜率: {best_win_rate:.1f}%")

                # 显示所有策略排名
                print(f"\n📈 策略排名 (按夏普比率):")
                for i, (strategy, result) in enumerate(sorted_results, 1):
                    perf = result["performance"]
                    sharpe = perf.get('sharpe_ratio', 0)
                    total_return = perf.get('total_return', 0)
                    win_rate = perf.get('win_rate', 0)
                    print(f"   {i:2d}. {strategy:20s} 夏普:{sharpe:6.3f} 收益:{total_return:7.2f}% 胜率:{win_rate:5.1f}%")

                # 不再生成重复的summary文件，因为strategy_comparison.csv已经包含所有信息

                # 生成total_trades.csv - 新增功能
                generate_total_trades_csv_unified(comparison_output_dir, symbol, strategy_names)
                print(f"   📄 已生成交易信号对比文件: total_trades.csv")

        else:
            print(f"⚠️ 策略对比分析未产生结果")

        return comparison_results

    except Exception as e:
        print(f"❌ 策略对比分析失败: {e}")
        import traceback
        traceback.print_exc()
        return None




def save_comparison_summary(output_dir, symbol, sorted_results):
    """保存策略对比汇总结果"""
    try:
        import pandas as pd

        # 创建汇总数据
        summary_data = []
        for i, (strategy, result) in enumerate(sorted_results, 1):
            # 处理不同的结果格式
            if hasattr(result, 'performance'):
                perf = result.performance
            elif isinstance(result, dict) and 'performance' in result:
                perf = result['performance']
            else:
                continue
            summary_data.append({
                "排名": i,
                "策略名称": strategy,
                "夏普比率": f"{perf.get('sharpe_ratio', 0):.3f}",
                "总收益率": f"{perf.get('total_return', 0):.2f}%",
                "年化收益率": f"{perf.get('annual_return', 0):.2f}%",
                "最大回撤": f"{perf.get('max_drawdown', 0):.2f}%",
                "胜率": f"{perf.get('win_rate', 0):.1f}%",
                "总交易次数": perf.get('total_trades', 0),
                "盈亏比": f"{perf.get('profit_loss_ratio', 0):.2f}",
                "卡尔玛比率": f"{perf.get('calmar_ratio', 0):.3f}",
                "年化波动率": f"{perf.get('volatility', 0):.2f}%"
            })

        # 保存汇总CSV
        summary_df = pd.DataFrame(summary_data)
        summary_csv_path = output_dir / "strategy_comparison_summary.csv"
        summary_df.to_csv(summary_csv_path, index=False, encoding='utf-8')

        print(f"   📊 策略对比汇总已保存到: {summary_csv_path}")

    except Exception as e:
        print(f"   ⚠️ 策略对比汇总保存失败: {e}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="策略对比分析脚本：多策略性能对比工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 对单个股票进行所有策略对比
  python run_comparison.py 000001

  # 对单个股票进行指定策略对比
  python run_comparison.py 000001 --strategies "双均线策略,MACD趋势策略,RSI反转策略"

  # 对多个股票进行策略对比
  python run_comparison.py 000001 600519 002594

  # 指定输出目录
  python run_comparison.py 000001 --output-dir /path/to/output

功能说明:
  - 策略对比分析: 对比多个策略在指定股票上的表现
  - 性能排名: 按夏普比率等指标对策略进行排名
  - 结果保存: 自动保存对比结果和汇总报告
  - 可视化支持: 生成策略对比图表

对比指标:
  - 夏普比率: 风险调整后的收益指标
  - 总收益率: 投资期间的总收益
  - 最大回撤: 最大亏损幅度
  - 胜率: 盈利交易占比
  - 盈亏比: 平均盈利与平均亏损的比值
        """,
    )

    parser.add_argument("symbol", help="股票代码")

    parser.add_argument("--strategies", type=str,
                        help="要对比的策略列表，用逗号分隔")

    parser.add_argument("--output-dir", type=str,
                        help="输出目录路径")

    parser.add_argument("--no-save", action="store_true",
                        help="不保存结果文件")

    args = parser.parse_args()

    # 处理策略参数
    strategy_names = None
    if args.strategies:
        strategy_names = [s.strip() for s in args.strategies.split(",") if s.strip()]
        print(f"📊 指定策略数: {len(strategy_names)}")
    else:
        print(f"📊 将对比所有可用策略")

    print(f"\n{'='*50}")
    print(f"📊 处理股票: {args.symbol}")
    print(f"{'='*50}")

    try:
        save_results = not args.no_save
        result = run_strategy_comparison(args.symbol, strategy_names, save_results)

        if result:
            print(f"\n🎉 股票 {args.symbol} 策略对比完成！")
        else:
            print(f"\n⚠️ 股票 {args.symbol} 策略对比失败")

    except Exception as e:
        print(f"\n❌ 股票 {args.symbol} 处理异常: {e}")

    print(f"\n{'='*50}")
    print(f"🏁 策略对比脚本执行完成！")


if __name__ == "__main__":
    main()