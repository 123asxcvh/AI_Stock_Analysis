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
        
        # 财务指标说明字典 - 从 financial_page_templates.py 整合
        self.financial_metric_descriptions = {
            # 盈利能力指标
            "盈利能力": {
                "净资产收益率": {
                    "name": "净资产收益率 (ROE)",
                    "description": "衡量股东权益的投资回报率，反映公司利用自有资本的效率",
                    "calculation": "净利润 / 平均净资产 × 100%",
                    "standard": ">15%优秀，10-15%良好，5-10%一般，<5%较差",
                    "investment_meaning": "ROE越高，说明公司为股东创造价值的能力越强",
                    "icon": "💰",
                    "color": "#22c55e"
                },
                "销售净利率": {
                    "name": "销售净利率",
                    "description": "每元销售收入的净利润，反映公司的盈利效率",
                    "calculation": "净利润 / 营业收入 × 100%",
                    "standard": ">20%优秀，10-20%良好，5-10%一般，<5%较差",
                    "investment_meaning": "净利率越高，说明公司控制成本的能力越强",
                    "icon": "📊",
                    "color": "#3b82f6"
                },
                "销售毛利率": {
                    "name": "销售毛利率",
                    "description": "每元销售收入的毛利润，反映产品的竞争力和定价能力",
                    "calculation": "(营业收入 - 营业成本) / 营业收入 × 100%",
                    "standard": ">40%优秀，20-40%良好，10-20%一般，<10%较差",
                    "investment_meaning": "毛利率越高，说明产品越有竞争力，议价能力越强",
                    "icon": "🏭",
                    "color": "#f59e0b"
                },
                "ROA": {
                    "name": "总资产收益率 (ROA)",
                    "description": "衡量公司利用总资产创造利润的能力",
                    "calculation": "净利润 / 平均总资产 × 100%",
                    "standard": ">10%优秀，5-10%良好，2-5%一般，<2%较差",
                    "investment_meaning": "ROA越高，说明公司资产利用效率越高",
                    "icon": "📈",
                    "color": "#10b981"
                }
            },

            # 偿债能力指标
            "偿债能力": {
                "流动比率": {
                    "name": "流动比率",
                    "description": "流动资产与流动负债的比值，衡量短期偿债能力",
                    "calculation": "流动资产 / 流动负债",
                    "standard": ">2优秀，1.5-2良好，1-1.5一般，<1较差",
                    "investment_meaning": "流动比率越高，短期偿债能力越强，但过高可能影响资金使用效率",
                    "icon": "🏦",
                    "color": "#22c55e"
                },
                "速动比率": {
                    "name": "速动比率",
                    "description": "速动资产与流动负债的比值，更严格的短期偿债能力指标",
                    "calculation": "(流动资产 - 存货) / 流动负债",
                    "standard": ">1优秀，0.8-1良好，0.5-0.8一般，<0.5较差",
                    "investment_meaning": "速动比率越高，短期偿债能力越强，排除存货变现的不确定性",
                    "icon": "⚡",
                    "color": "#3b82f6"
                },
                "资产负债率": {
                    "name": "资产负债率",
                    "description": "负债占总资产的比例，反映财务杠杆水平",
                    "calculation": "负债总额 / 资产总额 × 100%",
                    "standard": "<40%优秀，40-60%良好，60-80%一般，>80%较差",
                    "investment_meaning": "资产负债率过高增加财务风险，过低可能影响资金使用效率",
                    "icon": "⚖️",
                    "color": "#f59e0b"
                },
                "产权比率": {
                    "name": "产权比率",
                    "description": "负债总额与所有者权益的比值，反映财务杠杆水平",
                    "calculation": "负债总额 / 所有者权益",
                    "standard": "<1优秀，1-2良好，2-3一般，>3较差",
                    "investment_meaning": "产权比率过高说明公司过度依赖债务融资，财务风险较大",
                    "icon": "🏗️",
                    "color": "#ef4444"
                }
            },

            # 营运能力指标
            "营运能力": {
                "营业周期": {
                    "name": "营业周期",
                    "description": "从采购到回收现金的完整周期，反映营运效率",
                    "calculation": "存货周转天数 + 应收账款周转天数",
                    "standard": "<60天优秀，60-120天良好，120-180天一般，>180天较差",
                    "investment_meaning": "营业周期越短，营运效率越高，资金周转越快",
                    "icon": "⏱️",
                    "color": "#22c55e"
                },
                "存货周转率": {
                    "name": "存货周转率",
                    "description": "存货周转速度，反映存货管理效率",
                    "calculation": "营业成本 / 平均存货",
                    "standard": ">8次优秀，4-8次良好，2-4次一般，<2次较差",
                    "investment_meaning": "周转率越高，存货管理越好，资金占用越少",
                    "icon": "📦",
                    "color": "#3b82f6"
                },
                "存货周转天数": {
                    "name": "存货周转天数",
                    "description": "存货周转一次需要的天数，越少越好",
                    "calculation": "365 / 存货周转率",
                    "standard": "<45天优秀，45-90天良好，90-180天一般，>180天较差",
                    "investment_meaning": "周转天数越少，存货积压越少，资金效率越高",
                    "icon": "📅",
                    "color": "#f59e0b"
                },
                "应收账款周转天数": {
                    "name": "应收账款周转天数",
                    "description": "应收账款回收需要的天数，反映回款效率",
                    "calculation": "365 / 应收账款周转率",
                    "standard": "<30天优秀，30-60天良好，60-90天一般，>90天较差",
                    "investment_meaning": "周转天数越少，回款越快，现金流越好",
                    "icon": "💳",
                    "color": "#10b981"
                }
            },

            # 成长能力指标
            "成长能力": {
                "净利润同比增长率": {
                    "name": "净利润同比增长率",
                    "description": "净利润相对于上年同期的增长幅度",
                    "calculation": "(本期净利润 - 上年同期净利润) / 上年同期净利润 × 100%",
                    "standard": ">20%优秀，10-20%良好，0-10%一般，<0%较差",
                    "investment_meaning": "增长率越高，公司成长性越好，但需关注可持续性",
                    "icon": "📈",
                    "color": "#22c55e"
                },
                "营业总收入同比增长率": {
                    "name": "营业总收入同比增长率",
                    "description": "营业收入相对于上年同期的增长幅度",
                    "calculation": "(本期营业收入 - 上年同期营业收入) / 上年同期营业收入 × 100%",
                    "standard": ">15%优秀，8-15%良好，0-8%一般，<0%较差",
                    "investment_meaning": "收入增长是公司发展的基础，但需关注增长质量",
                    "icon": "💰",
                    "color": "#3b82f6"
                },
                "总资产增长率": {
                    "name": "总资产增长率",
                    "description": "总资产相对于上年同期的增长幅度",
                    "calculation": "(本期总资产 - 上年同期总资产) / 上年同期总资产 × 100%",
                    "standard": ">10%优秀，5-10%良好，0-5%一般，<0%较差",
                    "investment_meaning": "资产增长反映公司规模扩张，但需关注增长效率",
                    "icon": "🏢",
                    "color": "#f59e0b"
                }
            },

            # 估值指标
            "估值指标": {
                "PE(TTM)": {
                    "name": "市盈率(TTM)",
                    "description": "股价与过去12个月每股收益的比值",
                    "calculation": "股价 / 每股收益(TTM)",
                    "standard": "<15低估，15-25合理，25-40偏高，>40高估",
                    "investment_meaning": "PE越低，投资价值越高，但需结合成长性判断",
                    "icon": "📊",
                    "color": "#22c55e"
                },
                "市净率": {
                    "name": "市净率(PB)",
                    "description": "股价与每股净资产的比值",
                    "calculation": "股价 / 每股净资产",
                    "standard": "<1低估，1-2合理，2-3偏高，>3高估",
                    "investment_meaning": "PB越低，投资价值越高，适合价值投资",
                    "icon": "🏦",
                    "color": "#3b82f6"
                },
                "市销率": {
                    "name": "市销率(PS)",
                    "description": "股价与每股销售收入的比值",
                    "calculation": "股价 / 每股销售收入",
                    "standard": "<1低估，1-3合理，3-5偏高，>5高估",
                    "investment_meaning": "PS越低，投资价值越高，适合成长股估值",
                    "icon": "💰",
                    "color": "#f59e0b"
                },
                "PEG值": {
                    "name": "PEG比率",
                    "description": "市盈率与盈利增长率的比值，衡量成长性估值",
                    "calculation": "PE / 盈利增长率",
                    "standard": "<1低估，1-1.5合理，1.5-2偏高，>2高估",
                    "investment_meaning": "PEG越低，成长性投资价值越高",
                    "icon": "📈",
                    "color": "#10b981"
                }
            }
        }

    def _create_generic_pie_chart(self, data: dict, items: dict, title: str, total_key: str = None):
        """通用的饼图创建方法 - 使用templates中的方法"""
        # 使用chart_templates中的方法
        fig = self.ui_manager.financial_pie(data, title, show_legend=False)
        if fig:
            st.plotly_chart(fig, use_container_width=True, key="generic_pie_chart")
        else:
            st.info(f"暂无{title}数据")

    def _create_generic_bar_chart(self, data: dict, items: dict, title: str, x_label: str = "类型"):
        """通用的柱状图创建方法 - 使用templates中的方法"""
        # 使用chart_templates中的方法
        fig = self.ui_manager.bar(pd.DataFrame(list(items.items()), columns=[x_label, "数值"]), title)
        if fig:
            st.plotly_chart(fig, use_container_width=True, key="generic_bar_chart")
        else:
            st.info(f"暂无{title}数据")

    # ========== 从 financial_page_templates.py 整合的方法 ==========
    
    def display_trend_cards(self, trend_analysis: dict):
        """显示统一的趋势分析信息卡片 - 使用 core_template 中的方法"""
        self.ui_manager.display_trend_cards(trend_analysis)
        
    
    
    
    def _analyze_dimension_trends(self, df: pd.DataFrame, metrics: List[str], dimension: str) -> dict:
        """分析财务指标趋势，生成趋势卡片数据 - 使用 core_template 中的方法"""
        return self.ui_manager.analyze_dimension_trends(df, metrics, dimension)
    
    
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
    
    def filter_annual_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """过滤出每年最后日期的年报数据"""
        if df is None or df.empty:
            return df

        df = df.copy()

        # 处理日期索引
        if not hasattr(df.index, 'year'):
            return df

        try:
            # 按年分组，取每年最后一天的数据
            annual_data = []
            for _, year_group in df.groupby(df.index.year):
                if not year_group.empty:
                    # 获取该年的最后一天数据
                    latest_date = year_group.index.max()
                    latest_row = year_group.loc[latest_date:latest_date]
                    if not latest_row.empty:
                        annual_data.append(latest_row.iloc[0])

            if annual_data:
                result_df = pd.DataFrame(annual_data)
                result_df.index = pd.to_datetime([row.name for row in annual_data])
                return result_df.sort_index()
            else:
                return pd.DataFrame()

        except Exception:
            # 如果智能过滤失败，回退到12月31日过滤
            return self._filter_data_by_date(df, (12, 31))

    def filter_semi_annual_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """过滤出0630和1231的半年度数据"""
        return self._filter_data_by_date(df, [(6, 30), (12, 31)])

    def _filter_data_by_date(self, df: pd.DataFrame, month_day_tuples) -> pd.DataFrame:
        """通用日期过滤方法"""
        import pandas as pd

        if df is None or df.empty:
            return df

        df = df.copy()

        # 统一处理month_day_tuples参数
        if isinstance(month_day_tuples, int):
            # 单个month
            month_day_tuples = [(month_day_tuples, 31)] if month_day_tuples != 6 else [(month_day_tuples, 30)]
        elif isinstance(month_day_tuples, tuple) and len(month_day_tuples) == 2:
            # 单个(month, day)元组
            month_day_tuples = [month_day_tuples]

        # 获取日期列
        date_col = "日期" if "日期" in df.columns else None

        if date_col:
            df[date_col] = pd.to_datetime(df[date_col])
            mask = self._create_date_mask(df[date_col], month_day_tuples)
            filtered_df = df[mask].reset_index(drop=True)
            return filtered_df.sort_values(date_col)
        else:
            # 处理DatetimeIndex
            if not hasattr(df.index, 'to_datetime'):
                return df

            date_series = df.index
            mask = self._create_date_mask(date_series, month_day_tuples)
            return df[mask].sort_index()

    def _create_date_mask(self, date_series, month_day_tuples):
        """创建日期过滤掩码"""
        mask = pd.Series(False, index=date_series.index)

        for month, day in month_day_tuples:
            condition_mask = (date_series.dt.month == month) & (date_series.dt.day == day)
            mask = mask | condition_mask

        return mask

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
            df = df.dropna(subset=["日期"]).sort_values("日期")
        # DatetimeIndex不需要处理

        # 固定使用季度视图（移除报告期切换控件）
        if not df.empty:
            self.ui_manager.section_header("📅 数据时间范围", level=4)

            # 显示数据时间范围信息 - 支持DatetimeIndex和日期列
            if "日期" in df.columns:
                min_date = pd.to_datetime(df["日期"]).min().date()
                max_date = pd.to_datetime(df["日期"]).max().date()
            else:
                # 使用DatetimeIndex
                min_date = df.index.min().date()
                max_date = df.index.max().date()
            total_periods = len(df)

            # 计算实际年数
            years_span = (max_date - min_date).days / 365.25
            actual_years = int(years_span) + 1

            st.markdown(
                f"""
            <div style='background-color: rgba(255, 215, 0, 0.1); padding: 10px; border-radius: 5px; margin: 10px 0;'>
                <span style='color: #FFD700; font-weight: bold;'>📊 数据时间范围：</span>
                {min_date} 至 {max_date}
                <span style='color: #888;'>（共 {total_periods} 个数据点，约 {actual_years} 年）</span>
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
            df_sorted = df_sorted.dropna(subset=['日期']).sort_values('日期')

        # 确保数据不为空且有指标
        available_metrics = [m for m in metrics if m in df_sorted.columns]
        if not available_metrics:
            st.info(f"暂无{analysis_type}数据")
            return

        # 创建趋势卡片 - 使用同比对比
        self._create_trend_cards(df_sorted, available_metrics, icon, analysis_type)

        # 为每个指标创建独立的趋势图
        for i, metric in enumerate(available_metrics):
            st.markdown(f"#### 📈 {metric} 趋势分析")

            # 为单个指标创建趋势图
            fig = self.ui_manager.create_financial_trend_chart(
                df_sorted,
                [metric],  # 只传一个指标
                title=f"{metric} 趋势分析",
                stock_code=data.get("stock_code", "") if data else ""
            )
            if fig is not None:
                st.plotly_chart(fig, use_container_width=True, key=f"{analysis_type}_trend_{metric}")

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
        try:
            if df.empty or metric not in df.columns:
                return 0.0

            # 确保索引是日期类型
            if not isinstance(df.index, pd.DatetimeIndex):
                df.index = pd.to_datetime(df.index)

            # 获取最新日期
            latest_date = df.index[-1]

            # 计算去年同期日期
            previous_year_date = latest_date.replace(year=latest_date.year - 1)

            # 查找最接近去年同期日期的数据
            time_diff = abs(df.index - previous_year_date)
            closest_idx = time_diff.argmin()

            # 如果时间差超过3个月，返回0
            if time_diff[closest_idx] > pd.Timedelta(days=90):
                return 0.0

            # 返回去年同期值
            yoy_value = df[metric].iloc[closest_idx]
            return float(yoy_value) if pd.notna(yoy_value) else 0.0

        except Exception:
            # 如果无法找到去年同期数据，尝试使用前一个数据点
            try:
                if len(df) > 1:
                    fallback_value = df[metric].iloc[-2]
                    return float(fallback_value) if pd.notna(fallback_value) else 0.0
            except Exception:
                pass
            return 0.0

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
                    st.plotly_chart(fig, use_container_width=True, key="ocf_waterfall_chart")
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
                ("收到其他与投资活动有关的现金", 1),
                ("购建固定资产、无形资产和其他长期资产支付的现金", -1),
                ("投资支付的现金", -1),
                ("支付其他与投资活动有关的现金", -1),
                ("投资活动产生的现金流量净额", None)  # 净额直接使用原值，可能为负
            ]

            for field, multiplier in investing_fields:
                value = latest_data.get(field, 0)
                if pd.notna(value) and value != 0:
                    display_name = field.replace("收回投资收到的现金", "收回投资") \
                                        .replace("取得投资收益收到的现金", "投资收益") \
                                        .replace("处置固定资产、无形资产和其他长期资产收回的现金净额", "处置资产") \
                                        .replace("收到其他与投资活动有关的现金", "其他投资收入") \
                                        .replace("购建固定资产、无形资产和其他长期资产支付的现金", "购建资产") \
                                        .replace("投资支付的现金", "投资支付") \
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
                    st.plotly_chart(fig, use_container_width=True, key="icf_waterfall_chart")
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
                    st.plotly_chart(fig, use_container_width=True, key="fcf_waterfall_chart")
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
        cashflow_data["年份"] = cashflow_data.index.year

        # 获取所有可用的年份，从2022年开始，包含2025年
        available_years = sorted(cashflow_data["年份"].unique())
        # 过滤从2022年开始的年份数据
        available_years = [year for year in available_years if year >= 2022]
        cashflow_data = cashflow_data[cashflow_data["年份"].isin(available_years)]

        # 确保年份列是整数格式，用于x轴标签
        cashflow_data["年份"] = cashflow_data["年份"].astype(int)

        # 按年份排序以确保正确的顺序（2022->2023->2024->2025...）
        cashflow_data = cashflow_data.sort_values('年份')
        
        if cashflow_data.empty:
            st.warning("暂无现金流量数据")
            return

        # 使用core_templates中的单位转换方法
        all_values = []
        for metric, _ in available_metrics:
            if metric in cashflow_data.columns:
                all_values.extend(cashflow_data[metric].dropna().tolist())
        
        unit = self.ui_manager.get_appropriate_unit(all_values)
        if unit == "亿元":
            factor = 1e8
            unit_label = "亿"
        elif unit == "万元":
            factor = 1e4
            unit_label = "万"
        else:
            factor = 1
            unit_label = "元"
            
        # 将数据转换为合适的单位
        for metric, _ in available_metrics:
            if metric in cashflow_data.columns:
                cashflow_data[metric] = cashflow_data[metric] / factor

        # 使用统一的图表布局模板创建包含三个指标的图表
        metric_names = [metric for metric, _ in available_metrics]
        display_names = [name for _, name in available_metrics]
        
        # 重命名列以匹配显示名称
        rename_dict = dict(zip(metric_names, display_names))
        chart_df = cashflow_data.rename(columns=rename_dict)

        fig = self.ui_manager.line(
            df=chart_df,
            x_col="年份",
            y_cols=display_names,
            title="三大现金流趋势对比",
            x_title="年份",
            y_title=f"现金流金额({unit_label.replace('元', '')})",
            x_mode='category'  # 使用分类模式确保年份正确显示
        )
        if fig:
            st.plotly_chart(fig, use_container_width=True, key="cashflow_trend_chart")
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
        self.ui_manager.section_header("📊 资产结构", level=5)

        # 创建资产构成的百分比堆叠图（包含历史趋势）
        asset_trend_df = annual_df[['非流动资产合计', '流动资产合计']].copy()
        asset_trend_df['年份'] = annual_df.index.year

        # 清理和重命名列
        asset_trend_df = asset_trend_df.rename(columns={
            '流动资产合计': '流动资产',
            '非流动资产合计': '非流动资产'
        })

        # 显示百分比堆叠图
        fig_asset_percent = self.ui_manager.percent_stacked_bar(
            asset_trend_df,
            title="资产构成百分比趋势（流动资产 + 非流动资产 = 100%）",
            x_column='年份'
        )

        if fig_asset_percent:
            st.plotly_chart(fig_asset_percent, use_container_width=True, key="asset_percent_stacked_chart")
        else:
            st.info("暂无资产构成趋势数据")

        # 资产数据摘要已在上方显示

        # 显示详细的资产构成分析
        st.markdown("##### 📊 详细资产构成分析")
        col1, col2 = st.columns(2)

        with col1:
            current_asset_data = {}
            for key in ["货币资金", "交易性金融资产", "应收票据及应收账款", "预付款项", "其他应收款", "存货", "一年内到期的非流动资产", "其他流动资产"]:
                if key in latest_data and latest_data[key] > 0:
                    current_asset_data[key] = latest_data[key]
            fig = self.ui_manager.financial_pie(current_asset_data, "流动资产构成", height=400, show_legend=False)
            if fig:
                st.plotly_chart(fig, use_container_width=True, key="current_asset_pie_chart")
            else:
                st.info("暂无流动资产数据")

        with col2:
            non_current_asset_data = {}
            for key in ["可供出售金融资产", "长期股权投资", "固定资产合计", "在建工程合计", "无形资产", "商誉", "长期待摊费用", "递延所得税资产", "其他非流动资产"]:
                if key in latest_data and latest_data[key] > 0:
                    non_current_asset_data[key] = latest_data[key]
            fig = self.ui_manager.financial_pie(non_current_asset_data, "非流动资产构成", height=400, show_legend=False)
            if fig:
                st.plotly_chart(fig, use_container_width=True, key="non_current_asset_pie_chart")
            else:
                st.info("暂无非流动资产数据")

        st.markdown("---")

        # --- 负债结构 ---
        self.ui_manager.section_header("💳 负债结构", level=5)

        # 主要负债构成百分比趋势图（先非流动再流动）
        liability_trend_df = annual_df[['非流动负债合计', '流动负债合计']].copy()
        liability_trend_df['年份'] = annual_df.index.year
        liability_trend_df = liability_trend_df.rename(columns={
            '非流动负债合计': '非流动负债',
            '流动负债合计': '流动负债'
        })

        fig_liability_trend = self.ui_manager.percent_stacked_bar(
            liability_trend_df,
            "负债构成百分比趋势（流动负债 + 非流动负债 = 100%）",
            x_column='年份'
        )
        if fig_liability_trend:
            st.plotly_chart(fig_liability_trend, use_container_width=True, key="liability_trend_percent_stacked_chart")

        # 详细负债分解
        st.markdown("##### 📋 详细负债构成")
        col1, col2 = st.columns([0.5, 0.5])

        with col1:
            current_liability_data = {}
            for key in ["短期借款", "应付票据及应付账款", "预收款项", "合同负债", "应付职工薪酬", "应交税费", "其他应付款", "一年内到期的非流动负债", "其他流动负债"]:
                if key in latest_data and latest_data[key] > 0:
                    current_liability_data[key] = latest_data[key]
            fig = self.ui_manager.financial_pie(current_liability_data, "流动负债构成", height=400, show_legend=False)
            if fig:
                st.plotly_chart(fig, use_container_width=True, key="current_liability_pie_chart")
            else:
                st.info("暂无流动负债数据")

        with col2:
            non_current_liability_data = {}
            for key in ["长期借款", "应付债券", "长期应付款合计", "递延所得税负债", "其他非流动负债"]:
                if key in latest_data and latest_data[key] > 0:
                    non_current_liability_data[key] = latest_data[key]
            fig = self.ui_manager.financial_pie(non_current_liability_data, "非流动负债构成", height=400, show_legend=False)
            if fig:
                st.plotly_chart(fig, use_container_width=True, key="non_current_liability_pie_chart")
            else:
                st.info("暂无非流动负债数据")

        st.markdown("---")

        # --- 权益结构 ---
        self.ui_manager.section_header("🏛️ 权益结构", level=5)
        col1, col2 = st.columns(2)

        with col1:
            equity_data = {}
            for key in ["实收资本（或股本）", "资本公积", "减：库存股", "其他综合收益", "盈余公积", "未分配利润", "少数股东权益"]:
                if key in latest_data and latest_data[key] > 0:
                    equity_data[key] = latest_data[key]
            fig = self.ui_manager.financial_pie(equity_data, "所有者权益构成", height=400, show_legend=False)
            if fig:
                st.plotly_chart(fig, use_container_width=True, key="equity_pie_chart")
            else:
                st.info("暂无所有者权益数据")

        with col2:
            shareholder_equity_data = {}
            for key in ["归属于母公司所有者权益合计", "少数股东权益"]:
                if key in latest_data and latest_data[key] > 0:
                    shareholder_equity_data[key] = latest_data[key]
            fig = self.ui_manager.financial_pie(shareholder_equity_data, "股东权益构成", height=400, show_legend=False)
            if fig:
                st.plotly_chart(fig, use_container_width=True, key="shareholder_equity_pie_chart")
            else:
                st.info("暂无股东权益数据")

        st.markdown("---")

        # --- 资产负债表比重分析表格 ---
        self.ui_manager.section_header("📊 资产负债表比重分析", level=5)
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

        # 临时调试：检查latest_data的内容
        print(f"调试：latest_data中的一、营业总收入值: {latest_data.get('一、营业总收入', 'NOT FOUND')}")
        print(f"调试：latest_data中的营业总收入值: {latest_data.get('营业总收入', 'NOT FOUND')}")
        print(f"调试：latest_data类型: {type(latest_data)}")
        print(f"调试：latest_data前10个键: {list(latest_data.keys())[:10]}")

        # 左边：收入成本结构瀑布图，右边：成本构成饼图
        col1, col2 = st.columns([1, 1])

        with col1:
            # 收入成本结构瀑布图
            fig = self.ui_manager.revenue_cost_waterfall(latest_data, "收入成本结构", height=500)
            if fig:
                st.plotly_chart(fig, use_container_width=True, key="revenue_cost_waterfall_chart")
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
                        try:
                            revenue_value = float(latest_data[field])
                            if revenue_value != 0:
                                basic_data.append(("营业总收入", revenue_value))
                                break
                        except (ValueError, TypeError):
                            continue

                cost_value = 0
                for field in cost_fields:
                    if field in latest_data and latest_data[field] is not None:
                        try:
                            cost_value = float(latest_data[field])
                            if cost_value != 0:
                                basic_data.append(("营业成本", cost_value))
                                break
                        except (ValueError, TypeError):
                            continue

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
                                try:
                                    value = float(latest_data[field])
                                    if value != 0:
                                        basic_data.append((label, value))
                                        break
                                except (ValueError, TypeError):
                                    continue

                if basic_data:
                    df_basic = pd.DataFrame(basic_data, columns=["项目", "金额"])
                    st.dataframe(df_basic, use_container_width=True, hide_index=True)
                else:
                    st.warning("暂无可用的利润表数据")

        with col2:
            # 成本费用结构饼图 - 以营业成本为主，显示各项费用占比
            # 获取营业成本作为主要参考
            operating_cost_variants = ["其中：营业成本", "营业成本"]
            operating_cost = 0
            for variant in operating_cost_variants:
                if variant in latest_data and latest_data[variant] is not None:
                    try:
                        operating_cost = float(latest_data[variant])
                        if operating_cost != 0:
                            break
                    except (ValueError, TypeError):
                        continue

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
                    st.plotly_chart(fig, use_container_width=True, key="cost_pie_chart")
                else:
                    st.info("暂无成本费用数据")
            else:
                st.info("暂无营业成本数据，无法生成成本构成饼图")

        st.markdown("---")

        # --- 利润表比重分析表格 ---
        self.ui_manager.section_header("📊 利润表比重分析", level=5)
        self._display_income_statement_ratio_table(annual_df)

    def _get_year_end_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """获取每年最后一天的数据"""
        if df.empty:
            return df

        try:
            # 确保索引是datetime类型
            if not hasattr(df.index, 'year'):
                return df

            # 按年份分组，取每年最后一天
            year_end_data = []
            for year, group in df.groupby(df.index.year):
                if not group.empty:
                    # 取该年最后一天的数据
                    last_day = group.index.max()
                    year_end_data.append(group.loc[[last_day]])

            if year_end_data:
                result = pd.concat(year_end_data, ignore_index=False)
                result = result.sort_index()

                # 添加年份列
                result['年份'] = result.index.year.astype(int)

                return result
            else:
                return pd.DataFrame()

        except Exception as e:
            print(f"筛选年末数据失败: {e}")
            return df

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
                self._display_income_statement_structure(data)

            with structure_tabs[2]:
                self.display_cash_flow_structure(data)
        
        with main_tabs[2]:
            # 图表分析 - 财务可视化方案
            self.display_financial_chart_analysis(data)
        
        # 显示AI分析报告
        self._display_ai_analysis_report(data)

    def _create_cashflow_timeline_chart(self, historical_patterns: list):
        """创建现金流演变时间线图表"""
        if not historical_patterns:
            return
            
        # 显示现金流趋势对比
        # 创建现金流趋势对比图
        fig = self.ui_manager.line(pd.DataFrame(historical_patterns), "现金流趋势对比")
        if fig:
            st.plotly_chart(fig, use_container_width=True, key="cashflow_trends_comparison")
    
    def _display_ai_analysis_report(self, data: Dict[str, Any]):
        """显示AI分析报告 - 使用4个tab显示"""
        self.ui_manager.section_header("AI财务分析报告", "🤖")

        # 导入AI报告显示工具
        from src.web.utils import ai_report_manager

        # 获取股票代码
        stock_code = data.get("stock_code", "未知")

        # 定义要显示的4个财务分析报告
        financial_reports = {
            "📊 资产负债表分析": "balance_sheet_analysis.md",
            "💰 利润表分析": "income_statement_analysis.md",
            "💸 现金流量表分析": "cash_flow_analysis.md",
            "📈 财务指标分析": "financial_indicators_analysis.md"
        }

        try:
            # 加载AI报告
            reports = ai_report_manager.load_reports(stock_code, "stock")

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

        except Exception as e:
            st.error(f"加载财务分析AI报告时出错: {str(e)}")
            st.info("🤖 财务分析AI报告暂时无法加载，请稍后重试")

    def display_financial_chart_analysis(self, data: Dict[str, Any]):
        """显示财务图表分析 - 基于财务可视化方案"""
        st.markdown("### 📊 财务图表分析")
        st.markdown("基于财务可视化方案v1，提供结构+趋势双视角分析")
        
        # 获取财务数据
        balance_sheet = data.get('balance_sheet', pd.DataFrame())
        income_statement = data.get('income_statement', pd.DataFrame())
        cash_flow_statement = data.get('cash_flow_statement', pd.DataFrame())
        
        
        if balance_sheet.empty and income_statement.empty and cash_flow_statement.empty:
            st.warning("暂无财务数据，无法进行图表分析")
            return
        
        # 创建四个独立的标签页
        chart_tabs = st.tabs(["📊 资产负债表", "💰 利润表", "💸 现金流量表", "📈 财务指标对比"])
        
        with chart_tabs[0]:
            st.markdown("#### 📊 资产负债表趋势分析")
            if not balance_sheet.empty:
                self._display_balance_sheet_trend_analysis(balance_sheet, cash_flow_statement, data)
            else:
                st.warning("暂无资产负债表数据")
        
        with chart_tabs[1]:
            st.markdown("#### 💰 利润表趋势分析")
            if not income_statement.empty:
                self._display_income_statement_trend_analysis(income_statement)
            else:
                st.warning("暂无利润表数据")
        
        with chart_tabs[2]:
            st.markdown("#### 💸 现金流量表趋势分析")
            if not cash_flow_statement.empty:
                self._display_cash_flow_trend_analysis(cash_flow_statement)
            else:
                st.warning("暂无现金流量表数据")
        
        with chart_tabs[3]:
            st.markdown("#### 📈 财务指标对比分析")
            if not income_statement.empty:
                self._display_financial_ratios_analysis(income_statement)
            else:
                st.warning("暂无利润表数据")

    def _display_balance_sheet_trend_analysis(self, df: pd.DataFrame, cash_flow_df: pd.DataFrame = None, data: Dict[str, Any] = None):
        """资产负债表趋势分析"""

        # 数据预处理 - 数据已通过数据加载器设置日期索引
        df = df.copy()
        df['年份'] = df.index.year.astype(int)
        
        # 资产结构和负债结构的详细分析在其他方法中显示
        
        # 2. 固定资产与总资产趋势对比
        # 准备数据：固定资产合计+在建工程合计 vs 资产合计
        annual_df = self._get_year_end_data(df)
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
            st.plotly_chart(fig_fixed, use_container_width=True, key="balance_sheet_fixed_assets_analysis")

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
                try:
                    merged_cash_data = merged_cash_data.merge(
                        cash_flow_annual_df[['年份', cash_flow_col]],
                        on='年份',
                        how='left'
                    )
                except Exception as e:
                    print(f"合并现金流量数据失败: {e}")
                    st.warning("⚠️ 合并现金流量数据失败，仅显示货币资金")
                    cash_flow_col = None

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
            st.plotly_chart(fig_cash_trend, use_container_width=True, key="cash_trend_chart")
        
        # 6. 净利润与经营净现金流对比（柱状图）
        if cash_flow_df is not None and not cash_flow_df.empty:
            # 处理现金流量表数据
            cash_flow_df = cash_flow_df.copy()
            cash_flow_df['年份'] = cash_flow_df.index.year.astype(int)
            cash_flow_annual_df = self._get_year_end_data(cash_flow_df)

            # 合并利润表和现金流量表数据
            # 首先需要获取利润表数据
            income_df = data.get('income_statement', pd.DataFrame())
            if not income_df.empty:
                income_df = income_df.copy()
                # 转换日期列为datetime类型并添加年份列
                income_df['日期'] = pd.to_datetime(income_df['日期'], errors='coerce')
                income_df = income_df.dropna(subset=['日期'])  # 删除无效日期
                income_df['年份'] = income_df['日期'].dt.year.astype(int)

                # 按年份分组，取每年最后一天的数据
                income_annual_data = []
                for year, group in income_df.groupby('年份'):
                    if not group.empty:
                        # 取该年最后一天的数据
                        last_day_idx = group['日期'].idxmax()
                        year_end_data = group.loc[last_day_idx]
                        income_annual_data.append(year_end_data)

                if income_annual_data:
                    income_annual_df = pd.concat(income_annual_data, ignore_index=True)
                    income_annual_df = income_annual_df.sort_values('年份')
                else:
                    income_annual_df = pd.DataFrame()

                # 查找经营现金流列（可能有不同的列名）
                cash_flow_col = None
                possible_cash_flow_names = ['经营活动产生的现金流量净额']

                for col_name in possible_cash_flow_names:
                    if not cash_flow_annual_df.empty and col_name in cash_flow_annual_df.columns:
                        cash_flow_col = col_name
                        break

                if cash_flow_col and not cash_flow_annual_df.empty and '年份' in cash_flow_annual_df.columns and cash_flow_col in cash_flow_annual_df.columns:
                    # 合并利润表和现金流量表数据
                    try:
                        merged_df = income_annual_df.merge(
                            cash_flow_annual_df[['年份', cash_flow_col]],
                            on='年份',
                            how='left'
                        )
                    except Exception as e:
                        print(f"合并经营现金流数据失败: {e}")
                        st.warning("⚠️ 合并经营现金流数据失败，无法生成净利润与经营现金流对比图")
                        merged_df = None
                else:
                    # 如果没有找到经营现金流列，显示警告
                    st.warning("⚠️ 现金流量表中未找到经营活动产生的现金流量净额数据")
                    merged_df = None

                # 准备柱状图数据：净利润与经营净现金流对比
                st.markdown("#### 净利润与经营净现金流对比")

                # 只有在成功合并数据时才继续处理
                if merged_df is not None:
                    # 检查需要的列是否存在
                    required_cols = ['年份']
                    net_profit_col = None

                    # 查找净利润列
                    possible_net_profit_names = ['五、净利润', '净利润']
                    for col_name in possible_net_profit_names:
                        if col_name in merged_df.columns:
                            net_profit_col = col_name
                            required_cols.append(col_name)
                            break

                    # 使用之前找到的经营现金流列
                    if cash_flow_col:
                        required_cols.append(cash_flow_col)

                # 只有在成功合并数据且找到所需列时才创建图表
                if merged_df is not None and net_profit_col and cash_flow_col:
                    # 创建对比柱状图数据
                    chart_data = merged_df[['年份', net_profit_col, cash_flow_col]].copy()
                    chart_data = chart_data.rename(columns={
                        net_profit_col: '净利润',
                        cash_flow_col: '经营活动产生的现金流量净额'
                    })

                    # 创建柱状图配置
                    profit_cash_series = {
                        "净利润": "净利润",
                        "经营活动产生的现金流量净额": "经营活动产生的现金流量净额"
                    }

                    # 创建柱状图
                    fig_profit_cash = self.ui_manager.grouped_bar_years(
                        chart_data, profit_cash_series, "净利润与经营净现金流对比"
                    )

                    if fig_profit_cash:
                        st.plotly_chart(fig_profit_cash, use_container_width=True, key="profit_cash_flow_chart")
                elif merged_df is None:
                    st.warning("⚠️ 无法获取现金流数据，无法生成净利润与经营现金流对比图")
                else:
                    st.warning("⚠️ 暂无净利润或经营现金流数据")
            else:
                st.info("暂无利润表数据，无法显示净利润与经营现金流对比图")
        else:
            st.info("暂无现金流量表数据，无法显示净利润与经营现金流对比图")
        
        # 7. 存货双轴分析（存货 + 存货周转率）
        # 确保 annual_df 有 '年份' 列
        if '年份' not in annual_df.columns:
            annual_df['年份'] = annual_df.index.year.astype(int)

        # 存货双轴分析：存货（柱状图）+ 存货周转率（折线图）
        if '存货' in annual_df.columns and not annual_df.empty:
            try:
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
                        try:
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
                                st.plotly_chart(fig_inventory, use_container_width=True, key="inventory_dual_axis_chart")
                            else:
                                st.warning("⚠️ 存货双轴图表创建失败")
                                inventory_turnover_available = False

                        except Exception as e:
                            print(f"合并财务指标数据失败: {e}")
                            st.warning("⚠️ 合并财务指标数据失败")
                            inventory_turnover_available = False

                # 如果没有周转率数据，尝试计算
                if not inventory_turnover_available:
                    st.info("📊 未找到存货周转率数据，尝试从营业成本计算...")

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
                            try:
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
                                    st.plotly_chart(fig_inventory, use_container_width=True, key="inventory_dual_axis_calculated")
                                else:
                                    st.warning("⚠️ 存货双轴图表创建失败")

                            except Exception as e:
                                print(f"计算存货周转率失败: {e}")
                                st.warning("⚠️ 存货周转率计算失败，仅显示存货趋势")
                                # 降级显示简单的存货趋势图
                                fig_inventory = self.ui_manager.line(
                                    inventory_df.set_index('年份'), '存货趋势分析（2022-2024年）'
                                )
                                st.plotly_chart(fig_inventory, use_container_width=True, key="inventory_fallback_chart")
                        else:
                            st.warning("⚠️ 未找到营业成本数据，无法计算存货周转率")
                            # 仅显示存货趋势图
                            fig_inventory = self.ui_manager.line(
                                inventory_df.set_index('年份'), '存货趋势分析（2022-2024年）'
                            )
                            st.plotly_chart(fig_inventory, use_container_width=True, key="inventory_simple_chart")
                    else:
                        st.warning("⚠️ 无利润表数据，无法计算存货周转率")
                        # 仅显示存货趋势图
                        fig_inventory = self.ui_manager.line(
                            inventory_df.set_index('年份'), '存货趋势分析（2022-2024年）'
                        )
                        st.plotly_chart(fig_inventory, use_container_width=True, key="inventory_simple_chart2")

            except Exception as e:
                print(f"存货分析失败: {e}")
                st.warning("⚠️ 存货分析出现错误")

        # 8. 流动资产绝对值堆叠面积图
        current_assets_config = {
            '货币资金': '货币资金',
            '交易性金融资产': '交易性金融资产',
            '应收票据及应收账款': '应收账款',
            '预付款项': '预付款项',
            '其他应收款合计': '其他应收款',
            '存货': '存货',
            '一年内到期的非流动资产': '一年内到期资产',
            '其他流动资产': '其他流动资产'
        }
        # 使用堆叠面积图显示流动资产构成
        fig_current_assets = self.ui_manager.area(
            annual_df, current_assets_config, '流动资产绝对值堆叠分析（2022-2024年）',
            (2022, 2024)
        )
        if fig_current_assets:
            st.plotly_chart(fig_current_assets, use_container_width=True, key="current_assets_absolute_chart")
        
        # 9. 非流动资产绝对值堆叠面积图
        non_current_assets_config = {
            '长期股权投资': '长期股权投资',
            '固定资产合计': '固定资产',
            '在建工程合计': '在建工程',
            '无形资产': '无形资产',
            '递延所得税资产': '递延所得税资产',
            '其他非流动资产': '其他非流动资产'
        }
        fig_non_current_assets = self.ui_manager.area(
            annual_df, non_current_assets_config, '非流动资产绝对值堆叠分析（2022-2024年）',
            (2022, 2024)
        )
        if fig_non_current_assets:
            st.plotly_chart(fig_non_current_assets, use_container_width=True, key="non_current_assets_absolute_chart")
        
        # 10. 流动负债绝对值堆叠面积图
        current_liability_config = {
            '短期借款': '短期借款',
            '应付票据及应付账款': '应付账款',
            '预收款项': '预收款项',
            '应付职工薪酬': '应付职工薪酬',
            '应交税费': '应交税费',
            '其他应付款合计': '其他应付款',
            '一年内到期的非流动负债': '一年内到期负债',
            '其他流动负债': '其他流动负债'
        }
        fig_current_liability = self.ui_manager.area(
            annual_df, current_liability_config, '流动负债绝对值堆叠分析（2022-2024年）',
            (2022, 2024)
        )
        if fig_current_liability:
            st.plotly_chart(fig_current_liability, use_container_width=True, key="current_liability_absolute_chart")
        
        # 11. 非流动负债绝对值堆叠面积图
        non_current_liability_config = {
            '长期借款': '长期借款',
            '长期应付款合计': '长期应付款',
            '递延所得税负债': '递延所得税负债'
        }
        fig_non_current_liability = self.ui_manager.area(
            annual_df, non_current_liability_config, '非流动负债绝对值堆叠分析（2022-2024年）',
            (2022, 2024)
        )
        if fig_non_current_liability:
            st.plotly_chart(fig_non_current_liability, use_container_width=True, key="non_current_liability_absolute_chart")

        # 3. 负债结构占比
        liability_columns = ['流动负债合计', '非流动负债合计']
        available_liability_columns = [col for col in liability_columns if col in annual_df.columns]
        if available_liability_columns:
            liability_df = annual_df[available_liability_columns].copy()
            liability_df['年份'] = annual_df.index.year
            liability_df = liability_df.rename(columns={
                '流动负债合计': '流动负债',
                '非流动负债合计': '非流动负债'
            })
            fig_liability_percent = self.ui_manager.percent_stacked_bar(
                liability_df,
                "负债构成占比（流动负债 vs 非流动负债）",
                x_column='年份'
            )
            if fig_liability_percent:
                st.plotly_chart(fig_liability_percent, use_container_width=True, key="liability_percent_stacked_chart")

        
    def _display_income_statement_trend_analysis(self, df: pd.DataFrame):
        """利润表趋势分析"""

        # 数据预处理 - 数据已通过数据加载器设置日期索引
        df = df.copy()
        df['年份'] = df.index.year.astype(int)
        annual_df = self._get_year_end_data(df)
        
        # 1. 收入-成本-毛利趋势
        # 计算毛利（正确方式：营业收入 - 营业成本）
        if '一、营业总收入' in annual_df.columns and ('其中：营业成本' in annual_df.columns or '营业成本' in annual_df.columns):
            cost_col = '其中：营业成本' if '其中：营业成本' in annual_df.columns else '营业成本'
            annual_df['毛利'] = annual_df['一、营业总收入'] - annual_df[cost_col]

        series_revenue = {
            "一、营业总收入": "营业收入",
            "其中：营业成本": "营业成本",
            "毛利": "毛利",
        }
        fig_revenue = self.ui_manager.grouped_bar_years(annual_df, series_revenue, "收入-成本-毛利趋势")
        if fig_revenue:
            st.plotly_chart(fig_revenue, use_container_width=True, key="income_statement_revenue_analysis")
        
        # 2. 费用结构占比
        expense_columns = ['销售费用', '管理费用', '研发费用', '财务费用']
        available_expense_columns = [col for col in expense_columns if col in annual_df.columns]
        if available_expense_columns:
            expenses_df = annual_df[available_expense_columns].copy()
            expenses_df['年份'] = annual_df.index.year
            fig_expenses = self.ui_manager.percent_stacked_bar(expenses_df, "费用结构占比", x_column='年份')
        else:
            fig_expenses = None
        if fig_expenses:
            st.plotly_chart(fig_expenses, use_container_width=True, key="income_statement_expenses_analysis")

    def _display_cash_flow_trend_analysis(self, df: pd.DataFrame):
        """现金流量表趋势分析"""

        # 数据预处理 - 数据已通过数据加载器设置日期索引
        df = df.copy()
        df['年份'] = df.index.year.astype(int)
        annual_df = self._get_year_end_data(df)
        
        # 1. 自由现金流趋势
        # 计算自由现金流 FCF = OCF - CAPEX
        if '经营活动产生的现金流量净额' in annual_df.columns and '购建固定资产、无形资产和其他长期资产支付的现金' in annual_df.columns:
            annual_df['自由现金流'] = annual_df['经营活动产生的现金流量净额'] - annual_df['购建固定资产、无形资产和其他长期资产支付的现金']
            
            # 创建自由现金流折线图
            fig_fcf = self.ui_manager.line(
                annual_df, 
                x_col='年份', 
                y_cols=['自由现金流'], 
                title='自由现金流趋势',
                x_mode='category'
            )
            if fig_fcf:
                st.plotly_chart(fig_fcf, use_container_width=True, key="cashflow_fcf_analysis")
        
        # 2. 现金流三表瀑布
        st.markdown("##### 🌊 现金流三表瀑布")
        # 获取最新年度数据
        latest_year = df['年份'].max()
        latest_data = df[df['年份'] == latest_year].iloc[0]
        
        # 创建现金流瀑布图 - 使用新的专用函数
        fig_waterfall = self.ui_manager.cashflow_analysis_waterfall(latest_data, "现金流分析", height=700)
        if fig_waterfall:
            st.plotly_chart(fig_waterfall, use_container_width=True, key="cashflow_waterfall_analysis")
        
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
                st.plotly_chart(fig_quality, use_container_width=True, key="cashflow_quality_analysis")

    def _display_financial_ratios_analysis(self, df: pd.DataFrame):
        """财务指标对比分析"""
        
        # 数据预处理 - 数据已通过数据加载器设置日期索引
        df = df.copy()
        df['年份'] = df.index.year.astype(int)
        # 使用每年最后一天的数据
        annual_data = self._get_year_end_data(df)
        
        if annual_data.empty:
            st.warning("暂无年度财务数据")
            return
        
        # 按年份排序
        annual_data = annual_data.sort_values('年份')
        
        # 计算财务比率
        
        # 1. 营业毛利率趋势
        if '一、营业总收入' in annual_data.columns and '其中：营业成本' in annual_data.columns:
            # 计算毛利率 = (营业收入 - 营业成本) / 营业收入 * 100
            annual_data['毛利率'] = ((annual_data['一、营业总收入'] - annual_data['其中：营业成本']) / annual_data['一、营业总收入'] * 100)
            
            fig_margin = self.ui_manager.line(
                annual_data,
                x_col='年份',
                y_cols=['毛利率'],
                title='营业毛利率趋势',
                x_mode='category'
            )
            if fig_margin:
                st.plotly_chart(fig_margin, use_container_width=True, key="financial_ratios_margin_analysis")
        
        # 2. 费用率对比分析
        expense_ratios = {}
        
        # 计算各项费用率
        if '一、营业总收入' in annual_data.columns:
            revenue = annual_data['一、营业总收入']
            
            if '销售费用' in annual_data.columns:
                expense_ratios['销售费用率'] = (annual_data['销售费用'] / revenue * 100)
            if '管理费用' in annual_data.columns:
                expense_ratios['管理费用率'] = (annual_data['管理费用'] / revenue * 100)
            if '研发费用' in annual_data.columns:
                expense_ratios['研发费用率'] = (annual_data['研发费用'] / revenue * 100)
            if '财务费用' in annual_data.columns:
                expense_ratios['财务费用率'] = (annual_data['财务费用'] / revenue * 100)
        
        if expense_ratios:
            # 创建费用率对比图
            fig_expenses = self.ui_manager.grouped_bar_years(
                annual_data.assign(**expense_ratios),
                {k: k for k in expense_ratios.keys()},
                "费用率对比分析"
            )
            if fig_expenses:
                st.plotly_chart(fig_expenses, use_container_width=True, key="financial_ratios_expenses_analysis")
        
        # 3. 财务指标对比表
        st.markdown("###### 📋 财务指标对比表")
        
        # 准备对比表数据
        comparison_data = []
        years = sorted(annual_data['年份'].unique())
        
        for year in years:
            year_data = annual_data[annual_data['年份'] == year].iloc[0]
            row_data = {'年份': f"{year}年"}
            
            # 计算各项指标
            if '一、营业总收入' in year_data.index and '其中：营业成本' in year_data.index:
                revenue = year_data['一、营业总收入']
                cost = year_data['其中：营业成本']
                if revenue > 0:
                    row_data['营业毛利率'] = f"{((revenue - cost) / revenue * 100):.2f}%"
            
            if '五、净利润' in year_data.index and '一、营业总收入' in year_data.index:
                net_profit = year_data['五、净利润']
                revenue = year_data['一、营业总收入']
                if revenue > 0:
                    row_data['营业净利率'] = f"{(net_profit / revenue * 100):.2f}%"
            
            if '销售费用' in year_data.index and '一、营业总收入' in year_data.index:
                sales_expense = year_data['销售费用']
                revenue = year_data['一、营业总收入']
                if revenue > 0:
                    row_data['销售费用率'] = f"{(sales_expense / revenue * 100):.2f}%"
            
            if '管理费用' in year_data.index and '一、营业总收入' in year_data.index:
                admin_expense = year_data['管理费用']
                revenue = year_data['一、营业总收入']
                if revenue > 0:
                    row_data['管理费用率'] = f"{(admin_expense / revenue * 100):.2f}%"
            
            if '财务费用' in year_data.index and '一、营业总收入' in year_data.index:
                finance_expense = year_data['财务费用']
                revenue = year_data['一、营业总收入']
                if revenue > 0:
                    row_data['财务费用率'] = f"{(finance_expense / revenue * 100):.2f}%"
            
            if '研发费用' in year_data.index and '一、营业总收入' in year_data.index:
                rd_expense = year_data['研发费用']
                revenue = year_data['一、营业总收入']
                if revenue > 0:
                    row_data['研发费用率'] = f"{(rd_expense / revenue * 100):.2f}%"
            
            comparison_data.append(row_data)
        
        if comparison_data:
            comparison_df = pd.DataFrame(comparison_data)
            st.dataframe(comparison_df, use_container_width=True, hide_index=True)

    def _display_balance_sheet_ratio_table(self, annual_df: pd.DataFrame):
        """显示资产负债表比重分析 - 使用百分比趋势图"""
        if annual_df.empty:
            st.warning("暂无资产负债表数据")
            return

        # 检查必要的数据列 - 支持多种可能的列名
        liability_columns = ["负债合计", "负债总计", "总负债"]
        equity_columns = ["所有者权益合计", "股东权益合计", "归属于母公司所有者权益合计", "净资产总计", "所有者权益(或股东权益)总计"]

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
        liability_equity_df['年份'] = annual_df.index.year

        # 清理和重命名列 - 负债在下方（先），权益在上方（后）
        liability_equity_df = liability_equity_df.rename(columns={
            liability_col: '负债',
            equity_col: '所有者权益'
        })

        # 显示百分比堆叠图
        fig_ratio_percent = self.ui_manager.percent_stacked_bar(
            liability_equity_df,
            title="资产负债构成百分比趋势（负债 + 所有者权益 = 100%）",
            x_column='年份'
        )

        if fig_ratio_percent:
            st.plotly_chart(fig_ratio_percent, use_container_width=True, key="liability_equity_percent_stacked_chart")
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
            df_processed['年份'] = df_processed.index.year

        # 获取总资产和总负债作为分母 - 支持多种可能的列名
        asset_variants = ["*资产总计", "资产总计", "总资产", "资产合计", "负债和所有者权益总计"]
        liability_variants = ["*负债合计", "负债合计", "负债总计", "总负债"]

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
            "*货币资金": "货币资金",
            "货币资金": "货币资金",
            "*交易性金融资产": "交易性金融资产",
            "交易性金融资产": "交易性金融资产",
            "*应收票据及应收账款": "应收票据及应收账款",
            "应收票据及应收账款": "应收票据及应收账款",
            "应收账款": "应收账款",
            "*预付款项": "预付款项",
            "预付款项": "预付款项",
            "*其他应收款": "其他应收款",
            "其他应收款": "其他应收款",
            "其他应收款合计": "其他应收款",
            "*存货": "存货",
            "存货": "存货",
            "*一年内到期的非流动资产": "一年内到期非流动资产",
            "一年内到期的非流动资产": "一年内到期非流动资产",
            "*其他流动资产": "其他流动资产",
            "其他流动资产": "其他流动资产",
            "*流动资产合计": "流动资产合计",
            "流动资产合计": "流动资产合计",

            # 非流动资产
            "*长期股权投资": "长期股权投资",
            "长期股权投资": "长期股权投资",
            "*固定资产合计": "固定资产合计",
            "固定资产合计": "固定资产合计",
            "固定资产": "固定资产",
            "*在建工程合计": "在建工程合计",
            "在建工程合计": "在建工程合计",
            "在建工程": "在建工程",
            "*无形资产": "无形资产",
            "无形资产": "无形资产",
            "*商誉": "商誉",
            "商誉": "商誉",
            "*长期待摊费用": "长期待摊费用",
            "长期待摊费用": "长期待摊费用",
            "*递延所得税资产": "递延所得税资产",
            "递延所得税资产": "递延所得税资产",
            "*其他非流动资产": "其他非流动资产",
            "其他非流动资产": "其他非流动资产",
            "*非流动资产合计": "非流动资产合计",
            "非流动资产合计": "非流动资产合计",

            # 资产总计
            "*资产总计": "资产总计",
            "资产总计": "资产总计"
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
            if "资产总计" not in asset_ratios:
                asset_ratios["资产总计"] = {}
            asset_ratios["资产总计"][year] = 100.00

        if asset_ratios:
            # 定义标准资产顺序 - 总资产在第一行，然后是流动资产和非流动资产
            asset_standard_order = [
                "资产总计",  # 第一行：总资产（100%）
                "流动资产合计",  # 第二行：流动资产占总资产比例
                "非流动资产合计",  # 第三行：非流动资产占总资产比例
                # 然后是详细的资产构成
                "货币资金", "交易性金融资产", "应收票据及应收账款", "预付款项",
                "其他应收款", "存货", "一年内到期非流动资产", "其他流动资产",
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
            def format_value(x):
                if pd.isna(x):
                    return "-"
                else:
                    return f"{x:.2f}%"

            formatted_df = transposed_df.map(format_value)

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

            st.dataframe(formatted_df, use_container_width=True)
        else:
            st.info("暂无资产结构数据")

    def _display_liability_structure_analysis(self, df_processed: pd.DataFrame, liability_col: str):
        """显示负债结构分析 - 以总负债为100%"""

        # 定义负债类项目 - 按标准资产负债表顺序排列
        liability_items = {
            # 流动负债
            "*短期借款": "短期借款",
            "短期借款": "短期借款",
            "*应付票据及应付账款": "应付票据及应付账款",
            "应付票据及应付账款": "应付票据及应付账款",
            "应付账款": "应付账款",
            "*合同负债": "合同负债",
            "合同负债": "合同负债",
            "预收款项": "预收款项",
            "*应付职工薪酬": "应付职工薪酬",
            "应付职工薪酬": "应付职工薪酬",
            "*应交税费": "应交税费",
            "应交税费": "应交税费",
            "*其他应付款": "其他应付款",
            "其他应付款": "其他应付款",
            "其他应付款合计": "其他应付款",
            "*一年内到期的非流动负债": "一年内到期非流动负债",
            "一年内到期的非流动负债": "一年内到期非流动负债",
            "*其他流动负债": "其他流动负债",
            "其他流动负债": "其他流动负债",
            "*流动负债合计": "流动负债合计",
            "流动负债合计": "流动负债合计",

            # 非流动负债
            "*长期借款": "长期借款",
            "长期借款": "长期借款",
            "*应付债券": "应付债券",
            "应付债券": "应付债券",
            "*长期应付款合计": "长期应付款合计",
            "长期应付款合计": "长期应付款合计",
            "*递延所得税负债": "递延所得税负债",
            "递延所得税负债": "递延所得税负债",
            "*其他非流动负债": "其他非流动负债",
            "其他非流动负债": "其他非流动负债",
            "*非流动负债合计": "非流动负债合计",
            "非流动负债合计": "非流动负债合计",

            # 负债总计
            "*负债合计": "负债合计",
            "负债合计": "负债合计",
            "负债总计": "负债合计"
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
                "其他应付款", "一年内到期非流动负债", "其他流动负债",
                # 非流动负债
                "长期借款", "应付债券", "长期应付款合计", "递延所得税负债", "其他非流动负债"
            ]

            # 转换为DataFrame并排序
            transposed_df = pd.DataFrame(liability_ratios).T
            available_items = [item for item in liability_standard_order if item in transposed_df.index]
            other_items = [item for item in transposed_df.index if item not in liability_standard_order]
            final_order = available_items + other_items
            transposed_df = transposed_df.reindex(final_order)
            transposed_df = transposed_df.reindex(sorted(transposed_df.columns), axis=1)

            # 格式化显示
            def format_value(x):
                if pd.isna(x):
                    return "-"
                else:
                    return f"{x:.2f}%"

            formatted_df = transposed_df.map(format_value)

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

            st.dataframe(formatted_df, use_container_width=True)
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
            df_processed['年份'] = df_processed.index.year

        # 获取营业收入作为分母 - 支持多种可能的列名
        revenue_variants = ["一、营业总收入", "营业总收入", "*营业收入", "营业收入", "主营业务收入"]
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
            # 收入类
            "一、营业总收入": "营业总收入",
            "营业总收入": "营业总收入",
            "*营业收入": "营业总收入",
            "营业收入": "营业总收入",

            # 成本费用类
            "营业成本": "营业成本",

            "税金及附加": "税金及附加",
            "营业税金及附加": "税金及附加",

            # 期间费用
            "销售费用": "销售费用",
            "营业费用": "销售费用",

            "管理费用": "管理费用",

            "财务费用": "财务费用",

            "研发费用": "研发费用",
            "开发费用": "研发费用",

            # 利润类
            "毛利": "毛利",

            "营业利润": "营业利润",
            "经营利润": "营业利润",

            "净利润": "净利润",
            "归属于母公司所有者的净利润": "净利润"
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

            # 计算毛利（纯计算方式）
            # 毛利 = 营业收入 - 营业成本
            operating_cost_fields = ["其中：营业成本", "营业成本"]
            operating_cost = 0
            for field in operating_cost_fields:
                if field in row and pd.notna(row[field]):
                    operating_cost = row[field]
                    break

            if operating_cost > 0:
                gross_profit = revenue - operating_cost
                gross_ratio = (gross_profit / revenue) * 100
                if "毛利" not in profit_ratios:
                    profit_ratios["毛利"] = {}
                profit_ratios["毛利"][year] = gross_ratio

            # 计算营业利润（纯计算方式）
            # 营业利润 = 毛利 - 期间费用
            expense_fields = {
                "税金及附加": ["*税金及附加", "税金及附加", "*营业税金及附加", "营业税金及附加"],
                "销售费用": ["*销售费用", "销售费用", "*营业费用", "营业费用"],
                "管理费用": ["*管理费用", "管理费用"],
                "财务费用": ["*财务费用", "财务费用"],
                "研发费用": ["*研发费用", "研发费用", "*开发费用", "开发费用"]
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
            # 定义标准利润表顺序
            standard_order = [
                "营业总收入",
                "营业成本",
                "税金及附加",
                "毛利",
                "销售费用",
                "管理费用",
                "财务费用",
                "研发费用",
                "营业利润",
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
            def format_value(x):
                if pd.isna(x):
                    return "-"
                elif x < 0:
                    return f"{x:.2f}%"
                else:
                    return f"{x:.2f}%"

            formatted_df = transposed_df.map(format_value)

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

            st.dataframe(formatted_df, use_container_width=True)
        else:
            st.info("暂无利润表比重数据")


    def _display_income_statement_structure(self, data: Dict[str, Any]):
        """显示利润表结构分析 - 使用templates中的方法"""
        self.display_income_statement_structure(data)

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
            chart_df = chart_df.dropna(subset=['日期']).sort_values('日期')
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

        st.plotly_chart(fig, use_container_width=True, key=f"{dimension}_{metric}_chart")

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
