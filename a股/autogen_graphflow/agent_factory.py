#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
智能体工厂模块
基于 AutoGen 0.4+ 最新API - 简化版本，只保留核心智能体
"""

from typing import List, Dict, Any, Optional
import asyncio

# AutoGen 0.4+ API
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.tools.mcp import StdioServerParams, mcp_server_tools

from config import get_model_config, get_agent_config, MCP_SERVERS_CONFIG
from prompt import get_prompt


def create_model_client(model_config: Dict[str, Any]) -> OpenAIChatCompletionClient:
    """创建模型客户端"""
    return OpenAIChatCompletionClient(
        model=model_config["name"],
        api_key=model_config["api_key"],
        base_url=model_config["base_url"],
        model_info=model_config.get("model_info", {}),
        timeout=model_config.get("timeout", 120.0),
        max_retries=model_config.get("max_retries", 5),
        temperature=model_config.get("temperature", 0.7),
        parallel_tool_calls=False,  # 禁用并行工具调用
    )


async def collect_tools_for_agent(agent_name: str, mcp_servers: Dict[str, Any]) -> List:
    """为智能体收集MCP工具"""
    tools = []
    
    # 智能体工具映射 - 简化版本
    agent_tool_mapping = {
        "coordinator_agent": ["tavily", "sequentialthinking"],
        "strategy_advisor": ["tavily"],  # 策略顾问也需要搜索工具
    }
    
    server_names = agent_tool_mapping.get(agent_name, [])
    
    for server_name in server_names:
        if server_name in mcp_servers:
            server_config = mcp_servers[server_name]
            try:
                server_params = StdioServerParams(
                    command=server_config["command"],
                    args=server_config["args"],
                    env=server_config.get("env", {}),
                    read_timeout_seconds=60,
                )
                
                server_tools = await mcp_server_tools(server_params)
                tools.extend(server_tools)
                print(f"   📋 {agent_name} 获取 {server_name} 工具: {len(server_tools)} 个")
                
            except Exception as e:
                print(f"   ⚠️ {agent_name} 获取 {server_name} 工具失败: {e}")
    
    return tools


async def create_agent(agent_name: str, model_config: Dict[str, Any], 
                      mcp_servers: Dict[str, Any]) -> AssistantAgent:
    """创建智能体"""
    agent_config = get_agent_config(agent_name)
    if not agent_config:
        raise ValueError(f"未找到智能体配置: {agent_name}")
    
    model_client = create_model_client(model_config)
    system_message = get_prompt(agent_name)
    
    # 收集工具
    tools = await collect_tools_for_agent(agent_name, mcp_servers)
    
    # 创建智能体
    agent = AssistantAgent(
        name=agent_name,
        model_client=model_client,
        tools=tools,
        system_message=system_message,
        reflect_on_tool_use=agent_config.get("reflect_on_tool_use", True),
    )
    
    print(f"✅ 智能体创建: {agent_name} ({agent_config['role']}) - {len(tools)} 个工具")
    return agent


async def create_simple_analysis_team(model_config: Dict[str, Any]) -> List[AssistantAgent]:
    """创建简化的分析团队 - 只包含两个核心智能体"""
    mcp_servers = {server["name"]: server for server in MCP_SERVERS_CONFIG}
    
    # 只创建两个核心智能体
    core_agent_names = ["coordinator_agent", "strategy_advisor"]
    
    agents = []
    for agent_name in core_agent_names:
        try:
            agent = await create_agent(agent_name, model_config, mcp_servers)
            agents.append(agent)
        except Exception as e:
            print(f"❌ 创建智能体 {agent_name} 失败: {e}")
            continue
    
    print(f"✅ 简化分析团队创建完成: {len(agents)} 个智能体")
    print("   🎯 核心团队:")
    print("   ├─ coordinator_agent - 协调者 (tavily + sequentialthinking)")
    print("   └─ strategy_advisor - 策略顾问 (tavily)")
    print("   💡 说明：策略顾问直接使用搜索工具完成所有分析，避免重复")
    
    return agents


async def create_full_analysis_team(model_config: Dict[str, Any]) -> List[AssistantAgent]:
    """创建完整的分析团队 - 保留所有分析师但使用并行工作流"""
    mcp_servers = {server["name"]: server for server in MCP_SERVERS_CONFIG}
    
    agent_names = [
        "coordinator_agent",
        "company_analyst", 
        "financial_analyst",
        "industry_analyst",
        "market_analyst",
        "news_analyst",
        "technical_analyst",
        "strategy_advisor"
    ]
    
    agents = []
    for agent_name in agent_names:
        try:
            agent = await create_agent(agent_name, model_config, mcp_servers)
            agents.append(agent)
        except Exception as e:
            print(f"❌ 创建智能体 {agent_name} 失败: {e}")
            continue
    
    print(f"✅ 完整分析团队创建完成: {len(agents)} 个智能体")
    print("   🎯 GraphFlow团队:")
    print("   ├─ coordinator_agent - 协调者 (tavily + sequentialthinking)")
    print("   ├─ company_analyst - 公司分析师 (tavily)")
    print("   ├─ financial_analyst - 财务分析师 (tavily)")
    print("   ├─ industry_analyst - 行业分析师 (tavily)")
    print("   ├─ market_analyst - 市场分析师 (tavily)")
    print("   ├─ news_analyst - 新闻分析师 (tavily)")
    print("   ├─ technical_analyst - 技术分析师 (tavily)")
    print("   └─ strategy_advisor - 策略顾问 (tavily)")
    
    return agents


# 为了向后兼容，保留旧版本的函数名
async def create_analysis_team(model_config: Dict[str, Any], 
                             mcp_servers: Optional[Dict[str, Any]] = None) -> List[AssistantAgent]:
    """向后兼容的团队创建函数"""
    import warnings
    warnings.warn("create_analysis_team is deprecated, use create_full_analysis_team instead", 
                 DeprecationWarning, stacklevel=2)
    return await create_full_analysis_team(model_config)