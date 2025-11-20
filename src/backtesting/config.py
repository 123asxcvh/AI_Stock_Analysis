#!/usr/bin/env python3

"""
简化的回测配置模块
整合所有配置选项
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime


@dataclass
class BacktestConfig:
    """
    简化的回测配置类
    包含所有必要的回测参数
    """
    # 资金管理
    initial_capital: float = 1000000.0     # 初始资金
    position_size: float = 1.0             # 仓位比例
    max_positions: int = 1                 # 最大持仓数

    # 交易成本
    commission_rate: float = 0.0003        # 佣金费率
    slippage_rate: float = 0.001           # 滑点
    min_commission: float = 5.0            # 最低佣金
    min_shares: int = 100                  # 最小交易单位 (A股)
    stamp_tax_rate: float = 0.001          # 印花税 (卖出时)

    # 风险控制
    stop_loss_pct: float = 0.05            # 止损比例
    take_profit_pct: Optional[float] = None  # 止盈比例
    max_drawdown_limit: float = 0.5        # 最大回撤限制

    # 数据范围
    start_date: Optional[str] = "2024-01-01"       # 开始日期
    end_date: Optional[str] = None                 # 结束日期（动态获取当前日期）
    min_data_points: int = 100             # 最小数据点数

    # 优化设置
    enable_optimization: bool = False      # 启用优化
    optimization_metric: str = "sharpe_ratio"  # 优化目标
    max_combinations: int = 1000           # 最大参数组合数

    # 并行设置
    enable_parallel: bool = True           # 启用并行处理
    max_workers: Optional[int] = None      # 最大工作进程数
    timeout: Optional[int] = None          # 单个任务超时

    # 输出设置
    output_dir: Optional[str] = None       # 输出目录
    save_charts: bool = True               # 保存图表
    save_trades: bool = True               # 保存交易记录
    verbose: bool = True                   # 详细输出

    # 缓存设置
    enable_cache: bool = True              # 启用缓存
    cache_size: int = 100                  # 缓存大小

    def __post_init__(self):
        """初始化后的验证和设置"""
        # 动态设置结束日期为当前日期
        if self.end_date is None:
            self.end_date = datetime.now().strftime("%Y-%m-%d")

        # 设置默认输出目录
        if self.output_dir is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.output_dir = f"./backtest_results_{timestamp}"

        # 设置默认工作进程数
        if self.max_workers is None:
            import multiprocessing
            self.max_workers = max(1, multiprocessing.cpu_count() - 1)

        # 参数验证
        self._validate_params()

    def _validate_params(self):
        """验证参数合理性"""
        if self.initial_capital <= 0:
            raise ValueError("初始资金必须大于0")
        if not 0 < self.position_size <= 1:
            raise ValueError("仓位比例必须在(0,1]之间")
        if self.stop_loss_pct <= 0:
            raise ValueError("止损比例必须大于0")
        if self.commission_rate < 0:
            raise ValueError("佣金费率不能为负")

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "initial_capital": self.initial_capital,
            "position_size": self.position_size,
            "commission_rate": self.commission_rate,
            "slippage_rate": self.slippage_rate,
            "stop_loss_pct": self.stop_loss_pct,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "optimization_metric": self.optimization_metric
        }

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'BacktestConfig':
        """从字典创建配置"""
        return cls(**config_dict)

    @classmethod
    def conservative(cls) -> 'BacktestConfig':
        """保守配置：低风险，低交易频率"""
        return cls(
            position_size=0.8,
            stop_loss_pct=0.03,
            commission_rate=0.0005,
            slippage_rate=0.002
        )

    @classmethod
    def aggressive(cls) -> 'BacktestConfig':
        """激进配置：高风险，高交易频率"""
        return cls(
            position_size=1.0,
            stop_loss_pct=0.08,
            commission_rate=0.0002,
            slippage_rate=0.0005
        )

    @classmethod
    def optimization(cls) -> 'BacktestConfig':
        """优化配置：用于参数优化"""
        return cls(
            enable_optimization=True,
            enable_parallel=True,
            max_combinations=5000,
            verbose=False,
            save_charts=False
        )

    def copy(self, **kwargs) -> 'BacktestConfig':
        """创建配置副本"""
        import copy
        new_config = copy.deepcopy(self)
        for key, value in kwargs.items():
            if hasattr(new_config, key):
                setattr(new_config, key, value)
        return new_config

    def __str__(self) -> str:
        """字符串表示"""
        return f"""回测配置:
资金管理: 初始{self.initial_capital:,.0f}元, 仓位{self.position_size:.1%}
交易成本: 佣金{self.commission_rate:.3%}, 滑点{self.slippage_rate:.3%}
风险控制: 止损{self.stop_loss_pct:.1%}, 最大回撤{self.max_drawdown_limit:.1%}
优化设置: 目标{self.optimization_metric}, 最大组合{self.max_combinations}"""


# 预定义配置
CONSERVATIVE_CONFIG = BacktestConfig.conservative()
AGGRESSIVE_CONFIG = BacktestConfig.aggressive()
OPTIMIZATION_CONFIG = BacktestConfig.optimization()

# ==================== 回测优化配置 ====================

# 策略参数网格配置 - 统一管理所有策略的可优化参数
STRATEGY_PARAM_GRIDS = {
    # ========== 基础策略 ==========
    "双均线策略": {
        "short_period": [5, 10, 15, 20],          # 精简：聚焦有效短期窗口
        "long_period": [30, 40, 50, 60, 90, 120]  # 避免 < short；剔除 20（易重叠）
    },
    "MACD趋势策略": {
        "fast": [8, 10, 12, 15],
        "slow": [24, 26, 30, 35],                # slow > fast 必须成立
        "signal": [6, 9, 12]
    },
    "KDJ超卖反弹策略": {
        "j_oversold": [0, 5, 10, 15, 20, 25, 30],      # J值超卖阈值：更宽范围
        "j_overbought": [75, 80, 85, 90, 95, 100]    # J值超买阈值：更宽范围
    },
    "KDJ+布林带系统": {
        "bb_period": [10, 15, 20, 25, 30],        # 布林带周期：更宽范围
        "bb_std": [1.2, 1.5, 1.8, 2.2, 2.5],   # 布林带标准差：更宽范围
        "j_oversold": [10, 15, 20, 25, 30],       # J值超卖阈值：更宽范围
        "j_overbought": [85, 90, 95, 100, 105],  # J值超买阈值：更宽范围
        "volume_multiplier": [1.0, 1.3, 1.6, 2.0, 2.5, 3.0]  # 成交量放大倍数：更宽范围
    },
    "KDJ+MACD双重确认策略": {
        "j_oversold": [0, 5, 10, 15, 20],          # J值超卖阈值
        "j_overbought": [85, 90, 95, 100, 105],   # J值超买阈值
        "macd_fast": [8, 10, 12, 15],             # MACD快线周期
        "macd_slow": [24, 26, 30, 35],            # MACD慢线周期
        "macd_signal": [6, 9, 12]                 # MACD信号线周期
    },
    "RSI反转策略": {
        "rsi_period": [6, 9, 12, 14, 18, 21],    # 增加奇数周期，更符合波动节奏
        "oversold": [25, 30, 35],                # 20 在 A 股易频繁触发
        "overbought": [70, 75, 80]               # 85 几乎不触发，移除
    },
    "布林带策略": {
        "period": [15, 20, 25, 30, 40],          # 10 太短噪声多，60 太迟钝
        "std_dev": [1.8, 2.0, 2.2, 2.5]          # 1.5 太窄，易假突破
    },
    "成交量突破策略": {
        "volume_period": [5, 10, 20, 30],        # 精简：5/10 短期，20/30 中期
        "volume_multiplier": [1.5, 1.8, 2.0, 2.5]  # 1.1-1.3 太敏感，易噪音
    },

    # ========== 修正后的复合策略 ==========
    "布林带+RSI反转策略": {
        "bb_period": [15, 20, 25, 30],          # 布林带周期
        "std_dev": [1.8, 2.0, 2.2],            # 标准差倍数，移除过高值
        "rsi_period": [12, 14, 18],             # RSI周期
        "oversold": [30, 35, 40]                # 放宽RSI阈值，提高信号频率
    }
}
# 常用参数网格 - 保持向后兼容
COMMON_PARAM_GRIDS = STRATEGY_PARAM_GRIDS

# 优化配置
OPTIMIZATION_CONFIG = {
    # 优化目标配置
    "default_objective": "sharpe_ratio",
    "default_method": "bayesian",  # 只支持贝叶斯优化
    "default_max_evaluations": 10,

    # 优化约束
    "min_trades": 5,
    "max_drawdown_limit": 50.0,

    # 并行配置
    "optimization_workers": 2,
    "optimization_timeout": 60,

    # 结果配置
    "enable_comparison": False,  # 避免覆盖最优参数结果
    "comparison_sort_by": "sharpe_ratio"
}