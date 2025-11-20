#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
技术分析组件
优化后的单图表垂直布局版本
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any
from pathlib import Path

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

        # 原数据是倒序的（最新的在前），需要排序为正序（最旧在前，最新在后）
        # 这样图表才能正确显示时间序列走势
        if not df.empty:
            if '日期' in df.columns:
                df['日期'] = pd.to_datetime(df['日期'], errors='coerce')
                df = df.dropna(subset=['日期'])
                df = df.sort_values(by='日期', ascending=True).reset_index(drop=True)
                # 将日期列设置为索引，方便图表使用
                df = df.set_index('日期')
            elif isinstance(df.index, pd.DatetimeIndex):
                df = df.sort_index(ascending=True)
            else:
                # 如果没有日期列，尝试从索引推断
                try:
                    df.index = pd.to_datetime(df.index, errors='coerce')
                    df = df.dropna()
                    df = df.sort_index(ascending=True)
                except:
                    pass

        stock_code = data.get('stock_code', '未知')

        # 页面标题
        ui_template_manager.section_header(f"📈 {stock_code} 技术分析", level=1)

        # 关键指标展示
        self._show_key_metrics(df)

        # 主要图表 - 包含价格走势和技术指标
        self._show_main_charts_with_indicators(df)

        # 策略对比分析
        self._show_strategy_comparison(stock_code)

        # AI分析报告
        self._show_ai_report(data)

    def _show_key_metrics(self, df: pd.DataFrame):
        """显示关键指标"""
        ui_template_manager.section_header("🔑 关键指标")

        # 数据已在render方法中排序，无需重复排序

        cols = st.columns(4)

        with cols[0]:
            # 数据已排序为正序（最旧在前，最新在后），iloc[-1]是最新的
            if not df.empty and '收盘' in df.columns:
                current_price = df['收盘'].iloc[-1]
            else:
                current_price = 0
            display_metric("当前价格", f"¥{current_price:.2f}")

        with cols[1]:
            if len(df) > 1:
                # 数据已排序为正序（最旧在前，最新在后）
                # iloc[-1] 是最新的价格，iloc[-2] 是前一个交易日的价格
                current_price = df['收盘'].iloc[-1]
                prev_price = df['收盘'].iloc[-2]
                # 涨跌幅 = (当前价格 - 前一个交易日价格) / 前一个交易日价格 * 100
                price_change = (current_price - prev_price) / prev_price * 100
                formatted_change = f"{price_change:+.2f}%"

                # 中国股市红涨绿跌：使用inverse颜色模式
                # inverse模式：正delta显示红色，负delta显示绿色
                display_metric("涨跌幅", formatted_change, delta=f"{price_change:+.2f}%", delta_color="inverse")
            else:
                display_metric("涨跌幅", "N/A")

        with cols[2]:
            if '成交量' in df.columns and not df.empty:
                # 数据已排序为正序，iloc[-1]是最新的成交量
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
        """显示主图表和技术指标 - 可选择的垂直堆叠布局"""
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
            if st.button("1个月", key="1month", type=button_type):
                st.session_state.time_range = "1个月"
                st.rerun()

        with col2:
            button_type = "primary" if current_selection == "3个月" else "secondary"
            if st.button("3个月", key="3months", type=button_type):
                st.session_state.time_range = "3个月"
                st.rerun()

        with col3:
            button_type = "primary" if current_selection == "6个月" else "secondary"
            if st.button("6个月", key="6months", type=button_type):
                st.session_state.time_range = "6个月"
                st.rerun()

        with col4:
            button_type = "primary" if current_selection == "1年" else "secondary"
            if st.button("1年", key="1year", type=button_type):
                st.session_state.time_range = "1年"
                st.rerun()

        with col5:
            button_type = "primary" if current_selection == "全部" else "secondary"
            if st.button("全部", key="all", type=button_type):
                st.session_state.time_range = "全部"
                st.rerun()

        # 获取最终选择的时间范围
        time_range = getattr(st.session_state, 'time_range', '6个月')

        # 过滤数据
        filtered_df = self._filter_data_by_time(df, time_range)

        # 技术指标选择 - 多选按钮形式
        ui_template_manager.section_header("🔧 技术指标选择")

        # 定义可选的技术指标 - 使用不同的key避免冲突
        indicators = {
            '成交量': {'session_key': 'show_volume', 'default': False},
            'WEEKLY_KDJ_J': {'session_key': 'show_weekly_kdj', 'default': False},
            'DAILY_KDJ_J': {'session_key': 'show_daily_kdj', 'default': True},  # 默认显示
            'RSI': {'session_key': 'show_rsi', 'default': False},
            'MACD': {'session_key': 'show_macd', 'default': True}  # 默认显示
        }

        # 使用columns布局来排列按钮
        cols = st.columns(len(indicators))
        selected_indicators = []

        for i, (indicator_name, config) in enumerate(indicators.items()):
            with cols[i]:
                # 检查session_state中是否已选择，默认使用config中的default值
                is_selected = st.session_state.get(config['session_key'], config['default'])

                button_type = "primary" if is_selected else "secondary"
                # 使用唯一的widget key
                widget_key = f"btn_{config['session_key']}"

                if st.button(indicator_name, key=widget_key, type=button_type):
                    # 切换状态
                    st.session_state[config['session_key']] = not is_selected
                    st.rerun()

                if is_selected:
                    selected_indicators.append(indicator_name)

        # 根据选择的指标动态创建图表
        self._create_dynamic_chart(filtered_df, selected_indicators)

    def _create_dynamic_chart(self, df: pd.DataFrame, selected_indicators: list):
        """根据选择的指标动态创建图表"""
        if not selected_indicators:
            selected_indicators = ['DAILY_KDJ_J', 'MACD']  # 默认显示

        # 计算行数：K线图1行 + 每个选中的指标1行
        rows = 1 + len(selected_indicators)

        # 动态分配行高度：K线图占50%，每个选中指标占25%/指标数量，确保比例为5:2.5:2.5
        k_line_height = 0.5  # 50% - 价格图占据更多空间
        remaining_height = 1 - k_line_height  # 剩余50%空间
        indicator_height = remaining_height / len(selected_indicators) if selected_indicators else 0.25

        # 创建行高度列表
        row_heights = [k_line_height] + [indicator_height] * len(selected_indicators)

        # 创建子图标题列表：K线 + 选中的指标名称
        subplot_titles = ['K线 + BBI'] + selected_indicators

        # 创建子图规格
        specs = [[{"secondary_y": False}]]
        for indicator in selected_indicators:
            if indicator == 'MACD':
                specs.append([{"secondary_y": True}])  # MACD需要双轴
            else:
                specs.append([{"secondary_y": False}])

        # 创建垂直堆叠的技术指标图表
        fig = make_subplots(
            rows=rows,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.04,  # 增加垂直间距，给更多空间避免遮挡
            row_heights=row_heights,
            subplot_titles=subplot_titles,
            specs=specs
        )

        # 中国股市红涨绿跌颜色方案
        colors_up = '#FF4444'  # 红色上涨（收盘>开盘）
        colors_down = '#00C853'  # 绿色下跌（收盘<开盘）

        # 1. K线图 + BBI (第1行) - 中国股市红涨绿跌
        fig.add_trace(
            go.Candlestick(
                x=df.index,
                open=df['开盘'],
                high=df['最高'],
                low=df['最低'],
                close=df['收盘'],
                name='K线',
                # 中国股市红涨绿跌：
                # increasing: 收盘价 > 开盘价（上涨）-> 红色
                # decreasing: 收盘价 < 开盘价（下跌）-> 绿色
                increasing=dict(
                    line=dict(color=colors_up, width=1),
                    fillcolor=colors_up
                ),
                decreasing=dict(
                    line=dict(color=colors_down, width=1),
                    fillcolor=colors_down
                )
            ),
            row=1, col=1
        )

        # BBI线
        if 'BBI' in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=df['BBI'],
                    name='BBI',
                    line=dict(color='#FFD700', width=2.5)
                ),
                row=1, col=1
            )

        # 动态添加选中的技术指标
        current_row = 2
        for indicator in selected_indicators:
            if indicator == '成交量' and '成交量' in df.columns:
                # 成交量指标
                volume_colors = [colors_up if close >= open else colors_down
                               for close, open in zip(df['收盘'], df['开盘'])]

                fig.add_trace(
                    go.Bar(
                        x=df.index,
                        y=df['成交量'],
                        name='成交量',
                        marker_color=volume_colors,
                        opacity=0.8
                    ),
                    row=current_row, col=1
                )

            elif indicator == 'WEEKLY_KDJ_J' and 'WEEKLY_KDJ_J' in df.columns:
                # 周线KDJ指标
                fig.add_trace(
                    go.Scatter(
                        x=df.index,
                        y=df['WEEKLY_KDJ_J'],
                        name='WEEKLY_KDJ_J',
                        line=dict(color='#9C27B0', width=2)
                    ),
                    row=current_row, col=1
                )
                # 添加参考线
                fig.add_hline(y=80, line_dash="dash", line_color="red", opacity=0.7, row=current_row, col=1)
                fig.add_hline(y=20, line_dash="dash", line_color="green", opacity=0.7, row=current_row, col=1)

            elif indicator == 'DAILY_KDJ_J' and 'DAILY_KDJ_J' in df.columns:
                # 日线KDJ指标
                fig.add_trace(
                    go.Scatter(
                        x=df.index,
                        y=df['DAILY_KDJ_J'],
                        name='DAILY_KDJ_J',
                        line=dict(color='#FF9800', width=2)
                    ),
                    row=current_row, col=1
                )
                # 添加参考线
                fig.add_hline(y=80, line_dash="dash", line_color="red", opacity=0.7, row=current_row, col=1)
                fig.add_hline(y=20, line_dash="dash", line_color="green", opacity=0.7, row=current_row, col=1)

            elif indicator == 'RSI' and 'RSI' in df.columns:
                # RSI指标
                fig.add_trace(
                    go.Scatter(
                        x=df.index,
                        y=df['RSI'],
                        name='RSI',
                        line=dict(color='#00BCD4', width=2)
                    ),
                    row=current_row, col=1
                )
                # 添加参考线
                fig.add_hline(y=70, line_dash="dash", line_color="red", opacity=0.7, row=current_row, col=1)
                fig.add_hline(y=30, line_dash="dash", line_color="green", opacity=0.7, row=current_row, col=1)

            elif indicator == 'MACD' and all(col in df.columns for col in ['MACD_DIF', 'MACD_DEA', 'MACD_HIST']):
                # MACD指标 - 真正双轴结构
                # MACD HIST柱状图 - 左轴，中国股市红涨绿跌
                hist_colors = []
                for hist_val in df['MACD_HIST']:
                    if hist_val >= 0:
                        hist_colors.append('#FF0040')  # 鲜艳红色 (上涨/正值)
                    else:
                        hist_colors.append('#00FF41')  # 鲜艳绿色 (下跌/负值)

                fig.add_trace(
                    go.Bar(
                        x=df.index,
                        y=df['MACD_HIST'],
                        name='HIST',
                        marker_color=hist_colors,
                        opacity=0.8
                    ),
                    row=current_row, col=1,
                    secondary_y=False  # 使用左轴
                )

                # MACD DIF线 - 右轴
                fig.add_trace(
                    go.Scatter(
                        x=df.index,
                        y=df['MACD_DIF'],
                        name='DIF',
                        line=dict(color='#FFD700', width=2)
                    ),
                    row=current_row, col=1,
                    secondary_y=True  # 使用右轴
                )

                # MACD DEA线 - 右轴
                fig.add_trace(
                    go.Scatter(
                        x=df.index,
                        y=df['MACD_DEA'],
                        name='DEA',
                        line=dict(color='#FF6B6B', width=2)
                    ),
                    row=current_row, col=1,
                    secondary_y=True  # 使用右轴
                )

                # 设置MACD双轴标题
                fig.update_yaxes(title_text="HIST", row=current_row, col=1, secondary_y=False)
                fig.update_yaxes(title_text="DIF/DEA", row=current_row, col=1, secondary_y=True)

            current_row += 1

        # 更新布局
        fig.update_layout(
            height=250 + rows * 150,  # 增加基础高度和每行高度，适应5:2.5:2.5的比例
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            template="plotly_dark",
            # 增加边距，确保底部有足够空间
            margin=dict(l=50, r=50, t=50, b=80),  # 增加底部边距
            # 禁用底部的range selector和slider，避免遮挡其他图表
            xaxis_rangeslider_visible=False,  # 隐藏range slider
            xaxis=dict(
                rangeslider=dict(visible=False),  # 确保slider完全隐藏
                showgrid=True,
                gridwidth=1
            )
        )

        # 只在最下方显示x轴标签，并确保所有子图的x轴设置正确
        for i in range(1, rows + 1):
            if i == rows:
                # 最下方的子图显示x轴标签
                fig.update_xaxes(
                    showticklabels=True,
                    showgrid=True,
                    row=i,
                    col=1,
                    rangeslider=dict(visible=False)  # 确保每个子图都没有range slider
                )
            else:
                # 其他子图隐藏x轴标签
                fig.update_xaxes(
                    showticklabels=False,
                    showgrid=True,
                    row=i,
                    col=1,
                    rangeslider=dict(visible=False)  # 确保每个子图都没有range slider
                )

            # 隐藏所有子图的x轴标题
            fig.update_xaxes(title_text="", row=i, col=1)

        # 显示图表
        st.plotly_chart(fig, use_container_width=True)

    def _filter_data_by_time(self, df: pd.DataFrame, time_range: str) -> pd.DataFrame:
        """根据时间范围过滤数据
        数据已排序为正序（最旧在前，最新在后），tail取最新的N条数据
        """
        if time_range == "全部":
            return df

        days_map = {
            "1个月": 30,
            "3个月": 90,
            "6个月": 180,
            "1年": 365
        }

        days = days_map.get(time_range, 180)  # 默认6个月
        # 数据已排序为正序，tail取最新的N条数据
        return df.tail(days)

    def _show_ai_report(self, data: Dict[str, Any]):
        """显示AI分析报告 - 使用两个tab分别显示intraday_trading和technical_analysis"""
        ui_template_manager.section_header("🤖 AI分析报告")

        try:
            # 导入AI报告管理器
            from src.web.utils import ai_report_manager

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

    def _show_strategy_comparison(self, stock_code: str):
        """显示策略对比分析"""
        try:
            from .strategy_comparison_charts import StrategyComparisonCharts

            # 创建策略对比图表组件
            charts_component = StrategyComparisonCharts()

            # 检查是否存在策略对比数据
            comparison_file = Path(f"data/cleaned_stocks/{stock_code}/backtest_results/strategy_comparison.csv")

            if not comparison_file.exists():
                # 如果没有策略对比数据，显示提示信息
                ui_template_manager.section_header("📊 策略对比分析")
                st.info(f"⚠️ **{stock_code}** 暂无策略对比数据")

                # 提供运行策略对比的指引
                with st.expander("🔧 如何生成策略对比数据"):
                    st.markdown("""
                    ### 运行策略对比分析

                    请在命令行中执行以下命令来生成策略对比数据：

                    ```bash
                    # 切换到项目目录
                    cd /Users/alexwood/Desktop/python/网页App/股票网站/a股

                    # 运行策略对比（替换 STOCK_CODE 为目标股票代码）
                    python src/backtesting/launchers/strategy_comparison.py STOCK_CODE

                    # 示例：
                    python src/backtesting/launchers/strategy_comparison.py 603026
                    ```

                    ### 策略对比数据包含：
                    - 📈 **收益率分析**: 总收益率、年化收益率
                    - ⚡ **风险指标**: 夏普比率、最大回撤、波动率
                    - 🎯 **交易统计**: 交易次数、胜率、盈亏比
                    - 🔧 **参数优化**: 自动优化的最佳策略参数
                    """)

                return

            # 渲染策略对比图表
            charts_component.render(stock_code)

        except ImportError:
            # 如果无法导入策略对比组件，显示简化版本
            ui_template_manager.section_header("📊 策略对比分析")
            st.warning("⚠️ 策略对比可视化组件加载失败，显示简化版本")

            # 检查并显示基础数据
            comparison_file = Path(f"data/cleaned_stocks/{stock_code}/backtest_results/strategy_comparison.csv")
            if comparison_file.exists():
                try:
                    df = pd.read_csv(comparison_file, encoding='utf-8')
                    st.dataframe(df, use_container_width=True)
                except Exception as e:
                    st.error(f"读取策略对比数据失败: {e}")
            else:
                st.info(f"{stock_code} 暂无策略对比数据")

        except Exception as e:
            st.error(f"策略对比分析加载失败: {str(e)}")
            st.info("请检查策略对比数据文件是否存在")


# 创建全局组件实例
technical_analysis_component = TechnicalAnalysisComponent()