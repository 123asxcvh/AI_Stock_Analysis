#!/usr/bin/env/python
# -*- coding: utf-8 -*-

"""
工作流模块
基于 AutoGen 0.4+ 最新API - 8个智能体顺序执行
"""

import asyncio
from typing import List

# AutoGen 0.4+ API
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import DiGraphBuilder, GraphFlow
from autogen_agentchat.conditions import TextMentionTermination


async def create_analysis_workflow(agents: List[AssistantAgent]) -> GraphFlow:
    """创建完整的顺序分析工作流 - 8个智能体顺序执行"""
    name_to_agent = {agent.name: agent for agent in agents}
    
    # 检查必需的8个智能体
    required_agents = [
        "coordinator_agent",       # 1. 协调者
        "company_analyst",         # 2. 公司分析师
        "financial_analyst",       # 3. 财务分析师
        "industry_analyst",        # 4. 行业分析师
        "market_analyst",          # 5. 市场分析师
        "news_analyst",            # 6. 新闻分析师
        "technical_analyst",       # 7. 技术分析师
        "strategy_advisor"         # 8. 策略顾问
    ]
    
    for agent_name in required_agents:
        if agent_name not in name_to_agent:
            raise ValueError(f"缺少必需的智能体: {agent_name}")
    
    # 使用正确的 DiGraphBuilder API
    builder = DiGraphBuilder()
    
    # 添加8个节点
    execution_order = required_agents
    for agent_name in execution_order:
        if agent_name in name_to_agent:
            builder.add_node(name_to_agent[agent_name])
    
    # 构建7个顺序连接链：coordinator → company → financial → industry → market → news → technical → strategy
    for i in range(len(execution_order) - 1):
        current = execution_order[i]
        next_agent = execution_order[i + 1]
        
        if current in name_to_agent and next_agent in name_to_agent:
            builder.add_edge(name_to_agent[current], name_to_agent[next_agent])
    
    # 构建图
    graph = builder.build()
    
    # 创建终止条件
    termination_condition = TextMentionTermination("TERMINATE")
    
    # 创建工作流 - 使用正确的API
    flow = GraphFlow(
        participants=builder.get_participants(),
        graph=graph,
        termination_condition=termination_condition
    )
    
    print("✅ 完整顺序GraphFlow工作流创建 (8个智能体):")
    print("   📋 执行顺序:")
    for i, agent_name in enumerate(execution_order, 1):
        emoji = {
            "coordinator_agent": "🎯",
            "company_analyst": "🏢",
            "financial_analyst": "📊", 
            "industry_analyst": "🏭",
            "market_analyst": "📰",
            "news_analyst": "🗞️",
            "technical_analyst": "📈",
            "strategy_advisor": "💡"
        }.get(agent_name, "🤖")
        
        role = {
            "coordinator_agent": "协调者",
            "company_analyst": "公司基本面分析",
            "financial_analyst": "财务数据分析",
            "industry_analyst": "行业研究分析",
            "market_analyst": "市场情绪分析",
            "news_analyst": "新闻舆情分析",
            "technical_analyst": "技术面分析",
            "strategy_advisor": "整合分析并输出最终投资建议"
        }.get(agent_name, "分析任务")
        
        print(f"   {i}. {emoji} {agent_name} - {role}")
    
    print("   🏁 策略顾问负责输出投资建议并以 TERMINATE 结束")
    print(f"   🔧 工作流配置: {len(execution_order)} 个智能体严格顺序执行")
    
    return flow


# 向后兼容的函数
def create_legacy_workflow(agents: List[AssistantAgent]) -> GraphFlow:
    """向后兼容的工作流创建函数"""
    return asyncio.run(create_analysis_workflow(agents))