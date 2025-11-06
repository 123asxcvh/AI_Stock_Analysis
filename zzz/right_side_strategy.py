#!/usr/bin/env python3

"""
日线右侧增强策略（基于预计算指标）
直接使用 historical_quotes.csv 中已计算的指标，无需重新计算

策略逻辑（简化版状态机）：
- 当日线 J 值 < 阈值时，进入观察期
- 在观察期内，若同时满足：
    a) MACD柱线 > 0
    b) 价格突破：收盘价 > BBI30
    c) 量能验证：固定通过
  则生成买入信号，并退出观察期
- 下一次 J < 阈值时重新进入观察期

用法示例：
  python -m src.backtesting.strategies.right_side_strategy 601318 --start-date 2025-01-01 --end-date 2025-09-30
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# 统一路径工具
from config import config

from src.backtesting.backtest_engine import (
    StrategyBase,
    BrokerParams,
    run_backtest_single,
)
# 移除result_analyzer依赖，统一使用backtest_engine的统计功能
from src.backtesting.data_loader import DataLoader


class DailyRightSideStrategy(StrategyBase):
    """日线右侧策略（增强版状态机观察期机制）
    
    使用已计算的指标数据：
    - DAILY_J: 日线J值
    - MACD_HIST: MACD柱线
    - BBI30: 30日多空指标
    - 成交量: 成交量数据
    
    买入条件（增强版状态机）：
    1. 当前 DAILY_J < j_threshold → 进入观察期（仅当不在观察期时）
    2. 观察期超时机制：超过3天自动退出观察期
    3. 信号冷却期：生成信号后5天内不再进入观察期（禁止重新进入）
    4. 在观察期内，若同时满足：
        - 趋势确认：MACD柱线 > 0
        - 价格突破：收盘价 > BBI
        - 量能验证：固定通过
       则生成买入信号，并退出观察期
    
    卖出条件：无（仅用于买点分析）
    
    增强特性：
    - 观察期超时重置：避免长期无信号
    - 信号冷却期：防止频繁交易
    - 简化判断：快速响应右侧机会
    """

    def __init__(
        self,
        j_threshold: float = 5.0,
        volume_ma_days: int = 20,          # 成交量均线天数
        volume_increase_pct: float = 0.2,  # 成交量较前一日放大百分比（20%）
        volume_min_ratio: float = 0.7,     # 成交量最低比例（20日均量的70%）
        observation_timeout_days: int = 3,  # 观察期超时天数（改为3天）
        signal_cooldown_days: int = 5,     # 信号冷却期天数
    ) -> None:
        self.j_threshold = j_threshold
        self.volume_ma_days = volume_ma_days
        self.volume_increase_pct = volume_increase_pct
        self.volume_min_ratio = volume_min_ratio
        self.observation_timeout_days = observation_timeout_days
        self.signal_cooldown_days = signal_cooldown_days
        
        # 标识需要从signals.csv中排除的列
        self.excluded_signal_columns = ['sell_signal', 'sell_reason']



    def generate_signals(self, df: pd.DataFrame):
        """使用状态机实现观察期机制，返回已 shift(1) 的信号
        
        简化版趋势反转条件：
        1. MACD柱线 > 0
        2. 价格突破BBI30
        3. 量能验证：固定返回1.05
        """
        data = df.copy().sort_values("日期").reset_index(drop=True)
        
        # 转换指标为数值类型
        daily_j = pd.to_numeric(data['DAILY_J'], errors='coerce')
        macd_hist = pd.to_numeric(data['MACD_HIST'], errors='coerce')
        # 优先使用BBI30，如无则回退到BBI60
        if 'BBI30' in data.columns:
            bbi = pd.to_numeric(data['BBI30'], errors='coerce')
        elif 'BBI60' in data.columns:
            bbi = pd.to_numeric(data['BBI60'], errors='coerce')
        else:
            raise ValueError("数据文件中缺少BBI30或BBI60列")
        close_price = pd.to_numeric(data['收盘'], errors='coerce')
        volume = pd.to_numeric(data.get('成交量', 0), errors='coerce')
        
        # 计算成交量均线
        volume_ma = volume.rolling(window=self.volume_ma_days, min_periods=1).mean()
        
        # 创建诊断数据供引擎使用
        bbi_column_name = 'BBI30' if 'BBI30' in data.columns else 'BBI60'
        self._diag_df = pd.DataFrame({
            '日期': pd.to_datetime(data['日期']),
            'DAILY_J': daily_j,
            'MACD_HIST': macd_hist,
            bbi_column_name: bbi,
            '成交量': volume,
            '成交量_MA': volume_ma,
        })

        # 初始化信号
        buy_signals = pd.Series(0, index=data.index, dtype=int)
        in_observation = False  # 状态：是否处于观察期
        observation_start_idx = None  # 观察期开始索引
        last_signal_idx = None  # 上次生成信号的索引

        for i in range(len(data)):
            # 跳过含 NaN 的行
            if (pd.isna(daily_j.iloc[i]) or pd.isna(macd_hist.iloc[i]) or 
                pd.isna(bbi.iloc[i]) or pd.isna(close_price.iloc[i])):
                continue

            # 条件1：J < 阈值 且 不在观察期 且 不在冷静期 → 进入观察期
            if (
                not in_observation
                and daily_j.iloc[i] < self.j_threshold
                and (last_signal_idx is None or i - last_signal_idx >= self.signal_cooldown_days)
            ):
                in_observation = True
                observation_start_idx = i

            # 条件2：检查观察期超时
            if in_observation and observation_start_idx is not None:
                if i - observation_start_idx > self.observation_timeout_days:
                    in_observation = False
                    observation_start_idx = None

            # 条件3：在观察期内，检查反转条件
            if in_observation:
                # 2.1 MACD柱线 > 0
                macd_ok = macd_hist.iloc[i] > 0
                
                # 2.2 价格突破确认：收盘价 > BBI
                price_ok = close_price.iloc[i] > bbi.iloc[i]
                
                # 2.3 成交量确认
                volume_ok = True  # 默认通过
                if not pd.isna(volume.iloc[i]) and not pd.isna(volume_ma.iloc[i]) and volume_ma.iloc[i] > 0:
                    if i > 0:
                        # 成交量较前一日放大（至少 +20%）
                        vol_up = volume.iloc[i] > volume.iloc[i-1] * (1 + self.volume_increase_pct)
                        
                        # 且量能高于20日均量的70%（避免极端地量干扰）
                        vol_above_avg = volume.iloc[i] > volume_ma.iloc[i] * self.volume_min_ratio
                        
                        volume_ok = vol_up and vol_above_avg
                    # i=0时默认通过成交量确认
                
                # 综合判断
                if macd_ok and price_ok and volume_ok:
                    buy_signals.iloc[i] = 1000  # 固定买入1000股
                    in_observation = False     # 退出观察期
                    observation_start_idx = None  # 重置观察期开始索引
                    last_signal_idx = i        # 记录信号索引

        # 无卖出信号
        sell_signals = pd.Series(0, index=data.index, dtype=int)

        # 避免前视偏差：shift(1)
        entry_signals = buy_signals.shift(1).fillna(0).astype(int)
        exit_signals = sell_signals.shift(1).fillna(0).astype(int)

        return entry_signals, exit_signals
    
    def generate_signals_with_reasons(self, df: pd.DataFrame):
        """返回信号及原因（与 generate_signals 逻辑一致）"""
        entry_signals, exit_signals = self.generate_signals(df)
        
        data = df.copy()
        data['日期'] = pd.to_datetime(data['日期'], errors='coerce')
        data = data.sort_values('日期', ascending=True).reset_index(drop=True)
        
        buy_reasons = pd.Series([''] * len(data), index=data.index)
        sell_reasons = pd.Series([''] * len(data), index=data.index)
        
        # 为每个买入信号添加原因（注意 entry_signals 是 shift(1) 后的）
        for i in range(len(entry_signals)):
            if entry_signals.iloc[i] > 0:
                buy_reasons.iloc[i] = (
                    f"J<{self.j_threshold}后反转确认: "
                    f"MACD柱线>0, "
                    f"收盘>BBI, "
                    f"成交量较前日放大{self.volume_increase_pct*100:.0f}%且>{self.volume_min_ratio*100:.0f}%均量"
                )
        
        return entry_signals, exit_signals, buy_reasons, sell_reasons


def main() -> None:
    """主函数：执行回测"""
    parser = argparse.ArgumentParser(description="日线右侧策略回测（基于预计算指标）")
    parser.add_argument("stock_code", help="股票代码")
    parser.add_argument("--start-date", required=True, help="开始日期 YYYY-MM-DD")
    parser.add_argument("--end-date", required=True, help="结束日期 YYYY-MM-DD")
    parser.add_argument("--initial-capital", type=float, default=100000.0, help="初始资金")
    parser.add_argument("--j-threshold", type=float, default=5.0, help="J值阈值")
    parser.add_argument("--volume-ma-days", type=int, default=20, help="成交量均线天数")
    parser.add_argument("--volume-increase-pct", type=float, default=0.2, help="成交量较前一日放大百分比")
    parser.add_argument("--volume-min-ratio", type=float, default=0.7, help="成交量最低比例（20日均量的70%）")
    parser.add_argument("--output-dir", default=None, help="输出目录")

    args = parser.parse_args()

    # 构建CSV文件路径
    csv_path = config.get_stock_quotes_csv(args.stock_code, cleaned=True)
    
    if not csv_path.exists():
        print(f"错误: 找不到数据文件 {csv_path}")
        sys.exit(1)

    # 设置输出目录
    if args.output_dir is None:
        # 使用股票数据目录下的results子目录
        output_dir = config.get_stock_dir(args.stock_code, cleaned=True) / "results" / "daily_right_side"
    else:
        output_dir = Path(args.output_dir)
    
    output_dir.mkdir(parents=True, exist_ok=True)

    # 使用统一数据加载器
    print(f"加载数据: {csv_path}")
    loader = DataLoader()
    df = loader.load_stock_data(args.stock_code)
    if df is None:
        print(f"错误: 无法加载股票数据 {args.stock_code}")
        sys.exit(1)
    
    # 过滤日期范围
    df['日期'] = pd.to_datetime(df['日期'])
    start_date = pd.to_datetime(args.start_date)
    end_date = pd.to_datetime(args.end_date)
    
    mask = (df['日期'] >= start_date) & (df['日期'] <= end_date)
    df_filtered = df[mask].copy()
    
    if len(df_filtered) == 0:
        print(f"警告: 在指定日期范围内没有数据")
        sys.exit(1)
    
    print(f"数据范围: {df_filtered['日期'].min()} 到 {df_filtered['日期'].max()}")
    print(f"数据行数: {len(df_filtered)}")
    
    # 验证指标列
    required_columns = ['DAILY_J', 'MACD_HIST', 'BBI30']
    missing_columns = [col for col in required_columns if col not in df_filtered.columns]
    if missing_columns:
        print(f"错误: 数据文件缺少必需的指标列: {missing_columns}")
        print(f"可用列: {list(df_filtered.columns)}")
        sys.exit(1)

    # 创建策略实例
    strategy = DailyRightSideStrategy(
        j_threshold=args.j_threshold,
        volume_ma_days=args.volume_ma_days,
        volume_increase_pct=args.volume_increase_pct,
        volume_min_ratio=args.volume_min_ratio,
        observation_timeout_days=30,  # 观察期30天超时
        signal_cooldown_days=5,      # 信号冷却期5天
    )

    # 创建券商参数
    broker_params = BrokerParams(
        initial_capital=args.initial_capital,
        position_frac=1.0,
        fixed_quantity_mode=True,  # 启用固定股数模式
    )

    # 执行回测
    print(f"开始回测: {args.stock_code} ({args.start_date} 到 {args.end_date})")
    print(f"策略参数: J阈值={args.j_threshold}, MACD柱线>0, 价格突破BBI(优先BBI30), 成交量较前日放大{args.volume_increase_pct*100:.0f}%且>{args.volume_min_ratio*100:.0f}%{args.volume_ma_days}日均量")
    print(f"增强机制: 观察期超时3天, 信号冷却期5天")
    
    result = run_backtest_single(
        df=df_filtered,
        strategy=strategy,
        params=broker_params,
        output_dir=str(output_dir),
    )

    if result:
        print("回测完成!")
        print(f"结果保存在: {output_dir}")
        
        # 生成图表
        try:
            from src.backtesting.backtest_plotter import plot_daily_right_results
            plot_daily_right_results(
                stock_code=args.stock_code,
                start_date=args.start_date,
                end_date=args.end_date,
            )
            print("图表生成完成!")
        except Exception as e:
            print(f"⚠️ 图表生成失败: {e}")
    else:
        print("回测失败!")


if __name__ == "__main__":
    main()