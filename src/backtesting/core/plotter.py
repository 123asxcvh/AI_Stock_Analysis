#!/usr/bin/env python3

"""
回测结果可视化模块
提供图表绘制功能，展示策略表现
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.font_manager import FontProperties
from pathlib import Path
from typing import Dict, Any, Optional, List
import seaborn as sns

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'Arial']
plt.rcParams['axes.unicode_minus'] = False


class BacktestPlotter:
    """回测结果可视化器"""

    def __init__(self):
        self.style = 'seaborn-v0_8'
        self.figsize = (12, 8)
        self.dpi = 300

    def plot_equity_curve(self, result: Dict[str, Any], output_path: Optional[str] = None, show: bool = True):
        """
        绘制权益曲线图

        Args:
            result: 回测结果
            output_path: 图片保存路径
            show: 是否显示图片
        """
        equity_curve = result.get("equity_curve", pd.DataFrame())
        if equity_curve.empty:
            print("❌ 没有权益曲线数据")
            return

        # 创建图表
        fig, ax = plt.subplots(figsize=self.figsize)
        fig.patch.set_facecolor('white')

        # 绘制权益曲线
        ax.plot(equity_curve["date"], equity_curve["equity"],
                linewidth=2, color='#2E86AB', label='权益曲线')

        # 设置图表样式
        ax.set_title('权益曲线', fontsize=16, fontweight='bold', pad=20)
        ax.set_xlabel('日期', fontsize=12)
        ax.set_ylabel('权益 (元)', fontsize=12)
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=12)

        # 格式化x轴日期
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)

        # 添加初始资金线
        config = result.get("config", {})
        if hasattr(config, 'initial_capital'):
            initial_capital = config.initial_capital
        else:
            initial_capital = config.get("initial_capital", 100000) if isinstance(config, dict) else 100000
        ax.axhline(y=initial_capital, color='red', linestyle='--', alpha=0.5, label=f'初始资金: {initial_capital:,.0f}')

        plt.tight_layout()

        # 保存图片
        if output_path:
            plt.savefig(output_path, dpi=self.dpi, bbox_inches='tight')
            print(f"✅ 权益曲线图已保存: {output_path}")

        # 显示图片
        if show:
            plt.show()
        else:
            plt.close()

    def plot_trades(self, result: Dict[str, Any], output_path: Optional[str] = None, show: bool = True):
        """
        绘制交易点图

        Args:
            result: 回测结果
            output_path: 图片保存路径
            show: 是否显示图片
        """
        equity_curve = result.get("equity_curve", pd.DataFrame())
        trades = result.get("trades", pd.DataFrame())

        if equity_curve.empty or trades.empty:
            print("❌ 缺少权益曲线或交易数据")
            return

        # 创建图表
        fig, ax = plt.subplots(figsize=self.figsize)
        fig.patch.set_facecolor('white')

        # 绘制价格曲线
        ax.plot(equity_curve["date"], equity_curve["price"],
                linewidth=1.5, color='gray', alpha=0.7, label='价格')

        # 标记买卖点
        buy_trades = trades[trades["type"] == "buy"]
        sell_trades = trades[trades["type"] == "sell"]

        if not buy_trades.empty:
            buy_dates = pd.to_datetime(buy_trades["date"])
            buy_prices = buy_trades["price"]
            ax.scatter(buy_dates, buy_prices, color='red', s=100, marker='^',
                       label=f'买入点 ({len(buy_trades)}个)', zorder=5)

        if not sell_trades.empty:
            sell_dates = pd.to_datetime(sell_trades["date"])
            sell_prices = sell_trades["price"]
            ax.scatter(sell_dates, sell_prices, color='green', s=100, marker='v',
                       label=f'卖出点 ({len(sell_trades)}个)', zorder=5)

        # 设置图表样式
        ax.set_title('交易点分布', fontsize=16, fontweight='bold', pad=20)
        ax.set_xlabel('日期', fontsize=12)
        ax.set_ylabel('价格 (元)', fontsize=12)
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=12)

        # 格式化x轴日期
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)

        plt.tight_layout()

        # 保存图片
        if output_path:
            plt.savefig(output_path, dpi=self.dpi, bbox_inches='tight')
            print(f"✅ 交易点图已保存: {output_path}")

        # 显示图片
        if show:
            plt.show()
        else:
            plt.close()

    def plot_drawdown(self, result: Dict[str, Any], output_path: Optional[str] = None, show: bool = True):
        """
        绘制回撤图

        Args:
            result: 回测结果
            output_path: 图片保存路径
            show: 是否显示图片
        """
        equity_curve = result.get("equity_curve", pd.DataFrame())
        if equity_curve.empty:
            print("❌ 没有权益曲线数据")
            return

        # 计算回撤
        equity_values = equity_curve["equity"].values
        peak = np.maximum.accumulate(equity_values)
        drawdown = (equity_values - peak) / peak * 100

        # 创建图表
        fig, ax = plt.subplots(figsize=self.figsize)
        fig.patch.set_facecolor('white')

        # 绘制回撤曲线
        ax.fill_between(equity_curve["date"], 0, drawdown,
                         where=(drawdown < 0), color='red', alpha=0.3, label='回撤区域')
        ax.plot(equity_curve["date"], drawdown, linewidth=2, color='red', label='回撤曲线')

        # 标记最大回撤
        max_dd_idx = np.argmin(drawdown)
        max_dd_date = equity_curve["date"].iloc[max_dd_idx]
        max_dd_value = drawdown[max_dd_idx]

        ax.scatter(max_dd_date, max_dd_value, color='darkred', s=200, marker='o',
                   zorder=5, label=f'最大回撤: {max_dd_value:.2f}%')
        ax.annotate(f'{max_dd_value:.2f}%',
                    xy=(max_dd_date, max_dd_value),
                    xytext=(10, 10), textcoords='offset points',
                    fontsize=12, color='darkred')

        # 设置图表样式
        ax.set_title('回撤分析', fontsize=16, fontweight='bold', pad=20)
        ax.set_xlabel('日期', fontsize=12)
        ax.set_ylabel('回撤 (%)', fontsize=12)
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=12)
        ax.axhline(y=0, color='black', linestyle='-', alpha=0.3)

        # 格式化x轴日期
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)

        plt.tight_layout()

        # 保存图片
        if output_path:
            plt.savefig(output_path, dpi=self.dpi, bbox_inches='tight')
            print(f"✅ 回撤图已保存: {output_path}")

        # 显示图片
        if show:
            plt.show()
        else:
            plt.close()

    def plot_monthly_returns(self, result: Dict[str, Any], output_path: Optional[str] = None, show: bool = True):
        """
        绘制月度收益热力图

        Args:
            result: 回测结果
            output_path: 图片保存路径
            show: 是否显示图片
        """
        equity_curve = result.get("equity_curve", pd.DataFrame())
        if equity_curve.empty:
            print("❌ 没有权益曲线数据")
            return

        # 准备数据
        equity_curve = equity_curve.copy()
        equity_curve["date"] = pd.to_datetime(equity_curve["date"])
        equity_curve.set_index("date", inplace=True)

        # 计算月度收益
        monthly_equity = equity_curve["equity"].resample("M").last()
        monthly_returns = monthly_equity.pct_change().dropna() * 100

        if len(monthly_returns) == 0:
            print("❌ 无法计算月度收益")
            return

        # 创建年-月索引
        monthly_returns.index = pd.to_datetime(monthly_returns.index)
        monthly_returns = monthly_returns.to_frame()  # 转换为DataFrame
        monthly_returns["year"] = monthly_returns.index.year
        monthly_returns["month"] = monthly_returns.index.month

        # 创建透视表
        pivot_data = monthly_returns.pivot(index="year", columns="month", values="equity")

        # 设置月份名称
        month_names = ['1月', '2月', '3月', '4月', '5月', '6月',
                      '7月', '8月', '9月', '10月', '11月', '12月']
        if len(pivot_data.columns) > 0:
            pivot_data.columns = [month_names[i-1] for i in pivot_data.columns]

        # 创建热力图
        plt.figure(figsize=(14, 8))
        sns.heatmap(pivot_data, annot=True, fmt=".2f", cmap="RdYlGn", center=0,
                   cbar_kws={'label': '收益率 (%)'})
        plt.title('月度收益热力图', fontsize=16, fontweight='bold', pad=20)
        plt.xlabel('月份', fontsize=12)
        plt.ylabel('年份', fontsize=12)

        plt.tight_layout()

        # 保存图片
        if output_path:
            plt.savefig(output_path, dpi=self.dpi, bbox_inches='tight')
            print(f"✅ 月度收益热力图已保存: {output_path}")

        # 显示图片
        if show:
            plt.show()
        else:
            plt.close()

    def plot_comprehensive_report(self, result: Dict[str, Any], output_dir: str, show: bool = False):
        """
        生成综合图表报告

        Args:
            result: 回测结果
            output_dir: 输出目录
            show: 是否显示图片
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # 生成多个图表
        self.plot_equity_curve(result, str(output_path / "equity_curve.png"), show=False)
        self.plot_trades(result, str(output_path / "trades.png"), show=False)
        self.plot_drawdown(result, str(output_path / "drawdown.png"), show=False)
        self.plot_monthly_returns(result, str(output_path / "monthly_returns.png"), show=False)

        print(f"✅ 综合图表报告已生成，保存到: {output_dir}")

    def plot_strategy_comparison(self, results: Dict[str, Dict[str, Any]], output_path: Optional[str] = None, show: bool = True):
        """
        绘制策略比较图

        Args:
            results: 多个策略的结果字典
            output_path: 图片保存路径
            show: 是否显示图片
        """
        if not results:
            print("❌ 没有策略结果数据")
            return

        # 创建图表
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
        fig.patch.set_facecolor('white')

        # 准备数据
        comparison_data = []
        for strategy_name, result in results.items():
            equity_curve = result.get("equity_curve", pd.DataFrame())
            if not equity_curve.empty:
                performance = result.get("performance", {})
                comparison_data.append({
                    "策略": strategy_name,
                    "总收益率": performance.get("total_return", 0),
                    "最大回撤": performance.get("max_drawdown", 0),
                    "夏普比率": performance.get("sharpe_ratio", 0)
                })

        df = pd.DataFrame(comparison_data)
        if df.empty:
            print("❌ 没有有效的比较数据")
            return

        # 绘制收益率和回撤对比
        x_pos = np.arange(len(df))
        width = 0.35

        bars1 = ax1.bar(x_pos - width/2, df["总收益率"], width, label='总收益率', color='skyblue')
        bars2 = ax1.bar(x_pos + width/2, -df["最大回撤"], width, label='最大回撤', color='lightcoral')

        ax1.set_title('策略收益与回撤对比', fontsize=14, fontweight='bold')
        ax1.set_ylabel('百分比 (%)')
        ax1.set_xticks(x_pos)
        ax1.set_xticklabels(df["策略"], rotation=45)
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        ax1.axhline(y=0, color='black', linestyle='-', alpha=0.3)

        # 添加数值标签
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                ax1.annotate(f'{height:.1f}%',
                            xy=(bar.get_x() + bar.get_width() / 2, height),
                            xytext=(0, 3 if height > 0 else -15),
                            textcoords="offset points",
                            ha='center', va='bottom' if height > 0 else 'top',
                            fontsize=9)

        # 绘制夏普比率对比
        bars3 = ax2.bar(x_pos, df["夏普比率"], color='gold', alpha=0.7)

        ax2.set_title('策略夏普比率对比', fontsize=14, fontweight='bold')
        ax2.set_ylabel('夏普比率')
        ax2.set_xticks(x_pos)
        ax2.set_xticklabels(df["策略"], rotation=45)
        ax2.grid(True, alpha=0.3)
        ax2.axhline(y=0, color='black', linestyle='-', alpha=0.3)

        # 添加数值标签
        for bar in bars3:
            height = bar.get_height()
            ax2.annotate(f'{height:.3f}',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3 if height > 0 else -15),
                        textcoords="offset points",
                        ha='center', va='bottom' if height > 0 else 'top',
                        fontsize=9)

        plt.tight_layout()

        # 保存图片
        if output_path:
            plt.savefig(output_path, dpi=self.dpi, bbox_inches='tight')
            print(f"✅ 策略比较图已保存: {output_path}")

        # 显示图片
        if show:
            plt.show()
        else:
            plt.close()


# 全局绘图器实例
plotter = BacktestPlotter()


# 便捷函数
def plot_backtest_result(result: Dict[str, Any], output_dir: str = None, show: bool = False):
    """便捷函数：绘制回测结果"""
    if output_dir:
        plotter.plot_comprehensive_report(result, output_dir, show)
    else:
        plotter.plot_equity_curve(result, show=show)


def plot_strategy_comparison(results: Dict[str, Dict[str, Any]], output_path: str = None, show: bool = True):
    """便捷函数：绘制策略比较"""
    plotter.plot_strategy_comparison(results, output_path, show)