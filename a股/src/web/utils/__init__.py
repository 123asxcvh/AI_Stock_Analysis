#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
统一工具模块
提供所有工具函数的统一访问接口
"""

# 从ui_utils导入所有功能
from .ui_utils import *

__all__ = [
    # 格式化函数
    'format_number', 'format_percentage', 'format_money', 'format_change',
    
    # 金额转换函数
    'convert_money', 'convert_money_to_number', 'get_appropriate_unit', 'get_unit_factor_and_suffix',

    # 单位管理器
    'UnitManager',
    
    # UI组件函数
    'display_metric', 'display_info_box', 'create_expandable_section',
    'create_page_header', 'create_columns_layout', 'section_header',
    
    # 数据处理
    'get_stock_file_path', 'load_csv', 'get_available_stocks', 'get_stock_name',

    # 技术指标读取
    'get_technical_indicator', 'get_latest_indicator_value',

    # 数据验证
    'validate_data',

    # 财务数据处理工具
    'safe_get_year', 'safe_get_date_column', 'filter_annual_data', 
    'filter_semi_annual_data', 'filter_data_by_date', 'create_date_mask',
    'get_year_end_data', 'get_financial_metric_descriptions',

    # 数据加载器
    'data_loader',

    # AI报告管理器
    'ai_report_manager',
]