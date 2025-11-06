#!/usr/bin/env python

"""
新闻舆情页面组件
显示news_data.csv表格数据
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any
from pathlib import Path

# 使用模板系统
from src.web.templates import ui_template_manager


class NewsSentimentComponent:
    """新闻舆情组件类"""
    
    def __init__(self):
        """初始化新闻舆情组件"""
        self.ui_manager = ui_template_manager
        self.colors = self.ui_manager.colors
    
    def render(self, data: Dict[str, Any]) -> None:
        """渲染新闻舆情页面"""
        st.markdown("## 📰 新闻舆情")
        
        # 获取股票代码
        stock_code = data.get("stock_code")
        
        # 构建新闻数据文件路径
        news_data_path = Path(f"data/cleaned_stocks/{stock_code}/news_data.csv")
            
        # 读取新闻数据
        news_df = pd.read_csv(news_data_path, encoding='utf-8')
        
        # 显示新闻数据表格
        self._display_news_table(news_df)
        
        # 显示AI分析报告
        self._display_ai_analysis_report(data)
    
    def _display_news_table(self, news_df: pd.DataFrame) -> None:
        """显示新闻数据表格"""
        # 数据预处理
        display_df = news_df.copy()
        
        # 按日期排序（最新的在前）
        display_df['日期'] = pd.to_datetime(display_df['日期'])
        display_df = display_df.sort_values('日期', ascending=False)
        
        # 使用模板显示数据概览
        self._display_news_overview(display_df)
        
        st.markdown("---")
        
        # 显示新闻表格
        st.markdown("### 📋 新闻详细列表")
        
        # 限制显示的行数，避免页面过长
        max_rows = 200
        if len(display_df) > max_rows:
            st.info(f"显示最近 {max_rows} 条新闻（共 {len(news_df)} 条）")
            display_df = display_df.head(max_rows)
        
        # 创建可滚动的表格容器
        st.markdown("""
        <div style="
            max-height: 600px; 
            overflow-y: auto; 
            border: 1px solid #333; 
            border-radius: 8px; 
            padding: 10px;
            background: rgba(30,30,40,0.8);
        ">
        """, unsafe_allow_html=True)
        
        # 使用streamlit的dataframe显示，但设置固定高度
        st.dataframe(
            display_df,
            use_container_width=True,
            height=500,
            hide_index=True,
            column_config={
                "日期": st.column_config.DatetimeColumn(
                    "日期",
                    format="YYYY-MM-DD",
                )
            }
        )
        
        st.markdown("</div>", unsafe_allow_html=True)
 
    def _display_news_overview(self, news_df: pd.DataFrame) -> None:
        """显示新闻数据概览 - 使用模板样式"""
        st.markdown("### 📊 数据概览")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("总新闻数", f"{len(news_df):,}")
        
        with col2:
            if '日期' in news_df.columns:
                latest_date = news_df['日期'].max().strftime('%Y-%m-%d')
                st.metric("最新日期", latest_date)
            else:
                st.metric("最新日期", "未知")
        
        with col3:
            if '日期' in news_df.columns:
                earliest_date = news_df['日期'].min().strftime('%Y-%m-%d')
                st.metric("最早日期", earliest_date)
            else:
                st.metric("最早日期", "未知")
    
    def _display_ai_analysis_report(self, data: Dict[str, Any]):
        """显示AI分析报告"""
        st.markdown("---")
        self.ui_manager.section_header("AI分析报告", "🤖")
        
        # 导入AI报告显示工具
        from src.web.utils import ai_report_manager
        
        # 获取股票代码
        stock_code = data.get("stock_code", "未知")
        
        # 显示新闻舆情AI报告 - 直接显示news_data.md
        try:
            reports = ai_report_manager.load_reports(stock_code, "stock")

            if reports and "news_data.md" in reports:
                content = reports["news_data.md"]
                if content.startswith("❌"):
                    st.error(f"🤖 新闻舆情AI分析失败: {content}")
                else:
                    st.markdown("##### 📰 新闻舆情AI分析")
                    st.markdown(content)
            else:
                st.info("🤖 新闻舆情AI分析报告暂未加载")

        except Exception as e:
            st.error(f"加载新闻舆情AI报告时出错: {str(e)}")
            st.info("🤖 新闻舆情AI分析报告暂未加载")

# 创建全局实例
news_sentiment_component = NewsSentimentComponent()