#!/usr/bin/env python3

"""
统一回测测试器
简化的策略测试工具，整合单策略和批量测试功能
"""

import argparse
import sys
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import warnings

# 添加项目根目录到Python路径
current_file = Path(__file__).resolve()
project_root = current_file.parents[3]
sys.path.insert(0, str(project_root))

from config import config
from .engine import BacktestEngine, BacktestConfig
from .indicators import indicator_calculator
from .strategies import strategy_registry
from .plotter import BacktestPlotter

warnings.filterwarnings('ignore')


class BacktestTester:
    """统一回测测试器"""

    def __init__(self):
        self.config = BacktestConfig()
        self.results = {}
        self.plotter = BacktestPlotter()

    def load_data(self, symbol: str) -> pd.DataFrame:
        """加载股票数据，检查是否包含技术指标"""
        # 加载基础数据
        data_file = config.get_stock_file_path(symbol, "historical_quotes.csv", cleaned=True)
        if not data_file.exists():
            data_file = config.get_stock_file_path(symbol, "historical_quotes.csv", cleaned=False)

        if not data_file.exists():
            raise FileNotFoundError(f"找不到股票数据文件: {data_file}")

        df = pd.read_csv(data_file)
        print(f"✅ 加载数据: {symbol} ({len(df)} 条记录)")

        # 检查是否已经包含技术指标
        existing_indicators = [col for col in df.columns if any(ind in col for ind in ['MACD', 'KDJ', 'RSI', 'BOLL', 'BBI', 'ATR'])]

        if len(existing_indicators) >= 10:  # 如果大部分指标都存在，认为数据完整
            print(f"✅ 数据已包含技术指标: {len(existing_indicators)} 个指标列")
            print(f"   总列数: {len(df.columns)}")
            return df
        else:
            print(f"⚠️ 数据缺少技术指标 (当前只有 {len(existing_indicators)} 个)")
            print("   正在计算技术指标...")

            # 计算技术指标
            df_with_indicators = indicator_calculator.calculate_all(df)
            print(f"✅ 计算指标完成: {len(df_with_indicators.columns)} 列")

            return df_with_indicators

    def test_single_strategy(self, symbol: str, strategy_name: str, output_dir: str = None) -> Dict[str, Any]:
        """测试单个策略"""
        print(f"\n🚀 测试策略: {strategy_name} on {symbol}")
        print("-" * 40)

        # 加载数据
        data = self.load_data(symbol)

        # 获取策略
        strategy = strategy_registry.get(strategy_name)
        if not strategy:
            raise ValueError(f"未知策略: {strategy_name}")

        print(f"📊 策略: {strategy}")

        # 验证数据要求
        required_indicators = strategy.get_required_indicators()
        if required_indicators:
            missing = [ind for ind in required_indicators if ind not in data.columns]
            if missing:
                raise ValueError(f"缺少指标: {missing}")

        # 运行回测
        print("🔄 运行回测...")
        engine = BacktestEngine(self.config)
        result = engine.run(data, strategy, output_dir)

        # 显示结果
        self._display_result(result, strategy_name, symbol)

        # 生成可视化图表
        if output_dir:
            self.plotter.plot_comprehensive_report(result, output_dir, show=False)

        return result

    def test_multiple_strategies(self, symbol: str, strategy_names: List[str] = None, output_dir: str = None) -> Dict[str, Dict]:
        """测试多个策略"""
        if strategy_names is None:
            strategy_names = strategy_registry.list_all()

        print(f"\n🚀 批量测试策略: {len(strategy_names)} 个策略 on {symbol}")
        print("=" * 60)

        results = {}

        for i, strategy_name in enumerate(strategy_names, 1):
            try:
                print(f"\n[{i}/{len(strategy_names)}] 测试 {strategy_name}")
                strategy_output_dir = f"{output_dir}/{strategy_name}" if output_dir else None
                result = self.test_single_strategy(symbol, strategy_name, strategy_output_dir)
                results[strategy_name] = result
                print(f"✅ {strategy_name} 测试完成")
            except Exception as e:
                print(f"❌ {strategy_name} 测试失败: {e}")
                results[strategy_name] = {"error": str(e)}

        # 比较结果
        if results:
            self._compare_results(results, symbol, output_dir)

        return results

    def test_multiple_stocks(self, symbols: List[str], strategy_name: str, output_dir: str = None) -> Dict[str, Dict]:
        """在多只股票上测试单个策略"""
        print(f"\n🚀 批量测试股票: {len(symbols)} 只股票 with {strategy_name}")
        print("=" * 60)

        results = {}

        for i, symbol in enumerate(symbols, 1):
            try:
                print(f"\n[{i}/{len(symbols)}] 测试 {symbol}")
                stock_output_dir = f"{output_dir}/{symbol}" if output_dir else None
                result = self.test_single_strategy(symbol, strategy_name, stock_output_dir)
                results[symbol] = result
                print(f"✅ {symbol} 测试完成")
            except Exception as e:
                print(f"❌ {symbol} 测试失败: {e}")
                results[symbol] = {"error": str(e)}

        # 比较结果
        if results:
            self._compare_stock_results(results, strategy_name, output_dir)

        return results

    def _display_result(self, result: Dict[str, Any], strategy_name: str, symbol: str):
        """显示回测结果"""
        performance = result.get("performance", {})
        trades = result.get("trades", pd.DataFrame())

        print("\n📊 性能指标:")
        print(f"总收益率: {performance.get('total_return', 0):.2f}%")
        print(f"年化收益率: {performance.get('annual_return', 0):.2f}%")
        print(f"夏普比率: {performance.get('sharpe_ratio', 0):.3f}")
        print(f"最大回撤: {performance.get('max_drawdown', 0):.2f}%")
        print(f"总交易次数: {performance.get('total_trades', 0)}")
        print(f"胜率: {performance.get('win_rate', 0):.2f}%")
        print(f"盈亏比: {performance.get('profit_factor', 0):.3f}")

        if not trades.empty and "pnl" in trades.columns:
            profitable_trades = (trades["pnl"] > 0).sum()
            print(f"盈利交易: {profitable_trades}/{len(trades)}")

    def _compare_results(self, results: Dict[str, Dict], symbol: str, output_dir: str = None):
        """比较策略结果"""
        print(f"\n📈 策略比较结果 - {symbol}")
        print("=" * 80)

        # 提取成功的策略结果
        successful_results = {k: v for k, v in results.items() if "error" not in v}

        if not successful_results:
            print("没有成功的策略结果")
            return

        # 创建比较表
        comparison_data = []
        for strategy_name, result in successful_results.items():
            performance = result.get("performance", {})
            comparison_data.append({
                "策略": strategy_name,
                "总收益率": performance.get("total_return", 0),
                "年化收益率": performance.get("annual_return", 0),
                "夏普比率": performance.get("sharpe_ratio", 0),
                "最大回撤": performance.get("max_drawdown", 0),
                "胜率": performance.get("win_rate", 0),
                "交易次数": performance.get("total_trades", 0)
            })

        df = pd.DataFrame(comparison_data)

        # 按总收益率排序
        df = df.sort_values("总收益率", ascending=False)

        # 显示排名
        print(f"{'排名':<4} {'策略':<20} {'收益率':<10} {'夏普比率':<10} {'最大回撤':<10} {'胜率':<8}")
        print("-" * 80)
        for i, (_, row) in enumerate(df.iterrows(), 1):
            print(f"{i:<4} {row['策略']:<20} {row['总收益率']:<10.2f} {row['夏普比率']:<10.3f} "
                  f"{row['最大回撤']:<10.2f} {row['胜率']:<8.2f}")

        # 保存比较结果
        if output_dir:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            comparison_file = output_path / "strategy_comparison.csv"
            df.to_csv(comparison_file, index=False, encoding='utf-8')
            print(f"\n✅ 比较结果已保存: {comparison_file}")

            # 生成策略比较图
            comparison_chart = output_path / "strategy_comparison.png"
            self.plotter.plot_strategy_comparison(successful_results, comparison_chart, show=False)
            print(f"✅ 策略比较图已保存: {comparison_chart}")

    def _compare_stock_results(self, results: Dict[str, Dict], strategy_name: str, output_dir: str = None):
        """比较股票结果"""
        print(f"\n📈 股票比较结果 - {strategy_name}")
        print("=" * 80)

        # 提取成功的股票结果
        successful_results = {k: v for k, v in results.items() if "error" not in v}

        if not successful_results:
            print("没有成功的股票结果")
            return

        # 创建比较表
        comparison_data = []
        for symbol, result in successful_results.items():
            performance = result.get("performance", {})
            comparison_data.append({
                "股票": symbol,
                "总收益率": performance.get("total_return", 0),
                "年化收益率": performance.get("annual_return", 0),
                "夏普比率": performance.get("sharpe_ratio", 0),
                "最大回撤": performance.get("max_drawdown", 0),
                "胜率": performance.get("win_rate", 0),
                "交易次数": performance.get("total_trades", 0)
            })

        df = pd.DataFrame(comparison_data)

        # 按总收益率排序
        df = df.sort_values("总收益率", ascending=False)

        # 显示排名
        print(f"{'排名':<4} {'股票':<8} {'收益率':<10} {'夏普比率':<10} {'最大回撤':<10} {'胜率':<8}")
        print("-" * 80)
        for i, (_, row) in enumerate(df.iterrows(), 1):
            print(f"{i:<4} {row['股票']:<8} {row['总收益率']:<10.2f} {row['夏普比率']:<10.3f} "
                  f"{row['最大回撤']:<10.2f} {row['胜率']:<8.2f}")

        # 保存比较结果
        if output_dir:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            comparison_file = output_path / "stock_comparison.csv"
            df.to_csv(comparison_file, index=False, encoding='utf-8')
            print(f"\n✅ 比较结果已保存: {comparison_file}")

    def list_strategies(self):
        """列出所有可用策略"""
        print(strategy_registry.create_summary())

    def get_available_stocks(self) -> List[str]:
        """获取可用股票列表"""
        data_dir = config.get_data_dir()
        historical_dir = data_dir / "historical_quotes"

        if not historical_dir.exists():
            return []

        stock_files = []
        for file_path in historical_dir.glob("*.csv"):
            symbol = file_path.stem
            stock_files.append(symbol)

        return sorted(stock_files)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="统一回测测试器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 列出所有策略
  python tester.py --list-strategies

  # 测试单个策略
  python tester.py 000001 --strategy macd

  # 测试所有策略
  python tester.py 000001 --all-strategies

  # 在多只股票上测试策略
  python tester.py --strategy macd --stocks 000001,000002,600519

  # 批量测试
  python tester.py 000001 --strategies macd,kdj,rsi
        """
    )

    parser.add_argument("symbols", nargs="*", help="股票代码")
    parser.add_argument("--strategy", "-s", help="策略名称")
    parser.add_argument("--strategies", help="策略列表（逗号分隔）")
    parser.add_argument("--stocks", help="股票列表（逗号分隔）")
    parser.add_argument("--all-strategies", action="store_true", help="测试所有策略")
    parser.add_argument("--list-strategies", action="store_true", help="列出所有策略")
    parser.add_argument("--output-dir", "-o", help="输出目录")

    args = parser.parse_args()

    # 创建测试器
    tester = BacktestTester()

    # 列出策略
    if args.list_strategies:
        tester.list_strategies()
        return

    # 处理股票代码
    symbols = []
    if args.symbols:
        symbols.extend(args.symbols)
    if args.stocks:
        symbols.extend([s.strip() for s in args.stocks.split(",") if s.strip()])

    # 处理策略名称
    strategy_names = []
    if args.strategy:
        strategy_names.append(args.strategy)
    if args.strategies:
        strategy_names.extend([s.strip() for s in args.strategies.split(",") if s.strip()])
    if args.all_strategies:
        strategy_names = strategy_registry.list_all()

    # 设置输出目录
    if not args.output_dir:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        args.output_dir = f"./backtest_results_{timestamp}"

    # 执行测试
    try:
        if not symbols and not args.list_strategies:
            # 如果没有指定股票，使用默认股票
            available_stocks = tester.get_available_stocks()
            if available_stocks:
                symbols = [available_stocks[0]]  # 使用第一个可用股票
                print(f"使用默认股票: {symbols[0]}")
            else:
                print("❌ 没有可用的股票数据")
                return

        if not strategy_names:
            # 如果没有指定策略，使用默认策略
            strategy_names = ["MACD策略"]
            print(f"使用默认策略: {strategy_names[0]}")

        # 执行相应的测试
        if len(symbols) == 1 and len(strategy_names) == 1:
            # 单股票单策略
            tester.test_single_strategy(symbols[0], strategy_names[0], args.output_dir)

        elif len(symbols) == 1 and len(strategy_names) > 1:
            # 单股票多策略
            tester.test_multiple_strategies(symbols[0], strategy_names, args.output_dir)

        elif len(symbols) > 1 and len(strategy_names) == 1:
            # 多股票单策略
            tester.test_multiple_stocks(symbols, strategy_names[0], args.output_dir)

        else:
            # 多股票多策略（分别测试每个策略在所有股票上的表现）
            for strategy_name in strategy_names:
                strategy_output_dir = f"{args.output_dir}/{strategy_name}"
                tester.test_multiple_stocks(symbols, strategy_name, strategy_output_dir)

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return

    print(f"\n🎉 测试完成！结果已保存到: {args.output_dir}")


if __name__ == "__main__":
    main()