#!/usr/bin/env python3

"""
投资建议组件
只显示AI分析报告
"""

from typing import Dict, Any


class InvestmentRecommendationComponent:
    """投资建议组件类"""
    
    def __init__(self):
        """初始化投资建议组件"""
        pass
    
    def render(self, data: Dict[str, Any]):
        """渲染投资建议页面 - 直接显示AI分析报告"""
        import streamlit as st

        # 获取股票代码
        stock_code = data.get("stock_code", "未知") if data else "未知"

        st.markdown("## 💡 投资建议")

        # 导入AI报告显示工具
        from src.web.utils import ai_report_manager

        # 直接显示投资建议AI报告
        ai_report_manager.display_single_report(stock_code, "investment_recommendation")
