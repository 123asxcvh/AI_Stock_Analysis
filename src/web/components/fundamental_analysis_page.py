#!/usr/bin/env python

"""
财务分析组件
显示财务雷达图、三大报表、财务指标等
整合了原 financial_page_templates.py 的所有功能
"""

import importlib.util
from pathlib import Path
from config import config
from typing import Any, Dict, List

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# 移除不存在的导入


# ==================== 导入工具函数 ====================
# 从utils导入所有数据处理和工具函数
from src.web.utils import (
    safe_get_year, safe_get_date_column,
    filter_annual_data, filter_semi_annual_data, 
    filter_data_by_date, create_date_mask,
    get_year_end_data, get_financial_metric_descriptions,
    ai_report_manager, section_header, get_appropriate_unit,
    UnitManager
)

current_dir = Path(__file__).parent

# 加载配置和工具模块
config_dir = current_dir.parent / "config"
utils_dir = current_dir.parent / "utils"
templates_dir = current_dir.parent / "templates"

# 使用新的可视化配置管理器
from src.web.templates import ui_template_manager

# UI模板管理器已包含所有图表功能

# 使用可视化配置管理器获取颜色
color_scheme = ui_template_manager.colors
COLORS = {
    "pie_colors": [
        color_scheme['primary'],
        color_scheme['secondary'],
        color_scheme['success'],
        color_scheme['danger'],
        color_scheme['warning'],
        color_scheme['info']
    ],
    "dark": color_scheme['text_primary'],
    "muted": color_scheme['text_secondary'],
    "primary": color_scheme['primary'],
    "secondary": color_scheme['secondary'],
    "success": color_scheme['success'],
    "danger": color_scheme['danger'],
    "warning": color_scheme['warning'],
    "info": color_scheme['info']
}

# 财务指标配置 - 已移动到 financial_page_templates 中
# chart_utils已替换为ui_template_manager

class FinancialAnalysisComponent:
    """财务分析组件类 - 整合了原 financial_page_templates.py 的所有功能"""

    def __init__(self):
        # 使用新的可视化配置管理器
        self.ui_manager = ui_template_manager
        self.colors = self.ui_manager.colors
        
        # 向后兼容的颜色配置
        self.colors_dict = {
            "primary": self.colors['primary'],
            "secondary": self.colors['secondary'],
            "success": self.colors['success'],
            "danger": self.colors['danger'],
            "warning": self.colors['warning'],
            "info": self.colors['info'],
            "background": self.colors['background'],
            "text": self.colors['text_primary'],
            "surface": self.colors['surface'],
            "accent": self.colors.get('text_accent', self.colors['text_secondary']),
            "highlight": self.colors['primary'],
            "dark": self.colors['text_primary'],
            "muted": self.colors['text_secondary'],
            # 添加饼图颜色配置
            "pie_colors": [
                self.colors['primary'],
                self.colors['secondary'],
                self.colors['success'],
                self.colors['warning'],
                self.colors['info'],
                "#FF6B6B",  # 红色
                "#4ECDC4",  # 青色
                "#45B7D1",  # 蓝色
                "#96CEB4",  # 绿色
                "#FFEAA7",  # 黄色
            ]
        }
        # UI模板管理器已在类属性中设置
        
        # 财务指标说明字典 - 从utils获取
        self.financial_metric_descriptions = get_financial_metric_descriptions()

    # ========== 从 financial_page_templates.py 整合的方法 ==========

    def display_trend_cards(self, trend_analysis: dict):
        """显示统一的趋势分析信息卡片 - 使用 core_template 中的方法"""
        self.ui_manager.display_trend_cards(trend_analysis)

    def _analyze_dimension_trends(self, df: pd.DataFrame, metrics: List[str], dimension: str) -> dict:
        """分析财务指标趋势，生成趋势卡片数据 - 使用 core_template 中的方法"""
        return self.ui_manager.analyze_dimension_trends(df, metrics, dimension)

    def _format_percentage_value(self, x):
        """通用百分比格式化函数"""
        if pd.isna(x):
            return "-"
        else:
            return f"{x:.2f}%"
    
    
    def get_company_type_from_combination(self, combination: str) -> dict:
        """根据现金流组合获取企业类型"""
        cf_explanations = {
            "OCF+ / ICF- / FCF-": {"emoji": "🏆", "title": "成熟型", "color": "#22c55e", "desc": "健康现金流模式"},
            "OCF+ / ICF+ / FCF-": {"emoji": "🌱", "title": "成长型", "color": "#3b82f6", "desc": "扩张投资期"},
            "OCF+ / ICF- / FCF+": {"emoji": "🔄", "title": "稳定型", "color": "#f59e0b", "desc": "资金回收期"},
            "OCF- / ICF- / FCF+": {"emoji": "⚠️", "title": "转型期", "color": "#fb923c", "desc": "经营调整期"},
            "OCF- / ICF+ / FCF+": {"emoji": "🚀", "title": "创业期", "color": "#8b5cf6", "desc": "投入发展阶段"},
            "OCF- / ICF+ / FCF-": {"emoji": "💸", "title": "消耗型", "color": "#ef4444", "desc": "资金消耗期"},
            "OCF- / ICF- / FCF-": {"emoji": "❌", "title": "风险型", "color": "#dc2626", "desc": "全面收缩期"},
        }
        return cf_explanations.get(combination, {
            "emoji": "❓", "title": "待分析", "color": "#6b7280", "desc": "特殊现金流模式"
        })
    
    def calculate_trend_changes(self, df: pd.DataFrame, indicator: str) -> dict:
        """计算指标的趋势变化"""
        import numpy as np
        
        if indicator not in df.columns:
            return {}

        values = df[indicator].dropna()
        if len(values) < 2:
            return {}

        # 最新值和变化
        latest_value = values.iloc[-1]
        latest_change = values.iloc[-1] - values.iloc[-2] if len(values) >= 2 else 0

        # 计算趋势方向（使用线性回归斜率）
        x = np.arange(len(values))
        y = values.values
        slope = np.polyfit(x, y, 1)[0]

        # 趋势方向判断
        if slope > 0.5:  # 斜率阈值
            trend_direction = "上升"
        elif slope < -0.5:
            trend_direction = "下降"
        else:
            trend_direction = "震荡"

        # 趋势强度（R²值）
        correlation_matrix = np.corrcoef(x, y)
        r_squared = correlation_matrix[0, 1] ** 2
        trend_strength = (
            "强" if r_squared > 0.7 else "中等" if r_squared > 0.4 else "弱"
        )

        # 波动性（标准差）
        volatility = values.std()

        # 稳定性（变异系数）
        stability = "稳定" if volatility / abs(values.mean()) < 0.3 else "不稳定"

        # 计算关键时间点的变化
        changes = {
            "近1年": values.iloc[-1] - values.iloc[-2] if len(values) >= 2 else 0,
            "近3年": values.iloc[-1] - values.iloc[-4] if len(values) >= 4 else 0,
            "近5年": values.iloc[-1] - values.iloc[-6] if len(values) >= 6 else 0,
        }

        return {
            "indicator_name": indicator,
            "latest_value": latest_value,
            "latest_change": latest_change,
            "trend_direction": trend_direction,
            "trend_strength": trend_strength,
            "volatility": volatility,
            "stability": stability,
            "slope": slope,
            "r_squared": r_squared,
            "changes": changes,
        }
    
    # 数据处理方法已移至utils，这里直接调用
    def filter_annual_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """过滤出每年最后日期的年报数据"""
        from src.web.utils import filter_annual_data as _filter_annual_data
        return _filter_annual_data(df)

    def filter_semi_annual_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """过滤出0630和1231的半年度数据"""
        from src.web.utils import filter_semi_annual_data as _filter_semi_annual_data
        return _filter_semi_annual_data(df)

    def display_dimension_trend(self, data: Dict[str, Any], dimension: str):
        """根据维度绘制相关指标趋势图，并加时间滑块"""
        import pandas as pd

        # 指标映射
        dim_metrics = {
            "盈利能力": ["净资产收益率", "销售净利率", "销售毛利率"],
            "偿债能力": ["流动比率", "速动比率", "资产负债率"],
            "成长能力": [
                    "净利润同比增长率",
                    "扣非净利润同比增长率",
                    "营业总收入同比增长率",
                ],
            "营运能力": ["营业周期", "存货周转率", "存货周转天数", "应收账款周转天数"],
            "风险与估值": ["PE(TTM)", "PE(静)", "市净率", "PEG值", "市现率", "市销率"],
        }

        # 根据维度选择数据源
        if dimension == "风险与估值":
            df = data.get("stock_valuation")
        else:
            df = data.get("financial_indicators")

        if df is None:
            st.warning(f"❌ {dimension}数据未找到")
            return
        elif df.empty:
            st.warning(f"❌ {dimension}数据为空")
            return

        # 检查日期信息 - 支持DatetimeIndex或日期列
        has_date_info = False
        if "日期" in df.columns:
            has_date_info = True
        elif hasattr(df.index, 'name') and df.index.name == "日期":
            has_date_info = True
        elif hasattr(df.index, 'to_datetime'):  # DatetimeIndex
            has_date_info = True

        if not has_date_info:
            st.warning(f"❌ {dimension}数据缺少日期信息，可用列: {list(df.columns)}")
            return

        # 处理日期信息 - 如果是DatetimeIndex，保持原状；如果是日期列，确保格式正确
        df = df.copy()
        if "日期" in df.columns:
            df["日期"] = pd.to_datetime(df["日期"], errors="coerce")
            df = df.dropna(subset=["日期"])
            if isinstance(df, pd.DataFrame):
                df = df.sort_values(by="日期")
        # DatetimeIndex不需要处理

        # 固定使用季度视图（移除报告期切换控件）
        if not df.empty:
            section_header("📅 数据时间范围", level=4)

            # 显示数据时间范围信息 - 支持DatetimeIndex和日期列
            if "日期" in df.columns:
                min_date = pd.to_datetime(df["日期"]).min().date()
                max_date = pd.to_datetime(df["日期"]).max().date()
            elif isinstance(df.index, pd.DatetimeIndex):
                # 使用DatetimeIndex
                min_date = df.index.min().date()
                max_date = df.index.max().date()
            else:
                # 无法获取日期信息
                min_date = None
                max_date = None
            
            total_periods = len(df)

            # 计算实际年数
            if min_date and max_date:
                years_span = (max_date - min_date).days / 365.25
                actual_years = int(years_span) + 1
                date_range_text = f"{min_date} 至 {max_date}（共 {total_periods} 个数据点，约 {actual_years} 年）"
            else:
                date_range_text = f"共 {total_periods} 个数据点（日期信息不可用）"

            st.markdown(
                f"""
            <div style='background-color: rgba(255, 215, 0, 0.1); padding: 10px; border-radius: 5px; margin: 10px 0;'>
                <span style='color: #FFD700; font-weight: bold;'>📊 数据时间范围：</span>
                {date_range_text}
            </div>
            """,
                unsafe_allow_html=True,
            )
            
            # 选取该维度的指标
            dimension_config = {
                "成长能力": ("成长能力", "📈"),
                "盈利能力": ("盈利能力", "💰"),
                "营运能力": ("营运能力", "⚙️"),
                "偿债能力": ("偿债能力", "🏦")
            }
            
            if dimension in dimension_config:
                name, icon = dimension_config[dimension]
                self.display_financial_analysis(df, dim_metrics[dimension], name, icon, data)
            else:
                available_metrics = [
                    col for col in dim_metrics[dimension] if col in df.columns
                ]
                if available_metrics:
                        # 为每个指标创建单独的趋势图
                        cols = st.columns(2)  # 创建两列布局
                        for i, metric in enumerate(available_metrics):
                            with cols[i % 2]:  # 交替使用两列
                                # 为每个指标创建单独的线图
                                self._create_single_metric_chart(df, metric, dimension)

                # 移除数据表格显示，只保留图表
        else:
            st.info("📝 暂无财务指标数据")
    
    def display_financial_analysis(self, df: pd.DataFrame, metrics: List[str], analysis_type: str, icon: str, data: Dict[str, Any] = None):
        """统一的财务分析显示函数"""
        # 确保数据按时间顺序排序
        df_sorted = df.copy()

        # 检查并修复时间排序问题
        if hasattr(df_sorted.index, 'to_datetime'):
            # DatetimeIndex情况
            df_sorted = df_sorted.sort_index()
        elif '日期' in df_sorted.columns:
            # 日期列情况
            df_sorted['日期'] = pd.to_datetime(df_sorted['日期'], errors='coerce')
            df_sorted = df_sorted.dropna(subset=['日期'])
            if isinstance(df_sorted, pd.DataFrame):
                df_sorted = df_sorted.sort_values(by='日期')

        # 确保数据不为空且有指标
        available_metrics = [m for m in metrics if m in df_sorted.columns]
        if not available_metrics:
            st.info(f"暂无{analysis_type}数据")
            return

        # 创建趋势卡片 - 使用同比对比
        self._create_trend_cards(df_sorted, available_metrics, icon, analysis_type)

        # 为每个指标创建独立的趋势图
        for i, metric in enumerate(available_metrics):
            
            # 为单个指标创建趋势图
            fig = self.ui_manager.create_financial_trend_chart(
                df_sorted,
                [metric],  # 只传一个指标
                title=f"{metric} 趋势分析",
                stock_code=data.get("stock_code", "") if data else ""
            )
            if fig is not None:
                st.plotly_chart(fig, config={"displayModeBar": False}, key=f"{analysis_type}_trend_{metric}")

            # 添加分隔线（除了最后一个指标）
            if i < len(available_metrics) - 1:
                st.markdown("---")

    def _create_trend_cards(self, df: pd.DataFrame, metrics: List[str], icon: str, analysis_type: str):
        """创建趋势指标卡片"""
        if not metrics:
            return

        cols = st.columns(min(len(metrics), 4))
        for i, metric in enumerate(metrics):
            if metric in df.columns and not df[metric].empty:
                with cols[i % 4]:
                    latest_value = df[metric].iloc[-1] if not df[metric].empty else 0

                    # 计算同比变化 - 获取去年同期值
                    previous_value = self._get_yoy_value(df, metric)
                    change = latest_value - previous_value
                    change_pct = (change / previous_value * 100) if previous_value != 0 else 0

                    delta_color = "normal" if abs(change_pct) < 0.1 else "inverse"
                    trend_icon = "📈" if change > 0 else "📉" if change < 0 else "➡️"

                    st.metric(
                        f"{trend_icon} {metric}",
                        f"{latest_value:,.2f}",
                        f"{change_pct:+.2f}%",
                        delta_color=delta_color
                    )

    def _get_yoy_value(self, df: pd.DataFrame, metric: str) -> float:
        """计算同比值，获取去年同期数据"""
        if df.empty or metric not in df.columns:
            return 0.0

        # 确保索引是日期类型
        df_copy = df.copy()
        if not isinstance(df_copy.index, pd.DatetimeIndex):
            # 如果有日期列，使用日期列作为索引
            if '日期' in df_copy.columns:
                df_copy['日期'] = pd.to_datetime(df_copy['日期'], errors='coerce')
                df_copy = df_copy.dropna(subset=['日期'])
                df_copy = df_copy.set_index('日期')
            else:
                # 如果没有日期列，尝试转换索引
                df_copy.index = pd.to_datetime(df_copy.index, errors='coerce')
                df_copy = df_copy.dropna()

        if df_copy.empty:
            return 0.0

            # 获取最新日期
        latest_date = df_copy.index[-1]

        # 计算去年同期日期
        previous_year_date = latest_date.replace(year=latest_date.year - 1)

        # 查找最接近去年同期日期的数据
        time_diff = abs(df_copy.index - previous_year_date)
        closest_idx = time_diff.argmin()

        # 如果时间差超过3个月，使用前一个数据点
        if time_diff[closest_idx] > pd.Timedelta(days=90):
            if len(df_copy) > 1:
                fallback_value = df_copy[metric].iloc[-2]
                return float(fallback_value) if pd.notna(fallback_value) else 0.0
            return 0.0

        # 返回去年同期值
        yoy_value = df_copy[metric].iloc[closest_idx]
        return float(yoy_value) if pd.notna(yoy_value) else 0.0

    def display_cash_flow_structure(self, data: Dict[str, Any]):
        """显示现金流量表结构分析"""
        if "cash_flow_statement" not in data or data["cash_flow_statement"].empty:
            st.warning("暂无现金流量表数据")
            return

        df = data["cash_flow_statement"]
        annual_df = self.filter_annual_data(df)
        if annual_df.empty:
            st.warning("暂无年度现金流量表数据")
            return

        # 第一行：现金流量瀑布图分析（内部标题）
        self.create_cashflow_waterfall_chart(annual_df)

        st.markdown("---")

        # 第二行：现金流量趋势分析（内部标题）
        self.create_cashflow_trend_analysis(annual_df)

    
    def create_cashflow_waterfall_chart(self, annual_df: pd.DataFrame):
        """创建现金流量瀑布图 - 分为经营、投资、筹资三个维度"""
        if annual_df.empty:
            st.warning("暂无现金流量数据")
            return

        # 获取最新年度数据
        latest_data = annual_df.iloc[-1].to_dict()

        # 创建三个tab
        tab1, tab2, tab3 = st.tabs(["💼 经营活动", "📈 投资活动", "💰 筹资活动"])

        with tab1:
            st.subheader("💼 经营活动现金流")
            # 使用新的专用函数创建经营活动现金流瀑布图
            operating_data = {}
            operating_fields = [
                ("销售商品、提供劳务收到的现金", 1),
                ("收到的税费与返还", 1),
                ("收到其他与经营活动有关的现金", 1),
                ("购买商品、接受劳务支付的现金", -1),
                ("支付给职工以及为职工支付的现金", -1),
                ("支付的各项税费", -1),
                ("支付其他与经营活动有关的现金", -1),
                ("经营活动产生的现金流量净额", None)  # 净额直接使用原值，可能为负
            ]

            for field, multiplier in operating_fields:
                value = latest_data.get(field, 0)
                if pd.notna(value) and value != 0:
                    display_name = field.replace("销售商品、提供劳务收到的现金", "销售商品收入") \
                                        .replace("购买商品、接受劳务支付的现金", "购买商品支出") \
                                        .replace("支付给职工以及为职工支付的现金", "职工薪酬支出") \
                                        .replace("支付的各项税费", "税费支出") \
                                        .replace("支付其他与经营活动有关的现金", "其他经营支出") \
                                        .replace("经营活动产生的现金流量净额", "经营活动净额")
                    # 净额直接使用原值，其他项目使用multiplier
                    if multiplier is None:
                        operating_data[display_name] = value
                    else:
                        operating_data[display_name] = value * multiplier

            if operating_data:
                fig = self.ui_manager.cashflow_waterfall(operating_data, "经营活动现金流", self.colors_dict)
                if fig:
                    fig.update_layout(height=600)  # 增加经营活动现金流图高度
                    st.plotly_chart(fig, config={"displayModeBar": False}, key="ocf_waterfall_chart")
                else:
                    st.info("暂无经营活动现金流数据")
            else:
                st.info("暂无经营活动现金流数据")

        with tab2:
            st.subheader("📈 投资活动现金流")
            # 使用新的专用函数创建投资活动现金流瀑布图
            investing_data = {}
            investing_fields = [
                ("收回投资收到的现金", 1),
                ("取得投资收益收到的现金", 1),
                ("处置固定资产、无形资产和其他长期资产收回的现金净额", 1),
                ("处置子公司及其他营业单位收到的现金净额", 1),
                ("收到其他与投资活动有关的现金", 1),
                ("购建固定资产、无形资产和其他长期资产支付的现金", -1),
                ("投资支付的现金", -1),
                ("取得子公司及其他营业单位支付的现金净额", -1),
                ("支付其他与投资活动有关的现金", -1),
                ("投资活动产生的现金流量净额", None)  # 净额直接使用原值，可能为负
            ]

            for field, multiplier in investing_fields:
                value = latest_data.get(field, 0)
                if pd.notna(value) and value != 0:
                    display_name = field.replace("收回投资收到的现金", "收回投资") \
                                        .replace("取得投资收益收到的现金", "投资收益") \
                                        .replace("处置固定资产、无形资产和其他长期资产收回的现金净额", "处置资产") \
                                        .replace("处置子公司及其他营业单位收到的现金净额", "处置子公司") \
                                        .replace("收到其他与投资活动有关的现金", "其他投资收入") \
                                        .replace("购建固定资产、无形资产和其他长期资产支付的现金", "购建资产") \
                                        .replace("投资支付的现金", "投资支付") \
                                        .replace("取得子公司及其他营业单位支付的现金净额", "收购子公司") \
                                        .replace("支付其他与投资活动有关的现金", "其他投资支出") \
                                        .replace("投资活动产生的现金流量净额", "投资活动净额")
                    # 净额直接使用原值，其他项目使用multiplier
                    if multiplier is None:
                        investing_data[display_name] = value
                    else:
                        investing_data[display_name] = value * multiplier

            if investing_data:
                fig = self.ui_manager.cashflow_waterfall(investing_data, "投资活动现金流", self.colors_dict)
                if fig:
                    fig.update_layout(height=600)  # 增加投资活动现金流图高度
                    st.plotly_chart(fig, config={"displayModeBar": False}, key="icf_waterfall_chart")
                else:
                    st.info("暂无投资活动现金流数据")
            else:
                st.info("暂无投资活动现金流数据")

        with tab3:
            st.subheader("💰 筹资活动现金流")
            # 使用新的专用函数创建筹资活动现金流瀑布图
            financing_data = {}
            financing_fields = [
                ("吸收投资收到的现金", 1),
                ("取得借款收到的现金", 1),
                ("发行债券收到的现金", 1),
                ("收到其他与筹资活动有关的现金", 1),
                ("偿还债务支付的现金", -1),
                ("分配股利、利润或偿付利息支付的现金", -1),
                ("支付其他与筹资活动有关的现金", -1),
                ("筹资活动产生的现金流量净额", None)  # 净额直接使用原值，可能为负
            ]

            for field, multiplier in financing_fields:
                value = latest_data.get(field, 0)
                if pd.notna(value) and value != 0:
                    display_name = field.replace("吸收投资收到的现金", "吸收投资") \
                                        .replace("取得借款收到的现金", "取得借款") \
                                        .replace("发行债券收到的现金", "发行债券") \
                                        .replace("收到其他与筹资活动有关的现金", "其他筹资收入") \
                                        .replace("偿还债务支付的现金", "偿还债务") \
                                        .replace("分配股利、利润或偿付利息支付的现金", "股利支付") \
                                        .replace("支付其他与筹资活动有关的现金", "其他筹资支出") \
                                        .replace("筹资活动产生的现金流量净额", "筹资活动净额")
                    # 净额直接使用原值，其他项目使用multiplier
                    if multiplier is None:
                        financing_data[display_name] = value
                    else:
                        financing_data[display_name] = value * multiplier

            if financing_data:
                fig = self.ui_manager.cashflow_waterfall(financing_data, "筹资活动现金流", self.colors_dict)
                if fig:
                    fig.update_layout(height=600)  # 增加筹资活动现金流图高度
                    st.plotly_chart(fig, config={"displayModeBar": False}, key="fcf_waterfall_chart")
                else:
                    st.info("暂无筹资活动现金流数据")
            else:
                st.info("暂无筹资活动现金流数据")
    
    def create_cashflow_trend_analysis(self, annual_df: pd.DataFrame):
        """创建现金流量趋势分析 - 三个线在同一个图上"""
        if annual_df.empty:
            st.warning("暂无现金流量数据")
            return

        # 现金流量三大活动指标
        target_metrics = [
            ("经营活动产生的现金流量净额", "经营活动现金流"),
            ("投资活动产生的现金流量净额", "投资活动现金流"),
            ("筹资活动产生的现金流量净额", "筹资活动现金流"),
        ]

        # 查找可用的指标
        available_metrics = []
        for base_metric, display_name in target_metrics:
            if base_metric in annual_df.columns:
                available_metrics.append((base_metric, display_name))
            # 由于数据清洗已去除*前缀，这里不再需要备用查找

        if not available_metrics:
            st.warning("暂无可用的现金流量指标")
            return

        # 创建包含所有现金流指标的数据框
        cashflow_data = annual_df.copy()
        cashflow_data["年份"] = safe_get_year(annual_df)

        # 获取所有可用的年份，从2022年开始，包含2025年
        available_years = sorted(cashflow_data["年份"].unique())
        # 过滤从2022年开始的年份数据
        available_years = [year for year in available_years if year >= 2022]
        cashflow_data = cashflow_data[cashflow_data["年份"].isin(available_years)]

        # 确保年份列是整数格式，用于x轴标签
        cashflow_data["年份"] = cashflow_data["年份"].astype(int)

        # 按年份排序以确保正确的顺序（2022->2023->2024->2025...）
        if isinstance(cashflow_data, pd.DataFrame):
            cashflow_data = cashflow_data.sort_values(by='年份')
        
        if cashflow_data.empty:
            st.warning("暂无现金流量数据")
            return

        # 使用统一的单位管理器
        metric_columns = [metric for metric, _ in available_metrics if metric in cashflow_data.columns]

        # 分析列获取最优单位信息
        unit_info = UnitManager.analyze_columns_for_unit(cashflow_data, metric_columns)

        if unit_info['has_data']:
            unit = unit_info['unit']
            unit_label = unit_info['label'].replace('元', '')  # 去掉"元"字，只保留"亿"或"万"

            # 使用单位管理器转换数据
            cashflow_data = UnitManager.convert_dataframe_to_unit(cashflow_data, metric_columns, unit)
        else:
            unit = "元"
            unit_label = "元"

        # 使用统一的图表布局模板创建包含三个指标的图表
        metric_names = [metric for metric, _ in available_metrics]
        display_names = [name for _, name in available_metrics]
        
        # 重命名列以匹配显示名称
        rename_dict = dict(zip(metric_names, display_names))
        chart_df = cashflow_data.rename(columns=rename_dict)

        # 为图表添加更好的悬停文本格式化
        # 传递完整的单位标签用于悬停文本格式化
        if unit_info['has_data']:
            full_unit_label = unit_info['label']  # 完整的单位标签，如"亿元"
        else:
            full_unit_label = "元"

        fig = self.ui_manager.line(
            df=chart_df,
            x_col="年份",
            y_cols=display_names,
            title="三大现金流趋势对比",
            x_title="年份",
            y_title=f"现金流金额({unit_label})",  # 简化的单位标签
            x_mode='category',  # 使用分类模式确保年份正确显示
            unit_label=unit_label  # 传递简化的单位标签用于悬停文本处理
        )
        if fig:
            st.plotly_chart(fig, config={"displayModeBar": False}, key="cashflow_trend_chart")
        else:
            st.info("无法生成现金流量趋势图")

        # 显示最新数据摘要
        latest_data = annual_df.iloc[-1]
        st.markdown("**📈 最新年度现金流量摘要：**")

        summary_cols = st.columns(3)

        for idx, (metric, display_name) in enumerate(available_metrics[:3]):
            value = latest_data.get(metric, 0)
            with summary_cols[idx]:
                color = "🟢" if value >= 0 else "🔴"
                st.metric(
                    label=f"{color} {display_name}",
                    value=f"{value / 1e8:.0f}亿元"
                    if abs(value) > 1e8
                    else f"{value / 1e4:.0f}万元",
                )
    
    def display_balance_sheet_structure(self, data: Dict[str, Any]):
        """显示资产负债表结构分析"""
        if "balance_sheet" not in data or data["balance_sheet"].empty:
            st.warning("暂无资产负债表数据")
            return

        df = data["balance_sheet"]
        annual_df = self.filter_annual_data(df)
        if annual_df.empty:
            st.warning("暂无年度资产负债表数据")
            return

        latest_data = annual_df.iloc[-1]

        # --- 资产结构 ---
        section_header("📊 资产结构", level=5)

        # 创建资产构成的百分比堆叠图（包含历史趋势）
        asset_trend_df = annual_df[['非流动资产合计', '流动资产合计']].copy()
        asset_trend_df['年份'] = safe_get_year(annual_df)

        # 清理和重命名列
        asset_trend_df = asset_trend_df.rename(columns={
            '流动资产合计': '流动资产',
            '非流动资产合计': '非流动资产'
        })

        # 修复资产结构图表的legend
        asset_color_map = {
            '流动资产': '流动资产',
            '非流动资产': '非流动资产'
        }
        # 显示百分比堆叠图
        fig_asset_percent = self.ui_manager.percent_stacked_bar(
            asset_trend_df,
            title="资产构成百分比趋势（流动资产 + 非流动资产 = 100%）",
            x_column='年份',
            color_map=asset_color_map
        )

        if fig_asset_percent:
            st.plotly_chart(fig_asset_percent, config={"displayModeBar": False}, key="asset_percent_stacked_chart")
        else:
            st.info("暂无资产构成趋势数据")

        # 资产数据摘要已在上方显示

        # 显示详细的资产构成分析
        col1, col2 = st.columns(2)

        with col1:
            current_asset_data = {}
            for key in ["货币资金", "交易性金融资产", "应收票据及应收账款", "预付款项", "其他应收款合计", "存货", "一年内到期的非流动资产", "其他流动资产"]:
                if key in latest_data and latest_data[key] > 0:
                    current_asset_data[key] = latest_data[key]

            fig = self.ui_manager.financial_pie(current_asset_data, "流动资产构成", height=400, show_legend=False)
            if fig:
                st.plotly_chart(fig, config={"displayModeBar": False}, key="current_asset_pie_chart")
            else:
                st.info("暂无流动资产数据")

        with col2:
            non_current_asset_data = {}
            for key in ["长期股权投资", "其他非流动金融资产", "投资性房地产", "固定资产合计", "在建工程合计", "无形资产", "长期待摊费用", "递延所得税资产", "其他非流动资产"]:
                if key in latest_data and latest_data[key] > 0:
                    non_current_asset_data[key] = latest_data[key]
            fig = self.ui_manager.financial_pie(non_current_asset_data, "非流动资产构成", height=400, show_legend=False)
            if fig:
                st.plotly_chart(fig, config={"displayModeBar": False}, key="non_current_asset_pie_chart")
            else:
                st.info("暂无非流动资产数据")

        st.markdown("---")

        # --- 负债结构 ---
        section_header("💳 负债结构", level=5)

        # 主要负债构成百分比趋势图（先非流动再流动）
        liability_trend_df = annual_df[['非流动负债合计', '流动负债合计']].copy()
        liability_trend_df['年份'] = safe_get_year(annual_df)
        liability_trend_df = liability_trend_df.rename(columns={
            '非流动负债合计': '非流动负债',
            '流动负债合计': '流动负债'
        })

        # 修复负债结构图表的legend
        liability_color_map = {
            '流动负债': '流动负债',
            '非流动负债': '非流动负债'
        }
        fig_liability_trend = self.ui_manager.percent_stacked_bar(
            liability_trend_df,
            "负债构成百分比趋势（流动负债 + 非流动负债 = 100%）",
            x_column='年份',
            color_map=liability_color_map
        )
        if fig_liability_trend:
            st.plotly_chart(fig_liability_trend, config={"displayModeBar": False}, key="liability_trend_percent_stacked_chart")

        # 详细负债分解
        col1, col2 = st.columns([0.5, 0.5])

        with col1:
            current_liability_data = {}
            for key in ["短期借款", "应付票据及应付账款", "预收款项", "合同负债", "应付职工薪酬", "应交税费", "其他应付款合计", "一年内到期的非流动负债", "其他流动负债"]:
                if key in latest_data and latest_data[key] > 0:
                    current_liability_data[key] = latest_data[key]
            fig = self.ui_manager.financial_pie(current_liability_data, "流动负债构成", height=400, show_legend=False)
            if fig:
                st.plotly_chart(fig, config={"displayModeBar": False}, key="current_liability_pie_chart")
            else:
                st.info("暂无流动负债数据")

        with col2:
            non_current_liability_data = {}
            for key in ["长期借款", "长期应付款合计", "预计负债", "递延所得税负债", "递延收益-非流动负债", "其他非流动负债"]:
                if key in latest_data and latest_data[key] > 0:
                    non_current_liability_data[key] = latest_data[key]
            fig = self.ui_manager.financial_pie(non_current_liability_data, "非流动负债构成", height=400, show_legend=False)
            if fig:
                st.plotly_chart(fig, config={"displayModeBar": False}, key="non_current_liability_pie_chart")
            else:
                st.info("暂无非流动负债数据")

        st.markdown("---")

        # --- 权益结构 ---
        section_header("🏛️ 权益结构", level=5)
        col1, col2 = st.columns(2)

        with col1:
            equity_data = {}
            for key in ["实收资本（或股本）", "资本公积", "盈余公积", "未分配利润", "归属于母公司所有者权益合计", "少数股东权益"]:
                if key in latest_data and latest_data[key] > 0:
                    equity_data[key] = latest_data[key]
            fig = self.ui_manager.financial_pie(equity_data, "所有者权益构成", height=400, show_legend=False)
            if fig:
                st.plotly_chart(fig, config={"displayModeBar": False}, key="equity_pie_chart")
            else:
                st.info("暂无所有者权益数据")

        with col2:
            shareholder_equity_data = {}
            for key in ["归属于母公司所有者权益合计", "少数股东权益"]:
                if key in latest_data and latest_data[key] > 0:
                    shareholder_equity_data[key] = latest_data[key]
            fig = self.ui_manager.financial_pie(shareholder_equity_data, "股东权益构成", height=400, show_legend=False)
            if fig:
                st.plotly_chart(fig, config={"displayModeBar": False}, key="shareholder_equity_pie_chart")
            else:
                st.info("暂无股东权益数据")

        st.markdown("---")

        # --- 资产负债表比重分析表格 ---
        section_header("📊 资产负债表比重分析", level=5)
        self._display_balance_sheet_ratio_table(annual_df)
        self._display_balance_sheet_detailed_ratio_table(annual_df)

    def display_income_statement_structure(self, data: Dict[str, Any]):
        """显示利润表结构分析"""
        if "income_statement" not in data or data["income_statement"].empty:
            st.warning("暂无利润表数据")
            return

        df = data["income_statement"]
        annual_df = self.filter_annual_data(df)
        if annual_df.empty:
            st.warning("暂无年度利润表数据")
            return

        latest_data = annual_df.iloc[-1].to_dict()  # 转换为字典格式

    
        # 左边：收入成本结构瀑布图，右边：成本构成饼图
        col1, col2 = st.columns([1, 1])

        with col1:
            # 收入成本结构瀑布图
            fig = self.ui_manager.revenue_cost_waterfall(latest_data, "收入成本结构", height=500)
            if fig:
                st.plotly_chart(fig, config={"displayModeBar": False}, key="revenue_cost_waterfall_chart")
            else:
                # 如果瀑布图失败，显示简单的数据表格
                st.info("⚠️ 瀑布图数据不足，显示基础数据")

                # 显示可用的利润表基础数据
                basic_data = []
                revenue_fields = ["一、营业总收入", "其中：营业收入", "营业总收入", "营业收入", "主营业务收入"]
                cost_fields = ["其中：营业成本", "营业成本"]

                revenue_value = 0
                for field in revenue_fields:
                    if field in latest_data and latest_data[field] is not None:
                            revenue_value = float(latest_data[field])
                            if revenue_value != 0:
                                basic_data.append(("营业总收入", revenue_value))
                                break

                cost_value = 0
                for field in cost_fields:
                    if field in latest_data and latest_data[field] is not None:
                            cost_value = float(latest_data[field])
                            if cost_value != 0:
                                basic_data.append(("营业成本", cost_value))
                                break

                if revenue_value > 0:
                    gross_profit = revenue_value - cost_value
                    basic_data.append(("毛利", gross_profit))

                    # 显示其他费用
                    expense_fields = [
                        ("销售费用", ["销售费用"]),
                        ("管理费用", ["管理费用"]),
                        ("研发费用", ["研发费用"]),
                        ("财务费用", ["财务费用"])
                    ]

                    for label, field_variants in expense_fields:
                        for field in field_variants:
                            if field in latest_data and latest_data[field] is not None:
                                    value = float(latest_data[field])
                                    if value != 0:
                                        basic_data.append((label, value))
                                        break

                if basic_data:
                    df_basic = pd.DataFrame(basic_data, columns=["项目", "金额"])
                    st.dataframe(df_basic, config={"displayModeBar": False}, hide_index=True)
                else:
                    st.warning("暂无可用的利润表数据")

        with col2:
            # 成本费用结构饼图 - 以营业成本为主，显示各项费用占比
            # 获取营业成本作为主要参考
            operating_cost_variants = ["其中：营业成本", "营业成本"]
            operating_cost = 0
            for variant in operating_cost_variants:
                if variant in latest_data and latest_data[variant] is not None:
                        operating_cost = float(latest_data[variant])
                        if operating_cost != 0:
                            break

            if operating_cost > 0:
                # 收集所有成本费用项目
                cost_item_variants = [
                    ["营业成本", "其中：营业成本"],
                    ["销售费用", "营业费用"],
                    ["管理费用"],
                    ["财务费用"],
                    ["研发费用", "开发费用"],
                    ["税金及附加", "营业税金及附加"],
                    ["利息费用"],
                    ["信用减值损失"],
                    ["资产减值损失"],
                    ["营业外支出"],
                    ["营业成本及附加", "营业成本及附加"],
                    ["销售管理财务费用", "销售管理财务费用"]
                ]

                # 收集所有成本项目的数值
                collected_costs = []
                for item_variants in cost_item_variants:
                    for variant in item_variants:
                        if variant in latest_data and latest_data[variant] > 0:
                            collected_costs.append({
                                "name": item_variants[0],
                                "value": latest_data[variant]
                            })
                            break

                # 按数值排序，取前5大
                collected_costs.sort(key=lambda x: x["value"], reverse=True)
                top_5_costs = collected_costs[:5]

                # 准备饼图数据 - 计算占营业总成本的比重
                pie_data = {}
                for item in top_5_costs:
                    ratio = (item["value"] / operating_cost) * 100
                    pie_data[item["name"]] = ratio

                # 如果还有其他成本，添加"其他"项
                if len(collected_costs) > 5:
                    other_total = sum(item["value"] for item in collected_costs[5:])
                    other_ratio = (other_total / operating_cost) * 100
                    if other_ratio > 0.1:  # 只显示占比大于0.1%的其他项
                        pie_data["其他"] = other_ratio

                # 创建饼图
                fig = self.ui_manager.financial_pie(pie_data, "成本构成分析", height=500, show_legend=False)
                if fig:
                    st.plotly_chart(fig, config={"displayModeBar": False}, key="cost_pie_chart")
                else:
                    st.info("暂无成本费用数据")
            else:
                st.info("暂无营业成本数据，无法生成成本构成饼图")

        st.markdown("---")

        # --- 利润表比重分析表格 ---
        section_header("📊 利润表比重分析", level=5)
        self._display_income_statement_ratio_table(annual_df)

    def _get_year_end_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """获取每年最后一天的数据"""
        return get_year_end_data(df)

    def render(self, data: Dict[str, Any]):
        # 创建主要的三个标签页
        main_tabs = st.tabs(["📈 趋势分析", "🥧 结构分析", "📊 图表分析"])

        with main_tabs[0]:

            # 财务指标维度分析标签页
            tab_names = ["盈利能力", "偿债能力", "成长能力", "营运能力"]
            tabs = st.tabs(tab_names)
            for i, tab in enumerate(tabs):
                with tab:
                    self.display_dimension_trend(data, tab_names[i])

        with main_tabs[1]:
            # 结构分析 - 新增的饼图分析

            # 结构分析的子标签页
            structure_tabs = st.tabs(["📊 资产负债表", "💰 利润表", "💸 现金流量表"])

            with structure_tabs[0]:
                self.display_balance_sheet_structure(data)

            with structure_tabs[1]:
                self.display_income_statement_structure(data)

            with structure_tabs[2]:
                self.display_cash_flow_structure(data)
        
        with main_tabs[2]:
            # 图表分析 - 财务可视化方案
            self.display_financial_chart_analysis(data)

        # AI分析报告 - 专业AI生成的财务分析 (在标签页外部显示)
        self._display_ai_analysis_report(data)

    def _create_cashflow_timeline_chart(self, historical_patterns: list):
        """创建现金流演变时间线图表"""
        if not historical_patterns:
            return
            
        # 显示现金流趋势对比
        # 创建现金流趋势对比图
        fig = self.ui_manager.line(pd.DataFrame(historical_patterns), "现金流趋势对比")
        if fig:
            st.plotly_chart(fig, config={"displayModeBar": False}, key="cashflow_trends_comparison")
    
    def _display_ai_analysis_report(self, data: Dict[str, Any]):
        """显示AI分析报告 - 使用4个tab显示"""
        section_header("AI财务分析报告", level=2)

        # AI报告管理器已从utils导入

        # 获取股票代码
        stock_code = data.get("stock_code", "未知")
        
        if stock_code == "未知":
            st.warning("⚠️ 无法获取股票代码，AI报告无法加载")
            return

        # 定义要显示的4个财务分析报告
        financial_reports = {
            "📊 资产负债表分析": "balance_sheet_analysis.md",
            "💰 利润表分析": "income_statement_analysis.md",
            "💸 现金流量表分析": "cash_flow_analysis.md",
            "📈 财务指标分析": "financial_indicators_analysis.md"
        }

        # 加载AI报告
        reports = ai_report_manager.load_reports(stock_code, "stock")

        if not reports:
            st.warning("⚠️ 未找到AI分析报告，请确保已生成相应的分析文件")
            return

        # 创建4个tabs
        tab_names = list(financial_reports.keys())
        tabs = st.tabs(tab_names)

        for i, (tab_title, report_file) in enumerate(financial_reports.items()):
            with tabs[i]:
                if reports and report_file in reports:
                    content = reports[report_file]
                    if content.startswith("❌"):
                        st.error(f"🤖 {tab_title}分析失败: {content}")
                    else:
                        st.markdown(f"##### {tab_title}")
                        st.markdown(content)
                else:
                    st.info(f"🤖 {tab_title}分析报告暂未加载")
                    # 提供一些提示信息
                    if report_file == "balance_sheet_analysis.md":
                        st.info("💡 资产负债表分析展示公司的资产结构、负债情况和股东权益状况")
                    elif report_file == "income_statement_analysis.md":
                        st.info("💡 利润表分析展示公司的收入、成本、费用和盈利情况")
                    elif report_file == "cash_flow_analysis.md":
                        st.info("💡 现金流量表分析展示公司经营、投资和筹资活动的现金流状况")
                    elif report_file == "financial_indicators_analysis.md":
                        st.info("💡 财务指标分析展示公司的盈利能力、偿债能力、成长能力和营运能力等关键财务指标")

    def display_financial_chart_analysis(self, data: Dict[str, Any]):
        """显示财务图表分析 - 统一显示界面"""
        st.markdown("基于财务可视化方案，提供结构+趋势双视角分析")
        
        # 获取财务数据
        balance_sheet = data.get('balance_sheet', pd.DataFrame())
        income_statement = data.get('income_statement', pd.DataFrame())
        cash_flow_statement = data.get('cash_flow_statement', pd.DataFrame())

        
        if balance_sheet.empty and income_statement.empty and cash_flow_statement.empty:
            st.warning("暂无财务数据，无法进行图表分析")
            return
        
        # 统一显示所有财务图表
        
        # 1. 资产负债表趋势分析
        if not balance_sheet.empty:
            self._display_balance_sheet_trend_analysis(balance_sheet, cash_flow_statement, data)
        st.markdown("---")

        
        
        
    def _display_balance_sheet_trend_analysis(self, df: pd.DataFrame, cash_flow_df: pd.DataFrame = None, data: Dict[str, Any] = None):
        """资产负债表趋势分析"""

        # 数据预处理 - 数据已通过数据加载器设置日期索引
        df = df.copy()
        df['年份'] = safe_get_year(df).astype(int)

        # 创建统一的年度数据
        annual_df = self._get_year_end_data(df)
        
        # 资产结构和负债结构的详细分析在其他方法中显示
        
        # 2. 固定资产与总资产趋势对比
        # 准备数据：固定资产合计+在建工程合计 vs 资产合计
        if not annual_df.empty and '固定资产合计' in annual_df.columns and '资产合计' in annual_df.columns:
            # 计算固定资产合计+在建工程合计
            annual_df['固定资产合计_plus_在建工程合计'] = annual_df['固定资产合计']
            if '在建工程合计' in annual_df.columns:
                annual_df['固定资产合计_plus_在建工程合计'] += annual_df['在建工程合计']

            # 创建对比图表数据
            comparison_data = annual_df[['年份', '固定资产合计_plus_在建工程合计', '资产合计']].copy()

            
            # 使用grouped_bar_years创建对比柱状图
            series_comparison = {
                "固定资产合计_plus_在建工程合计": "固定资产合计+在建工程合计",
                "资产合计": "资产合计"
            }
            fig_fixed = self.ui_manager.grouped_bar_years(comparison_data, series_comparison, "固定资产与总资产趋势对比")
        else:
            fig_fixed = None

        if fig_fixed:
            st.plotly_chart(fig_fixed, config={"displayModeBar": False}, key="balance_sheet_fixed_assets_analysis")

        # 5. 货币资金与现金净增加额对比
        annual_df = self._get_year_end_data(df)

        # 准备合并数据：货币资金（资产负债表）和现金净增加额（现金流量表）
        if not annual_df.empty and cash_flow_df is not None and not cash_flow_df.empty:
            # 处理现金流量表数据
            cash_flow_annual_df = self._get_year_end_data(cash_flow_df)

            # 合并两个数据源
            merged_cash_data = annual_df[['年份', '货币资金']].copy()

            # 查找现金净增加额列（可能有不同的列名）
            cash_flow_col = None
            possible_names = ['现金及现金等价物净增加额', '五、现金及现金等价物净增加额']

            for col_name in possible_names:
                if not cash_flow_annual_df.empty and col_name in cash_flow_annual_df.columns:
                    cash_flow_col = col_name
                    break

            if cash_flow_col and not cash_flow_annual_df.empty and '年份' in cash_flow_annual_df.columns and cash_flow_col in cash_flow_annual_df.columns:
                # 合并现金净增加额数据
                merged_cash_data = merged_cash_data.merge(
                    cash_flow_annual_df[['年份', cash_flow_col]],
                    on='年份',
                    how='left'
                )

                # 重命名列以便显示
                merged_cash_data = merged_cash_data.rename(columns={
                    '货币资金': '货币资金',
                    cash_flow_col: '现金及现金等价物净增加额'
                })

                # 创建对比柱状图
                cash_series = {
                    "货币资金": "货币资金",
                    "现金及现金等价物净增加额": "现金及现金等价物净增加额"
                }
                fig_cash_trend = self.ui_manager.grouped_bar_years(
                    merged_cash_data, cash_series, "货币资金与现金净增加额趋势对比"
                )
            else:
                # 如果没有找到现金净增加额列，只显示货币资金
                st.warning("⚠️ 现金流量表中未找到现金净增加额数据，仅显示货币资金")
                cash_series = {
                    "货币资金": "货币资金"
                }
                fig_cash_trend = self.ui_manager.grouped_bar_years(
                    merged_cash_data, cash_series, "货币资金趋势"
                )
        else:
            fig_cash_trend = None

        if fig_cash_trend:
            st.plotly_chart(fig_cash_trend, config={"displayModeBar": False}, key="cash_trend_chart")
        
               
        # 6. 净利润与经营净现金流对比（简化版）
        # 获取数据
        income_df = data.get('income_statement', pd.DataFrame())
        cash_flow_df = data.get('cash_flow_statement', pd.DataFrame())

        # 检查必要列是否存在
        if '五、净利润' not in income_df.columns or '经营活动产生的现金流量净额' not in cash_flow_df.columns:
            pass

        # 获取每年最后一天的数据
        income_annual = get_year_end_data(income_df)
        cash_flow_annual = get_year_end_data(cash_flow_df)

        # 提取最近5年数据
        income_recent = income_annual[['日期', '五、净利润']].tail(5)
        cash_flow_recent = cash_flow_annual[['日期', '经营活动产生的现金流量净额']].tail(5)

        # 创建对比数据
        years = income_recent['日期'].dt.year.tolist()
        net_profits = income_recent['五、净利润'].tolist()
        cash_flows = cash_flow_recent['经营活动产生的现金流量净额'].tolist()[:len(years)]

        # 分析单位
        all_values = net_profits + cash_flows
        optimal_unit = UnitManager.get_optimal_unit(all_values)
        factor, label = UnitManager.get_factor_and_label(optimal_unit)

        # 转换单位
        net_profits_converted = [v / factor for v in net_profits]
        cash_flows_converted = [v / factor for v in cash_flows]

        # 使用模板柱状图直接对比
        comparison_config = {
            '净利润': '净利润',
            '经营活动现金流': '经营活动现金流'
        }

        fig_comparison = self.ui_manager.grouped_bar_years(
            pd.DataFrame({
                '年份': years,
                '净利润': net_profits_converted,
                '经营活动现金流': cash_flows_converted
            }),
            comparison_config,
            '净利润与经营净现金流对比'
        )
        if fig_comparison:
            st.plotly_chart(fig_comparison, config={"displayModeBar": False}, key="profit_cashflow_comparison_chart")

        # 7. 存货双轴分析（存货 + 存货周转率）
        # 确保 annual_df 有 '年份' 列
        if '年份' not in annual_df.columns:
            annual_df['年份'] = safe_get_year(annual_df).astype(int)

        # 存货双轴分析：存货（柱状图）+ 存货周转率（折线图）
        if '存货' in annual_df.columns and not annual_df.empty:
            # 准备存货数据
            inventory_df = annual_df[['年份', '存货']].copy().dropna()

            # 尝试从财务指标文件读取存货周转率
            financial_indicators = data.get('financial_indicators', pd.DataFrame())
            inventory_turnover_available = False

            if not financial_indicators.empty:
                # 使用年末数据
                indicators_annual_df = self._get_year_end_data(financial_indicators)

                if not indicators_annual_df.empty and '存货周转率' in indicators_annual_df.columns:
                    inventory_turnover_available = True

                    # 合并存货和周转率数据
                    merged_data = inventory_df.merge(
                        indicators_annual_df[['年份', '存货周转率']],
                        on='年份',
                        how='left'
                    )

                    # 创建双轴图表
                    fig_inventory = self.ui_manager.dual_axis_bar_line(
                        merged_data,
                        bar_col='存货',
                        line_col='存货周转率',
                        title='存货双轴分析（2022-2024年）',
                        x_column='年份',
                        bar_name='存货余额',
                        line_name='存货周转率'
                    )

                    if fig_inventory:
                        st.plotly_chart(fig_inventory, config={"displayModeBar": False}, key="inventory_dual_axis_chart")
                    else:
                        st.warning("⚠️ 存货双轴图表创建失败")

            # 如果没有周转率数据，尝试计算
            if not inventory_turnover_available:
                # 计算存货周转率
                income_df = data.get('income_statement', pd.DataFrame())
                if not income_df.empty:
                    # 使用年末数据
                    income_annual_df = self._get_year_end_data(income_df)

                    # 合并存货和营业成本数据
                    merged_data = inventory_df.copy()

                    # 查找营业成本列
                    cost_col = None
                    possible_cost_names = ['其中：营业成本', '营业成本', '主营业务成本']
                    for col_name in possible_cost_names:
                        if not income_annual_df.empty and col_name in income_annual_df.columns:
                            cost_col = col_name
                            break

                    if cost_col and not income_annual_df.empty and '年份' in income_annual_df.columns:
                        # 合并营业成本数据
                        merged_data = merged_data.merge(
                            income_annual_df[['年份', cost_col]],
                            on='年份',
                            how='left'
                        )

                        # 计算存货周转率
                        # 使用当年营业成本和当年存货余额计算（简化计算）
                        merged_data['存货周转率'] = merged_data[cost_col] / merged_data['存货']

                        # 创建双轴图表
                        fig_inventory = self.ui_manager.dual_axis_bar_line(
                            merged_data,
                            bar_col='存货',
                            line_col='存货周转率',
                            title='存货双轴分析（2022-2024年）',
                            x_column='年份',
                            bar_name='存货余额',
                            line_name='存货周转率'
                        )

                        if fig_inventory:
                            st.plotly_chart(fig_inventory, config={"displayModeBar": False}, key="inventory_dual_axis_chart")
                        else:
                            st.warning("⚠️ 存货双轴图表创建失败")
                    else:
                        st.warning("⚠️ 未找到营业成本数据，无法计算存货周转率")
                        # 仅显示存货趋势图
                        fig_inventory = self.ui_manager.line(
                            inventory_df.set_index('年份'), '存货趋势分析（2022-2024年）'
                        )
                        st.plotly_chart(fig_inventory, config={"displayModeBar": False}, key="inventory_simple_chart")
                else:
                    st.warning("⚠️ 无利润表数据，无法计算存货周转率")

        

        # 8-11. 绝对值堆叠面积图 - 重构为通用方法
        self._display_stacked_area_charts(annual_df)

    def _display_stacked_area_charts(self, annual_df: pd.DataFrame):
        """显示绝对值堆叠面积图"""
        if annual_df.empty:
            st.warning("暂无年度数据，无法生成堆叠图")
            return

        # 确保年份列是整数类型，便于x轴显示
        if '年份' in annual_df.columns:
            annual_df['年份'] = annual_df['年份'].astype(int)

        # 定义所有堆叠图配置
        chart_configs = [
            {
                'title': '流动资产绝对值堆叠分析（2022-2025年）',
                'config': {
                    '货币资金': '货币资金',
                    '交易性金融资产': '交易性金融资产',
                    '应收票据及应收账款': '应收账款',
                    '预付款项': '预付款项',
                    '其他应收款合计': '其他应收款合计',
                    '存货': '存货',
                    '其他流动资产': '其他流动资产'
                },
                'key': 'current_assets_absolute_chart',
                'height': 500,
                'empty_msg': '流动资产'
            },
            {
                'title': '非流动资产绝对值堆叠分析（2022-2025年）',
                'config': {
                    '长期股权投资': '长期股权投资',
                    '固定资产合计': '固定资产',
                    '在建工程合计': '在建工程',
                    '无形资产': '无形资产',
                    '递延所得税资产': '递延所得税资产',
                    '其他非流动资产': '其他非流动资产'
                },
                'key': 'non_current_assets_absolute_chart',
                'height': None,
                'empty_msg': '非流动资产'
            },
            {
                'title': '流动负债绝对值堆叠分析（2022-2025年）',
                'config': {
                    '短期借款': '短期借款',
                    '应付票据及应付账款': '应付票据及应付账款',
                    '预收款项': '预收款项',
                    '合同负债': '合同负债',
                    '应付职工薪酬': '应付职工薪酬',
                    '应交税费': '应交税费',
                    '其他应付款合计': '其他应付款合计',
                    '一年内到期的非流动负债': '一年内到期的非流动负债',
                    '其他流动负债': '其他流动负债'
                },
                'key': 'current_liability_absolute_chart',
                'height': None,
                'empty_msg': '流动负债'
            },
            {
                'title': '非流动负债绝对值堆叠分析（2022-2025年）',
                'config': {
                    '长期借款': '长期借款',
                    '长期应付款合计': '长期应付款合计',
                    '预计负债': '预计负债',
                    '递延所得税负债': '递延所得税负债',
                    '递延收益-非流动负债': '递延收益-非流动负债',
                    '其他非流动负债': '其他非流动负债'
                },
                'key': 'non_current_liability_absolute_chart',
                'height': None,
                'empty_msg': '非流动负债'
            }
        ]

        # 批量生成图表
        for chart_info in chart_configs:
            self._create_single_stacked_chart(annual_df, chart_info)

    def _create_single_stacked_chart(self, annual_df: pd.DataFrame, chart_info: dict):
        """创建单个堆叠图"""
        # 过滤出存在的列
        available_columns = {k: v for k, v in chart_info['config'].items() if k in annual_df.columns}

        if available_columns:
            # 创建堆叠图
            fig = self.ui_manager.stacked_area(
                annual_df,
                available_columns,
                chart_info['title'],
                year_range=(2022, 2025),
                height=chart_info.get('height', 450)
            )

            if fig:
                st.plotly_chart(fig, config={"displayModeBar": False}, key=chart_info['key'])
            else:
                st.warning(f"⚠️ {chart_info['empty_msg']}堆叠图生成失败")
        else:
            st.info(f"📊 暂无{chart_info['empty_msg']}数据或数据为空")

    def _display_income_statement_trend_analysis(self, df: pd.DataFrame):
        """利润表趋势分析"""

        # 数据预处理 - 数据已通过数据加载器设置日期索引
        df = df.copy()
        df['年份'] = safe_get_year(df).astype(int)
        annual_df = self._get_year_end_data(df)
        

    def _display_cash_flow_trend_analysis(self, df: pd.DataFrame):
        """现金流量表趋势分析"""

        # 数据预处理 - 数据已通过数据加载器设置日期索引
        df = df.copy()
        df['年份'] = safe_get_year(df).astype(int)
        annual_df = self._get_year_end_data(df)
        
        
        # 3. 现金含金量分析
        # 计算OCF/净利润比率
        if '经营活动产生的现金流量净额' in df.columns and '五、净利润' in df.columns:
            df['现金含金量'] = df['经营活动产生的现金流量净额'] / df['五、净利润']

            # 创建现金含金量单指标折线图（删除双轴）
            fig_quality = self.ui_manager.line(
                df,
                title='现金含金量分析',
                y_cols=['现金含金量'],
                x_col='年份'
            )
            if fig_quality:
                st.plotly_chart(fig_quality, config={"displayModeBar": False}, key="cashflow_quality_analysis")

    def _display_balance_sheet_ratio_table(self, annual_df: pd.DataFrame):
        """显示资产负债表比重分析 - 使用百分比趋势图"""
        if annual_df.empty:
            st.warning("暂无资产负债表数据")
            return

        # 检查必要的数据列 - 支持多种可能的列名
        liability_columns = ["负债合计", "负债总计", "总负债"]
        equity_columns = ["所有者权益（或股东权益）合计", "所有者权益合计", "股东权益合计", "归属于母公司所有者权益合计", "净资产总计", "所有者权益(或股东权益)总计"]

        # 找到实际存在的列名
        liability_col = None
        equity_col = None

        for col in liability_columns:
            if col in annual_df.columns:
                liability_col = col
                break

        for col in equity_columns:
            if col in annual_df.columns:
                equity_col = col
                break

        if not liability_col:
            st.warning(f"缺少负债数据列，尝试的列名: {', '.join(liability_columns)}")
            return

        if not equity_col:
            st.warning(f"缺少所有者权益数据列，尝试的列名: {', '.join(equity_columns)}")
            return

        # 创建负债与权益构成的百分比堆叠图
        liability_equity_df = annual_df[[liability_col, equity_col]].copy()
        liability_equity_df['年份'] = safe_get_year(annual_df)

        # 清理和重命名列 - 负债在下方（先），权益在上方（后）
        liability_equity_df = liability_equity_df.rename(columns={
            liability_col: '负债',
            equity_col: '所有者权益'
        })

        # 修复资产负债表比重分析图表的legend
        balance_sheet_color_map = {
            '负债': '负债',
            '所有者权益': '所有者权益'
        }
        # 显示百分比堆叠图
        fig_ratio_percent = self.ui_manager.percent_stacked_bar(
            liability_equity_df,
            title="资产负债构成百分比趋势（负债 + 所有者权益 = 100%）",
            x_column='年份',
            color_map=balance_sheet_color_map
        )

        if fig_ratio_percent:
            st.plotly_chart(fig_ratio_percent, config={"displayModeBar": False}, key="liability_equity_percent_stacked_chart")
        else:
            st.info("暂无资产负债构成趋势数据")

    def _display_balance_sheet_detailed_ratio_table(self, annual_df: pd.DataFrame):
        """显示资产负债表详细比重分析表格 - 分别分析资产和负债结构"""
        if annual_df.empty:
            st.warning("暂无资产负债表数据")
            return

        # 确保年份数据可用
        df_processed = annual_df.copy()
        if '年份' not in df_processed.columns:
            df_processed['年份'] = safe_get_year(df_processed)

        # 获取总资产和总负债作为分母 - 支持多种可能的列名
        asset_variants = ["资产总计", "总资产", "资产合计", "负债和所有者权益总计"]
        liability_variants = ["负债合计", "负债总计", "总负债"]

        asset_col = None
        liability_col = None

        for variant in asset_variants:
            if variant in df_processed.columns:
                asset_col = variant
                break

        for variant in liability_variants:
            if variant in df_processed.columns:
                liability_col = variant
                break

        if asset_col is None:
            st.warning("缺少总资产数据")
            return

        if liability_col is None:
            st.warning("缺少总负债数据")
            return

        # 创建两个标签页：资产结构分析和负债结构分析
        asset_tab, liability_tab = st.tabs(["🏢 资产结构分析", "💳 负债结构分析"])

        with asset_tab:
            self._display_asset_structure_analysis(df_processed, asset_col)

        with liability_tab:
            self._display_liability_structure_analysis(df_processed, liability_col)

    def _display_asset_structure_analysis(self, df_processed: pd.DataFrame, asset_col: str):
        """显示资产结构分析 - 以总资产为100%"""

        # 定义资产类项目 - 按标准资产负债表顺序排列
        asset_items = {
            # 流动资产
            "货币资金": "货币资金",
            "交易性金融资产": "交易性金融资产",
            "应收票据及应收账款": "应收票据及应收账款",
            "应收账款": "应收账款",
            "预付款项": "预付款项",
            "其他应收款合计": "其他应收款合计",
            "存货": "存货",
            "一年内到期的非流动资产": "一年内到期非流动资产",
            "其他流动资产": "其他流动资产",
            "流动资产合计": "流动资产合计",

            # 非流动资产
            "长期股权投资": "长期股权投资",
            "其他非流动金融资产": "其他非流动金融资产",
            "投资性房地产": "投资性房地产",
            "固定资产合计": "固定资产合计",
            "在建工程合计": "在建工程合计",
            "工程物资": "工程物资",
            "无形资产": "无形资产",
            "长期待摊费用": "长期待摊费用",
            "递延所得税资产": "递延所得税资产",
            "其他非流动资产": "其他非流动资产",
            "非流动资产合计": "非流动资产合计",

            # 资产总计
            "资产合计": "资产合计",
            "负债和所有者权益（或股东权益）合计": "负债和所有者权益合计"
        }

        # 创建资产结构分析数据
        asset_ratios = {}

        for idx, row in df_processed.iterrows():
            # 从索引或列中获取年份
            if hasattr(idx, 'year'):
                year = idx.year
            else:
                year = row.get('年份', '未知')

            # 处理所有有效的年份数据
            total_assets = row.get(asset_col, 0)
            if pd.isna(total_assets) or total_assets == 0:
                st.warning(f"⚠️ {year}年总资产数据无效: {total_assets}")
                continue

            # 计算各项资产占总资产的比重
            for col, label in asset_items.items():
                if col in df_processed.columns:
                    value = row.get(col, 0)
                    if pd.notna(value) and abs(value) > 0.01:  # 显示有意义的项目
                        ratio = (value / abs(total_assets)) * 100
                        if label not in asset_ratios:
                            asset_ratios[label] = {}
                        asset_ratios[label][year] = ratio

            # 确保资产总计总是显示为100%
            if "资产合计" not in asset_ratios:
                asset_ratios["资产合计"] = {}
            asset_ratios["资产合计"][year] = 100.00

        if asset_ratios:
            # 定义标准资产顺序 - 总资产在第一行，然后是流动资产和非流动资产
            asset_standard_order = [
                "资产合计",  # 第一行：总资产（100%）
                "流动资产合计",  # 第二行：流动资产占总资产比例
                "非流动资产合计",  # 第三行：非流动资产占总资产比例
                # 然后是详细的资产构成
                "货币资金", "交易性金融资产", "应收票据及应收账款", "预付款项",
                "其他应收款合计", "存货", "一年内到期非流动资产", "其他流动资产",
                "长期股权投资", "固定资产合计", "在建工程合计", "无形资产", "商誉",
                "长期待摊费用", "递延所得税资产", "其他非流动资产"
            ]

            # 转换为DataFrame并排序
            transposed_df = pd.DataFrame(asset_ratios).T
            available_items = [item for item in asset_standard_order if item in transposed_df.index]
            other_items = [item for item in transposed_df.index if item not in asset_standard_order]
            final_order = available_items + other_items
            transposed_df = transposed_df.reindex(final_order)
            transposed_df = transposed_df.reindex(sorted(transposed_df.columns), axis=1)

            # 格式化显示
            formatted_df = transposed_df.map(self._format_percentage_value)

            # 添加标题说明
            st.markdown("**🏢 资产结构占比分析（总资产 = 100%）**")
            st.markdown("*各项资产占总资产的百分比*")

            # 自定义CSS样式设置表格右对齐
            st.markdown("""
            <style>
            .dataframe div[data-testid="stDataFrame"] {
                text-align: right !important;
            }
            .dataframe div[data-testid="stDataFrame"] div {
                text-align: right !important;
            }
            .dataframe div[data-testid="stDataFrame"] td {
                text-align: right !important;
                padding-right: 10px !important;
            }
            </style>
            """, unsafe_allow_html=True)

            st.dataframe(formatted_df)
        else:
            st.info("暂无资产结构数据")

    def _display_liability_structure_analysis(self, df_processed: pd.DataFrame, liability_col: str):
        """显示负债结构分析 - 以总负债为100%"""

        # 定义负债类项目 - 按标准资产负债表顺序排列
        liability_items = {
            # 流动负债
            "短期借款": "短期借款",
            "衍生金融负债": "衍生金融负债",
            "应付票据及应付账款": "应付票据及应付账款",
            "预收款项": "预收款项",
            "合同负债": "合同负债",
            "应付职工薪酬": "应付职工薪酬",
            "应交税费": "应交税费",
            "其他应付款合计": "其他应付款合计",
            "应付股利": "应付股利",
            "一年内到期的非流动负债": "一年内到期的非流动负债",
            "其他流动负债": "其他流动负债",
            "流动负债合计": "流动负债合计",

            # 非流动负债
            "长期借款": "长期借款",
            "长期应付款合计": "长期应付款合计",
            "预计负债": "预计负债",
            "递延所得税负债": "递延所得税负债",
            "递延收益-非流动负债": "递延收益-非流动负债",
            "其他非流动负债": "其他非流动负债",
            "非流动负债合计": "非流动负债合计",

            # 负债总计
            "负债合计": "负债合计"
        }

        # 创建负债结构分析数据
        liability_ratios = {}

        for idx, row in df_processed.iterrows():
            # 从索引或列中获取年份
            if hasattr(idx, 'year'):
                year = idx.year
            else:
                year = row.get('年份', '未知')

            # 处理所有有效的年份数据
            total_liabilities = row.get(liability_col, 0)
            if pd.isna(total_liabilities) or total_liabilities == 0:
                st.warning(f"⚠️ {year}年总负债数据无效: {total_liabilities}")
                continue

            # 计算各项负债占总负债的比重
            for col, label in liability_items.items():
                if col in df_processed.columns:
                    value = row.get(col, 0)
                    if pd.notna(value) and abs(value) > 0.01:  # 显示有意义的项目
                        ratio = (value / abs(total_liabilities)) * 100
                        if label not in liability_ratios:
                            liability_ratios[label] = {}
                        liability_ratios[label][year] = ratio

            # 确保负债合计总是显示为100%
            if "负债合计" not in liability_ratios:
                liability_ratios["负债合计"] = {}
            liability_ratios["负债合计"][year] = 100.00

        if liability_ratios:
            # 定义标准负债顺序 - 总负债在第一行，然后是流动负债和非流动负债
            liability_standard_order = [
                "负债合计",  # 第一行：总负债（100%）
                "流动负债合计",  # 第二行：流动负债占总负债比例
                "非流动负债合计",  # 第三行：非流动负债占总负债比例
                # 然后是详细的负债构成
                # 流动负债
                "短期借款", "应付票据及应付账款", "合同负债", "应付职工薪酬", "应交税费",
                "其他应付款合计", "一年内到期非流动负债", "其他流动负债",
                # 非流动负债
                "长期借款", "长期应付款合计", "预计负债", "递延所得税负债", "递延收益-非流动负债", "其他非流动负债"
            ]

            # 转换为DataFrame并排序
            transposed_df = pd.DataFrame(liability_ratios).T
            available_items = [item for item in liability_standard_order if item in transposed_df.index]
            other_items = [item for item in transposed_df.index if item not in liability_standard_order]
            final_order = available_items + other_items
            transposed_df = transposed_df.reindex(final_order)
            transposed_df = transposed_df.reindex(sorted(transposed_df.columns), axis=1)

            # 格式化显示
            formatted_df = transposed_df.map(self._format_percentage_value)

            # 添加标题说明
            st.markdown("**💳 负债结构占比分析（总负债 = 100%）**")
            st.markdown("*各项负债占总负债的百分比*")

            # 自定义CSS样式设置表格右对齐
            st.markdown("""
            <style>
            .dataframe div[data-testid="stDataFrame"] {
                text-align: right !important;
            }
            .dataframe div[data-testid="stDataFrame"] div {
                text-align: right !important;
            }
            .dataframe div[data-testid="stDataFrame"] td {
                text-align: right !important;
                padding-right: 10px !important;
            }
            </style>
            """, unsafe_allow_html=True)

            st.dataframe(formatted_df)
        else:
            st.info("暂无负债结构数据")

    def _display_income_statement_ratio_table(self, annual_df: pd.DataFrame):
        """显示利润表比重分析表格 - 以营业收入为100%计算各项成本占比"""
        if annual_df.empty:
            st.warning("暂无利润表数据")
            return

        # 确保年份数据可用
        df_processed = annual_df.copy()
        if '年份' not in df_processed.columns:
            df_processed['年份'] = safe_get_year(df_processed)

        # 获取营业收入作为分母 - 支持多种可能的列名
        revenue_variants = ["一、营业总收入", "营业总收入", "其中：营业收入", "主营业务收入"]
        revenue_col = None
        for variant in revenue_variants:
            if variant in df_processed.columns:
                revenue_col = variant
                break

        if revenue_col is None:
            st.warning("缺少营业收入数据")
            return

        # 定义利润表项目 - 按标准利润表顺序排列
        profit_items = {
            # 收入类 - 移除重复的"其中：营业收入"避免显示重复
            "一、营业总收入": "营业总收入",

            # 成本费用类
            "其中：营业成本": "营业成本",
            "营业税金及附加": "营业税金及附加",
            "销售费用": "销售费用",
            "管理费用": "管理费用",
            "研发费用": "研发费用",
            "财务费用": "财务费用",
            "资产减值损失": "资产减值损失",
            "信用减值损失": "信用减值损失",

            # 收益类
            "加：公允价值变动收益": "公允价值变动收益",
            "投资收益": "投资收益",
            "资产处置收益": "资产处置收益",
            "其他收益": "其他收益",

            # 利润类
            "三、营业利润": "营业利润",
            "加：营业外收入": "营业外收入",
            "减：营业外支出": "营业外支出",
            "四、利润总额": "利润总额",
            "减：所得税费用": "所得税费用",
            "五、净利润": "净利润"
        }

        # 创建完整利润表比重分析数据 - 行为科目，列为年份
        years = []
        for idx, row in df_processed.iterrows():
            if hasattr(idx, 'year'):
                year = idx.year
            else:
                year = row.get('年份', '未知')
            years.append(year)

        # 创建科目为主键的数据结构
        profit_ratios = {}  # {科目: {年份: 占比}}

        for idx, row in df_processed.iterrows():
            # 从索引或列中获取年份
            if hasattr(idx, 'year'):
                year = idx.year
            else:
                year = row.get('年份', '未知')

            # 处理所有有效的年份数据
            revenue = row.get(revenue_col, 0)
            if pd.isna(revenue) or revenue == 0:
                st.warning(f"⚠️ {year}年营业收入数据无效: {revenue}")
                continue

            # 计算各项利润表项目占营业收入的比重
            for col, label in profit_items.items():
                if col in df_processed.columns:
                    value = row.get(col, 0)
                    if pd.notna(value) and abs(value) > 0.01:  # 显示有意义的项目
                        # 收入类项目显示正占比，成本费用类项目显示负占比
                        if label in ["营业总收入"]:
                            ratio = (value / revenue) * 100  # 收入为正占比
                        elif label in ["营业成本", "税金及附加", "销售费用", "管理费用", "财务费用", "研发费用"]:
                            ratio = -(value / revenue) * 100  # 成本费用为负占比
                        else:
                            # 利润类项目按实际符号显示
                            ratio = (value / revenue) * 100

                        if label not in profit_ratios:
                            profit_ratios[label] = {}
                        profit_ratios[label][year] = ratio

            # 计算毛利（考虑营业税金及附加）
            # 毛利 = 营业收入 - 营业成本 - 营业税金及附加
            operating_cost_fields = ["其中：营业成本", "营业成本"]
            tax_fields = ["营业税金及附加", "税金及附加"]

            operating_cost = 0
            for field in operating_cost_fields:
                if field in row and pd.notna(row[field]):
                    operating_cost = row[field]
                    break

            tax_amount = 0
            for field in tax_fields:
                if field in row and pd.notna(row[field]):
                    tax_amount = row[field]
                    break

            if operating_cost > 0:
                gross_profit = revenue - operating_cost - tax_amount
                gross_ratio = (gross_profit / revenue) * 100
                if "毛利" not in profit_ratios:
                    profit_ratios["毛利"] = {}
                profit_ratios["毛利"][year] = gross_ratio

            # 计算营业利润（纯计算方式）
            # 营业利润 = 毛利 - 期间费用（营业税金及附加已在毛利中扣除）
            expense_fields = {
                "销售费用": ["销售费用"],
                "管理费用": ["管理费用"],
                "财务费用": ["财务费用"],
                "研发费用": ["研发费用"]
            }

            total_expenses = 0
            for field_variants in expense_fields.values():
                expense_value = 0
                for field in field_variants:
                    if field in row and pd.notna(row[field]):
                        expense_value = row[field]
                        break
                total_expenses += expense_value

            if gross_profit != 0 and total_expenses > 0:
                operating_profit = gross_profit - total_expenses
                operating_ratio = (operating_profit / revenue) * 100
                if "营业利润" not in profit_ratios:
                    profit_ratios["营业利润"] = {}
                profit_ratios["营业利润"][year] = operating_ratio

        if profit_ratios:
            # 定义标准利润表顺序 - 与profit_items顺序保持一致
            standard_order = [
                "营业总收入",
                "营业成本",
                "营业税金及附加",
                "毛利",
                "销售费用",
                "管理费用",
                "研发费用",
                "财务费用",
                "资产减值损失",
                "信用减值损失",
                "公允价值变动收益",
                "投资收益",
                "资产处置收益",
                "其他收益",
                "营业利润",
                "营业外收入",
                "营业外支出",
                "利润总额",
                "所得税费用",
                "净利润"
            ]

            # 转换为DataFrame
            transposed_df = pd.DataFrame(profit_ratios).T

            # 按标准顺序重新排列行
            available_items = [item for item in standard_order if item in transposed_df.index]
            other_items = [item for item in transposed_df.index if item not in standard_order]
            final_order = available_items + other_items
            transposed_df = transposed_df.reindex(final_order)

            # 按年份排序列
            transposed_df = transposed_df.reindex(sorted(transposed_df.columns), axis=1)

            # 格式化显示
            formatted_df = transposed_df.map(self._format_percentage_value)

            # 添加标题说明
            st.markdown("**利润表项目占营业收入比重（%）**")

            # 自定义CSS样式设置表格右对齐
            st.markdown("""
            <style>
            .dataframe div[data-testid="stDataFrame"] {
                text-align: right !important;
            }
            .dataframe div[data-testid="stDataFrame"] div {
                text-align: right !important;
            }
            .dataframe div[data-testid="stDataFrame"] td {
                text-align: right !important;
                padding-right: 10px !important;
            }
            </style>
            """, unsafe_allow_html=True)

            st.dataframe(formatted_df)
        else:
            st.info("暂无利润表比重数据")


    def _create_single_metric_chart(self, df: pd.DataFrame, metric: str, dimension: str):
        """为单个指标创建独立的线图"""
        if metric not in df.columns:
            st.warning(f"数据中缺少指标: {metric}")
            return

        # 准备数据
        chart_df = df.copy()

        # 处理日期信息
        if hasattr(chart_df.index, 'to_datetime'):
            # DatetimeIndex情况
            chart_df = chart_df.sort_index()
            x_data = chart_df.index
            y_data = chart_df[metric]
        elif '日期' in chart_df.columns:
            # 日期列情况
            chart_df['日期'] = pd.to_datetime(chart_df['日期'], errors='coerce')
            chart_df = chart_df.dropna(subset=['日期'])
            if isinstance(chart_df, pd.DataFrame):
                chart_df = chart_df.sort_values(by='日期')
            x_data = chart_df['日期']
            y_data = chart_df[metric]
        else:
            st.warning(f"无法处理图表数据，缺少日期信息")
            return

        # 过滤掉空值和零值
        valid_mask = pd.notna(y_data) & (y_data != 0)
        if not valid_mask.any():
            st.warning(f"指标 {metric} 没有有效数据")
            return

        x_valid = x_data[valid_mask]
        y_valid = y_data[valid_mask]

        # 创建单指标线图
        import plotly.graph_objects as go
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=x_valid,
            y=y_valid,
            mode='lines+markers',
            name=metric,
            line=dict(color='#FFD700', width=3),
            marker=dict(size=6)
        ))

        # 设置图表样式
        fig.update_layout(
            title=dict(text=f"{metric}趋势分析", x=0.5, font=dict(size=16)),
            xaxis_title="时间",
            yaxis_title=metric,
            template="plotly_dark",
            height=350,
            margin=dict(l=60, r=40, t=60, b=60),
            showlegend=False,
            hovermode='x unified'
        )

        # X轴格式化
        fig.update_xaxes(
            title_text="时间",
            showgrid=True,
            gridcolor='rgba(128, 128, 128, 0.2)'
        )

        # Y轴格式化
        fig.update_yaxes(
            title_text=metric,
            showgrid=True,
            gridcolor='rgba(128, 128, 128, 0.2)'
        )

        st.plotly_chart(fig, config={"displayModeBar": False}, key=f"{dimension}_{metric}_chart")

        # 显示最新数值
        if len(y_valid) > 0:
            latest_value = y_valid.iloc[-1]
            st.metric(
                label=f"最新 {metric}",
                value=f"{latest_value:.2f}",
                delta=None
            )

# 创建组件实例
financial_analysis_component = FinancialAnalysisComponent()
