#!/usr/bin/env python
"""
股票估值分析页面组件
提供独立的估值数据分析和可视化
整合了 core_templates 的共同参数和图表管理
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from typing import Dict, Any, Optional, List

# 使用统一UI模板管理器
from src.web.templates import ui_template_manager


class StockValuationComponent:
    """股票估值分析组件类"""

    def __init__(self):
        """初始化估值分析组件 - 使用统一UI模板管理器"""
        # 使用统一UI模板管理器
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
        }

        # 估值指标配置 - 根据实际数据列名调整
        self.valuation_metrics = {
            "估值指标": ["市盈率", "市盈率(静)", "市净率", "PEG值", "市现率", "市销率"],
            "市值指标": ["总市值", "流通市值", "总股本", "流通股本"],
            "价格指标": ["当日收盘价", "当日涨跌幅"]
        }

        # 估值指标说明 - 根据实际数据列名调整
        self.valuation_descriptions = {
            "市盈率": "滚动市盈率，反映当前股价相对于过去12个月每股收益的倍数",
            "市盈率(静)": "静态市盈率，反映当前股价相对于最近一年每股收益的倍数",
            "市净率": "股价与每股净资产的比值，反映股价相对于净资产的溢价程度",
            "PEG值": "市盈率相对盈利增长比率，用于评估成长股的估值合理性",
            "市现率": "股价与每股现金流的比值，反映股价相对于现金流的倍数",
            "市销率": "股价与每股营业收入的比值，反映股价相对于营业收入的倍数",
            "总市值": "公司总市值，反映公司整体价值",
            "流通市值": "流通市值，反映可交易股票的总价值",
            "当日收盘价": "当日收盘价格",
            "当日涨跌幅": "当日涨跌幅度"
        }
    
    def _hex_to_rgb(self, hex_color: str) -> str:
        """将十六进制颜色转换为RGB格式"""
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return f"{r}, {g}, {b}"

    def render(self, data: Dict[str, Any]):
        """显示估值分析主页面"""
        st.markdown("## 💰 股票估值分析")
        
        # 检查估值数据
        valuation_data = data.get("stock_valuation")
        if valuation_data is None or valuation_data.empty:
            st.warning("📊 暂无估值数据")
            return

        # 整合估值概览和估值趋势
        self._display_valuation_overview(valuation_data)
        self._display_valuation_trends(valuation_data)

    def _display_valuation_overview(self, df: pd.DataFrame):
        """显示估值概览"""
        self.ui_manager.section_header("估值概览", "📊")
        
        if df.empty:
            st.info("暂无估值数据")
            return

        # 确保数据按时间排序（最新数据在最后）
        # 数据加载器已将日期设为索引，直接使用索引排序
        if hasattr(df.index, 'to_datetime'):
            df_sorted = df.sort_index()
        elif '日期' in df.columns:
            # 备用处理：如果日期仍在列中
            df_sorted = df.copy()
            df_sorted['日期'] = pd.to_datetime(df_sorted['日期'], errors='coerce')
            df_sorted = df_sorted.sort_values('日期').reset_index(drop=True)
        else:
            df_sorted = df.sort_index()

        # 获取最新数据（排序后的最后一行）
        latest_data = df_sorted.iloc[-1] if not df_sorted.empty else None
        if latest_data is None:
            st.info("暂无最新估值数据")
            return

        # 显示数据更新时间（调试信息）
        try:
            if hasattr(df_sorted.index, 'max'):
                latest_date = df_sorted.index.max()
                if hasattr(latest_date, 'strftime'):
                    formatted_date = latest_date.strftime('%Y-%m-%d')
                else:
                    formatted_date = str(latest_date).split()[0]
                st.caption(f"📅 数据更新时间: {formatted_date}")
            elif '日期' in df_sorted.columns:
                latest_date = df_sorted['日期'].iloc[-1]
                if hasattr(latest_date, 'strftime'):
                    formatted_date = latest_date.strftime('%Y-%m-%d')
                else:
                    formatted_date = str(latest_date).split()[0]
                st.caption(f"📅 数据更新时间: {formatted_date}")
        except Exception as e:
            st.caption(f"📅 数据更新时间: 未知")

        # 核心估值指标卡片
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            self._create_valuation_card(
                "市盈率", 
                latest_data.get("市盈率", 0),
                "市盈率",
                "倍",
                self._get_pe_rating(latest_data.get("市盈率", 0))
            )
        
        with col2:
            self._create_valuation_card(
                "市净率", 
                latest_data.get("市净率", 0),
                "市净率",
                "倍",
                self._get_pb_rating(latest_data.get("市净率", 0))
            )
        
        with col3:
            self._create_valuation_card(
                "PEG值", 
                latest_data.get("PEG值", 0),
                "PEG值",
                "",
                self._get_peg_rating(latest_data.get("PEG值", 0))
            )
        
        with col4:
            self._create_valuation_card(
                "市销率", 
                latest_data.get("市销率", 0),
                "市销率",
                "倍",
                self._get_ps_rating(latest_data.get("市销率", 0))
            )


    def _create_valuation_card(self, title: str, value: float, label: str, unit: str, rating: str):
        """创建估值指标卡片"""
        if pd.isna(value) or value == 0:
            st.markdown(
                f"""
                <div style='text-align: center; padding: 15px; border: 2px solid #e5e7eb; border-radius: 10px; background: #f9fafb;'>
                    <div style='font-size: 14px; color: #6b7280; margin-bottom: 5px;'>{label}</div>
                    <div style='font-size: 20px; font-weight: bold; color: #9ca3af;'>--</div>
                    <div style='font-size: 12px; color: #9ca3af;'>暂无数据</div>
                </div>
                """,
                unsafe_allow_html=True
            )
            return

        # 根据评级确定颜色 - 使用 ui_template_manager 的颜色
        color_map = {
            "优秀": self.colors['success'],
            "良好": self.colors['info'],
            "一般": self.colors['warning'],
            "较高": self.colors['danger'],
            "过高": self.colors['danger']
        }
        color = color_map.get(rating, "#6b7280")

        st.markdown(
            f"""
            <div style='text-align: center; padding: 15px; border: 2px solid {color}; border-radius: 10px; background: {color}10;'>
                <div style='font-size: 14px; color: white; margin-bottom: 5px;'>{label}</div>
                <div style='font-size: 24px; font-weight: bold; color: {color};'>{value:.2f}{unit}</div>
                <div style='font-size: 12px; color: {color}; font-weight: 600;'>{rating}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    def _get_pe_rating(self, pe: float) -> str:
        """获取PE评级"""
        if pe <= 15:
            return "优秀"
        elif pe <= 25:
            return "良好"
        elif pe <= 35:
            return "一般"
        elif pe <= 50:
            return "较高"
        else:
            return "过高"

    def _get_pb_rating(self, pb: float) -> str:
        """获取PB评级"""
        if pb <= 1.5:
            return "优秀"
        elif pb <= 2.5:
            return "良好"
        elif pb <= 4:
            return "一般"
        elif pb <= 6:
            return "较高"
        else:
            return "过高"

    def _get_peg_rating(self, peg: float) -> str:
        """获取PEG评级"""
        if peg <= 0.5:
            return "优秀"
        elif peg <= 1:
            return "良好"
        elif peg <= 1.5:
            return "一般"
        elif peg <= 2:
            return "较高"
        else:
            return "过高"

    def _get_ps_rating(self, ps: float) -> str:
        """获取PS评级"""
        if ps <= 1:
            return "优秀"
        elif ps <= 3:
            return "良好"
        elif ps <= 5:
            return "一般"
        elif ps <= 8:
            return "较高"
        else:
            return "过高"


    
    

    def _create_trend_cards(self, df: pd.DataFrame, metrics: List[str], icon: str, analysis_type: str):
        """创建趋势指标卡片 - 与财务分析页面保持一致"""
        if not metrics:
            return

        cols = st.columns(min(len(metrics), 4))

        for i, metric in enumerate(metrics):
            if i >= len(cols):
                break

            with cols[i]:
                if metric in df.columns:
                    values = df[metric].dropna()
                    if len(values) >= 2:
                        latest_value = values.iloc[-1]
                        prev_value = values.iloc[-2]

                        # 计算变化率
                        if prev_value != 0:
                            change_rate = (latest_value - prev_value) / abs(prev_value) * 100
                        else:
                            change_rate = 0

                        # 格式化显示
                        if abs(latest_value) >= 1e8:
                            formatted_value = f"{latest_value/1e8:.2f}亿"
                        elif abs(latest_value) >= 1e4:
                            formatted_value = f"{latest_value/1e4:.2f}万"
                        else:
                            formatted_value = f"{latest_value:.2f}"

                        # 确定颜色（红涨绿跌）
                        if change_rate > 0:
                            color = "#ff4444"  # 上涨红色
                            arrow = "📈"
                        elif change_rate < 0:
                            color = "#00ff88"  # 下跌绿色
                            arrow = "📉"
                        else:
                            color = "#FFD700"  # 持平黄色
                            arrow = "➡️"

                        st.markdown(f"""
                        <div style='text-align: center; padding: 15px; border: 2px solid {color};
                                    border-radius: 10px; background: {color}10;'>
                            <div style='font-size: 12px; color: white; margin-bottom: 5px;'>{metric}</div>
                            <div style='font-size: 20px; font-weight: bold; color: {color};'>
                                {arrow} {formatted_value}
                            </div>
                            <div style='font-size: 12px; color: {color}; font-weight: 600;'>
                                {change_rate:+.2f}%
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div style='text-align: center; padding: 15px; border: 2px solid #666;
                                    border-radius: 10px; background: #333;'>
                            <div style='font-size: 12px; color: #999; margin-bottom: 5px;'>{metric}</div>
                            <div style='font-size: 16px; color: #666;'>数据不足</div>
                        </div>
                        """, unsafe_allow_html=True)

    def _display_valuation_trends(self, df: pd.DataFrame):
        """显示估值趋势分析 - 单图表，点击切换指标"""
        self.ui_manager.section_header("估值趋势分析", "📈")

        if df.empty:
            st.info("暂无估值趋势数据")
            return

        # 确保数据按时间排序（与估值概览保持一致）
        # 数据加载器已将日期设为索引，直接使用索引排序
        if hasattr(df.index, 'to_datetime'):
            df_sorted = df.sort_index()
        elif '日期' in df.columns:
            # 备用处理：如果日期仍在列中
            df_sorted = df.copy()
            df_sorted['日期'] = pd.to_datetime(df_sorted['日期'], errors='coerce')
            df_sorted = df_sorted.sort_values('日期').reset_index(drop=True)
        else:
            df_sorted = df.sort_index()

        # 选择要分析的指标
        available_metrics = [col for col in df_sorted.columns if col != "日期"]
        if not available_metrics:
            st.warning("暂无可用指标")
            return

        # 直接显示核心估值指标的图表
        
        # 定义要显示的核心估值指标
        core_metrics = ["市盈率", "市净率", "市销率", "总市值", "总股本"]
        filtered_metrics = [metric for metric in available_metrics if metric in core_metrics]
        
        if not filtered_metrics:
            st.info("暂无核心估值指标数据")
            return
        
        # 为每个核心估值指标创建独立的趋势图（避免重复卡片显示）
        for i, metric in enumerate(filtered_metrics):
            self.ui_manager.section_header(f"📈 {metric} 趋势分析", level=2)

            # 为单个指标创建趋势图
            fig = self.ui_manager.create_financial_trend_chart(
                df_sorted,
                [metric],  # 只传一个指标
                title=f"{metric} 趋势分析",
                stock_code=""
            )
            if fig is not None:
                st.plotly_chart(fig, width="stretch", key=f"valuation_trend_{metric}")

            # 指标说明
            if metric in self.valuation_descriptions:
                st.caption(f"💡 {self.valuation_descriptions[metric]}")

            # 添加分隔线（除了最后一个指标）
            if i < len(filtered_metrics) - 1:
                st.markdown("---")




    def _calculate_trend_changes(self, df: pd.DataFrame, metric: str) -> Optional[Dict]:
        """计算趋势变化"""
        if metric not in df.columns or df.empty:
            return None
        
        try:
            values = df[metric].dropna()
            if len(values) < 2:
                return None
            
            # 最新值和变化
            latest_value = values.iloc[-1]
            latest_change = values.iloc[-1] - values.iloc[-2]
            
            # 趋势方向
            if len(values) >= 3:
                recent_trend = values.iloc[-3:].diff().mean()
                if recent_trend > 0.1:
                    trend_direction = "上升"
                elif recent_trend < -0.1:
                    trend_direction = "下降"
                else:
                    trend_direction = "平稳"
            else:
                trend_direction = "平稳"
            
            # 趋势强度
            if len(values) >= 5:
                volatility = values.std()
                if volatility > values.mean() * 0.3:
                    trend_strength = "强"
                elif volatility > values.mean() * 0.15:
                    trend_strength = "中"
                else:
                    trend_strength = "弱"
            else:
                trend_strength = "中"
            
            # 稳定性
            if len(values) >= 5:
                cv = values.std() / values.mean() if values.mean() != 0 else 0
                if cv <= 0.2:
                    stability = "稳定"
                elif cv <= 0.4:
                    stability = "较稳定"
                else:
                    stability = "不稳定"
            else:
                stability = "较稳定"
            
            return {
                "latest_value": latest_value,
                "latest_change": latest_change,
                "trend_direction": trend_direction,
                "trend_strength": trend_strength,
                "volatility": values.std(),
                "stability": stability
            }
        except Exception as e:
            return None
    
    