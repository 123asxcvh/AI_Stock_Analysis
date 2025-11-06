#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
UI模板系统
提供统一的UI管理器，避免重复
"""

# 导入统一的UI模板管理器
from .ui_templates import ui_template_manager

# 向后兼容的别名
core_template_manager = ui_template_manager
chart_template_manager = ui_template_manager
metric_template_manager = ui_template_manager
component_template_manager = ui_template_manager

# 导出所有模板管理器
__all__ = [
    'ui_template_manager',
    # 向后兼容
    'core_template_manager',
    'chart_template_manager',
    'metric_template_manager',
    'component_template_manager'
]