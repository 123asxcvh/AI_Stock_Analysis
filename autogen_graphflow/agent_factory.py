#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""智能体工厂"""

from typing import List, Optional, Dict, Any

# AutoGen imports
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.tools.mcp import McpWorkbench

# Local imports - 支持两种导入方式
try:
    from .config import get_model_config, get_agent_config, MCP_SERVERS_CONFIG
    from .prompt import get_prompt
except ImportError:
    from autogen_graphflow.config import get_model_config, get_agent_config, MCP_SERVERS_CONFIG
    from autogen_graphflow.prompt import get_prompt


def create_model_client(api_key: str) -> OpenAIChatCompletionClient:
    """创建模型客户端"""
    config = get_model_config()
    return OpenAIChatCompletionClient(**config)


def create_agent(agent_name: str, api_key: str,
                workbenches: Optional[Dict[str, McpWorkbench]] = None) -> AssistantAgent:
    """创建单个智能体"""
    agent_config = get_agent_config(agent_name)

    # 分配MCP工作台
    agent_workbenches = [
        workbenches[server["name"]]
        for server in MCP_SERVERS_CONFIG
        if agent_name in server.get("agents", []) and server["name"] in workbenches
    ] if workbenches else []

    agent = AssistantAgent(
        name=agent_name,
        model_client=create_model_client(api_key),
        workbench=agent_workbenches or None,
        system_message=get_prompt(agent_name),
        reflect_on_tool_use=agent_config["reflect_on_tool_use"],
        max_tool_iterations=10,
    )

    print(f"✅ 创建智能体: {agent_name} ({agent_config['role']})")
    return agent


def create_research_team(api_key: str, workbenches: Optional[Dict[str, McpWorkbench]] = None) -> List[AssistantAgent]:
    """创建研究团队 - 带质量评估循环的新架构"""
    agent_names = ["classifier", "research_brief", "supervisor", "research_agent_1", "research_agent_2", "research_agent_3", "investment_advisor"]

    agents = [create_agent(name, api_key, workbenches) for name in agent_names]
    print(f"✅ 创建研究团队: {len(agents)}个智能体")
    return agents