#!/usr/bin/env python3
"""
增强策略对比脚本 - 使用最优参数进行策略对比
能够读取已有的最优参数，确保使用最优参数进行回测对比
作者：AI Assistant
创建时间：2025年11月
"""

import argparse
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

# 添加项目根目录到Python路径
current_file = Path(__file__).resolve()
project_root = current_file.parents[3]
sys.path.insert(0, str(project_root))

# 现在可以正确导入模块
from src.backtesting.facade import (
    STRATEGY_PARAM_GRIDS, read_optimized_parameters,
    generate_total_trades_csv_unified,
    ensure_output_directory,
    get_data_manager, create_strategy_by_name
)
from src.backtesting.tools import normalize_params, parse_param_string
from src.backtesting.evaluator import StrategyEvaluator, StrategyResult


# 使用统一导入管理器
# 所有公共函数都从 src.backtesting.imports 导入


def get_comparison_file(symbol: str) -> Path:
    """返回策略对比文件路径"""
    return Path(f"data/cleaned_stocks/{symbol}/backtest_results/strategy_comparison.csv")


def get_top_strategies_from_comparison(symbol: str, top_n: int = 3) -> List[str]:
    """读取策略对比文件获取排名前N的策略"""
    comparison_file = get_comparison_file(symbol)
    if not comparison_file.exists():
        return []

    try:
        df = pd.read_csv(comparison_file, encoding='utf-8')
        if '排名' not in df.columns or '策略名称' not in df.columns:
            return []
        df = df.sort_values('排名')
        return df['策略名称'].head(top_n).tolist()
    except Exception:
        return []


def format_params_for_storage(strategy_name: str, params: Dict[str, float]) -> str:
    """按策略参数网格顺序将参数字典转换为列表字符串"""
    if not params:
        return "[N/A]"

    import numpy as np

    grid = STRATEGY_PARAM_GRIDS.get(strategy_name)
    if grid:
        ordered_values = [params.get(key) for key in grid.keys()]
    else:
        ordered_values = list(params.values())

    # 清理numpy类型，转换为简单的Python类型
    clean_values = []
    for val in ordered_values:
        if val is None:
            clean_values.append(None)
        elif isinstance(val, np.integer):
            clean_values.append(int(val))      # np.int64 -> int
        elif isinstance(val, np.floating):
            # 限制浮点数小数位数为2位
            clean_values.append(round(float(val), 2))
        elif isinstance(val, (int, float)):
            # 限制浮点数小数位数为2位
            if isinstance(val, float):
                clean_values.append(round(val, 2))
            else:
                clean_values.append(val)
        elif isinstance(val, str):
            clean_values.append(val)
        else:
            clean_values.append(str(val))

    return str(clean_values)


def convert_to_strategy_results(comparison_results: Dict[str, Dict], optimized_params: Dict[str, Dict]) -> Dict[str, StrategyResult]:
    """将字典格式的回测结果转换为 StrategyResult 对象"""
    strategy_results = {}
    for strategy_name, result_dict in comparison_results.items():
        strategy_results[strategy_name] = StrategyResult(
            symbol=result_dict.get("data_info", {}).get("symbol", "Unknown"),
            strategy_name=strategy_name,
            success=True,
            performance=result_dict.get("performance", {}),
            summary=result_dict.get("summary", {}),
            error=None,
            execution_time=result_dict.get("execution_time", 0.0)
        )
    return strategy_results


def save_parameter_combinations(strategy_output_dir: Path, history: List[Dict], strategy_name: str):
    """保存参数组合结果到策略目录，按夏普比率排序"""
    try:
        if not history:
            return

        # 创建参数组合数据
        combinations = []

        # 处理历史数据，获取所有唯一的参数组合
        seen_params = set()
        unique_combinations = []

        for record in history:
            params = record.get('params', {})
            # 将参数转换为排序的字符串作为唯一标识
            param_str = "_".join([f"{k}:{v}" for k, v in sorted(params.items())])

            if param_str not in seen_params:
                seen_params.add(param_str)

                # 获取性能指标
                performance = record.get('performance', {})
                score = record.get('score', 0)  # 优化目标得分（通常是夏普比率）

                combination = {
                    '参数组合': params,  # 直接存储参数字典
                    '夏普比率': score,
                    '总收益率': performance.get('total_return', 0),
                    '年化收益率': performance.get('annual_return', 0),
                    '最大回撤': performance.get('max_drawdown', 0),
                    '胜率': performance.get('win_rate', 0),
                    '总交易次数': performance.get('total_trades', 0),
                    '盈亏比': performance.get('profit_loss_ratio', 0),
                    '卡尔玛比率': performance.get('calmar_ratio', 0),
                    '年化波动率': performance.get('volatility', 0),
                    '最终资金': performance.get('final_capital', 0),
                }
                unique_combinations.append(combination)

        # 按夏普比率降序排序
        unique_combinations.sort(key=lambda x: x['夏普比率'], reverse=True)

        # 保存到CSV（转置：参数组合作为列，参数和指标作为行）
        if unique_combinations:
            # 创建转置格式的数据
            transposed_data = []

            # 首先添加参数行
            param_indicators = set()
            for combo in unique_combinations:
                # 直接使用参数对象，无需字符串转换
                params = combo['参数组合'] if isinstance(combo['参数组合'], dict) else {}
                param_indicators.update(params.keys())

            for param in sorted(list(param_indicators))[:5]:  # 最多显示5个参数
                row_data = {'指标': f'参数_{param}'}
                for i, combo in enumerate(unique_combinations):
                    param_name = f"参数组合{i+1}"
                    # 直接使用参数对象
                    params = combo['参数组合'] if isinstance(combo['参数组合'], dict) else {}
                    value = str(params.get(param, ''))
                    row_data[param_name] = value
                transposed_data.append(row_data)

            # 然后添加指标行
            indicators = ['夏普比率', '总收益率', '年化收益率', '最大回撤', '胜率', '总交易次数', '盈亏比', '卡尔玛比率', '年化波动率', '最终资金']

            for indicator in indicators:
                row_data = {'指标': indicator}
                for i, combo in enumerate(unique_combinations):
                    param_name = f"参数组合{i+1}"
                    if indicator == '总收益率' or indicator == '年化收益率' or indicator == '最大回撤' or indicator == '胜率':
                        # 百分比格式
                        value = f"{combo[indicator]:.2f}%" if combo[indicator] != 0 else "0.00%"
                    elif indicator == '夏普比率' or indicator == '卡尔玛比率' or indicator == '盈亏比':
                        # 小数格式
                        value = f"{combo[indicator]:.3f}"
                    elif indicator == '总交易次数':
                        # 整数格式
                        value = str(int(combo[indicator]))
                    else:
                        # 默认格式
                        value = str(combo[indicator])

                    row_data[param_name] = value
                transposed_data.append(row_data)

            df = pd.DataFrame(transposed_data)
        else:
            df = pd.DataFrame()

        output_file = strategy_output_dir / "parameter_combinations.csv"
        df.to_csv(output_file, index=False, encoding='utf-8')

        print(f"   📊 参数组合结果已保存: {output_file} (共{len(unique_combinations)}个组合)")

    except Exception as e:
        print(f"   ⚠️ 参数组合保存失败: {e}")


def generate_optimized_params(symbol: str, strategy_names: List[str], max_evaluations: int) -> Dict[str, Dict[str, float]]:
    """为指定策略列表运行参数优化"""
    from src.backtesting.facade import optimize_strategy
    from pathlib import Path
    import pandas as pd

    optimized_params = {}

    for strategy_name in strategy_names:
        try:
            print(f"   🔍 开始参数优化: {strategy_name}")
            optimization_result = optimize_strategy(
                symbol=symbol,
                strategy_name=strategy_name,
                max_evaluations=max_evaluations
            )
            if optimization_result and optimization_result.best_params:
                optimized_params[strategy_name] = optimization_result.best_params
                print(f"   ✅ {strategy_name} 完成优化: {optimization_result.best_params}")

                # 保存优化结果到策略目录
                try:
                    # 创建策略输出目录
                    strategy_output_dir = Path(f"data/cleaned_stocks/{symbol}/backtest_results/{strategy_name}")
                    strategy_output_dir.mkdir(parents=True, exist_ok=True)

                    if hasattr(optimization_result, 'all_results') and optimization_result.all_results:
                        # 保存参数组合结果到策略目录，按夏普比率排序
                        save_parameter_combinations(strategy_output_dir, optimization_result.all_results, strategy_name)

                    # 保存最佳参数详情
                    if optimization_result.best_params:
                        # 将参数字典转换为DataFrame
                        param_data = []
                        for key, value in optimization_result.best_params.items():
                            param_data.append({'参数': key, '最优值': value})
                        best_params_df = pd.DataFrame(param_data)
                        best_params_df.to_csv(strategy_output_dir / "best_params.csv", index=False, encoding='utf-8')

                    print(f"   📊 {strategy_name} 优化结果已保存到: {strategy_output_dir}")

                except Exception as e:
                    print(f"   ⚠️ {strategy_name} 优化详情保存失败: {e}")

            else:
                print(f"   ⚠️ {strategy_name} 未获取有效最优参数")

        except Exception as e:
            print(f"   ❌ {strategy_name} 优化失败: {e}")

    return optimized_params


def run_individual_backtest_with_params(symbol, strategy_name, params, output_dir):
    """使用指定参数运行单个策略的回测"""
    try:
        from src.backtesting.engine import BacktestEngine
        from src.backtesting.config import BacktestConfig

        print(f"   📈 回测策略: {strategy_name} (参数: {params})")

        # 安全地创建策略实例
        param_dict = params if isinstance(params, dict) else normalize_params(strategy_name, params)
        strategy = create_strategy_by_name(strategy_name, param_dict)

        # 加载数据（不重新计算技术指标，避免覆盖已有数据）
        data_manager = get_data_manager()
        data = data_manager.load_stock_data(symbol, required_indicators=[])
        if data is None or data.empty:
            print(f"   ⚠️ 无法加载股票 {symbol} 的数据")
            return None

        # 运行回测
        engine = BacktestEngine(BacktestConfig())
        start_time = time.time()
        result = engine.run(data, strategy, output_dir=str(output_dir / strategy_name))
        result["execution_time"] = time.time() - start_time

        perf = result.get("performance", {})
        print(f"   ✅ {strategy_name} 回测完成: 收益 {perf.get('total_return', 0):.2f}%")
        return result

    except Exception as e:
        print(f"   ❌ {strategy_name} 回测失败: {e}")
        return None


def read_optimized_params_from_files(symbol: str, strategy_names: List[str]) -> Dict[str, Dict[str, float]]:
    """从各个策略的best_params.csv文件中读取优化参数"""
    import pandas as pd
    from pathlib import Path

    optimized_params = {}

    for strategy_name in strategy_names:
        best_params_file = Path(f"data/cleaned_stocks/{symbol}/backtest_results/{strategy_name}/best_params.csv")

        if best_params_file.exists():
            try:
                df = pd.read_csv(best_params_file, encoding='utf-8')
                if '参数' in df.columns and '最优值' in df.columns:
                    params_dict = {}
                    for _, row in df.iterrows():
                        param_name = row['参数']
                        param_value = row['最优值']
                        # 转换参数值类型
                        try:
                            param_str = str(param_value)
                            # 对于周期类参数，转换为整数
                            if any(keyword in param_name.lower() for keyword in ['period', 'window', 'length']):
                                params_dict[param_name] = int(float(param_str))
                            elif '.' in param_str:
                                # 限制浮点数小数位数为2位
                                params_dict[param_name] = round(float(param_str), 2)
                            else:
                                params_dict[param_name] = int(param_str)
                        except:
                            params_dict[param_name] = param_value
                    optimized_params[strategy_name] = params_dict
                    print(f"   📖 从文件读取 {strategy_name} 参数: {params_dict}")
            except Exception as e:
                print(f"   ⚠️ 读取 {strategy_name} 参数失败: {e}")

    return optimized_params


def run_enhanced_strategy_comparison(symbol: str,
                                     strategy_names: Optional[List[str]] = None,
                                     save_results: bool = True,
                                     max_evaluations: int = 10,
                                     parallel: int = 4):
    """运行增强策略对比分析，每次运行所有策略并使用最优参数"""
    print(f"\n📊 开始增强策略对比分析: {symbol}")

    try:
        from src.backtesting import get_available_strategies

        # 创建输出目录
        comparison_output_dir = ensure_output_directory(symbol)

        # 总是运行所有策略
        target_strategies = strategy_names or get_available_strategies()
        print(f"   📊 运行所有策略: {len(target_strategies)}个")

        # 从best_params.csv文件中读取已有参数
        optimized_params = read_optimized_params_from_files(symbol, target_strategies)

        # 检查哪些策略缺少最优参数，对这些策略进行优化
        strategies_without_params = []
        for strategy_name in target_strategies:
            if strategy_name not in optimized_params:
                strategies_without_params.append(strategy_name)

        if strategies_without_params:
            print(f"   🔧 {len(strategies_without_params)}个策略需要参数优化: {', '.join(strategies_without_params)}")
            # 只对缺少参数的策略进行优化
            new_params = generate_optimized_params(symbol, strategies_without_params, max_evaluations)
            optimized_params.update(new_params)
            print("   ✅ 新策略参数优化完成")
        else:
            print(f"   ✅ 所有策略已有最优参数，直接使用")

        print(f"   📊 总策略数: {len(target_strategies)}")
        print(f"   🔧 有最优参数的策略数: {len(optimized_params)}")

        # 运行每个策略的回测
        comparison_results = {}

        for strategy_name in target_strategies:
            strategy_output_dir = comparison_output_dir / strategy_name
            strategy_output_dir.mkdir(exist_ok=True)

            # 使用最优参数或默认参数
            params = optimized_params.get(strategy_name, None)

            if params:
                result = run_individual_backtest_with_params(
                    symbol, strategy_name, params, comparison_output_dir
                )
            else:
                print(f"   ⚠️ 策略 {strategy_name} 没有最优参数，使用默认参数")
                # 使用默认参数运行回测
                result = run_individual_backtest_with_params(
                    symbol, strategy_name, {}, comparison_output_dir
                )

            if result:
                comparison_results[strategy_name] = result

        if comparison_results:
            print(f"✅ 增强策略对比分析完成")

            # 显示最佳策略
            sorted_results = sorted(
                comparison_results.items(),
                key=lambda x: x[1].get('performance', {}).get('sharpe_ratio', 0),
                reverse=True
            )

            print(f"\n🏆 增强策略对比分析结果:")
            print(f"   对比策略数: {len(sorted_results)}")

            if sorted_results:
                best_strategy, best_result = sorted_results[0]
                best_perf = best_result.get("performance", {})
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
                    perf = result.get("performance", {})
                    sharpe = perf.get('sharpe_ratio', 0)
                    total_return = perf.get('total_return', 0)
                    win_rate = perf.get('win_rate', 0)
                    execution_time = result.get('execution_time', 0)
                    params_str = str(optimized_params.get(strategy, "默认"))
                    print(f"   {i:2d}. {strategy:20s} 夏普:{sharpe:6.3f} 收益:{total_return:7.2f}% 胜率:{win_rate:5.1f}% 时间:{execution_time:5.1f}s 参数:{params_str}")

            
            # 使用 evaluator 保存策略对比结果（自动覆写原文件）
            strategy_results = convert_to_strategy_results(comparison_results, optimized_params)
            evaluator = StrategyEvaluator()
            
            # 临时修改 evaluator 的 get_strategy_params 方法，使用内存中的参数
            original_get_params = evaluator.get_strategy_params
            def get_params_with_dict(strategy_name: str, symbol: str) -> str:
                if strategy_name in optimized_params:
                    return format_params_for_storage(strategy_name, optimized_params[strategy_name])
                return original_get_params(strategy_name, symbol)
            evaluator.get_strategy_params = get_params_with_dict
            
            evaluator.save_comparison_results(
                strategy_results,
                symbol=symbol,
                output_dir=str(comparison_output_dir)
            )
            print("   📄 策略对比文件 strategy_comparison.csv 已保存/覆写")

            # 生成total_trades.csv
            generate_total_trades_csv_unified(comparison_output_dir, symbol, target_strategies)
            print(f"   📄 交易信号对比文件 total_trades.csv 已生成")

        else:
            print(f"⚠️ 增强策略对比分析未产生结果")

        return comparison_results

    except Exception as e:
        print(f"❌ 增强策略对比分析失败: {e}")
        import traceback
        traceback.print_exc()
        return None


# 这些函数已移动到 common_functions.py 和相关模块
# 不再需要重复定义


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="增强策略对比分析脚本：自动处理参数调优与策略对比",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 对单个股票进行所有策略对比
  python strategy_comparison.py 000001

  # 使用指定策略列表
  python strategy_comparison.py 000001 --strategies "双均线策略,MACD趋势策略"

  # 自定义最大评估次数
  python strategy_comparison.py 000001 --max-evaluations 50

功能说明:
  - 若缺少 strategy_comparison.csv：自动逐策略调参并生成对比文件
  - 若已存在：自动读取排名前3策略并使用其最佳参数回测
  - 输出：对比表、summary、total_trades.csv 等

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

    parser.add_argument("--max-evaluations", type=int, default=10,
                        help="当需要调参时，单个策略的最大评估次数 (默认10)")
    parser.add_argument("--parallel", type=int, default=4,
                        help="并行处理的进程数 (默认4)")

    args = parser.parse_args()

    strategy_names = None
    if args.strategies:
        strategy_names = [s.strip() for s in args.strategies.split(",") if s.strip()]
        print(f"📊 指定策略数: {len(strategy_names)}")
    else:
        print(f"📊 将对比所有可用策略")

    print(f"\n{'='*60}")
    print(f"📊 处理股票: {args.symbol}")
    print(f"{'='*60}")

    try:
        result = run_enhanced_strategy_comparison(
            args.symbol,
            strategy_names=strategy_names,
            save_results=True,
            max_evaluations=args.max_evaluations,
            parallel=args.parallel
        )

        if result:
            print(f"\n🎉 股票 {args.symbol} 策略对比完成！")
        else:
            print(f"\n⚠️ 股票 {args.symbol} 策略对比失败")

    except Exception as e:
        print(f"\n❌ 股票 {args.symbol} 处理异常: {e}")

    print(f"\n{'='*60}")
    print(f"🏁 脚本执行完成！")


if __name__ == "__main__":
    main()