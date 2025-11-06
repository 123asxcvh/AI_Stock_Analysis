#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
技术分析组件
优化后的单图表垂直布局版本
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any

# 安全导入plotly模块
try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError as e:
    st.error(f"❌ Plotly导入失败: {e}")
    st.error("请确保已安装plotly: pip install plotly")
    PLOTLY_AVAILABLE = False
    # 创建空的占位符以避免后续错误
    go = None
    make_subplots = None

# 添加项目根目录
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.web.utils import (
    format_number, display_metric,
    validate_data
)

# 使用UI模板管理器
from src.web.templates import ui_template_manager


class TechnicalAnalysisComponent:
    """统一的技术分析组件"""

    def __init__(self):
        self.name = "技术分析"
        self.config = None
        self.data_cache = {}

    def render(self, data: Dict[str, Any]) -> None:
        """渲染技术分析页面"""
        if not PLOTLY_AVAILABLE:
            st.error("❌ Plotly模块未加载，技术分析功能不可用")
            return

        if not data or 'historical_quotes' not in data:
            st.error("未找到历史行情数据")
            return

        df = data['historical_quotes']
        if not validate_data(df, ['开盘', '最高', '最低', '收盘']):
            st.error("历史行情数据格式不正确")
            return

        # 确保数据按时间排序（在所有处理开始前）
        if not df.empty and hasattr(df.index, 'sort_values'):
            df = df.sort_index()
        elif not df.empty and '日期' in df.columns:
            df = df.sort_values('日期')

        stock_code = data.get('stock_code', '未知')

        # 页面标题
        ui_template_manager.section_header(f"📈 {stock_code} 技术分析", level=1)

        # 关键指标展示
        self._show_key_metrics(df)

        # 主要图表 - 包含价格走势和技术指标
        self._show_main_charts_with_indicators(df)

        # AI分析报告
        self._show_ai_report(data)

    def _show_key_metrics(self, df: pd.DataFrame):
        """显示关键指标"""
        ui_template_manager.section_header("🔑 关键指标")

        # 数据已在render方法中排序，无需重复排序

        cols = st.columns(4)

        with cols[0]:
            # 安全获取最新收盘价
            if not df.empty and '收盘' in df.columns:
                current_price = df['收盘'].iloc[-1]
            else:
                current_price = 0
            display_metric("当前价格", f"¥{current_price:.2f}")

        with cols[1]:
            if len(df) > 1:
                current_price = df['收盘'].iloc[-1]
                prev_price = df['收盘'].iloc[-2]
                price_change = (current_price - prev_price) / prev_price * 100
                formatted_change = f"{price_change:+.2f}%"

                # 中国股市红涨绿跌：正涨幅显示红色，负跌幅显示绿色
                # Streamlit的delta会自动处理颜色，但我们需要反向显示
                # 对于中国股市，我们需要反转delta的符号来获得正确的颜色效果
                display_metric("涨跌幅", formatted_change, delta=f"{-price_change:+.2f}%")
            else:
                display_metric("涨跌幅", "N/A")

        with cols[2]:
            if '成交量' in df.columns and not df.empty:
                volume = df['成交量'].iloc[-1]
                display_metric("成交量", format_number(volume))
            else:
                display_metric("成交量", "N/A")

        with cols[3]:
            if len(df) >= 20:
                # 计算20日波动率
                returns = df['收盘'].pct_change().dropna()
                if len(returns) >= 20:
                    volatility = returns.rolling(20).std().iloc[-1] * (252**0.5) * 100
                    display_metric("20日波动率", f"{volatility:.1f}%")
                else:
                    display_metric("20日波动率", "N/A")
            else:
                display_metric("20日波动率", "N/A")

    def _show_main_charts_with_indicators(self, df: pd.DataFrame):
        """显示主图表和技术指标 - 垂直堆叠布局"""
        if not PLOTLY_AVAILABLE:
            st.error("❌ Plotly模块未加载，无法显示图表")
            return

        ui_template_manager.section_header("📊 价格走势")

        # 时间范围选择 - 一行显示，模拟radio效果
        col1, col2, col3, col4, col5 = st.columns(5)

        # 获取当前选择，默认为6个月
        current_selection = getattr(st.session_state, 'time_range', '6个月')

        with col1:
            button_type = "primary" if current_selection == "1个月" else "secondary"
            if st.button("1个月", key="1month", use_container_width=True, type=button_type):
                st.session_state.time_range = "1个月"
                st.rerun()

        with col2:
            button_type = "primary" if current_selection == "3个月" else "secondary"
            if st.button("3个月", key="3months", use_container_width=True, type=button_type):
                st.session_state.time_range = "3个月"
                st.rerun()

        with col3:
            button_type = "primary" if current_selection == "6个月" else "secondary"
            if st.button("6个月", key="6months", use_container_width=True, type=button_type):
                st.session_state.time_range = "6个月"
                st.rerun()

        with col4:
            button_type = "primary" if current_selection == "1年" else "secondary"
            if st.button("1年", key="1year", use_container_width=True, type=button_type):
                st.session_state.time_range = "1年"
                st.rerun()

        with col5:
            button_type = "primary" if current_selection == "全部" else "secondary"
            if st.button("全部", key="all", use_container_width=True, type=button_type):
                st.session_state.time_range = "全部"
                st.rerun()

        # 获取最终选择的时间范围
        time_range = getattr(st.session_state, 'time_range', '6个月')

        # 过滤数据
        filtered_df = self._filter_data_by_time(df, time_range)

        # 创建垂直堆叠的技术指标图表
        fig = make_subplots(
            rows=7,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.010,
            row_heights=[0.30, 0.05, 0.13, 0.13, 0.13, 0.13, 0.13],  # 用户指定的高度分配
            subplot_titles=['K线 + BBI', '成交量1', '成交量2', 'WEEKLY_KDJ_J', 'DAILY_KDJ_J', 'RSI', 'MACD'],
            specs=[
                [{"secondary_y": False}],  # K线 + BBI (30%)
                [{"secondary_y": False}],  # 成交量1 (5%)
                [{"secondary_y": False}],  # 成交量2 (13%)
                [{"secondary_y": False}],  # WEEKLY_J (13%)
                [{"secondary_y": False}],  # DAILY_J (13%)
                [{"secondary_y": False}],  # RSI (13%)
                [{"secondary_y": True}]    # MACD (13%, 双轴)
            ]
        )

        # 红涨绿跌颜色方案
        colors_up = '#FF4444'  # 红色上涨
        colors_down = '#00C853'  # 绿色下跌

        # 1. K线图 + BBI (第1行) - 中国股市红涨绿跌
        fig.add_trace(
            go.Candlestick(
                x=filtered_df.index,
                open=filtered_df['开盘'],
                high=filtered_df['最高'],
                low=filtered_df['最低'],
                close=filtered_df['收盘'],
                name='K线',
                # 中国股市：收盘价>=开盘价是上涨，显示红色
                increasing=dict(line=dict(color=colors_up), fillcolor=colors_up),   # 红色上涨
                decreasing=dict(line=dict(color=colors_down), fillcolor=colors_down) # 绿色下跌
            ),
            row=1, col=1
        )

        # BBI线
        if 'BBI' in filtered_df.columns:
            fig.add_trace(
                go.Scatter(
                    x=filtered_df.index,
                    y=filtered_df['BBI'],
                    name='BBI',
                    line=dict(color='#FFD700', width=2.5)
                ),
                row=1, col=1
            )

        # 2. 成交量1 (第2行) - 第一个成交量图表
        if '成交量' in filtered_df.columns:
            volume_colors = [colors_up if close >= open else colors_down
                           for close, open in zip(filtered_df['收盘'], filtered_df['开盘'])]

            fig.add_trace(
                go.Bar(
                    x=filtered_df.index,
                    y=filtered_df['成交量'],
                    name='成交量1',
                    marker_color=volume_colors,
                    opacity=0.8
                ),
                row=2, col=1
            )

        # 3. 成交量2 (第3行) - 第二个成交量图表
        if '成交量' in filtered_df.columns:
            volume_colors2 = [colors_up if close >= open else colors_down
                            for close, open in zip(filtered_df['收盘'], filtered_df['开盘'])]

            fig.add_trace(
                go.Bar(
                    x=filtered_df.index,
                    y=filtered_df['成交量'],
                    name='成交量2',
                    marker_color=volume_colors2,
                    opacity=0.6
                ),
                row=3, col=1
            )

        # 4. WEEKLY_KDJ_J (第4行)
        if 'WEEKLY_KDJ_J' in filtered_df.columns:
            fig.add_trace(
                go.Scatter(
                    x=filtered_df.index,
                    y=filtered_df['WEEKLY_KDJ_J'],
                    name='WEEKLY_KDJ_J',
                    line=dict(color='#9C27B0', width=2)
                ),
                row=4, col=1
            )

            # 添加参考线
            fig.add_hline(y=80, line_dash="dash", line_color="red", opacity=0.7, row=4, col=1)
            fig.add_hline(y=20, line_dash="dash", line_color="green", opacity=0.7, row=4, col=1)

        # 5. DAILY_KDJ_J (第5行)
        if 'DAILY_KDJ_J' in filtered_df.columns:
            fig.add_trace(
                go.Scatter(
                    x=filtered_df.index,
                    y=filtered_df['DAILY_KDJ_J'],
                    name='DAILY_KDJ_J',
                    line=dict(color='#FF9800', width=2)
                ),
                row=5, col=1
            )

            # 添加参考线
            fig.add_hline(y=80, line_dash="dash", line_color="red", opacity=0.7, row=5, col=1)
            fig.add_hline(y=20, line_dash="dash", line_color="green", opacity=0.7, row=5, col=1)

        # 6. RSI (第6行)
        if 'RSI' in filtered_df.columns:
            fig.add_trace(
                go.Scatter(
                    x=filtered_df.index,
                    y=filtered_df['RSI'],
                    name='RSI',
                    line=dict(color='#00BCD4', width=2)
                ),
                row=6, col=1
            )

            # 添加参考线
            fig.add_hline(y=70, line_dash="dash", line_color="red", opacity=0.7, row=6, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="green", opacity=0.7, row=6, col=1)

        # 7. MACD真正双轴结构 (第7行) - HIST左轴，DIF和DEA右轴
        if all(col in filtered_df.columns for col in ['MACD_DIF', 'MACD_DEA', 'MACD_HIST']):
            # MACD HIST柱状图 - 左轴，中国股市红涨绿跌
            hist_colors = []
            for hist_val in filtered_df['MACD_HIST']:
                if hist_val >= 0:
                    hist_colors.append('#FF0040')  # 鲜艳红色 (上涨/正值)
                else:
                    hist_colors.append('#00FF41')  # 鲜艳绿色 (下跌/负值)

            fig.add_trace(
                go.Bar(
                    x=filtered_df.index,
                    y=filtered_df['MACD_HIST'],
                    name='HIST',
                    marker_color=hist_colors,
                    opacity=0.8
                ),
                row=7, col=1,
                secondary_y=False  # 使用左轴
            )

            # MACD DIF线 - 右轴
            fig.add_trace(
                go.Scatter(
                    x=filtered_df.index,
                    y=filtered_df['MACD_DIF'],
                    name='DIF',
                    line=dict(color='#FFD700', width=2)
                ),
                row=7, col=1,
                secondary_y=True  # 使用右轴
            )

            # MACD DEA线 - 右轴
            fig.add_trace(
                go.Scatter(
                    x=filtered_df.index,
                    y=filtered_df['MACD_DEA'],
                    name='DEA',
                    line=dict(color='#FF6B6B', width=2)
                ),
                row=7, col=1,
                secondary_y=True  # 使用右轴
            )

        # 更新布局
        fig.update_layout(
            height=1000,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            template="plotly_dark"
        )

        # 设置MACD双轴标题
        fig.update_yaxes(title_text="HIST", row=7, col=1, secondary_y=False)
        fig.update_yaxes(title_text="DIF/DEA", row=7, col=1, secondary_y=True)

        # 只在最下方显示x轴标签 (现在是第7行的MACD)
        fig.update_xaxes(showticklabels=True, row=7, col=1)
        for i in range(1, 7):  # 第1-6行隐藏x轴标签
            fig.update_xaxes(showticklabels=False, row=i, col=1)

        # 隐藏所有子图的x轴标题
        for i in range(1, 8):
            fig.update_xaxes(title_text="", row=i, col=1)

        # 显示图表
        st.plotly_chart(fig, use_container_width=True)

    def _filter_data_by_time(self, df: pd.DataFrame, time_range: str) -> pd.DataFrame:
        """根据时间范围过滤数据"""
        if time_range == "全部":
            return df

        days_map = {
            "1个月": 30,
            "3个月": 90,
            "6个月": 180,
            "1年": 365
        }

        days = days_map.get(time_range, 180)  # 默认6个月
        return df.tail(days)

    def _show_ai_report(self, data: Dict[str, Any]):
        """显示AI分析报告 - 使用两个tab分别显示intraday_trading和technical_analysis"""
        ui_template_manager.section_header("🤖 AI分析报告")

        try:
            # 导入AI报告管理器
            from src.web.utils.unified_utils import ai_report_manager

            # 获取股票代码
            stock_code = data.get("stock_code", "未知")

            # 加载AI报告
            reports = ai_report_manager.load_reports(stock_code, "stock")

            # 创建两个tab
            intraday_tab, technical_tab = st.tabs(["📈 Intraday Trading", "🔧 Technical Analysis"])

            with intraday_tab:
                if reports and "intraday_trading.md" in reports:
                    content = reports["intraday_trading.md"]
                    if content.startswith("❌"):
                        st.error(f"📈 Intraday Trading AI分析失败: {content}")
                    else:
                        st.markdown(content)
                else:
                    st.info("📈 Intraday Trading AI分析报告暂未加载")

            with technical_tab:
                if reports and "technical_analysis.md" in reports:
                    content = reports["technical_analysis.md"]
                    if content.startswith("❌"):
                        st.error(f"🔧 Technical Analysis AI分析失败: {content}")
                    else:
                        st.markdown(content)
                else:
                    st.info("🔧 Technical Analysis AI分析报告暂未加载")

        except Exception as e:
            st.error(f"加载AI分析报告时出错: {str(e)}")
            st.info("AI分析报告暂未加载，请确保已生成相应的分析文件。")


# 创建全局组件实例
technical_analysis_component = TechnicalAnalysisComponent()