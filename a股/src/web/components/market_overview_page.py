#!/usr/bin/env python3

"""
市场概览组件
显示市场数据概览和分析
整合了原 market_page_templates.py 的所有功能
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import re
import sys
import time
import threading
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional
from src.web.templates import ui_template_manager
from src.web.utils import convert_money_to_number

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))


class MarketOverviewComponent:
    """市场概览组件类 - 整合了原 market_page_templates.py 的所有功能"""
    
    def __init__(self):
        """初始化市场概览组件"""
        self.ui_manager = ui_template_manager
        self.colors = self.ui_manager.colors
        
        # 数据目录配置
        from config import config
        self.data_dir = config.data_dir
        self.market_data_dir = config.get_market_data_dir(cleaned=True)
        self.index_stocks_dir = config.get_index_stocks_dir()
        
    def load_market_csv(self, filename: str) -> pd.DataFrame:
        """加载市场数据CSV文件，优先使用清洗后的数据"""
        # 首先尝试加载清洗后的数据
        cleaned_path = self.market_data_dir / filename
        if cleaned_path.exists():
            df = pd.read_csv(str(cleaned_path))
            # 确保返回的是DataFrame而不是Series
            if isinstance(df, pd.Series):
                df = df.to_frame().T
            return df

        # 如果清洗后的数据不存在，使用原始数据
        original_data_dir = self.data_dir / "market_data"
        path = original_data_dir / filename
        if path.exists():
            df = pd.read_csv(str(path))
            # 确保返回的是DataFrame而不是Series
            if isinstance(df, pd.Series):
                df = df.to_frame().T
            return df
        return pd.DataFrame()
    
    def load_cleaned_market_data(self) -> Dict[str, pd.DataFrame]:
        """加载清洗后的市场数据"""
        # 直接使用清洗后的数据文件名
        cleaned_files = {
            "sector_fund_flow": "sector_fund_flow.csv",
            "fund_flow_industry": "fund_flow_industry.csv", 
            "fund_flow_concept": "fund_flow_concept.csv",
            "fund_flow_individual": "fund_flow_individual.csv",
            "zt_pool": "zt_pool.csv",
            "lhb_detail": "lhb_detail.csv",
        }

        market_data = {}
        for data_type, filename in cleaned_files.items():
            df = self.load_market_csv(filename)
            if not df.empty:
                market_data[data_type] = df

        return market_data
    
    def load_market_summary_md(self) -> Optional[str]:
        """加载市场摘要Markdown文件"""
        # 自动查找最新日期的market_recommendation.md
        base_dir = self.data_dir / "ai_reports" / "market_summary_suggestion"
        if not base_dir.exists():
            return None
        date_dirs = [d.name for d in base_dir.iterdir() if d.is_dir() and re.match(r"\d{8}", d.name)]
        if not date_dirs:
            return None
        latest_dir = sorted(date_dirs)[-1]
        md_path = base_dir / latest_dir / "market_recommendation.md"
        if md_path.exists():
            with open(str(md_path), encoding="utf-8") as f:
                return f.read()
        return None
    
    def display_sector_fund_flow(self, df: pd.DataFrame) -> None:
        """显示板块资金流（已废弃，保留以避免错误）"""
        if df.empty:
            st.warning("暂无板块资金流数据")
            return

        st.markdown("#### 💰 板块资金流向")
        st.info("板块资金流数据收集已被移除")

        # 不再显示AI分析报告，因为sector_fund_flow已被删除
    
    def display_industry_fund_flow(self, df: pd.DataFrame) -> None:
        """显示行业资金流"""
        if df.empty:
            st.warning("暂无行业资金流数据")
            return
            
        st.markdown("#### 🏭 行业资金流向")
        
        if '行业' in df.columns and '净额' in df.columns:
            # 转换金额为数值
            df['净额数值'] = df['净额'].apply(convert_money_to_number)
            # 强制转换为数值类型，无法转换的变为NaN，然后填充为0
            df['净额数值'] = pd.to_numeric(df['净额数值'], errors='coerce').fillna(0)

            # 提取领涨行业（按涨跌幅排序）
            top_gainers_df = df.sort_values('行业-涨跌幅', ascending=False).head(10)
            top_gainers = top_gainers_df.sort_values('行业-涨跌幅', ascending=False)
            st.markdown("##### 🚀 领涨行业TOP10")
            top_names = [row['行业'] for idx, row in top_gainers.iterrows()]
            st.write("**" + " | ".join(top_names) + "**")

            # 按净额倒序排序，筛选前10个，倒序排列
            top_industries_df = df.sort_values('净额数值', ascending=False).head(10)
            top_industries = top_industries_df.sort_values('净额数值', ascending=False)

            # 使用图表模板创建图表 - 自动处理单位
            fig = self.ui_manager.fund_flow_chart(
                df=top_industries,
                x_col='行业',  # x轴为行业名称
                y_col='净额数值',  # y轴为净额数值
                title='行业资金净额TOP10',
                x_title='行业',  # x轴标题
                y_title='资金净额',  # y轴标题（自动添加单位）
                color_scale='Blues'
            )
            st.plotly_chart(fig, width="stretch")

            # 净额最低的10个行业
            bottom_industries_df = df.sort_values('净额数值', ascending=True).head(10)
            bottom_industries = bottom_industries_df.sort_values('净额数值', ascending=False)

            # 使用图表模板创建图表 - 自动处理单位
            fig_bottom = self.ui_manager.fund_flow_chart(
                df=bottom_industries,
                x_col='行业',  # x轴为行业名称
                y_col='净额数值',  # y轴为净额数值
                title='行业资金最低净额TOP10',
                x_title='行业',  # x轴标题
                y_title='资金净额',  # y轴标题（自动添加单位）
                color_scale='Greens'
            )
            st.plotly_chart(fig_bottom, width="stretch")
            
            # 显示完整数据表格 - 按行业-涨跌幅倒序排列
            sorted_data = df.sort_values('行业-涨跌幅', ascending=False)
            st.dataframe(
                sorted_data,
                width="stretch",
                hide_index=True
            )
        
        # 显示对应的AI分析报告
        self._display_ai_analysis_report("fund_flow_industry")
    
    def display_concept_fund_flow(self, df: pd.DataFrame) -> None:
        """显示概念资金流"""
        if df.empty:
            st.warning("暂无概念资金流数据")
            return
            
        st.markdown("#### 💡 概念资金流向")
        
        if '行业' in df.columns and '净额' in df.columns:
            # 转换金额为数值
            df['净额数值'] = df['净额'].apply(convert_money_to_number)
            # 强制转换为数值类型，无法转换的变为NaN，然后填充为0
            df['净额数值'] = pd.to_numeric(df['净额数值'], errors='coerce').fillna(0)

            # 提取领涨概念（按涨跌幅排序）
            top_gainers_df = df.sort_values('行业-涨跌幅', ascending=False).head(10)
            top_gainers = top_gainers_df.sort_values('行业-涨跌幅', ascending=False)
            st.markdown("##### 🚀 领涨概念TOP10")
            top_names = [row['行业'] for idx, row in top_gainers.iterrows()]
            st.write("**" + " | ".join(top_names) + "**")

            # 按净额倒序排序，筛选前10个，倒序排列
            top_concepts_df = df.sort_values('净额数值', ascending=False).head(10)
            top_concepts = top_concepts_df.sort_values('净额数值', ascending=False)

            # 使用图表模板创建图表 - 自动处理单位
            fig = self.ui_manager.fund_flow_chart(
                df=top_concepts,
                x_col='行业',  # x轴为行业名称
                y_col='净额数值',  # y轴为净额数值
                title='概念资金净额TOP10',
                x_title='行业',  # x轴标题
                y_title='资金净额',  # y轴标题（自动添加单位）
                color_scale='Viridis'
            )
            st.plotly_chart(fig, width="stretch")

            # 净额最低的10个概念
            bottom_concepts_df = df.sort_values('净额数值', ascending=True).head(10)
            bottom_concepts = bottom_concepts_df.sort_values('净额数值', ascending=False)

            # 使用图表模板创建图表 - 自动处理单位
            fig_bottom = self.ui_manager.fund_flow_chart(
                df=bottom_concepts,
                x_col='行业',  # x轴为行业名称
                y_col='净额数值',  # y轴为净额数值
                title='概念资金最低净额TOP10',
                x_title='行业',  # x轴标题
                y_title='资金净额',  # y轴标题（自动添加单位）
                color_scale='Greens'
            )
            st.plotly_chart(fig_bottom, width="stretch")
            
            # 显示完整数据表格 - 按行业-涨跌幅倒序排列
            sorted_data = df.sort_values('行业-涨跌幅', ascending=False)
            st.dataframe(
                sorted_data,
                width="stretch",
                hide_index=True
            )
        
        # 显示对应的AI分析报告
        self._display_ai_analysis_report("fund_flow_concept")
    
    def display_individual_fund_flow(self, df: pd.DataFrame) -> None:
        """显示个股资金流"""
        if df.empty:
            st.warning("暂无个股资金流数据")
            return
            
        st.markdown("#### 📈 个股资金流向")
        
        if '股票简称' in df.columns and '净额' in df.columns:
            # 转换金额为数值
            df['净额数值'] = df['净额'].apply(convert_money_to_number)
            # 强制转换为数值类型，无法转换的变为NaN，然后填充为0
            df['净额数值'] = pd.to_numeric(df['净额数值'], errors='coerce').fillna(0)

            # 提取领涨个股（按涨跌幅排序）
            top_gainers_df = df.sort_values('涨跌幅', ascending=False).head(10)
            top_gainers = top_gainers_df.sort_values('涨跌幅', ascending=False)
            st.markdown("##### 🚀 领涨个股TOP10")
            top_names = [row['股票简称'] for idx, row in top_gainers.iterrows()]
            st.write("**" + " | ".join(top_names) + "**")

            # 按净额倒序排序，筛选前10个，倒序排列
            top_stocks_df = df.sort_values('净额数值', ascending=False).head(10)
            top_stocks = top_stocks_df.sort_values('净额数值', ascending=False)

            # 使用图表模板创建图表 - 自动处理单位
            fig = self.ui_manager.fund_flow_chart(
                df=top_stocks,
                x_col='股票简称',  # x轴为股票简称
                y_col='净额数值',  # y轴为净额数值
                title='个股资金净额TOP10',
                x_title='股票简称',  # x轴标题
                y_title='资金净额',  # y轴标题（自动添加单位）
                color_scale='Blues'
            )
            st.plotly_chart(fig, width="stretch")

            # 净额最低的10个个股
            bottom_stocks_df = df.sort_values('净额数值', ascending=True).head(10)
            bottom_stocks = bottom_stocks_df.sort_values('净额数值', ascending=False)

            # 使用图表模板创建图表 - 自动处理单位
            fig_bottom = self.ui_manager.fund_flow_chart(
                df=bottom_stocks,
                x_col='股票简称',  # x轴为股票简称
                y_col='净额数值',  # y轴为净额数值
                title='个股资金最低净额TOP10',
                x_title='股票简称',  # x轴标题
                y_title='资金净额',  # y轴标题（自动添加单位）
                color_scale='Greens'
            )
            st.plotly_chart(fig_bottom, width="stretch")

            # 显示完整数据表格 - 按涨跌幅倒序排列
            sorted_data = df.sort_values('涨跌幅', ascending=False)
            st.dataframe(
                sorted_data,
                width="stretch",
                hide_index=True
            )

        # 显示AI分析报告
        self._display_ai_analysis_report("fund_flow_individual")
    
    def display_limit_up_pool(self, df: pd.DataFrame) -> None:
        """显示涨停股池"""
        if df.empty:
            st.warning("暂无涨停股数据")
            return
            
        st.markdown("#### 🚀 今日涨停股池")
        
        # 显示涨停股票数量
        st.metric("涨停股票总数", len(df))
        
        # 添加涨跌幅图表
        if '名称' in df.columns and '涨跌幅' in df.columns:
            # 按涨跌幅排序，取前10名，倒序排列
            top_stocks_df = df.sort_values('涨跌幅', ascending=False).head(10)
            top_stocks = top_stocks_df.sort_values('涨跌幅', ascending=False)
            
            # 使用柱状图显示涨跌幅TOP10
            fig = self.ui_manager.fund_flow_chart(
                df=top_stocks,
                x_col='名称',  # x轴改为名称
                y_col='涨跌幅',  # y轴改为涨跌幅
                title='涨停股涨跌幅TOP10',
                x_title='股票名称',  # x轴标题
                y_title='涨跌幅（%）',  # y轴标题
                color_scale='RdYlGn_r'
            )
            st.plotly_chart(fig, width="stretch")
        
        if '代码' in df.columns and '名称' in df.columns:
            # 显示涨停股数据 - 按涨跌幅倒序排列
            sorted_data = df.sort_values('涨跌幅', ascending=False)
            st.dataframe(
                sorted_data,
                width="stretch",
                hide_index=True
            )
        
        # 显示对应的AI分析报告
        self._display_ai_analysis_report("zt_pool")
    
    def display_lhb_detail(self, df: pd.DataFrame) -> None:
        """显示龙虎榜详情"""
        if df.empty:
            st.warning("暂无龙虎榜数据")
            return
            
        st.markdown("#### 🐉 龙虎榜详情")
        
        # 显示上榜股票数量
        st.metric("上榜股票总数", len(df))
        
        # 添加龙虎榜净买额图表
        if '名称' in df.columns and '龙虎榜净买额' in df.columns:
            # 转换净买额为数值
            df['净买额数值'] = df['龙虎榜净买额'].apply(convert_money_to_number)
            df['净买额数值'] = pd.to_numeric(df['净买额数值'], errors='coerce').fillna(0)

            # 按龙虎榜净买额排序，取前10个，倒序排列
            top_stocks_df = df.sort_values('净买额数值', ascending=False).head(10)
            top_stocks = top_stocks_df.sort_values('净买额数值', ascending=False)

            # 使用柱状图显示龙虎榜净买额TOP10 - 自动处理单位
            fig = self.ui_manager.fund_flow_chart(
                df=top_stocks,
                x_col='名称',  # x轴为股票名称
                y_col='净买额数值',  # y轴为净买额数值
                title='龙虎榜净买额TOP10',
                x_title='股票名称',  # x轴标题
                y_title='龙虎榜净买额',  # y轴标题（自动添加单位）
                color_scale='RdYlGn_r'
            )
            st.plotly_chart(fig, width="stretch")
        
        if '代码' in df.columns and '名称' in df.columns:
            # 显示主要上榜股票 - 按涨跌幅倒序排列
            sorted_data = df.sort_values('涨跌幅', ascending=False)
            st.dataframe(
                sorted_data,
                width="stretch",
                hide_index=True
            )
        
        # 显示对应的AI分析报告
        self._display_ai_analysis_report("lhb_detail")
    
    def display_financial_news(self) -> None:
        """显示财经新闻"""
        self.ui_manager.section_header("财经新闻", "📰")

        # 加载新闻数据
        news_df = self.load_market_csv("news_main_cx.csv")

        if news_df.empty:
            st.warning("暂无财经新闻数据")
            return

        # 显示新闻数据表格
        st.markdown("#### 📰 最新财经新闻")
        st.dataframe(news_df, width="stretch", hide_index=True)

        # 显示对应的AI分析报告
        self._display_ai_analysis_report("news_main_cx")

    def display_market_activity_legu(self) -> None:
        """显示乐股市场活跃度（赚钱效应）"""
        self.ui_manager.section_header("市场赚钱效应", "💎")

        # 加载市场活跃度数据
        activity_df = self.load_market_csv("market_activity_legu.csv")

        if activity_df.empty:
            st.warning("暂无市场活跃度数据")
            return

        # 准备数据
        # 过滤掉活跃度和统计日期的空数据行
        valid_data = activity_df[activity_df['指标'].isin(['上涨', '平盘', '下跌', '涨停', '真实涨停', 'st st*涨停', '跌停', '真实跌停', 'st st*跌停'])]

        if valid_data.empty:
            st.warning("暂无有效的市场活跃度数据")
            return

        # 创建图表
        col1, col2 = st.columns(2)

        with col1:
            # 上涨平盘下跌饼图
            pie_data = valid_data[valid_data['指标'].isin(['上涨', '平盘', '下跌'])]
            if not pie_data.empty:
                fig_pie = go.Figure(data=[go.Pie(
                    labels=pie_data['指标'],
                    values=pie_data['数值'],
                    hole=0.3,
                    marker_colors=['#ff4444', '#ffd700', '#00ff41']
                )])
                fig_pie.update_layout(
                    title="📊 市场涨跌分布",
                    font=dict(color="white"),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)'
                )
                st.plotly_chart(fig_pie, use_container_width=True)

        with col2:
            # 涨停数据柱状图
            limit_up_data = valid_data[valid_data['指标'].isin(['涨停', '真实涨停', 'st st*涨停'])]
            if not limit_up_data.empty:
                fig_limit_up = go.Figure(data=[go.Bar(
                    x=limit_up_data['指标'],
                    y=limit_up_data['数值'],
                    marker_color=['#ff4444', '#ff6666', '#ff8888']
                )])
                fig_limit_up.update_layout(
                    title="🚀 涨停股票统计",
                    xaxis_title="涨停类型",
                    yaxis_title="股票数量",
                    font=dict(color="white"),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)'
                )
                st.plotly_chart(fig_limit_up, use_container_width=True)

        # 跌停数据柱状图
        limit_down_data = valid_data[valid_data['指标'].isin(['跌停', '真实跌停', 'st st*跌停'])]
        if not limit_down_data.empty:
            fig_limit_down = go.Figure(data=[go.Bar(
                x=limit_down_data['指标'],
                y=limit_down_data['数值'],
                marker_color=['#00ff41', '#66ff66', '#88ff88']
            )])
            fig_limit_down.update_layout(
                title="📉 跌停股票统计",
                xaxis_title="跌停类型",
                yaxis_title="股票数量",
                font=dict(color="white"),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig_limit_down, use_container_width=True)

        
        # 显示对应的AI分析报告
        self._display_ai_analysis_report("market_activity_legu")

    def display_market_comprehensive_analysis(self, market_data: Dict[str, pd.DataFrame]) -> None:
        """显示市场综合分析 - 只显示AI分析报告"""
        # 显示对应的AI分析报告
        self._display_ai_analysis_report("market_comprehensive_analysis")
    
    
    
    def display_market_tabs(self, market_data: Dict[str, pd.DataFrame]) -> None:
        """显示市场数据标签页"""
        # 优化市场数据子标签页设计 - 更好的图标和分组
        market_tab_names = [
            "🏭 行业资金流",
            "💡 概念资金流",
            "📈 个股资金流",
            "🚀 涨停股池",
            "🐉 龙虎榜",
            "📰 财经新闻",
            "💎 赚钱效应",
            "📊 综合分析"
        ]
        
        # 应用样式
        st.markdown("""
        <style>
        .market-data-tabs .stTabs [data-baseweb="tab-list"] {
            gap: 10px;
            background: linear-gradient(90deg, rgba(13, 13, 13, 0.95) 0%, rgba(26, 26, 26, 0.95) 100%);
            padding: 10px;
            border-radius: 12px;
            border: 1px solid #FFD700;
            box-shadow: 0 4px 15px rgba(255, 215, 0, 0.1);
        }
        .market-data-tabs .stTabs [data-baseweb="tab"] {
            height: 52px;
            padding: 0px 22px;
            background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
            border-radius: 10px;
            color: #FFFFFF;
            font-weight: 600;
            font-size: 15px;
            border: 1px solid rgba(255, 215, 0, 0.2);
            transition: all 0.3s ease;
        }
        .market-data-tabs .stTabs [data-baseweb="tab"]:hover {
            background: linear-gradient(135deg, #2a2a2a 0%, #3d3d3d 100%);
            border-color: rgba(255, 215, 0, 0.4);
            transform: translateY(-2px);
        }
        .market-data-tabs .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
            color: #000000;
            border-color: #FFD700;
            box-shadow: 0 2px 8px rgba(255, 215, 0, 0.3);
        }
        </style>
        """, unsafe_allow_html=True)
        
        with st.container():
            tabs = st.tabs(market_tab_names)

            with tabs[0]:
                self.display_industry_fund_flow(market_data.get('fund_flow_industry', pd.DataFrame()))

            with tabs[1]:
                self.display_concept_fund_flow(market_data.get('fund_flow_concept', pd.DataFrame()))

            with tabs[2]:
                self.display_individual_fund_flow(market_data.get('fund_flow_individual', pd.DataFrame()))

            with tabs[3]:
                self.display_limit_up_pool(market_data.get('zt_pool', pd.DataFrame()))

            with tabs[4]:
                self.display_lhb_detail(market_data.get('lhb_detail', pd.DataFrame()))

            with tabs[5]:
                self.display_financial_news()

            with tabs[6]:
                self.display_market_activity_legu()

            with tabs[7]:
                self.display_market_comprehensive_analysis(market_data)
        
    def render(self, data=None):
        """渲染市场数据页面"""
        # 直接加载和显示市场数据
        market_data = self.load_cleaned_market_data()
        
        self.display_market_tabs(market_data)
    
    def _display_ai_analysis_report(self, report_type: str):
        """显示AI分析报告"""
        # 龙虎榜不显示AI分析报告
        if report_type == "lhb_detail":
            return

        st.markdown("---")
        self.ui_manager.section_header("AI分析报告", "🤖")

        # 导入AI报告显示工具
        from src.web.utils import ai_report_manager

        # 报告类型到文件名的映射
        report_file_mapping = {
            "fund_flow_industry": "fund_flow_industry.md",
            "fund_flow_concept": "fund_flow_concept.md",
            "fund_flow_individual": "fund_flow_individual.md",
            "zt_pool": "zt_pool.md",
            "news_main_cx": "news_main_cx.md",
            "market_activity_legu": "market_activity_legu.md",
            "market_comprehensive_analysis": "comprehensive.md"
        }

        # 获取报告文件名
        report_file = report_file_mapping.get(report_type)
        if not report_file:
            st.info(f"🤖 {report_type} 分析报告暂未配置")
            return

        # 加载市场分析报告
        # 市场分析报告在 market_analysis 目录下，没有子目录
        from config import config
        report_dir = config.ai_reports_dir / "market_analysis"
        
        if report_dir.exists():
            report_file_path = report_dir / report_file
            if report_file_path.exists():
                with open(report_file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if content.startswith("❌"):
                        st.error(f"🤖 {report_type} 分析失败: {content}")
                    else:
                        st.markdown(content)
                return
            else:
                st.info(f"🤖 {report_type} 分析报告文件不存在: {report_file}")
                return
        else:
            st.info(f"🤖 市场分析报告目录不存在")
            return
    
    def display_index_stocks_collector(self):
        """显示指数成份股收集器界面"""
        st.markdown("#### 📋 指数成份股收集器")
        st.markdown("---")
        
        # 创建两列布局
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.markdown("##### 🎯 收集设置")
            
            # 选择收集类型
            collection_type = st.radio(
                "选择收集类型：",
                ["概念板块", "行业板块"],
                help="选择要收集的板块类型"
            )
            
            # 输入框
            if collection_type == "概念板块":
                st.markdown("**💡 概念板块输入**")
                concept_input = st.text_area(
                    "请输入概念板块名称（用逗号分隔）：",
                    placeholder="例如：融资融券,人工智能,新能源汽车",
                    height=100,
                    help="多个概念用逗号分隔，如：融资融券,人工智能,新能源汽车"
                )
                symbols = [s.strip() for s in concept_input.split(',') if s.strip()] if concept_input else []
            else:
                st.markdown("**🏭 行业板块输入**")
                industry_input = st.text_area(
                    "请输入行业板块名称（用逗号分隔）：",
                    placeholder="例如：小金属,银行,房地产",
                    height=100,
                    help="多个行业用逗号分隔，如：小金属,银行,房地产"
                )
                symbols = [s.strip() for s in industry_input.split(',') if s.strip()] if industry_input else []
            
            # 开始收集按钮
            if st.button("🚀 开始收集", type="primary", disabled=len(symbols) == 0):
                if symbols:
                    self._run_index_stocks_collection(collection_type, symbols)
        
        with col2:
            st.markdown("##### 📊 收集进度")
            
            # 显示进度容器
            progress_container = st.container()
            status_container = st.container()
            results_container = st.container()
            
            # 初始化session state
            if 'collection_progress' not in st.session_state:
                st.session_state.collection_progress = 0
            if 'collection_status' not in st.session_state:
                st.session_state.collection_status = "等待开始..."
            if 'collection_results' not in st.session_state:
                st.session_state.collection_results = []
            
            with progress_container:
                progress_bar = st.progress(st.session_state.collection_progress)
                st.text(f"进度: {st.session_state.collection_progress:.1f}%")
            
            with status_container:
                st.info(f"状态: {st.session_state.collection_status}")
            
            with results_container:
                if st.session_state.collection_results:
                    st.markdown("##### 📋 收集结果")
                    for result in st.session_state.collection_results:
                        if result['success']:
                            st.success(f"✅ {result['name']}: 成功收集 {result['count']} 只股票")
                        else:
                            st.error(f"❌ {result['name']}: 收集失败 - {result['error']}")
    
    def _run_index_stocks_collection(self, collection_type: str, symbols: list):
        """运行指数成份股流水线"""
        try:
            import subprocess
            import os
            from pathlib import Path
            
            # 重置进度
            st.session_state.collection_progress = 0
            st.session_state.collection_status = "开始运行指数成份股流水线..."
            st.session_state.collection_results = []
            
            # 构建命令行参数
            symbols_str = ",".join(symbols)
            cmd = [
                "python",
                "src/launchers/scripts/run_index_pipeline_async.py",
                symbols_str,
                "--type", collection_type
            ]
            
            # 获取项目根目录
            project_root = Path(__file__).parent.parent.parent.parent
            
            # 运行流水线脚本
            with st.spinner("🚀 正在运行指数成份股流水线..."):
                result = subprocess.run(
                    cmd,
                    cwd=str(project_root),
                    capture_output=True,
                    text=True,
                    env=dict(os.environ, PYTHONPATH=str(project_root))
                )
            
            if result.returncode == 0:
                # 解析输出结果
                output_lines = result.stdout.split('\n')
                success_count = 0
                total_count = len(symbols)
                
                # 从输出中提取成功信息
                for line in output_lines:
                    if "收集完成:" in line and "个板块成功" in line:
                        # 提取成功数量
                        try:
                            success_part = line.split("收集完成:")[1].split("个板块成功")[0].strip()
                            success_count = int(success_part.split("/")[0])
                        except:
                            pass
                    elif "✅" in line and "成功收集" in line:
                        success_count += 1
                
                # 更新结果
                st.session_state.collection_results = [
                    {
                        'name': symbol,
                        'success': True,  # 简化处理，假设都成功
                        'count': 0,
                        'error': None
                    }
                    for symbol in symbols
                ]
                
                st.session_state.collection_status = f"流水线执行完成！成功: {success_count}/{total_count}"
                
                if success_count > 0:
                    st.balloons()
                    st.success(f"🎉 指数成份股流水线执行完成！")
                    st.info("📋 流水线包含: 数据收集 + 数据清洗")
                    
                    # 显示输出信息
                    st.text_area("执行日志", result.stdout, height=200)
                else:
                    st.warning("⚠️ 流水线执行完成，但没有收集到数据")
            else:
                st.session_state.collection_status = f"流水线执行失败"
                st.error(f"❌ 流水线执行失败: {result.stderr}")
                st.text_area("错误日志", result.stderr, height=200)
            
        except Exception as e:
            st.session_state.collection_status = f"流水线执行出错: {str(e)}"
            st.error(f"❌ 流水线执行过程出错: {str(e)}")
    
    def _run_data_cleaning(self):
        """运行数据清洗"""
        try:
            # 导入数据清洗模块
            from src.cleaning.index_stocks_cleaner import IndexStocksCleaner
            
            with st.spinner("🧹 正在清洗数据..."):
                # 创建清洗器实例
                cleaner = IndexStocksCleaner()
                
                # 执行清洗
                results = cleaner.clean_all_index_stocks()
                
                # 显示清洗结果
                concept_success = sum(results['concept'].values())
                concept_total = len(results['concept'])
                industry_success = sum(results['industry'].values())
                industry_total = len(results['industry'])
                
                st.success(f"✅ 数据清洗完成！")
                st.info(f"💡 概念板块: {concept_success}/{concept_total} 个文件清洗成功")
                st.info(f"🏭 行业板块: {industry_success}/{industry_total} 个文件清洗成功")
                
                # 显示清洗后的数据预览
                self._show_cleaned_data_preview()
                
        except Exception as e:
            st.error(f"❌ 数据清洗失败: {str(e)}")
    
    def _show_cleaned_data_preview(self):
        """显示清洗后的数据预览"""
        try:
            st.markdown("##### 📊 清洗后数据预览")
            
            # 显示概念板块数据
            concept_dir = self.index_stocks_dir / "concept"
            if concept_dir.exists():
                concept_files = list(concept_dir.glob("*.csv"))
                if concept_files:
                    st.markdown("**💡 概念板块数据:**")
                    for file_path in concept_files[:3]:  # 只显示前3个
                        if file_path.exists():
                            df = pd.read_csv(file_path)
                            st.write(f"📄 {file_path.name}: {len(df)} 条记录")
                            if len(df) > 0 and '排名' in df.columns:
                                st.dataframe(df[['排名', '代码', '名称', '成交额']].head(10), width="stretch")
            
            # 显示行业板块数据
            industry_dir = self.index_stocks_dir / "industry"
            if industry_dir.exists():
                industry_files = list(industry_dir.glob("*.csv"))
                if industry_files:
                    st.markdown("**🏭 行业板块数据:**")
                    for file_path in industry_files[:3]:  # 只显示前3个
                        if file_path.exists():
                            df = pd.read_csv(file_path)
                            st.write(f"📄 {file_path.name}: {len(df)} 条记录")
                            if len(df) > 0 and '排名' in df.columns:
                                st.dataframe(df[['排名', '代码', '名称', '成交额']].head(10), width="stretch")
                            
        except Exception as e:
            st.warning(f"⚠️ 无法显示数据预览: {str(e)}")
    


# 创建组件实例
market_overview_component = MarketOverviewComponent()


def render_market_data(data=None):
    """渲染市场数据页面 - 向后兼容的函数"""
    market_overview_component.render(data)