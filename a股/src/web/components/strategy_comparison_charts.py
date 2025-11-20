#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
策略对比结果可视化组件
用于展示策略回测结果的交互式图表
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, Any, List
from pathlib import Path

class StrategyComparisonCharts:
    """策略对比可视化组件"""

    def __init__(self):
        self.name = "策略对比图表"

    def create_single_metric_comparison_chart(self, metric_name: str, df: pd.DataFrame, metric_column: str,
                                              value_format: str = ".2f", is_percentage: bool = False,
                                              is_negative_better: bool = False) -> go.Figure:
        """创建通用的单指标对比柱状图 - 保持策略原始顺序"""
        if df.empty:
            return go.Figure()

        # 保持策略的原始顺序，不排序
        strategies = df['策略名称'].tolist()

        # 安全获取指标值，处理不同数据类型
        try:
            if metric_column in df.columns:
                column_data = df[metric_column]

                # 处理百分比字符串
                if is_percentage:
                    # 检查是否为字符串类型且包含%
                    if column_data.dtype == 'object':
                        # 尝试转换为字符串并移除%
                        values = pd.to_numeric(column_data.astype(str).str.rstrip('%'), errors='coerce')
                    else:
                        # 如果已经是数值类型，直接使用
                        values = pd.to_numeric(column_data, errors='coerce')
                else:
                    # 非百分比列，直接转换为数值
                    values = pd.to_numeric(column_data, errors='coerce')

                # 不处理NaN值，保持原始数据状态
                # NaN值将在图表中自然处理
            else:
                st.error(f"❌ 列 '{metric_column}' 不存在于数据中")
                return go.Figure()

        except Exception as e:
            st.error(f"❌ 处理指标 '{metric_column}' 时出错: {str(e)}")
            return go.Figure()

        # 颜色映射：最好两个红色，最差两个绿色，中间黄色（无渐变）
        if len(values) > 0 and not values.isna().all():
            # 获取有效值的索引并排序
            valid_indices = [(i, v) for i, v in enumerate(values) if not pd.isna(v)]
            sorted_indices = sorted(valid_indices, key=lambda x: x[1], reverse=is_negative_better)

            # 初始化所有值为灰色
            colors = ['rgba(156, 163, 175, 0.8)'] * len(values)

            # 分配颜色
            for idx, (original_idx, value) in enumerate(sorted_indices):
                if idx < 2:  # 最好的两个
                    colors[original_idx] = 'rgba(239, 68, 68, 0.8)'  # 红色
                elif idx >= len(sorted_indices) - 2:  # 最差的两个
                    colors[original_idx] = 'rgba(34, 197, 94, 0.8)'  # 绿色
                else:  # 中间的
                    colors[original_idx] = 'rgba(251, 191, 36, 0.8)'  # 黄色
        else:
            # 如果没有有效数据，使用灰色
            colors = ['rgba(156, 163, 175, 0.8)'] * len(values)

        # 格式化显示文本，跳过NaN值
        if is_percentage:
            text_values = [f'{v:{value_format}}%' if not pd.isna(v) else '' for v in values]
        else:
            text_values = [f'{v:{value_format}}' if not pd.isna(v) else '' for v in values]

        # 创建图表
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=strategies,
            y=values,
            marker_color=colors,
            text=text_values,
            textposition='outside',
            textfont=dict(size=10)
        ))

        # 设置y轴标题
        yaxis_title = f"{metric_name} ({'%' if is_percentage else ''})"

        # 更新布局
        fig.update_layout(
            title=f"{metric_name}对比分析",
            xaxis_title="策略",
            yaxis_title=yaxis_title,
            height=500
        )
        fig.update_xaxes(tickangle=45)

        return fig

    def load_strategy_comparison_data(self, symbol: str) -> pd.DataFrame:
        """加载策略对比数据"""
        comparison_file = Path(f"data/cleaned_stocks/{symbol}/backtest_results/strategy_comparison.csv")

        if not comparison_file.exists():
            st.error(f"❌ 未找到策略对比文件: {comparison_file}")
            return pd.DataFrame()

        try:
            # 尝试用不同编码读取文件
            encodings = ['utf-8', 'utf-8-sig', 'gbk', 'gb2312']
            df = None

            for encoding in encodings:
                try:
                    df = pd.read_csv(comparison_file, encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue

            if df is None:
                raise Exception("无法解码文件，请检查文件编码")

            # 验证必要的列是否存在
            required_columns = ['策略名称', '总收益率', '年化收益率', '夏普比率', '最大回撤', '胜率', '盈亏比']
            missing_columns = [col for col in required_columns if col not in df.columns]

            if missing_columns:
                st.warning(f"⚠️ 数据文件缺少必要列: {missing_columns}")
                # 如果只是缺少某些列，仍然返回数据，但会有警告

            # 验证数据不为空
            if df.empty:
                st.warning("⚠️ 策略对比数据为空")
                return pd.DataFrame()

            return df

        except Exception as e:
            st.error(f"❌ 读取策略对比文件失败: {e}")
            st.info("请检查文件格式和编码，确保CSV文件包含正确的策略对比数据")
            return pd.DataFrame()

    def create_returns_comparison_chart(self, df: pd.DataFrame) -> go.Figure:
        """创建收益率对比图表"""
        if df.empty:
            return go.Figure()

        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=('总收益率排名', '年化收益率对比'),
            specs=[[{"type": "bar"}, {"type": "bar"}]]
        )

        # 准备数据
        strategies = df['策略名称'].tolist()
        total_returns = df['总收益率'].str.rstrip('%').astype(float).tolist()
        annual_returns = df['年化收益率'].str.rstrip('%').astype(float).tolist()

        # 按总收益率排序
        sorted_indices = sorted(range(len(total_returns)), key=lambda i: total_returns[i])
        sorted_strategies = [strategies[i] for i in sorted_indices]
        sorted_total_returns = [total_returns[i] for i in sorted_indices]
        sorted_annual_returns = [annual_returns[i] for i in sorted_indices]

        # 颜色映射
        colors = ['rgba(34, 197, 94, 0.8)' if r >= 50 else
                  'rgba(251, 191, 36, 0.8)' if r >= 20 else
                  'rgba(156, 163, 175, 0.8)' if r >= 0 else
                  'rgba(239, 68, 68, 0.8)'
                  for r in sorted_total_returns]

        # 总收益率柱状图
        fig.add_trace(
            go.Bar(
                x=sorted_strategies,
                y=sorted_total_returns,
                name='总收益率 (%)',
                marker_color=colors,
                text=[f'{r:.2f}%' for r in sorted_total_returns],
                textposition='auto',
                textfont=dict(color='white' if any(r < 0 for r in sorted_total_returns) else 'black')
            ),
            row=1, col=1
        )

        # 年化收益率柱状图
        fig.add_trace(
            go.Bar(
                x=sorted_strategies,
                y=sorted_annual_returns,
                name='年化收益率 (%)',
                marker_color='rgba(59, 130, 246, 0.8)',
                text=[f'{r:.2f}%' for r in sorted_annual_returns],
                textposition='auto',
                visible='legendonly'  # 开始时隐藏，由图例控制
            ),
            row=1, col=2
        )

        fig.update_layout(
            title="📈 收益率维度对比分析",
            height=500,
            showlegend=True
        )
        fig.update_xaxes(tickangle=45)
        fig.update_yaxes(title_text="收益率 (%)", row=1, col=1)
        fig.update_yaxes(title_text="年化收益率 (%)", row=1, col=2)

        return fig

    def create_risk_analysis_chart(self, df: pd.DataFrame) -> go.Figure:
        """创建风险分析对比图表"""
        if df.empty:
            return go.Figure()

        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('最大回撤对比', '波动率分析', '夏普 vs 卡尔玛比率', '风险收益雷达图'),
            specs=[[{"type": "bar"}, {"type": "bar"}],
                   [{"type": "scatter"}, {"type": "scatter"}]]
        )

        strategies = df['策略名称'].tolist()
        max_drawdown = df['最大回撤'].str.rstrip('%').astype(float).tolist()
        volatility = df['年化波动率'].str.rstrip('%').astype(float).tolist()
        sharpe_ratios = df['夏普比率'].tolist()
        calmar_ratios = df['卡尔玛比率'].tolist()
        returns = df['总收益率'].str.rstrip('%').astype(float).tolist()

        # 最大回撤柱状图 (倒序显示，最大回撤越小越好)
        fig.add_trace(
            go.Bar(
                x=strategies,
                y=[-x for x in max_drawdown],  # 负值显示，越接近0越好
                name='最大回撤 (-%)',
                marker_color='rgba(239, 68, 68, 0.8)',
                text=[f'{x:.2f}%' for x in max_drawdown],
                textposition='auto'
            ),
            row=1, col=1
        )

        # 波动率柱状图
        fig.add_trace(
            go.Bar(
                x=strategies,
                y=volatility,
                name='年化波动率 (%)',
                marker_color='rgba(245, 158, 11, 0.8)',
                text=[f'{x:.2f}%' for x in volatility],
                textposition='auto'
            ),
            row=1, col=2
        )

        # 夏普 vs 卡尔玛比率散点图
        fig.add_trace(
            go.Scatter(
                x=sharpe_ratios,
                y=calmar_ratios,
                mode='markers+text',
                text=strategies,
                textposition="top center",
                marker=dict(
                    size=15,
                    color=returns,
                    colorscale='RdYlGn',
                    colorbar=dict(title="总收益率(%)"),
                    line=dict(width=2, color='white')
                ),
                name='策略'
            ),
            row=2, col=1
        )

        # 风险收益散点图
        fig.add_trace(
            go.Scatter(
                x=max_drawdown,
                y=returns,
                mode='markers+text',
                text=strategies,
                textposition="top center",
                marker=dict(
                    size=15,
                    color=sharpe_ratios,
                    colorscale='Viridis',
                    colorbar=dict(title="夏普比率"),
                    line=dict(width=2, color='white')
                ),
                name='策略'
            ),
            row=2, col=2
        )

        fig.update_layout(
            title="⚡ 风险维度对比分析",
            height=800,
            showlegend=False
        )
        fig.update_xaxes(tickangle=45)
        fig.update_yaxes(title_text="最大回撤 (%)", row=1, col=1)
        fig.update_yaxes(title_text="波动率 (%)", row=1, col=2)
        fig.update_yaxes(title_text="卡尔玛比率", row=2, col=1)
        fig.update_yaxes(title_text="总收益率 (%)", row=2, col=2)
        fig.update_xaxes(title_text="最大回撤 (%)", row=2, col=2)

        return fig

    def create_trading_performance_chart(self, df: pd.DataFrame) -> go.Figure:
        """创建交易表现对比图表"""
        if df.empty:
            return go.Figure()

        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('交易次数 vs 胜率', '盈亏比分析', '止损情况', '最终资金规模'),
            specs=[[{"type": "scatter"}, {"type": "bar"}],
                   [{"type": "bar"}, {"type": "bar"}]]
        )

        strategies = df['策略名称'].tolist()
        trade_counts = df['总交易次数'].tolist()
        win_rates = df['胜率'].str.rstrip('%').astype(float).tolist()
        profit_loss_ratios = df['盈亏比'].tolist()
        stop_loss_counts = df['止损次数'].tolist()
        final_capitals = [float(str(x).replace(',', '')) for x in df['最终资金'].tolist()]

        # 处理inf盈亏比
        profit_loss_ratios_clean = []
        for ratio in profit_loss_ratios:
            if ratio == 'inf' or ratio == float('inf'):
                profit_loss_ratios_clean.append(max(plr for plr in profit_loss_ratios if plr != 'inf' and plr != float('inf')) * 2)
            else:
                profit_loss_ratios_clean.append(float(ratio))

        # 交易次数 vs 胜率散点图
        fig.add_trace(
            go.Scatter(
                x=trade_counts,
                y=win_rates,
                mode='markers+text',
                text=strategies,
                textposition="top center",
                marker=dict(
                    size=20,
                    color=final_capitals,
                    colorscale='Blues',
                    colorbar=dict(title="最终资金"),
                    line=dict(width=2, color='white')
                ),
                name='策略'
            ),
            row=1, col=1
        )

        # 盈亏比柱状图
        fig.add_trace(
            go.Bar(
                x=strategies,
                y=profit_loss_ratios_clean,
                name='盈亏比',
                marker_color='rgba(34, 197, 94, 0.8)',
                text=[f'{x:.2f}' for x in profit_loss_ratios_clean],
                textposition='auto'
            ),
            row=1, col=2
        )

        # 止损次数
        fig.add_trace(
            go.Bar(
                x=strategies,
                y=stop_loss_counts,
                name='止损次数',
                marker_color='rgba(239, 68, 68, 0.8)',
                text=stop_loss_counts,
                textposition='auto'
            ),
            row=2, col=1
        )

        # 最终资金规模 (转换为百万)
        final_capitals_millions = [c/1000000 for c in final_capitals]
        fig.add_trace(
            go.Bar(
                x=strategies,
                y=final_capitals_millions,
                name='最终资金 (百万)',
                marker_color='rgba(59, 130, 246, 0.8)',
                text=[f'{c:.2f}M' for c in final_capitals_millions],
                textposition='auto'
            ),
            row=2, col=2
        )

        fig.update_layout(
            title="🔄 交易表现维度对比分析",
            height=800,
            showlegend=False
        )
        fig.update_xaxes(tickangle=45)
        fig.update_yaxes(title_text="胜率 (%)", row=1, col=1)
        fig.update_yaxes(title_text="盈亏比", row=1, col=2)
        fig.update_yaxes(title_text="止损次数", row=2, col=1)
        fig.update_yaxes(title_text="资金 (百万)", row=2, col=2)
        fig.update_xaxes(title_text="策略", row=2, col=2)

        return fig

    def create_comprehensive_analysis_chart(self, df: pd.DataFrame) -> go.Figure:
        """创建综合分析图表"""
        if df.empty:
            return go.Figure()

        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('策略综合评分', '执行效率对比', '参数复杂度', '策略类型分析'),
            specs=[[{"type": "bar"}, {"type": "bar"}],
                   [{"type": "bar"}, {"type": "pie"}]]
        )

        strategies = df['策略名称'].tolist()
        returns = df['总收益率'].str.rstrip('%').astype(float).tolist()
        sharpe_ratios = df['夏普比率'].tolist()
        trade_counts = df['总交易次数'].tolist()
        execution_times = df.get('执行时间(s)', [1.0] * len(strategies)).tolist()

        # 综合评分 (夏普比率 * 40% + 收益率贡献 * 30% + 胜率 * 20% + 交易频率 * 10%)
        win_rates = df['胜率'].str.rstrip('%').astype(float).tolist()
        trade_frequency = [min(tc/10, 10) for tc in trade_counts]  # 标准化交易频率

        comprehensive_scores = []
        for i in range(len(strategies)):
            score = (sharpe_ratios[i] * 0.4 +
                     (returns[i] / max(abs(r) for r in returns)) * 0.3 +
                     win_rates[i] / 100 * 0.2 +
                     trade_frequency[i] / 10 * 0.1)
            comprehensive_scores.append(score)

        # 综合评分柱状图
        fig.add_trace(
            go.Bar(
                x=strategies,
                y=comprehensive_scores,
                name='综合评分',
                marker_color='rgba(34, 197, 94, 0.8)',
                text=[f'{score:.3f}' for score in comprehensive_scores],
                textposition='auto'
            ),
            row=1, col=1
        )

        # 执行效率对比 (执行时间，时间越短越好)
        fig.add_trace(
            go.Bar(
                x=strategies,
                y=execution_times,
                name='执行时间 (秒)',
                marker_color='rgba(156, 163, 175, 0.8)',
                text=[f'{t:.2f}s' for t in execution_times],
                textposition='auto'
            ),
            row=1, col=2
        )

        # 参数复杂度 (参数数量)
        param_counts = []
        for strategy in strategies:
            # 简单的参数数量估算
            if '策略' in strategy and ('双均线' in strategy or 'MACD' in strategy or 'RSI' in strategy):
                param_counts.append(2)
            elif 'KDJ' in strategy and '布林带' not in strategy and 'MACD' not in strategy:
                param_counts.append(2)
            elif '布林带' in strategy and 'RSI' in strategy or 'MACD' in strategy:
                param_counts.append(4)
            elif 'KDJ' in strategy and ('布林带' in strategy or 'MACD' in strategy):
                param_counts.append(5)
            else:
                param_counts.append(3)

        fig.add_trace(
            go.Bar(
                x=strategies,
                y=param_counts,
                name='参数数量',
                marker_color='rgba(245, 158, 11, 0.8)',
                text=param_counts,
                textposition='auto'
            ),
            row=2, col=1
        )

        # 策略类型饼图
        strategy_types = {
            '趋势跟踪': ['双均线策略', 'MACD趋势策略', '成交量突破策略'],
            '超买超卖': ['KDJ超卖反弹策略', 'RSI反转策略', '布林带策略'],
            '复合策略': ['KDJ+布林带系统', 'KDJ+MACD双重确认策略', '布林带+RSI反转策略']
        }

        type_counts = []
        type_labels = []
        for type_name, type_strategies in strategy_types.items():
            count = len([s for s in strategies if s in type_strategies])
            if count > 0:
                type_counts.append(count)
                type_labels.append(f'{type_name} ({count})')

        fig.add_trace(
            go.Pie(
                labels=type_labels,
                values=type_counts,
                name="策略类型分布"
            ),
            row=2, col=2
        )

        fig.update_layout(
            title="📊 综合维度对比分析",
            height=800,
            showlegend=True
        )
        fig.update_xaxes(tickangle=45)

        return fig

    def create_detailed_metrics_table(self, df: pd.DataFrame) -> None:
        """创建详细的策略指标表格"""
        if df.empty:
            return

        st.subheader("📊 策略详细指标对比")

        # 格式化数据用于显示
        display_df = df.copy()

        # 选择要显示的关键列
        key_columns = [
            '排名', '策略名称', '总收益率', '年化收益率', '夏普比率',
            '最大回撤', '总交易次数', '胜率', '盈亏比', '最终资金'
        ]

        display_df = display_df[key_columns]

        # 重命名为中文显示
        column_mapping = {
            '排名': '🥇 排名',
            '策略名称': '📈 策略名称',
            '总收益率': '💰 总收益率',
            '年化收益率': '📅 年化收益率',
            '夏普比率': '⚡ 夏普比率',
            '最大回撤': '📉 最大回撤',
            '总交易次数': '🔄 交易次数',
            '胜率': '🎯 胜率',
            '盈亏比': '⚖️ 盈亏比',
            '最终资金': '💵 最终资金'
        }

        display_df = display_df.rename(columns=column_mapping)

        # 根据收益率添加颜色标识
        def color_returns(val):
            if isinstance(val, str) and '%' in val:
                return_val = float(val.rstrip('%'))
                if return_val >= 50:
                    return 'background-color: rgba(34, 197, 94, 0.2); color: black'
                elif return_val >= 20:
                    return 'background-color: rgba(251, 191, 36, 0.2); color: black'
                elif return_val >= 0:
                    return 'background-color: rgba(156, 163, 175, 0.2); color: black'
                else:
                    return 'background-color: rgba(239, 68, 68, 0.2); color: white'
            return ''

        # 应用样式
        styled_df = display_df.style.map(color_returns, subset=['💰 总收益率'])

        st.dataframe(styled_df, use_container_width=True, hide_index=True)

    def create_best_strategies_highlight(self, df: pd.DataFrame) -> None:
        """突出显示最佳策略"""
        if df.empty:
            return

        st.subheader("🏆 最佳策略分析")

        col1, col2, col3 = st.columns(3)

        with col1:
            # 最高收益率
            best_return_idx = df['总收益率'].str.rstrip('%').astype(float).idxmax()
            best_return_strategy = df.loc[best_return_idx]

            st.metric(
                label="🥇 最高收益率",
                value=best_return_strategy['总收益率'],
                delta=f"夏普: {best_return_strategy['夏普比率']}"
            )
            st.write(f"**策略**: {best_return_strategy['策略名称']}")
            st.write(f"**胜率**: {best_return_strategy['胜率']}")

        with col2:
            # 最高夏普比率
            best_sharpe_idx = df['夏普比率'].idxmax()
            best_sharpe_strategy = df.loc[best_sharpe_idx]

            st.metric(
                label="⚡ 最佳风险收益",
                value=best_sharpe_strategy['夏普比率'],
                delta=f"收益: {best_sharpe_strategy['总收益率']}"
            )
            st.write(f"**策略**: {best_sharpe_strategy['策略名称']}")
            st.write(f"**最大回撤**: {best_sharpe_strategy['最大回撤']}")

        with col3:
            # 最高胜率
            best_winrate_idx = df['胜率'].str.rstrip('%').astype(float).idxmax()
            best_winrate_strategy = df.loc[best_winrate_idx]

            st.metric(
                label="🎯 最高胜率",
                value=best_winrate_strategy['胜率'],
                delta=f"交易: {best_winrate_strategy['总交易次数']}次"
            )
            st.write(f"**策略**: {best_winrate_strategy['策略名称']}")
            st.write(f"**盈亏比**: {best_winrate_strategy['盈亏比']}")

    def create_all_strategies_comparison_chart(self, df: pd.DataFrame) -> go.Figure:
        """创建所有策略对比图表（按照示例图片的格式）"""
        if df.empty:
            return go.Figure()

        # 按总收益率降序排序策略
        df_sorted = df.sort_values('总收益率', key=lambda x: x.str.rstrip('%').astype(float), ascending=False)
        strategies = df_sorted['策略名称'].tolist()

        # 数据转换
        total_returns = df_sorted['总收益率'].str.rstrip('%').astype(float)
        annual_returns = df_sorted['年化收益率'].str.rstrip('%').astype(float)
        sharpe_ratios = df_sorted['夏普比率'].tolist()
        max_drawdowns = df_sorted['最大回撤'].str.rstrip('%').astype(float)
        win_rates = df_sorted['胜率'].str.rstrip('%').astype(float)
        trade_counts = df_sorted['总交易次数'].tolist()

        # 创建4个子图的布局
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('总收益率对比', '夏普比率对比', '最大回撤对比', '胜率对比'),
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}]]
        )

        # 1. 总收益率柱状图 (左上)
        colors = ['rgba(34, 197, 94, 0.8)' if r > 0 else 'rgba(239, 68, 68, 0.8)' for r in total_returns]

        fig.add_trace(
            go.Bar(
                x=strategies,
                y=total_returns,
                name='总收益率 (%)',
                marker_color=colors,
                text=[f'{r:.1f}%' for r in total_returns],
                textposition='outside',
                textfont=dict(size=10)
            ),
            row=1, col=1
        )

        # 2. 夏普比率柱状图 (右上)
        sharpe_colors = ['rgba(59, 130, 246, 0.8)' if s > 0 else 'rgba(156, 163, 175, 0.8)' for s in sharpe_ratios]

        fig.add_trace(
            go.Bar(
                x=strategies,
                y=sharpe_ratios,
                name='夏普比率',
                marker_color=sharpe_colors,
                text=[f'{s:.2f}' for s in sharpe_ratios],
                textposition='outside',
                textfont=dict(size=10)
            ),
            row=1, col=2
        )

        # 3. 最大回撤柱状图 (左下) - 注意：回撤越小越好，所以用倒序
        fig.add_trace(
            go.Bar(
                x=strategies,
                y=[-x for x in max_drawdowns],  # 负值显示，越接近0越好
                name='最大回撤 (-%)',
                marker_color='rgba(245, 158, 11, 0.8)',
                text=[f'{x:.1f}%' for x in max_drawdowns],
                textposition='outside',
                textfont=dict(size=10)
            ),
            row=2, col=1
        )

        # 4. 胜率柱状图 (右下)
        win_rate_colors = ['rgba(34, 197, 94, 0.8)' if w > 50 else 'rgba(245, 158, 11, 0.8)' for w in win_rates]

        fig.add_trace(
            go.Bar(
                x=strategies,
                y=win_rates,
                name='胜率 (%)',
                marker_color=win_rate_colors,
                text=[f'{w:.0f}%' for w in win_rates],
                textposition='outside',
                textfont=dict(size=10)
            ),
            row=2, col=2
        )

        # 更新布局
        fig.update_layout(
            height=800,
            showlegend=False,
            title_text="策略表现对比分析",
            title_x=0.5
        )

        # 更新坐标轴
        fig.update_xaxes(tickangle=45, tickfont=dict(size=9), row=1, col=1)
        fig.update_xaxes(tickangle=45, tickfont=dict(size=9), row=1, col=2)
        fig.update_xaxes(tickangle=45, tickfont=dict(size=9), row=2, col=1)
        fig.update_xaxes(tickangle=45, tickfont=dict(size=9), row=2, col=2)

        fig.update_yaxes(title_text="收益率 (%)", tickfont=dict(size=9), row=1, col=1)
        fig.update_yaxes(title_text="夏普比率", tickfont=dict(size=9), row=1, col=2)
        fig.update_yaxes(title_text="最大回撤 (%)", tickfont=dict(size=9), row=2, col=1)
        fig.update_yaxes(title_text="胜率 (%)", tickfont=dict(size=9), row=2, col=2)

        return fig

    def create_detailed_metrics_comparison(self, df: pd.DataFrame) -> None:
        """创建详细指标对比表格"""
        if df.empty:
            return

        # 准备显示数据
        display_df = df.copy()

        # 选择要显示的关键列
        key_columns = [
            '策略名称', '总收益率', '年化收益率', '夏普比率', '卡尔玛比率',
            '最大回撤', '年化波动率', '总交易次数', '胜率', '盈亏比', '最终资金'
        ]

        display_df = display_df[key_columns]

        # 重命名为中文显示
        column_mapping = {
            '策略名称': '📈 策略名称',
            '总收益率': '💰 总收益率',
            '年化收益率': '📅 年化收益率',
            '夏普比率': '⚡ 夏普比率',
            '卡尔玛比率': '🛡️ 卡尔玛比率',
            '最大回撤': '📉 最大回撤',
            '年化波动率': '📊 年化波动率',
            '总交易次数': '🔄 交易次数',
            '胜率': '🎯 胜率',
            '盈亏比': '⚖️ 盈亏比',
            '最终资金': '💵 最终资金'
        }

        display_df = display_df.rename(columns=column_mapping)

        # 根据收益率添加颜色标识
        def color_returns(val):
            if isinstance(val, str) and '%' in val:
                return_val = float(val.rstrip('%'))
                if return_val >= 50:
                    return 'background-color: rgba(34, 197, 94, 0.3); color: black'
                elif return_val >= 20:
                    return 'background-color: rgba(251, 191, 36, 0.3); color: black'
                elif return_val >= 0:
                    return 'background-color: rgba(156, 163, 175, 0.2); color: black'
                else:
                    return 'background-color: rgba(239, 68, 68, 0.3); color: white'
            return ''

        # 应用样式
        styled_df = display_df.style.map(color_returns, subset=['💰 总收益率'])

        st.dataframe(styled_df, use_container_width=True, hide_index=True)

    def render(self, symbol: str) -> None:
        """渲染策略对比图表 - 每个Tab显示一个指标"""
        st.header(f"📈 {symbol} 策略对比分析")

        # 加载数据
        df = self.load_strategy_comparison_data(symbol)

        if df.empty:
            st.warning("⚠️ 未找到策略对比数据，请先运行策略回测")
            return

        # 显示最佳策略亮点
        self.create_best_strategies_highlight(df)

        # 创建多个tab，每个Tab显示一个指标的对比
        tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
            "💰 总收益率",
            "📅 年化收益率",
            "⚡ 夏普比率",
            "🛡️ 卡尔玛比率",
            "📉 最大回撤",
            "📊 年化波动率",
            "🔄 交易次数",
            "🎯 胜率",
            "⚖️ 盈亏比"
        ])

        with tab1:
            st.subheader("💰 总收益率对比")
            # 使用通用函数创建总收益率对比图表
            fig = self.create_single_metric_comparison_chart(
                metric_name="总收益率",
                df=df,
                metric_column="总收益率",
                value_format=".1f",
                is_percentage=True
            )
            st.plotly_chart(fig, use_container_width=True)

        with tab2:
            st.subheader("📅 年化收益率对比")
            # 使用通用函数创建年化收益率对比图表
            fig = self.create_single_metric_comparison_chart(
                metric_name="年化收益率",
                df=df,
                metric_column="年化收益率",
                value_format=".1f",
                is_percentage=True
            )
            st.plotly_chart(fig, use_container_width=True)

        with tab3:
            st.subheader("⚡ 夏普比率对比")
            # 使用通用函数创建夏普比率对比图表
            fig = self.create_single_metric_comparison_chart(
                metric_name="夏普比率",
                df=df,
                metric_column="夏普比率",
                value_format=".2f",
                is_percentage=False
            )
            st.plotly_chart(fig, use_container_width=True)

        with tab4:
            st.subheader("🛡️ 卡尔玛比率对比")
            # 使用通用函数创建卡尔玛比率对比图表
            fig = self.create_single_metric_comparison_chart(
                metric_name="卡尔玛比率",
                df=df,
                metric_column="卡尔玛比率",
                value_format=".2f",
                is_percentage=False
            )
            st.plotly_chart(fig, use_container_width=True)

        with tab5:
            st.subheader("📉 最大回撤对比")
            # 最大回撤对比（越小越好，使用负值显示）
            try:
                # 安全获取最大回撤数据
                max_drawdowns = pd.to_numeric(df['最大回撤'].astype(str).str.rstrip('%'), errors='coerce')
                # 不填充NaN值，保持原始数据状态

                # 创建临时数据框用于负值显示
                temp_df = df.copy()
                temp_df['最大回撤_负值'] = -max_drawdowns

                # 使用通用函数创建最大回撤对比图表
                fig = self.create_single_metric_comparison_chart(
                    metric_name="最大回撤",
                    df=temp_df,
                    metric_column="最大回撤_负值",
                    value_format=".1f",
                    is_percentage=False  # 不使用百分比处理，因为已经转换为负值
                )

                # 更新标题和y轴说明
                fig.update_layout(title="最大回撤对比分析 (越小越好)")
                fig.update_yaxes(
                    title_text="最大回撤 (%)",
                    tickvals=[-40, -30, -20, -10, 0],
                    ticktext=["40%", "30%", "20%", "10%", "0%"]
                )

                # 更新显示文本为正数
                if hasattr(fig.data[0], 'text') and fig.data[0].text:
                    for i in range(len(fig.data[0].text)):
                        original_text = fig.data[0].text[i]
                        if isinstance(original_text, str) and '%' in original_text:
                            # 去掉负号显示
                            fig.data[0].text[i] = original_text.replace('-', '')

                st.plotly_chart(fig, use_container_width=True)

            except Exception as e:
                st.error(f"❌ 处理最大回撤数据时出错: {str(e)}")
                st.info("请检查数据文件中的最大回撤列格式")

        with tab6:
            st.subheader("📊 年化波动率对比")
            # 使用通用函数创建年化波动率对比图表
            fig = self.create_single_metric_comparison_chart(
                metric_name="年化波动率",
                df=df,
                metric_column="年化波动率",
                value_format=".1f",
                is_percentage=True
            )
            st.plotly_chart(fig, use_container_width=True)

        with tab7:
            st.subheader("🔄 交易次数对比")
            # 使用通用函数创建交易次数对比图表
            fig = self.create_single_metric_comparison_chart(
                metric_name="交易次数",
                df=df,
                metric_column="总交易次数",
                value_format=".0f",
                is_percentage=False
            )
            st.plotly_chart(fig, use_container_width=True)

        with tab8:
            st.subheader("🎯 胜率对比")
            # 使用通用函数创建胜率对比图表
            fig = self.create_single_metric_comparison_chart(
                metric_name="胜率",
                df=df,
                metric_column="胜率",
                value_format=".0f",
                is_percentage=True
            )
            st.plotly_chart(fig, use_container_width=True)

        with tab9:
            st.subheader("⚖️ 盈亏比对比")
            try:
                # 处理inf盈亏比
                profit_loss_ratios_clean = []
                original_ratios = []

                for ratio in df['盈亏比']:
                    # 转换为字符串处理
                    ratio_str = str(ratio).strip()
                    original_ratios.append(ratio_str)

                    if ratio_str.lower() == 'inf' or ratio_str == 'inf' or ratio == float('inf'):
                        profit_loss_ratios_clean.append(10.0)  # 用10.0代表∞
                    else:
                        # 尝试转换为数值
                        try:
                            clean_ratio = float(ratio)
                            profit_loss_ratios_clean.append(clean_ratio)
                        except (ValueError, TypeError):
                            # 无法转换的保持为NaN，不填充0
                            profit_loss_ratios_clean.append(float('nan'))

                # 创建临时数据框用于处理后的盈亏比
                temp_df = df.copy()
                temp_df['盈亏比_处理'] = profit_loss_ratios_clean

                # 使用通用函数创建盈亏比对比图表
                fig = self.create_single_metric_comparison_chart(
                    metric_name="盈亏比",
                    df=temp_df,
                    metric_column="盈亏比_处理",
                    value_format=".2f",
                    is_percentage=False
                )

                # 更新显示文本，将10.0显示为∞
                if hasattr(fig.data[0], 'text') and fig.data[0].text:
                    for i, ratio in enumerate(profit_loss_ratios_clean):
                        if ratio == 10.0:
                            fig.data[0].text[i] = '∞'

                st.plotly_chart(fig, use_container_width=True)

            except Exception as e:
                st.error(f"❌ 处理盈亏比数据时出错: {str(e)}")
                st.info("请检查数据文件中的盈亏比列格式")

        # 添加交易信号表格
        st.markdown("---")
        self._show_trades_table(symbol)

    def _show_trades_table(self, symbol: str):
        """显示交易信号表格"""
        st.subheader("📋 策略交易信号详情")

        # 读取total_trades.csv文件
        trades_file = Path(f"data/cleaned_stocks/{symbol}/backtest_results/total_trades.csv")

        if not trades_file.exists():
            st.warning("⚠️ 未找到交易信号数据文件")
            return

        try:
            trades_df = pd.read_csv(trades_file, encoding='utf-8')

            if trades_df.empty:
                st.warning("⚠️ 交易信号数据为空")
                return

            # 策略列名
            strategy_columns = [
                '双均线策略', 'MACD趋势策略', 'KDJ超卖反弹策略', 'KDJ+布林带系统',
                'KDJ+MACD双重确认策略', 'RSI反转策略', '布林带策略',
                '成交量突破策略', '布林带+RSI反转策略'
            ]

            # 过滤：只显示至少有一个策略有信号的日期
            trades_df_filtered = trades_df.copy()

            # 添加一个新列来统计每个日期有多少策略有信号
            trades_df_filtered['信号数量'] = 0

            for strategy in strategy_columns:
                if strategy in trades_df_filtered.columns:
                    # 计算每个策略的信号数量
                    signals = trades_df_filtered[strategy].notna() & (trades_df_filtered[strategy] != '')
                    trades_df_filtered.loc[signals, '信号数量'] += 1

            # 只保留有信号的日期
            trades_with_signals = trades_df_filtered[trades_df_filtered['信号数量'] > 0].copy()

            if trades_with_signals.empty:
                st.info("📊 暂无策略交易信号记录")
                return

            # 按日期降序排序（最新的在前）
            trades_with_signals = trades_with_signals.sort_values('日期', ascending=False)

            # 准备显示数据
            display_columns = ['日期', '收盘价'] + strategy_columns
            display_df = trades_with_signals[display_columns].copy()

            # 格式化日期和价格
            display_df['日期'] = pd.to_datetime(display_df['日期']).dt.strftime('%Y-%m-%d')
            display_df['收盘价'] = display_df['收盘价'].apply(lambda x: f'¥{x:.2f}')

            # 为信号单元格添加颜色标记
            def highlight_signals(val):
                if pd.isna(val) or val == '':
                    return 'background-color: rgba(248, 249, 250, 0.5); color: transparent;'
                elif val == 'buy':
                    return 'background-color: rgba(239, 68, 68, 0.8); color: white; font-weight: bold; text-align: center;'
                elif val == 'sell':
                    return 'background-color: rgba(34, 197, 94, 0.8); color: white; font-weight: bold; text-align: center;'
                return 'background-color: rgba(251, 191, 36, 0.8); color: black; text-align: center;'

            # 应用样式
            styled_df = display_df.style.applymap(
                highlight_signals,
                subset=strategy_columns
            ).set_properties(**{
                'width': '100px',
                'text-align': 'center'
            })

            # 添加统计信息
            col1, col2, col3 = st.columns(3)

            with col1:
                total_signals = len(trades_with_signals)
                st.metric("📊 总信号天数", f"{total_signals}")

            with col2:
                buy_signals = 0
                sell_signals = 0
                for strategy in strategy_columns:
                    if strategy in trades_with_signals.columns:
                        buy_signals += (trades_with_signals[strategy] == 'buy').sum()
                        sell_signals += (trades_with_signals[strategy] == 'sell').sum()
                st.metric("📈 买入信号", f"{buy_signals}")

            with col3:
                st.metric("📉 卖出信号", f"{sell_signals}")

            # 显示表格
            st.markdown("#### 📋 交易信号明细表")
            st.markdown("*红色背景 = 买入信号 | 绿色背景 = 卖出信号*")

            # 设置表格显示选项
            st.dataframe(
                styled_df,
                use_container_width=True,
                hide_index=True,
                height=400
            )

            # 添加下载按钮
            csv = display_df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 下载交易信号数据",
                data=csv,
                file_name=f"{symbol}_策略交易信号_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
                mime='text/csv'
            )

        except Exception as e:
            st.error(f"❌ 读取交易信号数据时出错: {str(e)}")

        