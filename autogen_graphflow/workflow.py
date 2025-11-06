#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
工作流 - GraphFlow循环架构
使用AutoGen GraphFlow的内置循环机制
"""

from typing import List, Dict

# AutoGen imports - 更新到最新版本
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import DiGraphBuilder, GraphFlow
from autogen_agentchat.conditions import MaxMessageTermination
from autogen_agentchat.messages import BaseChatMessage


def create_research_workflow(agents: List[AssistantAgent]) -> GraphFlow:
    """创建带GraphFlow循环机制的研究团队"""
    name_to_agent: Dict[str, AssistantAgent] = {agent.name: agent for agent in agents}
    builder = DiGraphBuilder()

    # 添加所有节点
    for agent in agents:
        builder.add_node(agent)

    # 获取关键节点
    classifier = name_to_agent["classifier"]
    research_brief = name_to_agent["research_brief"]
    supervisor = name_to_agent["supervisor"]
    investment_advisor = name_to_agent["investment_advisor"]
    research_agents = [
        name_to_agent["research_agent_1"],
        name_to_agent["research_agent_2"],
        name_to_agent["research_agent_3"]
    ]

    # 设置入口点
    builder.set_entry_point(classifier)

    # 第一阶段：线性流程 - 意图分类 → 研究简报 → 任务监督
    builder.add_edge(classifier, research_brief)
    builder.add_edge(research_brief, supervisor)

    # 第二阶段：supervisor分配任务给并行research agents
    for research_agent in research_agents:
        builder.add_edge(supervisor, research_agent)

    # 第三阶段：research agents完成后汇总到investment_advisor
    # 使用activation_condition="any"实现并行等待
    for research_agent in research_agents:
        builder.add_edge(
            research_agent,
            investment_advisor,
            activation_condition="any"
        )

    # 第四阶段：investment_advisor生成报告后返回supervisor进行质量评估
    builder.add_edge(investment_advisor, supervisor)

    # 第五阶段：GraphFlow循环机制
    # 如果质量不合格，循环回supervisor重新分配任务
    # 如果质量合格，supervisor发送TERMINATE消息终止流程
    builder.add_edge(
        supervisor,
        supervisor,  # 自循环回supervisor
        condition=lambda msg: "RESEARCH_AGAIN" in msg.to_model_text(),
        activation_condition="single"
    )

    print(f"✅ 创建GraphFlow循环工作流:")
    print(f"   1. classifier → research_brief → supervisor")
    print(f"   2. supervisor → [3个research_agents] (并行)")
    print(f"   3. [3个research_agents] → investment_advisor (条件激活)")
    print(f"   4. investment_advisor → supervisor (质量评估)")
    print(f"   5. supervisor → supervisor (循环: if 'RESEARCH_AGAIN')")
    print(f"   6. supervisor → TERMINATE (终止: if no 'RESEARCH_AGAIN')")

    # 创建GraphFlow，添加终止条件防止无限循环
    graph = builder.build()
    return GraphFlow(
        participants=agents,
        graph=graph,
        termination_condition=MaxMessageTermination(50),  # 最多50条消息，防止无限循环
        name="ResearchWorkflow"
    )


