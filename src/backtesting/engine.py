#!/usr/bin/env python3

"""
简化的回测引擎
核心交易逻辑和性能计算
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class BacktestEngine:
    """
    简化的回测引擎
    专注于核心交易逻辑，避免不必要的复杂性
    """

    def __init__(self, config=None):
        from .config import BacktestConfig
        self.config = config or BacktestConfig()
        self.reset_state()

    def reset_state(self):
        """重置引擎状态"""
        self.cash = self.config.initial_capital
        self.position = 0
        self.avg_cost = 0
        self.trades = []
        self.equity_curve = []
        self.current_date = None

    def run(self, data: pd.DataFrame, strategy, output_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        运行回测

        Args:
            data: 股票数据
            strategy: 交易策略实例
            output_dir: 输出目录

        Returns:
            回测结果字典
        """
        logger.info(f"开始回测: {strategy.name}")

        # 重置状态
        self.reset_state()

        if not self._validate_data(data):
            raise ValueError("数据格式不正确或为空")

        data = self._filter_data_by_date(data)

        # 生成交易信号
        buy_signals, sell_signals = strategy.generate_signals(data)

        # 执行回测
        for i, (idx, row) in enumerate(data.iterrows()):
            self.current_date = row["日期"]
            price = row["收盘"]
            low_price = row["最低"]

            # 检查止损
            stop_loss_triggered = self._check_stop_loss(low_price, price)

            # 执行交易
            if not stop_loss_triggered:
                if self.position > 0 and sell_signals.iloc[i]:
                    self._execute_sell(row, "signal")
                elif self.position == 0 and buy_signals.iloc[i]:
                    self._execute_buy(row)

            # 更新权益曲线
            self._update_equity_curve(row)

        # 计算性能指标
        performance = self._calculate_performance()
        performance['strategy_name'] = strategy.name

        # 构建结果
        result = {
            "strategy_name": strategy.name,
            "trades": pd.DataFrame(self.trades),
            "equity_curve": pd.DataFrame(self.equity_curve),
            "performance": performance,
            "config": self.config,
            "raw_data": data,  # 添加原始数据供可视化使用
            "data_info": {
                "symbol": getattr(data, 'symbol', 'Unknown'),
                "start_date": data["日期"].min().strftime("%Y-%m-%d"),
                "end_date": data["日期"].max().strftime("%Y-%m-%d"),
                "total_days": len(data)
            },
            "summary": self._generate_summary(performance)
        }

        if output_dir:
            self._save_results(result, output_dir)

        logger.info(f"回测完成: 总收益 {performance['total_return']:.2f}%")
        return result

    def _validate_data(self, data: pd.DataFrame) -> bool:
        """验证数据格式"""
        required_columns = ["日期", "开盘", "最高", "最低", "收盘", "成交量"]
        return not data.empty and all(col in data.columns for col in required_columns)

    def _filter_data_by_date(self, data: pd.DataFrame) -> pd.DataFrame:
        """按日期过滤数据"""
        data = data.copy()
        data["日期"] = pd.to_datetime(data["日期"])

        if self.config.start_date:
            start_date = pd.to_datetime(self.config.start_date)
            data = data[data["日期"] >= start_date]

        if self.config.end_date:
            end_date = pd.to_datetime(self.config.end_date)
            data = data[data["日期"] <= end_date]

        return data.sort_values("日期").reset_index(drop=True)

    def _check_stop_loss(self, low_price: float, current_price: float) -> bool:
        """检查止损条件"""
        if self.position <= 0 or self.avg_cost <= 0:
            return False

        stop_loss_price = self.avg_cost * (1 - self.config.stop_loss_pct)

        if low_price <= stop_loss_price:
            # 触发止损
            actual_price = max(stop_loss_price * (1 - self.config.slippage_rate), low_price)
            self._execute_sell_at_price(actual_price, "stop_loss")
            return True

        return False

    def _execute_buy(self, row: pd.Series):
        """执行买入"""
        price = row["收盘"]
        actual_price = price * (1 + self.config.slippage_rate)
        available_cash = self.cash * self.config.position_size
        shares_to_buy = int(available_cash / actual_price / self.config.min_shares) * self.config.min_shares
        
        if shares_to_buy < self.config.min_shares:
            return
            
        total_cost = shares_to_buy * actual_price
        commission = max(total_cost * self.config.commission_rate, self.config.min_commission)
        
        if self.cash < total_cost + commission:
            return
            
        self.cash -= total_cost + commission
        self.position = shares_to_buy
        self.avg_cost = actual_price
        self.trades.append({
            "日期": self.current_date, "类型": "buy", "价格": float(price),
            "实际价格": float(actual_price), "数量": int(shares_to_buy),
            "金额": float(total_cost), "手续费": float(commission), "原因": "signal"
        })

    def _execute_sell(self, row: pd.Series, reason: str = "signal"):
        """执行卖出"""
        if self.position > 0:
            self._execute_sell_at_price(row["收盘"], reason)

    def _execute_sell_at_price(self, price: float, reason: str):
        """按指定价格卖出"""
        actual_price = price * (1 - self.config.slippage_rate)
        proceeds = self.position * actual_price
        commission = max(proceeds * self.config.commission_rate, self.config.min_commission)
        stamp_tax = proceeds * self.config.stamp_tax_rate
        net_proceeds = proceeds - commission - stamp_tax
        
        pnl = net_proceeds - (self.position * self.avg_cost)
        pnl_pct = (pnl / (self.position * self.avg_cost)) * 100 if self.avg_cost > 0 else 0
        
        self.cash += net_proceeds
        self.trades.append({
            "日期": self.current_date, "类型": "sell", "价格": float(price),
            "实际价格": float(actual_price), "数量": int(self.position),
            "收入": float(proceeds), "手续费": float(commission),
            "印花税": float(stamp_tax), "盈亏": float(pnl), "盈亏率": float(pnl_pct),
            "原因": reason, "成本价": float(self.avg_cost)
        })
        self.position = 0
        self.avg_cost = 0

    def _update_equity_curve(self, row: pd.Series):
        """更新权益曲线"""
        price = row["收盘"]
        equity = self.cash + self.position * price
        prev_equity = self.equity_curve[-1]["权益"] if self.equity_curve else equity
        daily_return = (equity / prev_equity - 1) if prev_equity > 0 else 0
        
        self.equity_curve.append({
            "日期": self.current_date, "价格": float(price), "现金": float(self.cash),
            "持仓": int(self.position), "权益": float(equity), "收益率": float(daily_return),
            "成本价": float(self.avg_cost) if self.position > 0 else 0,
            "未实现盈亏": float(self.position * (price - self.avg_cost)) if self.position > 0 else 0
        })

    def _calculate_performance(self) -> Dict[str, float]:
        """计算性能指标"""
        if not self.equity_curve:
            return {}

        initial_equity = self.config.initial_capital
        final_equity = self.equity_curve[-1]["权益"]

        # 收益指标
        total_return = (final_equity / initial_equity - 1) * 100

        # 计算年化收益率
        start_date = pd.to_datetime(self.equity_curve[0]["日期"])
        end_date = pd.to_datetime(self.equity_curve[-1]["日期"])
        days = (end_date - start_date).days
        years = max(days / 365.25, 1/365)
        annual_return = ((final_equity / initial_equity) ** (1/years) - 1) * 100

        # 收益率序列和风险指标
        returns = np.array([point["收益率"] for point in self.equity_curve[1:]])
        sharpe_ratio = (np.mean(returns) - 0.03/252) / np.std(returns) * np.sqrt(252) if len(returns) > 1 and np.std(returns) > 0 else 0

        # 最大回撤
        equity_values = np.array([point["权益"] for point in self.equity_curve])
        peak = np.maximum.accumulate(equity_values)
        drawdown = (equity_values - peak) / peak * 100
        max_drawdown = abs(np.min(drawdown))

        # 交易统计
        buy_trades = [t for t in self.trades if t["类型"] == "buy"]
        sell_trades = [t for t in self.trades if t["类型"] == "sell"]
        profitable_trades = [t for t in sell_trades if t.get("盈亏", 0) > 0]

        total_trades = len(buy_trades)
        win_rate = (len(profitable_trades) / total_trades * 100) if total_trades > 0 else 0

        # 止损统计
        stop_loss_trades = [t for t in sell_trades if t.get("reason") == "stop_loss"]
        stop_loss_rate = (len(stop_loss_trades) / total_trades * 100) if total_trades > 0 else 0

        # 盈亏比
        losing_trades = [t for t in sell_trades if t.get("盈亏", 0) <= 0]
        avg_profit = np.mean([t["盈亏"] for t in profitable_trades]) if profitable_trades else 0
        avg_loss = abs(np.mean([t["盈亏"] for t in losing_trades])) if losing_trades else 0
        profit_loss_ratio = avg_profit / avg_loss if avg_loss > 0 else (float('inf') if avg_profit > 0 else 0)

        # 波动率
        volatility = np.std(returns) * np.sqrt(252) * 100 if len(returns) > 1 else 0

        # 卡尔玛比率
        calmar_ratio = annual_return / max_drawdown if max_drawdown > 0 else 0

        return {
            "total_return": float(total_return),
            "annual_return": float(annual_return),
            "sharpe_ratio": float(sharpe_ratio),
            "calmar_ratio": float(calmar_ratio),
            "max_drawdown": float(max_drawdown),
            "volatility": float(volatility),
            "total_trades": int(total_trades),
            "win_rate": float(win_rate),
            "profit_loss_ratio": float(profit_loss_ratio),
            "stop_loss_count": len(stop_loss_trades),
            "stop_loss_rate": float(stop_loss_rate),
            "initial_capital": float(initial_equity),
            "final_capital": float(final_equity),
            "total_profit": float(sum(t.get("盈亏", 0) for t in profitable_trades)),
            "total_loss": float(abs(sum(t.get("盈亏", 0) for t in sell_trades if t.get("盈亏", 0) <= 0)))
        }

    def _generate_summary(self, performance: Dict[str, float]) -> Dict[str, Any]:
        """生成回测摘要"""
        return {
            "key_metrics": {
                # 收益指标
                "总收益率": f"{performance.get('total_return', 0):.2f}%",
                "年化收益率": f"{performance.get('annual_return', 0):.2f}%",
                "初始资金": f"{performance.get('initial_capital', 0):,.0f}",
                "最终资金": f"{performance.get('final_capital', 0):,.0f}",
                "总盈利": f"{performance.get('total_profit', 0):,.0f}",
                "总亏损": f"{performance.get('total_loss', 0):,.0f}",

                # 风险指标
                "夏普比率": f"{performance.get('sharpe_ratio', 0):.3f}",
                "卡尔玛比率": f"{performance.get('calmar_ratio', 0):.3f}",
                "最大回撤": f"{performance.get('max_drawdown', 0):.2f}%",
                "年化波动率": f"{performance.get('volatility', 0):.2f}%",

                # 交易统计
                "总交易次数": f"{performance.get('total_trades', 0)}",
                "胜率": f"{performance.get('win_rate', 0):.1f}%",
                "盈亏比": f"{performance.get('profit_loss_ratio', 0):.2f}",
                "止损次数": f"{performance.get('stop_loss_count', 0)}",
                "止损率": f"{performance.get('stop_loss_rate', 0):.1f}%"
            }
        }

    
    def _save_results(self, result: Dict[str, Any], output_dir: str):
        """保存回测结果"""
        from pathlib import Path

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        if not result["trades"].empty:
            # 按日期倒序排列trades数据
            trades_df = result["trades"].copy()
            if "日期" in trades_df.columns:
                trades_df = trades_df.sort_values("日期", ascending=False)
                print("   📅 trades数据已按日期列倒序排列")
            else:
                print("   ⚠️ 未找到trades的日期列，保持原顺序")

            trades_df.to_csv(output_path / "trades.csv", index=False, encoding='utf-8')

        if not result["equity_curve"].empty:
            # 按日期倒序排列equity_curve数据
            equity_df = result["equity_curve"].copy()
            if "日期" in equity_df.columns:
                equity_df = equity_df.sort_values("日期", ascending=False)
                print("   📅 equity_curve数据已按日期列倒序排列")
            else:
                print("   ⚠️ 未找到equity_curve的日期列，保持原顺序")

            equity_df.to_csv(output_path / "equity_curve.csv", index=False, encoding='utf-8')

        # 性能指标的中文映射
        chinese_metrics = {
            "total_return": "总收益率",
            "annual_return": "年化收益率",
            "sharpe_ratio": "夏普比率",
            "calmar_ratio": "卡尔玛比率",
            "max_drawdown": "最大回撤",
            "volatility": "年化波动率",
            "total_trades": "总交易次数",
            "win_rate": "胜率",
            "profit_loss_ratio": "盈亏比",
            "stop_loss_count": "止损次数",
            "stop_loss_rate": "止损率",
            "initial_capital": "初始资金",
            "final_capital": "最终资金",
            "total_profit": "总盈利",
            "total_loss": "总亏损"
        }

        # 保存performance.csv（中文列名）
        performance_data = []
        for metric, value in result["performance"].items():
            chinese_name = chinese_metrics.get(metric, metric)

            # 跳过非数字指标（如strategy_name）
            if not isinstance(value, (int, float)):
                performance_data.append({"指标": chinese_name, "值": str(value)})
                continue

            if metric in ["total_return", "annual_return", "max_drawdown", "volatility", "win_rate", "stop_loss_rate"]:
                # 百分比指标
                performance_data.append({"指标": chinese_name, "值": f"{value:.2f}%"})
            elif metric in ["sharpe_ratio", "calmar_ratio", "profit_loss_ratio"]:
                # 小数指标
                performance_data.append({"指标": chinese_name, "值": f"{value:.3f}"})
            elif metric in ["total_trades", "stop_loss_count"]:
                # 整数指标
                performance_data.append({"指标": chinese_name, "值": f"{int(value)}"})
            else:
                # 资金指标
                performance_data.append({"指标": chinese_name, "值": f"{value:,.0f}"})

        pd.DataFrame(performance_data).to_csv(
            output_path / "performance.csv", index=False, encoding='utf-8')

        # 保存图表
        try:
            self._save_charts(result, output_path)
        except Exception as e:
            logger.warning(f"图表保存失败: {e}")

        logger.info(f"结果已保存到: {output_dir}")

    def _save_charts(self, result: Dict[str, Any], output_path: Path):
        """保存图表"""
        try:
            from .visualizer import BacktestVisualizer

            visualizer = BacktestVisualizer()

            # 生成并保存图表
            chart_files = visualizer.save_all_charts(
                result['equity_curve'],
                result['trades'],
                result['performance'],
                output_path
            )

            # 生成技术指标图表
            if 'raw_data' in result:
                trades_path = output_path / "trades_analysis.png"
                visualizer.plot_trades_with_indicator(
                    result,
                    result['performance'].get('strategy_name', 'Unknown'),
                    output_path=str(trades_path),
                    show=False
                )
                if trades_path.exists():
                    chart_files.append(str(trades_path))

            logger.info(f"图表已保存: {len(chart_files)} 个文件")

        except ImportError:
            logger.warning("可视化模块未找到，跳过图表生成")
        except Exception as e:
            logger.warning(f"图表生成失败: {e}")