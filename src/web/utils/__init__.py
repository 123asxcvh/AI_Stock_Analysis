#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
统一工具模块
提供所有工具函数的统一访问接口
"""

# 从unified_utils导入所有功能
from .unified_utils import *

__all__ = [
    # 格式化函数
    'format_number', 'format_percentage', 'format_money', 'format_change',

    # 数据处理
    'get_stock_file_path', 'load_csv', 'get_available_stocks', 'get_stock_name',

    # UI组件
    'display_metric', 'display_info_box', 'create_expandable_section',
    'create_page_header', 'create_section_header', 'create_columns_layout',
    'display_error', 'display_warning', 'display_success',

    # 图表函数
    'create_candlestick_chart', 'create_line_chart', 'create_volume_chart',
    'create_simple_line_chart',

    # 技术指标
    'calculate_rsi', 'calculate_macd', 'calculate_ma',

    # 数据验证
    'validate_data', 'safe_get_value',

    # 缓存和性能
    'clear_cache', 'get_cache_key',

    # 错误处理
    'handle_error',

    # 数据加载器
    'data_loader', 'UnifiedDataLoader',

    # AI报告管理器
    'ai_report_manager', 'UnifiedAIReportManager',

    # 验证器
    'validator', 'UnifiedValidator',
    'validate_dataframe', 'validate_financial_data',
    'show_no_data_message', 'get_stock_code', 'safe_get_value',

    # 移除的方法标记
    'create_benchmark_portfolio'
]