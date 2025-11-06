#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
UI模板系统
整合核心模板和图表功能，避免重复
"""

from typing import Dict, List, Any, Optional
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dataclasses import dataclass
import sys
import re
from pathlib import Path

# 添加项目根目录
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))




def convert_money(money_str: str) -> float:
    """转换金额字符串为数字"""
    if not money_str or money_str in [None, '', 'N/A']:
        return 0.0

    try:
        # 移除非数字字符（除了负号和小数点）
        clean_str = re.sub(r'[^\d.-]', '', str(money_str))

        if clean_str in ['', '-', '.']:
            return 0.0

        # 处理单位
        if '亿' in str(money_str):
            return float(clean_str) * 100000000
        elif '万' in str(money_str):
            return float(clean_str) * 10000
        elif '千' in str(money_str):
            return float(clean_str) * 1000
        else:
            return float(clean_str)
    except:
        return 0.0


@dataclass
class ThemeConfig:
    """主题配置"""
    # 颜色配置
    primary: str = "#FFD700"
    secondary: str = "#1E90FF"
    success: str = "#00ff88"
    danger: str = "#ff4444"
    warning: str = "#FFA500"
    info: str = "#17a2b8"

    # 背景色
    background: str = "#000000"
    surface: str = "rgba(30,30,40,0.8)"

    # 文本色
    text_primary: str = "#FFFFFF"
    text_secondary: str = "#E0E0E0"
    text_muted: str = "#B0B0B0"

    # 图表色（红升绿跌）
    chart_up: str = "#ff4444"
    chart_down: str = "#00ff88"
    chart_neutral: str = "#FFD700"

    # 边框和网格
    border: str = "rgba(255, 215, 0, 0.3)"
    grid: str = "rgba(255,255,255,0.1)"


class UITemplateManager:
    """UI模板管理器 - 整合所有UI功能"""

    def __init__(self):
        self.theme = ThemeConfig()
        self.color_sequence = [
            "#FFD700", "#1E90FF", "#00ff88", "#ff4444", "#FFA500",
            "#17a2b8", "#9C27B0", "#4CAF50", "#FF9800", "#795548"
        ]

        # 向后兼容的colors属性
        self.colors = {
            'primary': self.theme.primary,
            'secondary': self.theme.secondary,
            'success': self.theme.success,
            'danger': self.theme.danger,
            'warning': self.theme.warning,
            'info': self.theme.info,
            'background': self.theme.background,
            'surface': self.theme.surface,
            'text_primary': self.theme.text_primary,
            'text_secondary': self.theme.text_secondary,
            'text_muted': self.theme.text_muted,
            'chart_up': self.theme.chart_up,
            'chart_down': self.theme.chart_down,
            'chart_neutral': self.theme.chart_neutral
        }

        # 财务指标映射 - 定义每个指标的分子和分母（基于清洗后的数据结构）
        self.financial_metrics_mapping = {
            "净资产收益率": {
                "numerator": "五、净利润",
                "denominator": "归属于母公司所有者权益合计",
                "unit": "%",
                "description": "净利润 / 平均所有者权益 × 100%"
            },
            "销售净利率": {
                "numerator": "五、净利润",
                "denominator": "一、营业总收入",
                "unit": "%",
                "description": "净利润 / 营业总收入 × 100%"
            },
            "销售毛利率": {
                "numerator": "毛利",
                "denominator": "一、营业总收入",
                "unit": "%",
                "description": "(营业总收入 - 营业成本) / 营业总收入 × 100%"
            },
            "资产负债率": {
                "numerator": "负债合计",
                "denominator": "资产合计",
                "unit": "%",
                "description": "负债合计 / 资产合计 × 100%"
            },
            "流动比率": {
                "numerator": "流动资产合计",
                "denominator": "流动负债合计",
                "unit": "倍",
                "description": "流动资产合计 / 流动负债合计"
            },
            "速动比率": {
                "numerator": "速动资产",
                "denominator": "流动负债合计",
                "unit": "倍",
                "description": "速动资产 / 流动负债合计"
            },
            "净利润同比增长率": {
                "numerator": "净利润",
                "denominator": None,
                "unit": "%",
                "description": "净利润同比增长率"
            },
            "扣非净利润同比增长率": {
                "numerator": "扣非净利润",
                "denominator": None,
                "unit": "%",
                "description": "扣非净利润同比增长率"
            },
            "营业总收入同比增长率": {
                "numerator": "营业总收入",
                "denominator": None,
                "unit": "%",
                "description": "营业总收入同比增长率"
            },
            "存货周转率": {
                "numerator": "存货周转率",
                "denominator": "存货周转天数",
                "unit": "次/天",
                "description": "存货周转率 vs 周转天数"
            },
            "应收账款周转天数": {
                "numerator": "应收账款周转天数",
                "denominator": "营业周期",
                "unit": "天",
                "description": "应收账款周转天数 vs 营业周期"
            }
        }

    def apply_theme_css(self):
        """应用主题CSS样式"""
        css = f"""
        <style>
        /* 全局样式 - 纯黑主题 */
        .stApp {{
            background: {self.theme.background};
            color: {self.theme.text_primary};
        }}

        .main .block-container {{
            background: {self.theme.background};
            max-width: 1400px;
        }}

        /* 卡片样式 */
        .modern-card {{
            background: {self.theme.surface};
            border: 1px solid {self.theme.border};
            border-radius: 12px;
            padding: 1.5rem;
            margin: 1rem 0;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        }}

        /* 指标卡片 */
        .metric-card {{
            background: {self.theme.surface};
            border: 1px solid {self.theme.border};
            border-radius: 12px;
            padding: 1.5rem;
            text-align: center;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        }}

        /* 标签页样式 */
        .stTabs [data-baseweb="tab-list"] {{
            background: {self.theme.surface};
            border-radius: 8px;
            padding: 0.5rem;
        }}

        .stTabs [data-baseweb="tab"] {{
            background: transparent;
            color: {self.theme.text_secondary};
            border-radius: 6px;
        }}

        .stTabs [data-baseweb="tab"][aria-selected="true"] {{
            background: {self.theme.primary};
            color: white;
        }}

        /* 标题样式 */
        .gradient-title {{
            background: linear-gradient(90deg, {self.theme.primary} 0%, {self.theme.text_primary} 50%, {self.theme.primary} 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-size: 2.5rem;
            font-weight: 800;
            text-align: center;
        }}
        </style>
        """
        st.markdown(css, unsafe_allow_html=True)

    
    def section_header(self, title: str, level: int = 2):
        """创建章节标题"""
        if level == 1:
            st.markdown(f"""
            <h1 style="color: {self.theme.text_primary}; font-size: 28px; font-weight: 700;
                      margin: 2rem 0 1rem 0; border-bottom: 2px solid {self.theme.primary};">
                {title}
            </h1>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <h2 style="color: {self.theme.text_primary}; font-size: 22px; font-weight: 600;
                      margin: 1.5rem 0 1rem 0; border-left: 4px solid {self.theme.primary}; padding-left: 1rem;">
                {title}
            </h2>
            """, unsafe_allow_html=True)

    def candlestick(self, df: pd.DataFrame, title: str = "K线图",
                               show_volume: bool = True, ma_periods: List[int] = [5, 10, 20]) -> go.Figure:
        """创建K线图"""
        if df.empty:
            return go.Figure()

        rows = 2 if show_volume and '成交量' in df.columns else 1
        fig = make_subplots(
            rows=rows, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            subplot_titles=["价格走势", "成交量"] if show_volume else ["价格走势"]
        )

        # K线图
        fig.add_trace(go.Candlestick(
            x=df.index,
            open=df['开盘'],
            high=df['最高'],
            low=df['最低'],
            close=df['收盘'],
            name="K线",
            increasing_line_color=self.theme.chart_up,
            decreasing_line_color=self.theme.chart_down
        ), row=1, col=1)

        # 移动平均线
        df_ma = df.copy()  # 创建副本避免SettingWithCopyWarning
        for i, period in enumerate(ma_periods):
            if len(df_ma) >= period:
                ma_col = f'MA{period}'
                df_ma[ma_col] = df_ma['收盘'].rolling(window=period).mean()
                fig.add_trace(go.Scatter(
                    x=df_ma.index, y=df_ma[ma_col], mode='lines',
                    name=ma_col, line=dict(color=self.color_sequence[i], width=2)
                ), row=1, col=1)

        # 成交量
        if show_volume and '成交量' in df.columns:
            colors = [self.theme.chart_up if close >= open else self.theme.chart_down
                     for close, open in zip(df['收盘'], df['开盘'])]
            fig.add_trace(go.Bar(
                x=df.index, y=df['成交量'],
                name="成交量", marker_color=colors, opacity=0.7
            ), row=2, col=1)

        fig.update_layout(
            title=title,
            xaxis_rangeslider_visible=False,
            template="plotly_dark",
            height=600 if show_volume else 400,
            paper_bgcolor=self.theme.background,
            plot_bgcolor=self.theme.background,
            font=dict(color=self.theme.text_primary)
        )

        return fig

    def line(self, df: pd.DataFrame, title: str = "折线图",
                  y_column: str = None, x_col: str = None, y_cols: List[str] = None,
                  x_title: str = None, y_title: str = None, x_mode: str = None) -> go.Figure:
        """创建折线图 - 简化版本，支持x_mode参数"""
        if df.empty:
            return go.Figure()

        # 确定x轴数据
        if x_col and x_col in df.columns:
            x_data = df[x_col]
            chart_df = df.copy()
        else:
            x_data = df.index
            chart_df = df.copy()

        # 确定要绘制的列
        if y_cols:
            columns_to_plot = y_cols
        elif y_column:
            columns_to_plot = [y_column]
        else:
            # 使用第一个数值列
            numeric_cols = chart_df.select_dtypes(include=['number']).columns
            columns_to_plot = [numeric_cols[0]] if len(numeric_cols) > 0 else []

        if not columns_to_plot:
            return go.Figure()

        # 创建图表
        fig = go.Figure()

        # 添加线条
        for i, col in enumerate(columns_to_plot):
            if col in chart_df.columns:
                fig.add_trace(go.Scatter(
                    x=x_data,
                    y=chart_df[col],
                    mode='lines',
                    name=col,
                    line=dict(color=self.get_chart_color(i), width=2)
                ))

        # 应用基本样式
        fig.update_layout(
            title=title,
            template="plotly_dark",
            paper_bgcolor=self.theme.background,
            plot_bgcolor=self.theme.background,
            font=dict(color=self.theme.text_primary),
            height=450,  # 增加50像素高度
            xaxis_title=f"<b>{x_title or '时间'}</b>",
            yaxis_title=f"<b>{y_title or '数值'}</b>",
            xaxis=dict(
                title_font=dict(size=12),
                tickfont=dict(size=10)
            ),
            yaxis=dict(
                title_font=dict(size=12),
                tickfont=dict(size=10),
                tickformat=",",
                separatethousands=True
            )
        )

        # 处理x_mode
        if x_mode == 'category':
            fig.update_xaxes(type='category')
        elif x_mode == 'date':
            fig.update_xaxes(type='date')
            fig.update_xaxes(tickformat='%Y-%m-%d')

        return fig

    
    def pie(self, data: Dict[str, float], title: str = "",
                         max_items: int = 6, height: int = 400) -> go.Figure:
        """创建饼图"""
        if not data:
            return go.Figure()

        # 过滤正数并排序
        filtered_data = {k: v for k, v in data.items() if isinstance(v, (int, float)) and v > 0}
        sorted_items = sorted(filtered_data.items(), key=lambda x: x[1], reverse=True)
        top_items = dict(sorted_items[:max_items])

        # 计算其他
        other_total = sum(v for v in dict(sorted_items[max_items:]).values())
        if other_total > 0:
            top_items["其他"] = other_total

        fig = go.Figure(data=[go.Pie(
            labels=list(top_items.keys()),
            values=list(top_items.values()),
            marker_colors=self.color_sequence[:len(top_items)],
            textinfo='label+percent',
            textfont_size=12
        )])

        # 应用统一布局
        self.apply_unified_layout(fig, title, height=height, show_legend=False)

        return fig

    def bar(self, df: pd.DataFrame, title: str = "柱状图",
                        x_column: str = None, y_column: str = None,
                        height: int = 400) -> go.Figure:
        """创建柱状图"""
        if df.empty:
            return go.Figure()

        if x_column is None:
            x_column = df.columns[0]
        if y_column is None:
            y_column = df.columns[1] if len(df.columns) > 1 else df.columns[0]

        # 检查是否需要格式化日期数据
        x_data = self.format_axis_data(df[x_column])

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=x_data,
            y=df[y_column],
            marker_color=self.theme.primary,
            name=y_column
        ))

        # 应用统一布局
        self.apply_unified_layout(fig, title, height=height, show_legend=False)

        return fig

  
  
    def get_chart_color(self, index: int) -> str:
        """获取图表颜色"""
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57', '#FF9FF3', '#54A0FF', '#48DBFB']
        return colors[index % len(colors)]

    
    
    def financial_pie(self, data: Dict[str, float], title: str = "", height: int = 400, top_n: int = 5, show_legend: bool = True) -> Optional[Any]:
        """创建财务饼图 - 只显示前N大项，其余合并为'其他'"""
        try:
            import plotly.graph_objects as go

            if not data or all(v == 0 for v in data.values()):
                return None

            # 处理数据（排序和合并）
            pie_data = self._prepare_pie_data(data, top_n)

            if not pie_data:
                return None

            # 创建图表
            fig = go.Figure(data=[go.Pie(
                labels=list(pie_data.keys()),
                values=list(pie_data.values()),
                hole=0.3,
                marker_colors=[self.get_chart_color(i) for i in range(len(pie_data))],
                textinfo='label+percent',
                textposition='outside'
            )])

            # 应用样式
            fig.update_layout(
                title=title,
                height=height,
                template="plotly_dark",
                paper_bgcolor=self.theme.background,
                plot_bgcolor=self.theme.background,
                font=dict(color=self.theme.text_primary),
                showlegend=show_legend,
                margin=dict(l=20, r=20, t=40, b=20)
            )

            return fig
        except Exception as e:
            print(f"创建财务饼图失败: {e}")
            return None

    def _prepare_pie_data(self, data: Dict[str, float], top_n: int) -> Dict[str, float]:
        """准备饼图数据：排序、合并小项"""
        # 按值排序并分离前N大项
        sorted_items = sorted(data.items(), key=lambda x: x[1], reverse=True)
        top_items = sorted_items[:top_n]
        other_items = sorted_items[top_n:]

        # 合并其余项为'其他'
        pie_data = dict(top_items)
        if other_items:
            other_total = sum(item[1] for item in other_items if item[1] > 0)
            if other_total > 0:
                pie_data['其他'] = other_total

        # 过滤零值
        return {k: v for k, v in pie_data.items() if v > 0}

  
    def cost_pie(self, data: Dict[str, float], title: str = "", height: int = 400) -> Optional[Any]:
        """创建成本构成饼图 - 用于分析各成本占比"""
        try:
            import plotly.graph_objects as go

            # 构建成本数据，包含更多成本项目以进行详细分析
            cost_data = {
                "营业成本": data.get("营业成本", 0),
                "销售费用": data.get("销售费用", 0),
                "管理费用": data.get("管理费用", 0),
                "财务费用": data.get("财务费用", 0),
                "研发费用": data.get("研发费用", 0),
                "税金及附加": data.get("税金及附加", 0),
                "其他经营收益": data.get("其他经营收益", 0)
            }

            # 过滤掉为0的项目
            cost_data = {k: v for k, v in cost_data.items() if v > 0}

            if not cost_data:
                return None

            # 使用与资产结构相同的财务饼图逻辑
            # 处理数据（排序和合并），显示前5大项，其余合并为'其他'
            pie_data = self._prepare_pie_data(cost_data, top_n=5)

            if not pie_data:
                return None

            # 创建图表
            fig = go.Figure(data=[go.Pie(
                labels=list(pie_data.keys()),
                values=list(pie_data.values()),
                hole=0.3,
                marker_colors=[self.get_chart_color(i) for i in range(len(pie_data))],
                textinfo='label+percent',
                textposition='outside'
            )])

            # 应用样式
            fig.update_layout(
                title=title,
                height=height,
                template="plotly_dark",
                paper_bgcolor=self.theme.background,
                plot_bgcolor=self.theme.background,
                font=dict(color=self.theme.text_primary),
                showlegend=True,
                margin=dict(l=20, r=20, t=40, b=20)
            )

            return fig
        except Exception as e:
            print(f"创建成本构成饼图失败: {e}")
            return None

    def revenue_cost_waterfall(self, data: Dict[str, float], title: str = "", height: int = 400) -> Optional[Any]:
        """创建收入成本结构瀑布图 - 统一版本"""
        try:
            # 直接获取核心数据字段（基于清洗后的真实数据结构）
            revenue = self._get_numeric_value(data, ["一、营业总收入", "其中：营业收入"])
            operating_cost = self._get_numeric_value(data, ["其中：营业成本", "营业成本"])
            sales_expense = self._get_numeric_value(data, ["销售费用"])
            admin_expense = self._get_numeric_value(data, ["管理费用"])
            rd_expense = self._get_numeric_value(data, ["研发费用"])
            finance_expense = self._get_numeric_value(data, ["财务费用"])
            tax_surcharges = self._get_numeric_value(data, ["营业税金及附加"])
            net_profit = self._get_numeric_value(data, ["五、净利润"])

            # 简单数据验证
            if revenue <= 0:
                return None

            # 构建瀑布图数据
            waterfall_data = {
                "营业总收入": revenue,
                "营业成本": -operating_cost,
                "税金及附加": -tax_surcharges,
                "销售费用": -sales_expense,
                "管理费用": -admin_expense,
                "研发费用": -rd_expense,
                "财务费用": -finance_expense,
                "净利润": net_profit
            }

            # 过滤掉零值
            waterfall_data = {k: v for k, v in waterfall_data.items() if v != 0}

            # 使用统一瀑布图函数
            fig = self._create_unified_waterfall(waterfall_data, title or "收入成本结构", "收入成本分析")

            # 设置高度
            fig.update_layout(height=height + 50)  # 增加50像素高度

            return fig

        except Exception as e:
            print(f"创建收入成本瀑布图失败: {e}")
            return None

    def _get_numeric_value(self, data: Dict[str, Any], key_list: List[str]) -> float:
        """获取数值，支持字符串转换"""
        for key in key_list:
            if key in data:
                value = data[key]
                if value is None or value == "":
                    continue
                try:
                    if isinstance(value, str):
                        return convert_money(value.replace(',', '').replace(' ', ''))
                    return float(value)
                except (ValueError, TypeError):
                    continue
        return 0

    def convert_money_to_number(self, money_str: str) -> float:
        """转换金额字符串为数字 - 兼容函数"""
        if not money_str or money_str in [None, '', 'N/A']:
            return 0.0
        try:
            return convert_money(str(money_str).replace(',', '').replace(' ', ''))
        except:
            return 0.0

    def get_appropriate_unit(self, values: List[float]) -> str:
        """根据数值大小获取合适的单位"""
        if not values:
            return ""

        max_value = max(abs(v) for v in values if v is not None)

        if max_value >= 1e8:  # 1亿
            return "亿"
        elif max_value >= 1e4:  # 1万
            return "万"
        else:
            return ""

    def get_unit_factor_and_suffix(self, unit: str) -> tuple[float, str]:
        """获取单位的转换因子和后缀名称"""
        if unit == "亿":
            return 1e8, "亿元"
        elif unit == "万":
            return 1e4, "万元"
        else:
            return 1, "元"

    def create_dual_axis_chart(self) -> go.Figure:
        """创建标准的双子图模板"""
        return make_subplots(specs=[[{"secondary_y": True}]])

    def display_comparison_table(self, df: pd.DataFrame, stock_code: str, analysis_type: str, metric_name: str):
        """显示对比表格 - 简化版本"""
        try:
            if df.empty:
                st.info(f"暂无{metric_name}对比数据")
                return

            # 确保目标股票在数据中
            if stock_code not in df.index and stock_code not in df.get('股票代码', []):
                # 静默处理，不显示错误信息
                return

            st.markdown(f"##### 📊 {metric_name} 对比分析")

            # 格式化显示
            display_df = df.copy()

            # 如果有数值列，进行格式化
            numeric_cols = display_df.select_dtypes(include=['number']).columns
            for col in numeric_cols:
                if display_df[col].dtype in ['float64', 'int64']:
                    display_df[col] = display_df[col].round(2)

            # 高亮目标股票
            def highlight_target_stock(row):
                if stock_code in row.values:
                    return ['background-color: rgba(255, 215, 0, 0.2)'] * len(row)
                return [''] * len(row)

            styled_df = display_df.style.apply(highlight_target_stock, axis=1)
            st.dataframe(styled_df, use_container_width=True)

        except Exception as e:
            print(f"显示对比表格失败: {e}")
            st.error(f"对比表格显示失败: {e}")

    def grouped_bar_years(self, data: pd.DataFrame, color_map: Dict[str, str], title: str = "") -> Optional[Any]:
        """创建按年份分组的柱状图 - 简化版本"""
        try:
            if data.empty:
                return None

            # 简单数据处理
            chart_data = data.copy()
            if '年份' in chart_data.columns:
                chart_data['年份'] = chart_data['年份'].astype(int)
                chart_data = chart_data.sort_values('年份')
                x_data = chart_data['年份']
            else:
                x_data = chart_data.index

            # 收集所有数值用于确定单位
            all_values = []
            for column in color_map.keys():
                if column in chart_data.columns and column != '年份':
                    all_values.extend(chart_data[column].dropna().tolist())

            # 获取合适的单位和转换因子
            unit = self.get_appropriate_unit(all_values)
            factor, unit_suffix = self.get_unit_factor_and_suffix(unit)

            # 创建图表
            fig = go.Figure()

            # 添加柱状图
            for column, display_name in color_map.items():
                if column in chart_data.columns and column != '年份':
                    # 转换数值并格式化hover文本
                    converted_values = [v / factor if v is not None else None for v in chart_data[column]]
                    hover_text = [f"{v:,.2f}{unit_suffix}" if v is not None else "无数据" for v in converted_values]

                    fig.add_trace(go.Bar(
                        x=x_data,
                        y=converted_values,
                        name=display_name,
                        marker_color=self.get_chart_color(len(fig.data)),
                        hovertemplate="<b>%{fullData.name}</b><br>" +
                                     "年份: %{x}<br>" +
                                     "金额: %{text}<extra></extra>",
                        text=hover_text,
                        textposition='outside'
                    ))

            # 应用样式
            fig.update_layout(
                title=title,
                xaxis_title="<b>年份</b>",
                yaxis_title=f"<b>金额</b><br>({unit_suffix})",
                template="plotly_dark",
                paper_bgcolor=self.theme.background,
                plot_bgcolor=self.theme.background,
                font=dict(color=self.theme.text_primary),
                showlegend=True,
                barmode='group',
                height=450,  # 增加50像素高度
                xaxis=dict(
                    title_font=dict(size=12),
                    tickfont=dict(size=10)
                ),
                yaxis=dict(
                    title_font=dict(size=12),
                    tickfont=dict(size=10),
                    tickformat=",",
                    separatethousands=True
                )
            )

            return fig
        except Exception as e:
            print(f"创建分组柱状图失败: {e}")
            return None

    def percent_stacked_bar(self, df: pd.DataFrame, title: str = "", x_column: str = None,
                           color_map: Dict[str, str] = None) -> Optional[Any]:
        """创建百分比堆叠柱状图"""
        try:
            import plotly.graph_objects as go

            if df.empty:
                return None

            chart_df = df.copy()

            # 确定x轴列
            if x_column and x_column in chart_df.columns:
                x_data = chart_df[x_column]
                chart_df = chart_df.drop(columns=[x_column])
            else:
                x_data = chart_df.index
                chart_df = chart_df.reset_index(drop=True)

            # 默认颜色映射
            if color_map is None:
                color_map = {
                    chart_df.columns[0]: "流动资产",
                    chart_df.columns[1]: "非流动资产" if len(chart_df.columns) > 1 else "其他"
                }

            fig = go.Figure()

            # 添加堆叠柱状图
            for i, column in enumerate(chart_df.columns):
                if column in color_map:
                    fig.add_trace(go.Bar(
                        x=x_data,
                        y=chart_df[column],
                        name=color_map[column],
                        marker_color=self.get_chart_color(i)
                    ))

            # 设置为百分比堆叠
            fig.update_layout(
                barmode='stack',
                barnorm='percent',  # 设置为百分比堆叠
                title=title,
                xaxis_title=x_column if x_column else "时间",
                yaxis_title="占比(%)",
                yaxis=dict(ticksuffix="%", range=[0, 100]),
                template="plotly_dark",
                paper_bgcolor=self.theme.background,
                plot_bgcolor=self.theme.background,
                font=dict(color=self.theme.text_primary),
                height=450  # 增加50像素高度
            )

            return fig
        except Exception as e:
            print(f"创建百分比堆叠图失败: {e}")
            return None

    def create_financial_trend_chart(self, df: pd.DataFrame, metrics: List[str],
                                  title: str = "财务指标趋势", stock_code: str = "") -> go.Figure:
        """创建财务指标趋势图 - 专门处理财务数据的排序和显示问题"""
        if df.empty or not metrics:
            return go.Figure()

        try:
            # 数据预处理和排序
            chart_df = df.copy()

            # 确保时间正确排序
            if hasattr(chart_df.index, 'to_datetime'):
                # DatetimeIndex情况
                chart_df = chart_df.sort_index()
                x_data = chart_df.index
            elif '日期' in chart_df.columns:
                # 日期列情况
                chart_df['日期'] = pd.to_datetime(chart_df['日期'], errors='coerce')
                chart_df = chart_df.dropna(subset=['日期']).sort_values('日期')
                x_data = chart_df['日期']
            else:
                # 其他情况，使用默认索引
                x_data = chart_df.index

            # 创建图表
            fig = go.Figure()

            # 添加指标线条
            for i, metric in enumerate(metrics):
                if metric in chart_df.columns and not chart_df[metric].empty:
                    fig.add_trace(go.Scatter(
                        x=x_data,
                        y=chart_df[metric],
                        mode='lines+markers',  # 添加标记点
                        name=metric,
                        line=dict(color=self.get_chart_color(i), width=2),
                        marker=dict(size=4)
                    ))

            # 应用统一的暗色主题样式
            fig.update_layout(
                title=title,
                template="plotly_dark",
                paper_bgcolor=self.theme.background,
                plot_bgcolor=self.theme.background,
                font=dict(color=self.theme.text_primary),
                height=450,  # 增加50像素高度
                hovermode='x unified',
                margin=dict(l=50, r=50, t=80, b=50),
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )

            # 设置坐标轴
            fig.update_xaxes(
                title_text="时间",
                showgrid=True,
                gridcolor='rgba(128,128,128,0.2)',
                tickangle=-45
            )

            fig.update_yaxes(
                title_text="数值",
                showgrid=True,
                gridcolor='rgba(128,128,128,0.2)'
            )

            # 特殊处理半年标签（如果有日期数据）
            if hasattr(x_data, 'to_datetime'):
                self._apply_datetime_labeling(fig, x_data)

            return fig

        except Exception as e:
            print(f"创建财务趋势图失败: {e}")
            return go.Figure()

    def bid_ask_depth(self, bid_ask_dict: Dict[str, Any], title: str = "") -> Optional[Any]:
        """创建盘口深度图 - 基于实际bid_ask数据结构"""
        try:
            import plotly.graph_objects as go

            if not bid_ask_dict:
                return None

            fig = go.Figure()

            # 提取买单数据 (buy_1到buy_5)
            buy_prices = []
            buy_volumes = []
            for i in range(1, 6):
                price_key = f'buy_{i}'
                vol_key = f'buy_{i}_vol'

                if price_key in bid_ask_dict and vol_key in bid_ask_dict:
                    try:
                        price = float(bid_ask_dict[price_key])
                        volume = float(bid_ask_dict[vol_key])
                        buy_prices.append(price)
                        buy_volumes.append(volume)
                    except (ValueError, TypeError):
                        continue

            # 提取卖单数据 (sell_1到sell_5)
            sell_prices = []
            sell_volumes = []
            for i in range(1, 6):
                price_key = f'sell_{i}'
                vol_key = f'sell_{i}_vol'

                if price_key in bid_ask_dict and vol_key in bid_ask_dict:
                    try:
                        price = float(bid_ask_dict[price_key])
                        volume = float(bid_ask_dict[vol_key])
                        sell_prices.append(price)
                        sell_volumes.append(volume)
                    except (ValueError, TypeError):
                        continue

            # 添加买单柱状图（红色）
            if buy_prices and buy_volumes:
                fig.add_trace(go.Bar(
                    x=buy_prices,
                    y=buy_volumes,
                    name='买单',
                    marker_color='#ff6b6b',
                    opacity=0.8
                ))

            # 添加卖单柱状图（绿色）
            if sell_prices and sell_volumes:
                fig.add_trace(go.Bar(
                    x=sell_prices,
                    y=sell_volumes,
                    name='卖单',
                    marker_color='#00ff88',
                    opacity=0.8
                ))

            # 设置布局
            fig.update_layout(
                title=title,
                xaxis_title="价格",
                yaxis_title="数量",
                template="plotly_dark",
                paper_bgcolor=self.theme.background,
                plot_bgcolor=self.theme.background,
                font=dict(color=self.theme.text_primary),
                showlegend=True,
                barmode='group',
                height=450  # 增加50像素高度
            )

            return fig
        except Exception as e:
            print(f"创建盘口深度图失败: {e}")
            return None

    def area(self, df: pd.DataFrame, config_or_title, title: str = None,
                     year_range: tuple = None, height: int = 450) -> go.Figure:
        """创建面积图 - 支持配置字典格式"""
        if df.empty:
            return go.Figure()

        try:
            fig = go.Figure()

            # 处理两种调用方式：
            # 1. area(df, config_dict, title, year_range)
            # 2. area(df, title, x_column, y_columns, height)
            if isinstance(config_or_title, dict):
                # 新的调用方式：config_or_title是配置字典
                config = config_or_title
                chart_title = title or "面积图"

                # 准备数据
                chart_df = df.copy()
                if hasattr(chart_df.index, 'year'):
                    chart_df['年份'] = chart_df.index.year
                elif '日期' in chart_df.columns:
                    chart_df['年份'] = pd.to_datetime(chart_df['日期']).dt.year

                # 过滤年份范围
                if year_range and len(year_range) == 2:
                    chart_df = chart_df[(chart_df['年份'] >= year_range[0]) & (chart_df['年份'] <= year_range[1])]

                # 使用年份作为x轴
                x_column = '年份'

                # 获取y列
                y_columns = []
                for col in config.keys():
                    if col in chart_df.columns:
                        y_columns.append(col)

                # 重命名列
                rename_dict = config
                chart_df = chart_df.rename(columns=rename_dict)
                y_columns = [rename_dict.get(col, col) for col in y_columns]

            else:
                # 旧的调用方式：直接指定列
                chart_title = config_or_title
                chart_df = df.copy()
                x_column = title
                y_columns = year_range  # 这里year_range实际上是y_columns列表
                title = None  # 重置title，因为已经用作x_column了

                if not x_column and len(chart_df.columns) >= 1:
                    x_column = chart_df.columns[0]

                if not y_columns:
                    y_columns = [col for col in chart_df.columns if col != x_column]

            # 添加面积图轨迹 - 需要累积计算
            cumulative_values = None
            for i, y_col in enumerate(y_columns):
                if y_col in chart_df.columns:
                    # 获取当前列的数值
                    current_values = chart_df[y_col].copy()

                    # 累积计算：当前值 + 前面所有值的累积
                    if cumulative_values is None:
                        # 第一个系列，使用原值
                        display_values = current_values
                        cumulative_values = current_values.copy()
                    else:
                        # 后续系列，累积计算
                        display_values = cumulative_values + current_values
                        cumulative_values = display_values.copy()

                    fig.add_trace(go.Scatter(
                        x=chart_df[x_column],
                        y=display_values,
                        mode='lines',
                        name=y_col,
                        fill='tonexty' if i > 0 else 'tozeroy',
                        line=dict(color=self.get_chart_color(i)),
                        stackgroup='one'  # 确保正确的堆积分组
                    ))

            # 设置布局
            fig.update_layout(
                title=chart_title,
                xaxis_title=f"<b>{x_column}</b>",
                yaxis_title="<b>数值</b>",
                template="plotly_dark",
                paper_bgcolor=self.theme.background,
                plot_bgcolor=self.theme.background,
                font=dict(color=self.theme.text_primary),
                showlegend=len(y_columns) > 1,
                height=height,
                xaxis=dict(
                    title_font=dict(size=12),
                    tickfont=dict(size=10),
                    tickmode='linear'
                ),
                yaxis=dict(
                    title_font=dict(size=12),
                    tickfont=dict(size=10),
                    tickformat=",",
                    separatethousands=True
                )
            )

            return fig
        except Exception as e:
            print(f"创建面积图失败: {e}")
            return None

    def dual_axis(self, df: pd.DataFrame, left_col: str, right_col: str,
                          title: str = "双轴图", x_column: str = None) -> go.Figure:
        """创建双轴图"""
        if df.empty or left_col not in df.columns or right_col not in df.columns:
            return go.Figure()

        try:
            # 自动检测x轴
            if not x_column:
                x_column = df.columns[0] if df.columns[0] not in [left_col, right_col] else df.index

            # 创建双子图
            fig = self.create_dual_axis_chart()

            # 添加左轴数据
            fig.add_trace(
                go.Scatter(x=df[x_column] if x_column != df.index else df.index,
                          y=df[left_col],
                          name=left_col,
                          line=dict(color=self.theme.primary)),
                secondary_y=False,
            )

            # 添加右轴数据
            fig.add_trace(
                go.Scatter(x=df[x_column] if x_column != df.index else df.index,
                          y=df[right_col],
                          name=right_col,
                          line=dict(color=self.theme.secondary)),
                secondary_y=True,
            )

            # 设置布局
            fig.update_layout(
                title=title,
                template="plotly_dark",
                paper_bgcolor=self.theme.background,
                plot_bgcolor=self.theme.background,
                font=dict(color=self.theme.text_primary)
            )

            # 设置y轴标题
            fig.update_yaxes(title_text=left_col, secondary_y=False)
            fig.update_yaxes(title_text=right_col, secondary_y=True)

            return fig
        except Exception as e:
            print(f"创建双轴图失败: {e}")
            return None

    def dual_axis_bar_line(self, df: pd.DataFrame, bar_col: str, line_col: str,
                          title: str = "双轴图表", x_column: str = None,
                          bar_name: str = None, line_name: str = None,
                          height: int = 450) -> go.Figure:
        """创建双轴图表：左轴柱状图 + 右轴折线图"""
        if df.empty or bar_col not in df.columns or line_col not in df.columns:
            return go.Figure()

        try:
            import plotly.graph_objects as go
            from plotly.subplots import make_subplots

            # 自动检测x轴
            if not x_column:
                if len(df.columns) > 0 and df.columns[0] not in [bar_col, line_col]:
                    x_column = df.columns[0]
                else:
                    x_column = df.index

            # 获取数据
            if hasattr(x_column, '__iter__') and not isinstance(x_column, str):
                # 如果x_column是索引或类似对象
                x_data = x_column
            else:
                # 如果x_column是列名
                x_data = df[x_column]
            bar_data = df[bar_col]
            line_data = df[line_col]

            # 收集数值用于确定单位
            all_values = bar_data.dropna().tolist()

            # 获取合适的单位和转换因子
            unit = self.get_appropriate_unit(all_values)
            factor, unit_suffix = self.get_unit_factor_and_suffix(unit)

            # 转换柱状图数值
            converted_bar_data = [v / factor if v is not None else None for v in bar_data]

            # 创建双子图
            fig = self.create_dual_axis_chart()

            # 添加左轴柱状图
            fig.add_trace(
                go.Bar(
                    x=x_data,
                    y=converted_bar_data,
                    name=bar_name or bar_col,
                    marker_color=self.theme.primary,
                    hovertemplate="<b>%{fullData.name}</b><br>" +
                                 "年份: %{x}<br>" +
                                 "金额: %{y:,.2f}" + unit_suffix + "<extra></extra>"
                ),
                secondary_y=False,
            )

            # 添加右轴折线图
            fig.add_trace(
                go.Scatter(
                    x=x_data,
                    y=line_data,
                    mode='lines+markers',
                    name=line_name or line_col,
                    line=dict(color=self.theme.secondary, width=3),
                    marker=dict(size=8),
                    hovertemplate="<b>%{fullData.name}</b><br>" +
                                 "年份: %{x}<br>" +
                                 "数值: %{y:.2f}<extra></extra>"
                ),
                secondary_y=True,
            )

            # 设置布局
            fig.update_layout(
                title=title,
                template="plotly_dark",
                paper_bgcolor=self.theme.background,
                plot_bgcolor=self.theme.background,
                font=dict(color=self.theme.text_primary),
                height=height,
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )

            # 设置y轴标题和格式
            fig.update_yaxes(
                title_text=f"<b>{bar_name or bar_col}</b><br>({unit_suffix})",
                secondary_y=False,
                showgrid=True,
                gridcolor="rgba(128, 128, 128, 0.2)",
                title_font=dict(size=12),
                tickfont=dict(size=10),
                tickformat=",",
                separatethousands=True
            )
            fig.update_yaxes(
                title_text=f"<b>{line_name or line_col}</b>",
                secondary_y=True,
                showgrid=False,
                title_font=dict(size=12),
                tickfont=dict(size=10),
                tickformat=".2f"  # 周转率显示2位小数
            )

            # 设置x轴标题和格式
            if isinstance(x_column, str):
                fig.update_xaxes(
                    title_text=f"<b>{x_column}</b>",
                    title_font=dict(size=12),
                    tickfont=dict(size=10),
                    tickmode='linear',
                    dtick=1 if x_data.dtype.kind in ['i', 'u'] else None  # 整数数据显示整数间隔
                )

            return fig
        except Exception as e:
            print(f"创建双轴柱状折线图失败: {e}")
            return None

    def financial_dual_axis(self, df: pd.DataFrame, metric_name: str, title: str = None) -> go.Figure:
        """创建财务指标双轴图表 - 简化版本，支持毛利计算"""
        if df.empty or metric_name not in df.columns:
            return go.Figure()

        # 检查是否有该指标的映射
        if metric_name not in self.financial_metrics_mapping:
            return self.line(df, title=title or f"{metric_name}趋势", y_cols=[metric_name])

        try:
            mapping = self.financial_metrics_mapping[metric_name]
            numerator = mapping["numerator"]

            # 处理需要计算的字段
            chart_df = df.copy()
            if numerator == "毛利":
                if "一、营业总收入" in chart_df.columns and ("其中：营业成本" in chart_df.columns or "营业成本" in chart_df.columns):
                    cost_col = "其中：营业成本" if "其中：营业成本" in chart_df.columns else "营业成本"
                    chart_df["毛利"] = chart_df["一、营业总收入"] - chart_df[cost_col]
                else:
                    return self.line(df, title=title or f"{metric_name}趋势", y_cols=[metric_name])
            elif numerator == "速动资产":
                if "流动资产合计" in chart_df.columns and "存货" in chart_df.columns:
                    chart_df["速动资产"] = chart_df["流动资产合计"] - chart_df["存货"]
                else:
                    return self.line(df, title=title or f"{metric_name}趋势", y_cols=[metric_name])

            # 简单数据检查
            if numerator not in chart_df.columns:
                return self.line(df, title=title or f"{metric_name}趋势", y_cols=[metric_name])

            # 创建双子图
            fig = self.create_dual_axis_chart()

            x_data = df.index

            # 添加分子柱状图（左轴）
            fig.add_trace(
                go.Bar(x=x_data, y=chart_df[numerator], name=numerator,
                      marker_color=self.theme.primary, opacity=0.8),
                secondary_y=False,
            )

            # 添加指标折线图（右轴）
            fig.add_trace(
                go.Scatter(x=x_data, y=df[metric_name], name=metric_name,
                          mode='lines+markers', line=dict(color=self.theme.info, width=3)),
                secondary_y=True,
            )

            # 设置布局
            chart_title = title or f"{metric_name}分析"
            fig.update_layout(
                title=chart_title,
                template="plotly_dark",
                paper_bgcolor=self.theme.background,
                plot_bgcolor=self.theme.background,
                font=dict(color=self.theme.text_primary),
                height=450,  # 增加50像素高度
                barmode='group'
            )

            # 设置坐标轴
            fig.update_xaxes(title_text="时间")
            fig.update_yaxes(title_text=numerator, secondary_y=False)
            fig.update_yaxes(title_text=metric_name, secondary_y=True)

            return fig

        except Exception as e:
            print(f"创建财务双轴图失败: {e}")
            return self.line(df, title=title or f"{metric_name}趋势", y_cols=[metric_name])

    
    
    
    def cashflow_waterfall(self, cashflow_data: Dict[str, float], title: str = "现金流瀑布图",
                                  colors_dict: Dict[str, str] = None) -> go.Figure:
        """创建现金流瀑布图 - 统一版本"""
        return self._create_unified_waterfall(cashflow_data, title, "现金流分析")

    def cashflow_analysis_waterfall(self, data: Dict[str, Any], title: str = "现金流量分析", height: int = 400) -> Optional[Any]:
        """创建现金流量分析瀑布图 - 直接从数据提取，类似revenue_cost_waterfall"""
        try:
            # 获取经营活动现金流项目
            operating_inflow = self._get_numeric_value(data, ["销售商品、提供劳务收到的现金"])
            tax_refund = self._get_numeric_value(data, ["收到的税费与返还"])
            other_operating_inflow = self._get_numeric_value(data, ["收到其他与经营活动有关的现金"])

            operating_outflow_goods = self._get_numeric_value(data, ["购买商品、接受劳务支付的现金"])
            operating_outflow_employees = self._get_numeric_value(data, ["支付给职工以及为职工支付的现金"])
            operating_outflow_tax = self._get_numeric_value(data, ["支付的各项税费"])
            operating_outflow_other = self._get_numeric_value(data, ["支付其他与经营活动有关的现金"])

            # 获取投资活动现金流项目
            investment_invest_return = self._get_numeric_value(data, ["收回投资收到的现金"])
            investment_income = self._get_numeric_value(data, ["取得投资收益收到的现金"])
            investment_asset_disposal = self._get_numeric_value(data, ["处置固定资产、无形资产和其他长期资产收回的现金净额"])
            investment_asset_purchase = self._get_numeric_value(data, ["购建固定资产、无形资产和其他长期资产支付的现金"])
            investment_payment = self._get_numeric_value(data, ["投资支付的现金"])

            # 获取筹资活动现金流项目
            financing_absorb = self._get_numeric_value(data, ["吸收投资收到的现金"])
            financing_loan = self._get_numeric_value(data, ["取得借款收到的现金"])
            financing_bond = self._get_numeric_value(data, ["发行债券收到的现金"])
            financing_repay = self._get_numeric_value(data, ["偿还债务支付的现金"])
            financing_dividend = self._get_numeric_value(data, ["分配股利、利润或偿付利息支付的现金"])

            # 获取净现金流项目（已去除*前缀）
            operating_net = self._get_numeric_value(data, ["经营活动产生的现金流量净额"])
            investing_net = self._get_numeric_value(data, ["投资活动产生的现金流量净额"])
            financing_net = self._get_numeric_value(data, ["筹资活动产生的现金流量净额"])
            net_increase = self._get_numeric_value(data, ["现金及现金等价物净增加额"])

            # 构建瀑布图数据 - 流入为正，流出为负
            waterfall_data = {}

            # 经营活动现金流
            if operating_inflow > 0:
                waterfall_data["销售商品收入"] = operating_inflow
            if tax_refund > 0:
                waterfall_data["税费返还"] = tax_refund
            if other_operating_inflow > 0:
                waterfall_data["其他经营收入"] = other_operating_inflow

            if operating_outflow_goods > 0:
                waterfall_data["购买商品支出"] = -operating_outflow_goods
            if operating_outflow_employees > 0:
                waterfall_data["职工薪酬支出"] = -operating_outflow_employees
            if operating_outflow_tax > 0:
                waterfall_data["税费支出"] = -operating_outflow_tax
            if operating_outflow_other > 0:
                waterfall_data["其他经营支出"] = -operating_outflow_other

            # 投资活动现金流
            if investment_invest_return > 0:
                waterfall_data["收回投资"] = investment_invest_return
            if investment_income > 0:
                waterfall_data["投资收益"] = investment_income
            if investment_asset_disposal > 0:
                waterfall_data["处置资产"] = investment_asset_disposal

            if investment_asset_purchase > 0:
                waterfall_data["购建资产"] = -investment_asset_purchase
            if investment_payment > 0:
                waterfall_data["投资支付"] = -investment_payment

            # 筹资活动现金流
            if financing_absorb > 0:
                waterfall_data["吸收投资"] = financing_absorb
            if financing_loan > 0:
                waterfall_data["取得借款"] = financing_loan
            if financing_bond > 0:
                waterfall_data["发行债券"] = financing_bond

            if financing_repay > 0:
                waterfall_data["偿还债务"] = -financing_repay
            if financing_dividend > 0:
                waterfall_data["股利支付"] = -financing_dividend

            # 添加净现金流项目
            if operating_net != 0:
                waterfall_data["经营活动净额"] = operating_net
            if investing_net != 0:
                waterfall_data["投资活动净额"] = investing_net
            if financing_net != 0:
                waterfall_data["筹资活动净额"] = financing_net
            if net_increase != 0:
                waterfall_data["现金净增加额"] = net_increase

            # 过滤掉零值
            waterfall_data = {k: v for k, v in waterfall_data.items() if v != 0}

            if not waterfall_data:
                return None

            # 使用统一瀑布图函数
            fig = self._create_unified_waterfall(waterfall_data, title or "现金流量分析", "现金流量分析")

            # 设置高度
            fig.update_layout(height=height + 50)  # 增加50像素高度

            return fig

        except Exception as e:
            print(f"创建现金流量分析瀑布图失败: {e}")
            return None

    def _create_unified_waterfall(self, data: Dict[str, float], title: str, chart_name: str) -> go.Figure:
        """创建统一的瀑布图 - 使用标准颜色方案：增加值红色，减少值绿色，净值黄色"""
        if not data:
            return go.Figure()

        try:
            # 准备数据
            labels = []
            values = []
            measures = []

            # 判断是否是总计项（通常是最后一个或者包含"净"、"总计"等关键词）
            is_total = [False] * len(data)
            data_items = list(data.items())

            for i, (item, value) in enumerate(data_items):
                labels.append(str(item))
                values.append(value)

                # 判断是否为总计项
                item_lower = item.lower()
                if any(keyword in item for keyword in ["净", "总计", "合计", "余额", "剩余"]):
                    is_total[i] = True
                    measures.append("total")
                else:
                    measures.append("relative")

            # 如果数据只有一行，设置为absolute
            if len(labels) == 1:
                measures[0] = "absolute"

            # 计算合适的单位
            all_values = [abs(v) for v in values if v != 0]
            if all_values:
                max_value = max(all_values)
                if max_value >= 1e8:
                    unit, factor = "亿", 1e8
                elif max_value >= 1e4:
                    unit, factor = "万", 1e4
                else:
                    unit, factor = "", 1

                # 转换数值
                converted_values = [v / factor if factor > 1 else v for v in values]
                unit_suffix = f"({unit})" if unit else ""
            else:
                converted_values = values
                unit_suffix = ""

            # 更新标签添加单位
            if unit_suffix:
                labels = [f"{label}{unit_suffix}" for label in labels]

            # 创建瀑布图 - 使用正确的颜色方案
            fig = go.Figure(go.Waterfall(
                name=chart_name,
                orientation="v",
                measure=measures,
                x=labels,
                y=converted_values,
                textposition="outside",
                text=[f"{v:.2f}" for v in converted_values],
                # 关键：正值（增加值）显示为红色，负值（减少值）显示为绿色
                increasing={"marker": {"color": "#ff4444"}},  # 增加值 - 红色
                decreasing={"marker": {"color": "#00ff88"}},  # 减少值 - 绿色
                totals={"marker": {"color": "#FFD700"}}       # 总计/净值 - 黄色
            ))

            # 应用统一布局
            fig.update_layout(
                title=title,
                template="plotly_dark",
                paper_bgcolor=self.theme.background,
                plot_bgcolor=self.theme.background,
                font=dict(color=self.theme.text_primary),
                showlegend=False,
                height=400,
                yaxis=dict(tickformat=",", title=f"金额({unit})" if unit else "金额"),
                xaxis=dict(title="", tickangle=45)
            )

            return fig

        except Exception as e:
            print(f"创建统一瀑布图失败: {e}")
            return go.Figure()

    def fund_flow_chart(self, df: pd.DataFrame, x_col: str, y_col: str, title: str = "",
                              x_title: str = None, y_title: str = None, color_scale: str = "RdYlGn_r") -> go.Figure:
        """创建资金流向图表 - 转置版本（垂直条形图），带数值格式化"""
        if df.empty or x_col not in df.columns or y_col not in df.columns:
            return go.Figure()

        try:
            import plotly.graph_objects as go

            # 按y值排序（从大到小）
            sorted_df = df.sort_values(y_col, ascending=False)

            # 获取合适的单位和转换因子
            unit = self.get_appropriate_unit(sorted_df[y_col].tolist())
            factor, unit_suffix = self.get_unit_factor_and_suffix(unit)

            # 转换数值并格式化显示文本
            converted_values = [v / factor for v in sorted_df[y_col]]
            formatted_text = [f"{v:,.2f}{unit_suffix}" for v in converted_values]

            fig = go.Figure(data=[
                go.Bar(
                    x=sorted_df[x_col],  # x轴为类别（板块/行业名称）
                    y=converted_values,  # y轴为转换后的数值
                    orientation='v',     # 垂直条形图
                    marker=dict(
                        color=sorted_df[y_col],  # 使用原始数值着色
                        colorscale=color_scale,
                        colorbar=dict(title="金额")
                    ),
                    text=formatted_text,
                    textposition='outside'
                )
            ])

            fig.update_layout(
                title=title,
                xaxis_title=x_title or x_col,  # x轴标题为类别名称
                yaxis_title=y_title or f"金额({unit_suffix})",  # y轴标题包含单位
                template="plotly_dark",
                paper_bgcolor=self.theme.background,
                plot_bgcolor=self.theme.background,
                font=dict(color=self.theme.text_primary),
                height=500,
                xaxis_tickangle=-45  # x轴标签倾斜45度以避免重叠
            )

            return fig
        except Exception as e:
            print(f"创建资金流向图失败: {e}")
            return None



# 创建全局模板管理器实例
ui_template_manager = UITemplateManager()