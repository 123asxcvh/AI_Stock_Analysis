#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
配置模块
使用纯变量的方式定义项目配置
参考股票分析项目的现代化设计
"""

from typing import List, Dict, Any, Optional

# ==================== 基础配置变量 ====================

# 模型配置
MODEL_NAME = "kimi-k2-thinking-turbo"
MODEL_BASE_URL = "https://api.moonshot.cn/v1"
MODEL_API_KEY = "sk-mQYk8FHlx47aHiiOTJjGZlMtolVXWZImnAYkLOx3f2HwAsTs"  # 请替换为你的API密钥
MODEL_TIMEOUT = 120.0
MODEL_MAX_RETRIES = 5
MODEL_TEMPERATURE = 0.7
MODEL_INFO = {
    "vision": False,           # KIMI 不支持视觉功能
    "function_calling": True,  # 支持函数调用
    "json_output": True,       # 支持JSON输出
    "family": "KIMI",          # KIMI模型系列
    "structured_output": True, # 支持结构化输出
}

# 智能体配置 - GraphFlow团队（基于任务分配）
AGENT_NAMES = [
    "coordinator_agent",       # 协调者 + 背景研究
    "company_analyst",         # 公司信息分析师
    "financial_analyst",       # 财务数据分析师
    "industry_analyst",        # 行业分析师
    "market_analyst",          # 市场分析师
    "news_analyst",            # 新闻分析师
    "technical_analyst",       # 技术分析师
    "strategy_advisor"         # 策略顾问 - 综合分析和投资建议
]
AGENT_ROLES = [
    "协调者", "公司信息分析师", "财务数据分析师",
    "行业分析师", "市场分析师", "新闻分析师", "技术分析师", "策略顾问"
]
AGENT_MAX_TOOL_ITERATIONS = 10
AGENT_REFLECT_ON_TOOL_USE = True

# ==================== 配置字典 ====================

# 模型配置字典
MODEL_CONFIG = {
    "name": MODEL_NAME,
    "api_key": MODEL_API_KEY,
    "base_url": MODEL_BASE_URL,
    "timeout": MODEL_TIMEOUT,
    "max_retries": MODEL_MAX_RETRIES,
    "temperature": MODEL_TEMPERATURE,
    "model_info": MODEL_INFO,
}

# 智能体配置列表
AGENTS_CONFIG = [
    {
        "name": name,
        "role": role,
        "max_tool_iterations": AGENT_MAX_TOOL_ITERATIONS,
        "reflect_on_tool_use": AGENT_REFLECT_ON_TOOL_USE,
    }
    for name, role in zip(AGENT_NAMES, AGENT_ROLES)
]

# MCP服务器配置列表 - 移除filesystem，只使用网络搜索工具
MCP_SERVERS_CONFIG = [
    # Tavily搜索工具 - 网页搜索和信息搜集
    {
        "name": "tavily",
        "command": "npx",
        "args": ["-y", "tavily-mcp@0.2.1"],
        "env": {
            "TAVILY_API_KEY": "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"
        },
        "agents": ["coordinator_agent", "company_analyst", "financial_analyst", "industry_analyst", "market_analyst", "news_analyst", "technical_analyst"]
    },
  
    # 顺序思考工具 - 深度思考和分析
    {
        "name": "sequentialthinking",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"],
        "agents": ["coordinator_agent"]  # 只有协调者需要深度思考工具
    },
]

# 项目总配置
PROJECT_CONFIG = {
    "model": MODEL_CONFIG,
    "agents": AGENTS_CONFIG,
    "mcp_servers": MCP_SERVERS_CONFIG,
}

# ==================== 配置访问函数 ====================

def get_model_config() -> Dict[str, Any]:
    """获取模型配置"""
    return PROJECT_CONFIG["model"]


def get_agent_config(agent_name: str) -> Optional[Dict[str, Any]]:
    """获取指定智能体配置"""
    for agent in PROJECT_CONFIG["agents"]:
        if agent["name"] == agent_name:
            return agent
    return None
    

def get_mcp_servers() -> List[Dict[str, Any]]:
    """获取MCP服务器配置"""
    return PROJECT_CONFIG["mcp_servers"]


def print_config():
    """打印当前配置"""
    print("📋 当前配置:")
    print(f"   模型名称: {PROJECT_CONFIG['model']['name']}")
    print(f"   API地址: {PROJECT_CONFIG['model']['base_url']}")
    print(f"   超时时间: {PROJECT_CONFIG['model']['timeout']}秒")
    print(f"   最大重试: {PROJECT_CONFIG['model']['max_retries']}次")
    print(f"   智能体数量: {len(PROJECT_CONFIG['agents'])}")
    print(f"   MCP服务器数量: {len(get_mcp_servers())}")
    print(f"   API密钥: {'已配置' if PROJECT_CONFIG['model']['api_key'] else '未配置'}")