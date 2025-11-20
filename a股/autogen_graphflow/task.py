#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
任务描述模块
股票分析任务描述
"""

from datetime import datetime


def get_stock_analysis_task(stock_code: str) -> str:
    """
    获取股票分析任务描述（简化版，让AI自主制定研究大纲）
    
    Args:
        stock_code: 股票代码，如 "000001"、"600519"、"AAPL" 等
        
    Returns:
        str: 简化的股票分析任务描述
    """
    return f"""请对股票代码 {stock_code} 进行全面的投资分析。

请协调者自主制定研究大纲和分析策略，研究分析师执行研究，策略顾问给出最终投资建议。"""

