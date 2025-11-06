#!/usr/bin/env python3

"""
核心回测引擎
专注于简洁、高效的策略回测功能
"""

import dataclasses
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple, Optional

import numpy as np
import pandas as pd


@dataclass
class BacktestConfig:
    """回测配置参数"""
    initial_capital: float = 100000.0
    position_size: float = 1.0  # 每次买入使用现金的比例 (0-1)

    def __post_init__(self):
        """参数验证"""
        if not 0 < self.position_size <= 1:
            raise ValueError("position_size 必须在 (0, 1] 范围内")
        if self.initial_capital <= 0:
            raise ValueError("initial_capital 必须大于 0")


class BacktestEngine:
    """简化的回测引擎"""

    def __init__(self, config: Optional[BacktestConfig] = None):
        self.config = config or BacktestConfig()

    def run(self,
            data: pd.DataFrame,
            strategy,
            output_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        运行回测

        Args:
            data: 包含OHLCV数据的DataFrame
            strategy: 策略实例，必须有generate_signals方法
            output_dir: 结果输出目录

        Returns:
            回测结果字典
        """
        # 数据验证和准备
        data = self._prepare_data(data)

        # 生成交易信号
        buy_signals, sell_signals = self._generate_signals(data, strategy)

        # 执行回测
        trades, equity_curve = self._execute_backtest(data, buy_signals, sell_signals)

        # 计算性能指标
        performance = self._calculate_performance(equity_curve, trades)

        # 整理结果
        results = {
            "trades": pd.DataFrame(trades),
            "equity_curve": pd.DataFrame(equity_curve),
            "performance": performance,
            "config": self.config,
            "data_summary": {
                "start_date": data["日期"].min(),
                "end_date": data["日期"].max(),
                "total_days": len(data),
                "trading_days": len(data[data["成交量"] > 0])
            }
        }

        # 保存结果
        if output_dir:
            self._save_results(results, output_dir)

        return results

    def _prepare_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """准备和验证数据"""
        df = data.copy()

        # 检查必要列
        required_cols = ["日期", "开盘", "最高", "最低", "收盘", "成交量"]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"缺少必要列: {missing_cols}")

        # 数据类型转换
        df["日期"] = pd.to_datetime(df["日期"], errors="coerce")
        numeric_cols = ["开盘", "最高", "最低", "收盘", "成交量"]
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        # 数据清洗
        df = df.dropna(subset=["日期"]).sort_values("日期").reset_index(drop=True)
        df = df.dropna(subset=numeric_cols, how='any')

        return df

    def _generate_signals(self, data: pd.DataFrame, strategy) -> Tuple[pd.Series, pd.Series]:
        """生成交易信号"""
        if hasattr(strategy, 'generate_signals'):
            # 标准策略接口
            buy_signals, sell_signals = strategy.generate_signals(data)
        elif hasattr(strategy, 'generate_signals_with_reasons'):
            # 带原因的策略接口
            buy_signals, sell_signals, _, _ = strategy.generate_signals_with_reasons(data)
        else:
            raise AttributeError("策略必须有 generate_signals 或 generate_signals_with_reasons 方法")

        # 确保信号是Series类型
        if isinstance(buy_signals, np.ndarray):
            buy_signals = pd.Series(buy_signals, index=data.index)
        if isinstance(sell_signals, np.ndarray):
            sell_signals = pd.Series(sell_signals, index=data.index)

        return buy_signals.fillna(False), sell_signals.fillna(False)

    def _execute_backtest(self,
                         data: pd.DataFrame,
                         buy_signals: pd.Series,
                         sell_signals: pd.Series) -> Tuple[List[Dict], List[Dict]]:
        """执行回测交易逻辑"""

        cash = self.config.initial_capital
        position = 0
        avg_cost = 0

        trades = []
        equity_curve = []

        for i, (idx, row) in enumerate(data.iterrows()):
            price = row["收盘"]
            date = row["日期"]

            # 卖出逻辑
            if position > 0 and sell_signals.iloc[i]:
                shares_to_sell = position

                # 执行卖出（无费用计算）
                proceeds = shares_to_sell * price
                cash += proceeds

                # 记录交易
                trades.append({
                    "date": date,
                    "type": "sell",
                    "price": float(price),
                    "shares": int(shares_to_sell),
                    "proceeds": float(proceeds),
                    "pnl": float(proceeds - shares_to_sell * avg_cost),
                    "cash_after": float(cash)
                })

                position = 0
                avg_cost = 0

            # 买入逻辑
            elif position == 0 and buy_signals.iloc[i]:
                # 计算可买入数量
                available_cash = cash * self.config.position_size
                shares_to_buy = int(available_cash / price)

                if shares_to_buy > 0:
                    total_cost = shares_to_buy * price

                    # 执行买入（无费用计算）
                    if cash >= total_cost:
                        cash -= total_cost
                        position = shares_to_buy
                        avg_cost = price

                        # 记录交易
                        trades.append({
                            "date": date,
                            "type": "buy",
                            "price": float(price),
                            "shares": int(shares_to_buy),
                            "cost": float(total_cost),
                            "cash_after": float(cash)
                        })

            # 更新权益曲线
            equity = cash + position * price
            equity_curve.append({
                "date": date,
                "price": float(price),
                "cash": float(cash),
                "position": int(position),
                "equity": float(equity),
                "returns": 0.0 if len(equity_curve) == 0 else (equity / equity_curve[-1]["equity"] - 1.0)
            })

        return trades, equity_curve

    def _calculate_performance(self, equity_curve: List[Dict], trades: List[Dict]) -> Dict[str, float]:
        """计算性能指标"""
        if not equity_curve:
            return {}

        # 基础指标
        initial_equity = self.config.initial_capital
        final_equity = equity_curve[-1]["equity"]
        total_return = (final_equity / initial_equity - 1) * 100

        # 收益率序列
        returns = [point["returns"] for point in equity_curve[1:]]  # 跳过第一天
        returns = np.array(returns)

        # 年化收益率 (假设252个交易日)
        trading_days = len(equity_curve)
        years = trading_days / 252
        annual_return = (final_equity / initial_equity) ** (1/years) - 1 if years > 0 else 0
        annual_return *= 100

        # 夏普比率
        if len(returns) > 1 and np.std(returns) > 0:
            excess_return = np.mean(returns) - 0.03/252  # 假设无风险利率3%
            sharpe_ratio = excess_return / np.std(returns) * np.sqrt(252)
        else:
            sharpe_ratio = 0

        # 最大回撤
        equity_values = [point["equity"] for point in equity_curve]
        peak = equity_values[0]
        max_drawdown = 0
        for equity_val in equity_values:
            if equity_val > peak:
                peak = equity_val
            drawdown = (peak - equity_val) / peak * 100
            max_drawdown = max(max_drawdown, drawdown)

        # 交易统计
        buy_trades = [t for t in trades if t["type"] == "buy"]
        sell_trades = [t for t in trades if t["type"] == "sell"]

        total_trades = len(sell_trades)
        profitable_trades = len([t for t in sell_trades if "pnl" in t and t["pnl"] > 0])
        win_rate = (profitable_trades / total_trades * 100) if total_trades > 0 else 0

        # 盈亏比
        profits = [t["pnl"] for t in sell_trades if "pnl" in t and t["pnl"] > 0]
        losses = [abs(t["pnl"]) for t in sell_trades if "pnl" in t and t["pnl"] < 0]
        profit_factor = sum(profits) / sum(losses) if losses else float('inf')

        # 平均持仓天数
        holding_days = []
        for i, sell_trade in enumerate(sell_trades):
            if i < len(buy_trades):
                buy_date = buy_trades[i]["date"]
                sell_date = sell_trade["date"]
                holding_days.append((sell_date - buy_date).days)
        avg_holding_days = np.mean(holding_days) if holding_days else 0

        return {
            "total_return": float(total_return),
            "annual_return": float(annual_return),
            "sharpe_ratio": float(sharpe_ratio),
            "max_drawdown": float(max_drawdown),
            "total_trades": int(total_trades),
            "win_rate": float(win_rate),
            "profit_factor": float(profit_factor),
            "avg_holding_days": float(avg_holding_days),
            "initial_capital": float(initial_equity),
            "final_capital": float(final_equity)
        }

    def _save_results(self, results: Dict[str, Any], output_dir: str):
        """保存回测结果"""
        from pathlib import Path
        import os

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # 保存交易记录
        trades_path = output_path / "trades.csv"
        results["trades"].to_csv(trades_path, index=False, encoding='utf-8')
        print(f"✅ 交易记录已保存: {trades_path}")

        # 保存权益曲线
        equity_path = output_path / "equity_curve.csv"
        results["equity_curve"].to_csv(equity_path, index=False, encoding='utf-8')
        print(f"✅ 权益曲线已保存: {equity_path}")

        # 保存性能指标
        perf_path = output_path / "performance.csv"
        perf_df = pd.DataFrame({
            "指标": list(results["performance"].keys()),
            "数值": list(results["performance"].values())
        })
        perf_df.to_csv(perf_path, index=False, encoding='utf-8')
        print(f"✅ 性能指标已保存: {perf_path}")

        # 保存配置信息
        config_path = output_path / "config.json"
        import json
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(results["config"].__dict__, f, indent=2, ensure_ascii=False)
        print(f"✅ 配置信息已保存: {config_path}")


# 向后兼容的别名
BrokerParams = BacktestConfig
run_backtest_single = lambda df, strategy, params, output_dir=None: BacktestEngine(params).run(df, strategy, output_dir)