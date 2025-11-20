#!/usr/bin/env python3

"""
简化的策略评估器
专注于核心评估功能，避免与engine重复
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class StrategyResult:
    """策略结果数据类"""
    symbol: str
    strategy_name: str
    success: bool
    performance: Dict[str, float]
    summary: Dict[str, Any]
    error: Optional[str] = None
    execution_time: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "symbol": self.symbol,
            "strategy_name": self.strategy_name,
            "success": self.success,
            "performance": self.performance,
            "summary": self.summary,
            "error": self.error,
            "execution_time": self.execution_time
        }


class StrategyEvaluator:
    """
    简化的策略评估器
    只保留核心的评估功能，避免与engine重复
    """

    def __init__(self, config=None):
        from .config import BacktestConfig
        from .strategies import strategy_registry
        from .data_manager import DataManager

        self.config = config or BacktestConfig()
        self.strategy_registry = strategy_registry
        self.data_manager = DataManager()

    def evaluate_strategy(self, symbol: str, strategy_name: str,
                          strategy_params: Dict[str, Any] = None) -> StrategyResult:
        """
        评估单个策略

        Args:
            symbol: 股票代码
            strategy_name: 策略名称
            strategy_params: 策略参数

        Returns:
            策略评估结果
        """
        start_time = datetime.now()

        try:
            # 加载数据（不重新计算技术指标，避免覆盖已有数据）
            data = self.data_manager.load_stock_data(symbol, required_indicators=[])
            if data.empty:
                return StrategyResult(
                    symbol=symbol,
                    strategy_name=strategy_name,
                    success=False,
                    performance={},
                    summary={},
                    error=f"无法加载股票数据: {symbol}",
                    execution_time=0
                )

            # 获取策略类
            strategy_template = self.strategy_registry.get(strategy_name)
            if not strategy_template:
                return StrategyResult(
                    symbol=symbol,
                    strategy_name=strategy_name,
                    success=False,
                    performance={},
                    summary={},
                    error=f"策略不存在: {strategy_name}",
                    execution_time=0
                )

            # 安全地创建策略实例，传入参数
            from .facade import create_strategy_by_name
            strategy = create_strategy_by_name(strategy_name, strategy_params)

            # 执行回测
            from .engine import BacktestEngine
            engine = BacktestEngine(self.config)
            result = engine.run(data, strategy)

            execution_time = (datetime.now() - start_time).total_seconds()

            return StrategyResult(
                symbol=symbol,
                strategy_name=strategy_name,
                success=True,
                performance=result['performance'],
                summary=result['summary'],
                error=None,
                execution_time=execution_time
            )

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"评估策略失败 {strategy_name} on {symbol}: {e}")
            return StrategyResult(
                symbol=symbol,
                strategy_name=strategy_name,
                success=False,
                performance={},
                summary={},
                error=str(e),
                execution_time=execution_time
            )

    def compare_strategies(self, symbol: str, strategy_names: List[str] = None, save_results: bool = True) -> Dict[str, StrategyResult]:
        """
        比较多个策略

        Args:
            symbol: 股票代码
            strategy_names: 策略名称列表
            save_results: 是否保存结果

        Returns:
            策略比较结果
        """
        if strategy_names is None:
            strategy_names = self.strategy_registry.list_all()

        logger.info(f"开始比较 {len(strategy_names)} 个策略 on {symbol}")

        results = {}
        for strategy_name in strategy_names:
            result = self.evaluate_strategy(symbol, strategy_name)
            results[strategy_name] = result
            status = "✅" if result.success else "❌"
            logger.info(f"{status} {strategy_name}")

        # 保存结果（如果需要）
        if save_results:
            from .tools import ensure_output_directory
            output_dir = ensure_output_directory(symbol)
            self.save_comparison_results(results, symbol, str(output_dir))

        return results

    def get_strategy_params(self, strategy_name: str, symbol: str) -> str:
        """获取策略的最优参数"""
        try:
            from pathlib import Path
            # 获取项目根目录
            current_dir = Path(__file__).parent.parent.parent
            param_file = current_dir / "data" / "cleaned_stocks" / symbol / "backtest_results" / strategy_name / "optimization_results.csv"

            if param_file.exists():
                param_df = pd.read_csv(param_file, encoding='utf-8')
                # 找到参数行，提取第一列（组合1）的参数值
                param_rows = param_df[param_df['指标'].str.contains('参数_')]
                params = []
                for _, row in param_rows.iterrows():
                    param_value = row.get('组合1', '')
                    if param_value and param_value != '':
                        params.append(str(param_value))
                return f"[{','.join(params)}]" if params else "[N/A]"
        except Exception as e:
            logger.debug(f"获取{strategy_name}参数失败: {e}")
        return "[N/A]"

    def create_comparison_table(self, results: Dict[str, StrategyResult],
                               sort_by: str = "sharpe_ratio", symbol: str = None) -> pd.DataFrame:
        """创建策略比较表格 - 包含15个标准指标和参数列"""
        rows = []
        for name, r in results.items():
            if r.success:
                # 获取策略参数
                params = self.get_strategy_params(name, symbol) if symbol else "[N/A]"

                # 处理盈亏比的特殊显示
                pl_ratio = r.performance.get('profit_loss_ratio', 0)
                pl_display = f"{pl_ratio:.2f}" if pl_ratio != float('inf') else "inf"

                row = {
                    "策略名称": name,
                    "参数": params,
                    "总收益率": f"{r.performance.get('total_return', 0):.2f}%",
                    "年化收益率": f"{r.performance.get('annual_return', 0):.2f}%",
                    "夏普比率": f"{r.performance.get('sharpe_ratio', 0):.3f}",
                    "卡尔玛比率": f"{r.performance.get('calmar_ratio', 0):.3f}",
                    "最大回撤": f"{r.performance.get('max_drawdown', 0):.2f}%",
                    "年化波动率": f"{r.performance.get('volatility', 0):.2f}%",
                    "总交易次数": r.performance.get('total_trades', 0),
                    "胜率": f"{r.performance.get('win_rate', 0):.1f}%",
                    "盈亏比": pl_display,
                    "止损次数": r.performance.get('stop_loss_count', 0),
                    "止损率": f"{r.performance.get('stop_loss_rate', 0):.2f}%",
                    "初始资金": f"{int(r.performance.get('initial_capital', 0)):,}",
                    "最终资金": f"{int(r.performance.get('final_capital', 0)):,}",
                    "总盈利": f"{int(r.performance.get('total_profit', 0)):,}",
                    "总亏损": f"{int(r.performance.get('total_loss', 0)):,}",
                    "执行时间(s)": f"{r.execution_time:.2f}"
                }
                rows.append(row)

        if not rows:
            return pd.DataFrame()

        df = pd.DataFrame(rows)

        # 按指定指标排序（默认按夏普比率降序）
        if sort_by == "sharpe_ratio":
            df = df.sort_values("夏普比率", ascending=False)
        elif sort_by == "total_return":
            df["_sort"] = df["总收益率"].str.rstrip("%").astype(float)
            df = df.sort_values("_sort", ascending=False).drop(columns=["_sort"])
        elif sort_by == "max_drawdown":
            df["_sort"] = df["最大回撤"].str.rstrip("%").astype(float)
            df = df.sort_values("_sort", ascending=True).drop(columns=["_sort"])
        elif sort_by == "win_rate":
            df["_sort"] = df["胜率"].str.rstrip("%").astype(float)
            df = df.sort_values("_sort", ascending=False).drop(columns=["_sort"])

        # 添加排名列
        df.insert(0, '排名', range(1, len(df) + 1))

        return df.reset_index(drop=True)

    def save_comparison_results(self, results: Dict[str, StrategyResult],
                               symbol: str, output_dir: str) -> None:
        """
        保存策略对比结果到CSV和生成图表

        Args:
            results: 策略对比结果
            symbol: 股票代码
            output_dir: 输出目录
        """
        try:
            import pandas as pd
            from pathlib import Path

            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            # 创建包含参数和15个标准指标的对比表格
            comparison_df = self.create_comparison_table(
                results,
                sort_by="sharpe_ratio",
                symbol=symbol
            )

            if not comparison_df.empty:
                # 保存为CSV文件（无日期命名）
                comparison_csv_path = output_path / "strategy_comparison.csv"
                comparison_df.to_csv(comparison_csv_path, index=False, encoding='utf-8')
                logger.info(f"策略对比结果已保存: {comparison_csv_path}")

                # 生成策略比较图表
                self._generate_comparison_chart(results, output_path)
            else:
                logger.warning("策略对比表格为空")

        except Exception as e:
            logger.error(f"保存策略对比结果失败: {e}")

    def _generate_comparison_chart(self, results: Dict[str, StrategyResult], output_path: Path) -> None:
        """生成策略比较图表"""
        try:
            from .visualizer import BacktestVisualizer
            visualizer = BacktestVisualizer()

            # 将StrategyResult结果转换为可视化器需要的格式，并按夏普比率排序
            viz_results = {}
            sorted_results = sorted(
                results.items(),
                key=lambda x: x[1].performance.get('sharpe_ratio', 0),
                reverse=True
            )

            for strategy_name, strategy_result in sorted_results:
                if hasattr(strategy_result, 'performance') and strategy_result.performance:
                    viz_results[strategy_name] = {
                        "performance": strategy_result.performance,
                        "strategy_name": strategy_name,
                        "success": strategy_result.success
                    }

            if viz_results:
                chart_path = output_path / "strategy_comparison.png"
                visualizer.plot_strategy_comparison(
                    viz_results,
                    output_path=str(chart_path),
                    show=False
                )
                logger.info(f"策略比较图表已保存: {chart_path}")

        except Exception as e:
            logger.error(f"生成策略比较图表失败: {e}")

    def get_top_strategies(self, results: Dict[str, StrategyResult],
                          metric: str = "sharpe_ratio", top_n: int = 5) -> List[StrategyResult]:
        """获取表现最佳的策略"""
        successful_results = [r for r in results.values() if r.success]
        if not successful_results:
            return []

        key_map = {
            "total_return": lambda r: r.performance.get('total_return', 0),
            "max_drawdown": lambda r: -r.performance.get('max_drawdown', 0),
            "win_rate": lambda r: r.performance.get('win_rate', 0),
            "sharpe_ratio": lambda r: r.performance.get('sharpe_ratio', 0)
        }
        key_func = key_map.get(metric, key_map["sharpe_ratio"])
        return sorted(successful_results, key=key_func, reverse=True)[:top_n]