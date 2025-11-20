#!/usr/bin/env python3
"""
简化的可视化模块
重构消除冗余，统一配置驱动
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from pathlib import Path
from typing import Dict, List, Any, Tuple
import logging

from .evaluator import StrategyResult

logger = logging.getLogger(__name__)


# ==================== 配置和常量 ====================

class StandardColumns:
    """标准列名定义 - 使用中文为默认"""
    # 基础数据列
    DATE = "日期"
    OPEN = "开盘"
    HIGH = "最高"
    LOW = "最低"
    CLOSE = "收盘"
    VOLUME = "成交量"

    # 权益曲线列
    EQUITY = "权益"
    CASH = "现金"
    POSITION = "持仓"
    AVG_COST = "成本价"
    UNREALIZED_PNL = "未实现盈亏"
    RETURNS = "收益率"

    # 交易列
    TRADE_TYPE = "类型"
    TRADE_PRICE = "价格"
    ACTUAL_PRICE = "实际价格"
    SHARES = "数量"
    AMOUNT = "金额"
    COMMISSION = "手续费"
    STAMP_TAX = "印花税"
    AVG_COST = "成本价"
    PNL = "盈亏"
    PNL_PCT = "盈亏率"
    REASON = "原因"


# 技术指标类型枚举
class IndicatorType:
    MACD = "macd"
    KDJ = "kdj"
    RSI = "rsi"
    MA = "ma"
    EMA = "ema"
    BOLLINGER = "bollinger"
    VOLUME = "volume"


# 策略指标映射 - 消除数据耦合
STRATEGY_INDICATOR_MAP = {
    "双均线策略": [IndicatorType.MA],
    "MACD趋势策略": [IndicatorType.MACD],
    "KDJ超卖反弹策略": [IndicatorType.KDJ],
    "KDJ+布林带系统": [IndicatorType.KDJ, IndicatorType.BOLLINGER],
    "KDJ+MACD双重确认策略": [IndicatorType.KDJ, IndicatorType.MACD],
    "RSI反转策略": [IndicatorType.RSI],
    "布林带策略": [IndicatorType.BOLLINGER],
    "成交量突破策略": [IndicatorType.VOLUME],
    "双EMA策略": [IndicatorType.EMA],
    "MACD+KDJ双重确认策略": [IndicatorType.MACD, IndicatorType.KDJ],
    "RSI背离策略": [IndicatorType.RSI],
    "均线多头排列策略": [IndicatorType.MA],
    "布林带收缩策略": [IndicatorType.BOLLINGER],
    "量价配合策略": [IndicatorType.VOLUME, IndicatorType.MA],
    "MACD柱状图策略": [IndicatorType.MACD],
    "布林带RSI反转策略": [IndicatorType.BOLLINGER, IndicatorType.RSI],
    "双ATR反转策略": [IndicatorType.MA],  # 简化处理
    "KDJ钝化策略": [IndicatorType.KDJ],
    "RSI趋势策略": [IndicatorType.RSI],

    # 新增的20个策略指标映射
    "布林带+RSI反转策略": [IndicatorType.BOLLINGER, IndicatorType.RSI],
    "双ATR反转策略": [IndicatorType.MA],  # 使用MA代替ATR绘图
    "VWAP反转策略": [IndicatorType.VOLUME],  # 使用VOLUME指标显示
    "KDJ+MACD反转策略": [IndicatorType.KDJ, IndicatorType.MACD],
    "移动平均线组合反转策略": [IndicatorType.MA],
    "MACD柱状图反转策略": [IndicatorType.MACD],
    "波动率收缩突破策略": [IndicatorType.BOLLINGER],
    "RSI+价格形态反转策略": [IndicatorType.RSI],
    "MACD零轴反转策略": [IndicatorType.MACD],
    "三重均线反转策略": [IndicatorType.MA],
    "价格通道突破反转策略": [IndicatorType.RSI],  # 使用RSI作为代表
    "CCI+布林带反转策略": [IndicatorType.BOLLINGER],  # CCI指标暂无绘图，用布林带代替
    "形态突破+趋势过滤策略": [IndicatorType.RSI],  # 使用RSI作为代表
    "趋势线反转策略": [IndicatorType.MA],
    "动态带宽反转策略": [IndicatorType.BOLLINGER],
    "多周期协同反转策略": [IndicatorType.MACD],
    "波动率加权反转策略": [IndicatorType.BOLLINGER],
    "吊灯止损反转策略": [IndicatorType.MA],
    "多因子反转策略": [IndicatorType.RSI],
    "趋势衰竭反转策略": [IndicatorType.MACD]
}


# 统一的指标绘制配置
INDICATOR_PLOTTERS = {
    IndicatorType.MACD: {
        "required_columns": ["MACD_DIF", "MACD_DEA", "MACD_HIST"],
        "plot_func": "_plot_macd",
        "title": "MACD指标",
        "ylabel": "MACD"
    },
    IndicatorType.KDJ: {
        "required_columns": ["DAILY_KDJ_K", "DAILY_KDJ_D", "DAILY_KDJ_J"],
        "plot_func": "_plot_kdj",
        "title": "KDJ指标",
        "ylabel": "KDJ",
        "ylim": (-20, 120),
        "reference_lines": [(80, 'red', '--', 0.5, '超买线'), (20, 'green', '--', 0.5, '超卖线')]
    },
    IndicatorType.RSI: {
        "required_columns": ["RSI"],
        "plot_func": "_plot_rsi",
        "title": "RSI指标",
        "ylabel": "RSI",
        "ylim": (0, 100),
        "reference_lines": [(70, 'red', '--', 0.7), (30, 'green', '--', 0.7), (50, 'gray', ':', 0.5)],
        "fill_zones": [(70, 100, 0.1, 'red'), (0, 30, 0.1, 'green')]
    },
    IndicatorType.MA: {
        "required_columns": ["MA5", "MA10", "MA20", "MA60"],
        "plot_func": "_plot_ma",
        "title": "均线指标",
        "ylabel": "价格 (元)",
        "colors": ['red', 'orange', 'blue', 'green'],
        "labels": ['MA5', 'MA10', 'MA20', 'MA60']
    },
    IndicatorType.EMA: {
        "required_columns": ["EMA12", "EMA26"],
        "plot_func": "_plot_ema",
        "title": "EMA指标",
        "ylabel": "价格 (元)",
        "colors": ['red', 'blue'],
        "labels": ['EMA12', 'EMA26']
    },
    IndicatorType.BOLLINGER: {
        "required_columns": ["BOLL_UPPER", "BOLL_MIDDLE", "BOLL_LOWER"],
        "plot_func": "_plot_bollinger",
        "title": "布林带指标",
        "ylabel": "价格 (元)",
        "fill_between": True
    },
    IndicatorType.VOLUME: {
        "required_columns": ["成交量", "VOLUME_MA20"],
        "plot_func": "_plot_volume",
        "title": "成交量指标",
        "ylabel": "成交量"
    }
}


# ==================== 字体配置 ====================

def setup_chinese_font():
    """设置中文字体配置"""
    available_fonts = [f.name for f in fm.fontManager.ttflist]
    available_fonts = sorted(list(set(available_fonts)))

    chinese_fonts = ['SimHei', 'Hiragino Sans GB', 'STHeiti', 'STFangsong']
    fallback_fonts = ['Arial', 'Helvetica', 'Times New Roman', 'Verdana']

    available_chinese = [f for f in chinese_fonts if f in available_fonts]
    available_fallback = [f for f in fallback_fonts if f in available_fonts]

    if not available_chinese:
        primary_font = available_fallback[0] if available_fallback else 'Arial'
        font_list = available_fallback
    else:
        primary_font = available_chinese[0]
        font_list = available_chinese + available_fallback

    plt.rcParams['font.family'] = primary_font
    plt.rcParams['font.sans-serif'] = font_list
    plt.rcParams['axes.unicode_minus'] = False

    # 统一设置文本样式
    plt.rcParams['font.size'] = 12
    plt.rcParams['axes.titlesize'] = 14
    plt.rcParams['axes.labelsize'] = 12
    plt.rcParams['xtick.labelsize'] = 10
    plt.rcParams['ytick.labelsize'] = 10
    plt.rcParams['legend.fontsize'] = 11

    return primary_font


# ==================== 数据处理 ====================

class DataProcessor:
    """数据处理器 - 统一数据格式化"""

    @staticmethod
    def prepare_data(data: pd.DataFrame, data_type: str) -> pd.DataFrame:
        """统一数据预处理"""
        if data.empty:
            return data

        data = data.copy()

        # 标准化列名映射
        if data_type == "stock":
            mapping = {
                "date": StandardColumns.DATE, "open": StandardColumns.OPEN,
                "high": StandardColumns.HIGH, "low": StandardColumns.LOW,
                "close": StandardColumns.CLOSE, "volume": StandardColumns.VOLUME
            }
        elif data_type == "equity":
            mapping = {
                "date": StandardColumns.DATE, "equity": StandardColumns.EQUITY,
                "cash": StandardColumns.CASH, "position": StandardColumns.POSITION,
                "returns": StandardColumns.RETURNS, "avg_cost": StandardColumns.AVG_COST,
                "unrealized_pnl": StandardColumns.UNREALIZED_PNL
            }
        elif data_type == "trades":
            mapping = {
                "date": StandardColumns.DATE, "type": StandardColumns.TRADE_TYPE,
                "price": StandardColumns.TRADE_PRICE, "actual_price": StandardColumns.ACTUAL_PRICE,
                "shares": StandardColumns.SHARES, "amount": StandardColumns.AMOUNT,
                "commission": StandardColumns.COMMISSION, "pnl": StandardColumns.PNL,
                "pnl_pct": StandardColumns.PNL_PCT, "reason": StandardColumns.REASON,
                "avg_cost": StandardColumns.AVG_COST
            }
        else:
            return data

        data = data.rename(columns=mapping)

        # 确保日期格式
        if StandardColumns.DATE in data.columns:
            data[StandardColumns.DATE] = pd.to_datetime(data[StandardColumns.DATE])

        return data

    @staticmethod
    def calculate_drawdown(equity_values: np.ndarray) -> np.ndarray:
        """计算回撤"""
        peak = np.maximum.accumulate(equity_values)
        return (equity_values - peak) / peak * 100


# ==================== 主要可视化类 ====================

class BacktestVisualizer:
    """简化的回测可视化器"""

    def __init__(self, figsize: Tuple[int, int] = (14, 8), dpi: int = 150):
        self.figsize = figsize
        self.dpi = dpi
        self.chinese_font = setup_chinese_font()

        # 颜色配置
        self.colors = {
            'primary': '#2E86AB', 'secondary': '#A23B72', 'success': '#F18F01',
            'danger': '#C73E1D', 'warning': '#F4A261', 'info': '#264653'
        }

    def _ensure_chinese_font(self):
        """确保中文字体设置"""
        try:
            plt.rcParams['font.family'] = self.chinese_font
            plt.rcParams['axes.unicode_minus'] = False
        except Exception as e:
            logger.warning(f"字体设置失败: {e}")

    # ==================== 统一的指标绘制方法 ====================

    def _plot_indicator_by_type(self, data: pd.DataFrame, ax, indicator_type: str) -> bool:
        """统一的指标绘制方法 - 消除重复代码"""
        config = INDICATOR_PLOTTERS.get(indicator_type)
        if not config:
            self._plot_rsi(data, ax, {})  # 默认RSI
            return True

        # 检查必需列是否存在
        required_cols = config.get("required_columns", [])
        if not all(col in data.columns for col in required_cols):
            logger.warning(f"指标 {indicator_type} 缺少必需列: {required_cols}")
            return False

        # 调用对应的绘制方法
        plot_method = getattr(self, config["plot_func"], None)
        if plot_method:
            plot_method(data, ax, config)
            return True

        return False

    # ==================== 具体的指标绘制方法 ====================

    def _plot_macd(self, data: pd.DataFrame, ax, config: Dict[str, Any]):
        """MACD指标绘制"""
        cols = config["required_columns"]
        ax.plot(data[StandardColumns.DATE], data[cols[0]], label="DIF", linewidth=2, color='blue')
        ax.plot(data[StandardColumns.DATE], data[cols[1]], label="DEA", linewidth=2, color='red')

        if len(cols) > 2 and cols[2] in data.columns:
            colors = ['green' if x >= 0 else 'red' for x in data[cols[2]]]
            ax.bar(data[StandardColumns.DATE], data[cols[2]], color=colors, alpha=0.6, label="MACD")

        ax.axhline(y=0, color='black', linestyle='-', alpha=0.3)
        ax.set_title(config["title"], fontsize=14, fontweight='bold')
        ax.set_ylabel(config["ylabel"])
        ax.grid(True, alpha=0.3)
        ax.legend()

    def _plot_kdj(self, data: pd.DataFrame, ax, config: Dict[str, Any]):
        """KDJ指标绘制"""
        cols = config["required_columns"]
        colors = ['blue', 'red', 'green']
        labels = ['K', 'D', 'J']

        for col, color, label in zip(cols, colors, labels):
            ax.plot(data[StandardColumns.DATE], data[col], label=label, linewidth=2, color=color)

        # 添加参考线
        for line_value, line_color, line_style, line_alpha, line_label in config.get("reference_lines", []):
            ax.axhline(y=line_value, color=line_color, linestyle=line_style, alpha=line_alpha, label=line_label)

        ax.axhline(y=0, color='gray', linestyle=':', alpha=0.5)
        ax.axhline(y=100, color='gray', linestyle=':', alpha=0.5)

        ax.set_title(config["title"], fontsize=14, fontweight='bold')
        ax.set_ylabel(config["ylabel"])
        ax.set_ylim(config.get("ylim", (0, 100)))
        ax.grid(True, alpha=0.3)
        ax.legend()

    def _plot_rsi(self, data: pd.DataFrame, ax, config: Dict[str, Any]):
        """RSI指标绘制"""
        col = config["required_columns"][0]
        ax.plot(data[StandardColumns.DATE], data[col], label="RSI(14)", linewidth=2.5, color='purple')

        # 添加填充区域
        for y1, y2, alpha, color in config.get("fill_zones", []):
            ax.fill_between(data[StandardColumns.DATE], y1, y2, alpha=alpha, color=color)

        # 添加参考线
        for line_value, line_color, line_style, line_alpha in config.get("reference_lines", []):
            ax.axhline(y=line_value, color=line_color, linestyle=line_style, alpha=line_alpha)

        ax.set_title(config["title"], fontsize=14, fontweight='bold')
        ax.set_ylabel(config["ylabel"])
        ax.set_ylim(config.get("ylim", (0, 100)))
        ax.grid(True, alpha=0.3)
        ax.legend()

    def _plot_ma(self, data: pd.DataFrame, ax, config: Dict[str, Any]):
        """均线指标绘制"""
        ax.plot(data[StandardColumns.DATE], data[StandardColumns.CLOSE],
                label="收盘价", color='black', linewidth=1.5, alpha=0.7)

        cols = config["required_columns"]
        colors = config.get("colors", ['red', 'orange', 'blue', 'green'])
        labels = config.get("labels", ['MA5', 'MA10', 'MA20', 'MA60'])

        for col, color, label in zip(cols, colors, labels):
            if col in data.columns:
                ax.plot(data[StandardColumns.DATE], data[col], label=label, linewidth=2, color=color)

        ax.set_title(config["title"], fontsize=14, fontweight='bold')
        ax.set_ylabel(config["ylabel"])
        ax.grid(True, alpha=0.3)
        ax.legend()

    def _plot_ema(self, data: pd.DataFrame, ax, config: Dict[str, Any]):
        """EMA指标绘制"""
        ax.plot(data[StandardColumns.DATE], data[StandardColumns.CLOSE],
                label="收盘价", color='black', linewidth=1.5, alpha=0.7)

        cols = config["required_columns"]
        colors = config.get("colors", ['red', 'blue'])
        labels = config.get("labels", ['EMA12', 'EMA26'])

        for col, color, label in zip(cols, colors, labels):
            if col in data.columns:
                ax.plot(data[StandardColumns.DATE], data[col], label=label, linewidth=2, color=color)

        ax.set_title(config["title"], fontsize=14, fontweight='bold')
        ax.set_ylabel(config["ylabel"])
        ax.grid(True, alpha=0.3)
        ax.legend()

    def _plot_bollinger(self, data: pd.DataFrame, ax, config: Dict[str, Any]):
        """布林带指标绘制"""
        cols = config["required_columns"]

        ax.plot(data[StandardColumns.DATE], data[StandardColumns.CLOSE],
                label="收盘价", color='black', linewidth=1.5)

        # 绘制布林带线
        for col, label, color, alpha in [
            (cols[0], '上轨', 'red', 0.7), (cols[1], '中轨', 'blue', 0.7), (cols[2], '下轨', 'green', 0.7)
        ]:
            if col in data.columns:
                ax.plot(data[StandardColumns.DATE], data[col], label=label, linewidth=1.5, color=color, alpha=alpha)

        # 填充布林带区域
        if config.get("fill_between") and all(col in data.columns for col in cols[:3]):
            ax.fill_between(data[StandardColumns.DATE], data[cols[0]], data[cols[2]],
                           alpha=0.1, color='gray', label='布林带通道')

        ax.set_title(config["title"], fontsize=14, fontweight='bold')
        ax.set_ylabel(config["ylabel"])
        ax.grid(True, alpha=0.3)
        ax.legend()

    def _plot_volume(self, data: pd.DataFrame, ax, config: Dict[str, Any]):
        """成交量指标绘制"""
        cols = config["required_columns"]

        # 计算涨跌颜色
        open_col = StandardColumns.OPEN
        close_col = StandardColumns.CLOSE
        colors = ['red' if data[close_col].iloc[i] >= data[open_col].iloc[i] else 'green'
                 for i in range(len(data))]

        # 绘制成交量
        ax.bar(data[StandardColumns.DATE], data[cols[0]], color=colors, alpha=0.6, width=0.8)

        # 绘制均量线
        if len(cols) > 1 and cols[1] in data.columns:
            ax.plot(data[StandardColumns.DATE], data[cols[1]], label="20日均量", linewidth=2, color='blue')

        ax.set_title(config["title"], fontsize=14, fontweight='bold')
        ax.set_ylabel(config["ylabel"])
        ax.grid(True, alpha=0.3)
        ax.legend()

    # ==================== 主要绘图方法 ====================

    def plot_equity_with_drawdown(self, result: Dict[str, Any], output_path: str = None, show: bool = False):
        """绘制权益曲线和回撤图"""
        equity_curve = result.get("equity_curve", pd.DataFrame())
        if equity_curve.empty:
            return None

        equity_curve = DataProcessor.prepare_data(equity_curve, "equity")

        # 计算回撤
        equity_values = equity_curve[StandardColumns.EQUITY].values
        drawdown = DataProcessor.calculate_drawdown(equity_values)

        # 创建图表
        fig, (ax_equity, ax_drawdown) = plt.subplots(2, 1, figsize=self.figsize, sharex=True,
                                                     gridspec_kw={'height_ratios': [3, 1]})

        # 权益曲线
        ax_equity.plot(equity_curve[StandardColumns.DATE], equity_curve[StandardColumns.EQUITY],
                      linewidth=2.5, color=self.colors['primary'], label='权益曲线')

        initial = getattr(result.get("config"), 'initial_capital', None)
        if initial:
            ax_equity.axhline(y=initial, color=self.colors['warning'], linestyle='--',
                             alpha=0.6, label=f'初始资金: {initial:,.0f}')

        ax_equity.set_title('权益曲线', fontsize=16, fontweight='bold')
        ax_equity.set_ylabel('权益 (元)')
        ax_equity.grid(True, alpha=0.3)
        ax_equity.legend()

        # 回撤分析
        ax_drawdown.fill_between(equity_curve[StandardColumns.DATE], 0, drawdown,
                                where=(drawdown < 0), color=self.colors['danger'], alpha=0.3)
        ax_drawdown.plot(equity_curve[StandardColumns.DATE], drawdown,
                        linewidth=2, color=self.colors['danger'], label='回撤曲线')

        # 标记最大回撤
        max_dd_idx = np.argmin(drawdown)
        max_dd_date = equity_curve[StandardColumns.DATE].iloc[max_dd_idx]
        max_dd_value = drawdown[max_dd_idx]

        ax_drawdown.scatter(max_dd_date, max_dd_value, color='darkred', s=150,
                           marker='o', label=f'最大回撤: {max_dd_value:.2f}%')
        ax_drawdown.annotate(f'{max_dd_value:.2f}%',
                           xy=(max_dd_date, max_dd_value), xytext=(10, 10),
                           textcoords="offset points", fontsize=11, color='darkred', fontweight='bold')

        ax_drawdown.set_title('回撤分析', fontsize=14, fontweight='bold')
        ax_drawdown.set_ylabel('回撤 (%)')
        ax_drawdown.set_xlabel('日期')
        ax_drawdown.grid(True, alpha=0.3)
        ax_drawdown.legend()
        ax_drawdown.axhline(y=0, color='black', linestyle='-', alpha=0.3)

        ax_drawdown.tick_params(axis='x', rotation=45)
        plt.tight_layout()

        self._ensure_chinese_font()

        if output_path:
            plt.savefig(output_path, dpi=self.dpi, bbox_inches='tight')
            logger.info(f"权益回撤图已保存: {output_path}")

        if show:
            plt.show()
        else:
            if output_path:
                plt.close(fig)
                return None
            return fig

    def plot_trades_with_indicator(self, result: Dict[str, Any], strategy_name: str,
                                   output_path: str = None, show: bool = False, data: pd.DataFrame = None):
        """绘制交易点和技术指标图"""
        data = data or result.get("raw_data")

        if data is None or data.empty:
            logger.warning("无法获取股票数据，跳过技术指标图")
            return None

        data = DataProcessor.prepare_data(data, "stock")

        fig, (ax_price, ax_indicator) = plt.subplots(2, 1, figsize=self.figsize, sharex=True)

        # 价格图
        ax_price.plot(data[StandardColumns.DATE], data[StandardColumns.CLOSE],
                     linewidth=2, color='black', alpha=0.7, label='收盘价')

        # 标记交易点
        trades = result.get("trades", pd.DataFrame())
        if not trades.empty:
            trades = DataProcessor.prepare_data(trades, "trades")
            buy_trades = trades[trades[StandardColumns.TRADE_TYPE] == 'buy']
            sell_trades = trades[trades[StandardColumns.TRADE_TYPE] == 'sell']

            if not buy_trades.empty:
                ax_price.scatter(buy_trades[StandardColumns.DATE], buy_trades[StandardColumns.TRADE_PRICE],
                               color='green', s=100, marker='^', alpha=0.8, zorder=5,
                               label=f'买入 {len(buy_trades)}')
            if not sell_trades.empty:
                ax_price.scatter(sell_trades[StandardColumns.DATE], sell_trades[StandardColumns.TRADE_PRICE],
                               color='red', s=100, marker='v', alpha=0.8, zorder=5,
                               label=f'卖出 {len(sell_trades)}')

        ax_price.set_title(f'{strategy_name} - 交易点分析', fontsize=16, fontweight='bold')
        ax_price.set_ylabel('价格 (元)')
        ax_price.grid(True, alpha=0.3)
        ax_price.legend()

        # 技术指标图
        self._plot_indicator_for_strategy(data, ax_indicator, strategy_name)

        ax_indicator.tick_params(axis='x', rotation=45)
        plt.tight_layout()

        self._ensure_chinese_font()

        if output_path:
            plt.savefig(output_path, dpi=self.dpi, bbox_inches='tight')
            logger.info(f"技术指标图已保存: {output_path}")

        if show:
            plt.show()
        else:
            if output_path:
                plt.close(fig)
                return None
            return fig

    def _plot_indicator_for_strategy(self, data: pd.DataFrame, ax, strategy_name: str):
        """根据策略名称绘制对应指标"""
        indicator_types = STRATEGY_INDICATOR_MAP.get(strategy_name, [IndicatorType.RSI])

        for indicator_type in indicator_types:
            if self._plot_indicator_by_type(data, ax, indicator_type):
                return

        # 默认显示RSI
        self._plot_indicator_by_type(data, ax, IndicatorType.RSI)

    
    def save_all_charts(self, equity_curve: pd.DataFrame, trades: pd.DataFrame,
                        performance: Dict[str, Any], output_dir: Path) -> List[str]:
        """保存所有图表到指定目录"""
        saved_files = []

        try:
            result = {'equity_curve': equity_curve, 'trades': trades, 'performance': performance}
            output_dir.mkdir(parents=True, exist_ok=True)

            # 生成权益曲线和回撤图表
            equity_path = output_dir / "equity_drawdown.png"
            self.plot_equity_with_drawdown(result, output_path=str(equity_path), show=False)
            if equity_path.exists():
                saved_files.append(str(equity_path))
                logger.info(f"保存资金曲线: {equity_path}")

            
        except Exception as e:
            logger.error(f"图表生成失败: {e}")

        return saved_files

    def plot_strategy_comparison(self, strategy_results: Dict[str, Any],
                               output_path: str = None, show: bool = True) -> None:
        """
        绘制策略对比图表

        Args:
            strategy_results: 策略结果字典 {策略名称: StrategyResult或包含performance的字典}
            output_path: 输出路径
            show: 是否显示图表
        """
        import matplotlib.pyplot as plt

        if not strategy_results:
            logger.warning("没有策略结果数据，无法生成对比图表")
            return

        # 创建子图
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('策略性能对比', fontsize=16, fontweight='bold')

        # 提取数据 - 兼容StrategyResult对象和字典格式
        strategies = list(strategy_results.keys())
        returns = []
        sharpes = []
        max_drawdowns = []
        win_rates = []

        for strategy in strategies:
            result = strategy_results[strategy]
            if hasattr(result, 'performance'):
                perf = result.performance
            elif isinstance(result, dict) and 'performance' in result:
                perf = result['performance']
            else:
                perf = {}

            returns.append(perf.get('total_return', 0))
            sharpes.append(perf.get('sharpe_ratio', 0))
            max_drawdowns.append(perf.get('max_drawdown', 0))
            win_rates.append(perf.get('win_rate', 0))

        # 设置中文字体
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False

        # 1. 总收益率对比
        axes[0, 0].bar(strategies, returns, color='steelblue', alpha=0.7)
        axes[0, 0].set_title('总收益率对比 (%)')
        axes[0, 0].set_ylabel('收益率 (%)')
        axes[0, 0].tick_params(axis='x', rotation=45)
        for i, v in enumerate(returns):
            axes[0, 0].text(i, v + 1, f'{v:.1f}%', ha='center', va='bottom')

        # 2. 夏普比率对比
        axes[0, 1].bar(strategies, sharpes, color='green', alpha=0.7)
        axes[0, 1].set_title('夏普比率对比')
        axes[0, 1].set_ylabel('夏普比率')
        axes[0, 1].tick_params(axis='x', rotation=45)
        axes[0, 1].axhline(y=1.0, color='red', linestyle='--', alpha=0.7, label='夏普比率=1.0')
        for i, v in enumerate(sharpes):
            axes[0, 1].text(i, v + 0.05, f'{v:.3f}', ha='center', va='bottom')

        # 3. 最大回撤对比
        axes[1, 0].bar(strategies, [-abs(d) for d in max_drawdowns], color='red', alpha=0.7)
        axes[1, 0].set_title('最大回撤对比 (%)')
        axes[1, 0].set_ylabel('回撤 (%)')
        axes[1, 0].tick_params(axis='x', rotation=45)
        for i, v in enumerate(max_drawdowns):
            axes[1, 0].text(i, -abs(v) - 1, f'{v:.1f}%', ha='center', va='top')

        # 4. 胜率对比
        axes[1, 1].bar(strategies, win_rates, color='orange', alpha=0.7)
        axes[1, 1].set_title('胜率对比 (%)')
        axes[1, 1].set_ylabel('胜率 (%)')
        axes[1, 1].tick_params(axis='x', rotation=45)
        axes[1, 1].axhline(y=50, color='red', linestyle='--', alpha=0.7, label='胜率=50%')
        for i, v in enumerate(win_rates):
            axes[1, 1].text(i, v + 2, f'{v:.1f}%', ha='center', va='bottom')

        plt.tight_layout()

        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            logger.info(f"策略对比图表已保存: {output_path}")

        if show:
            plt.show()
        else:
            plt.close()

        logger.info("策略对比图表生成完成")


# 全局可视化器实例
visualizer = BacktestVisualizer()