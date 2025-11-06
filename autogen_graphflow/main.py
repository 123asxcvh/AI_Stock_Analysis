#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
股票分析主程序
"""

import asyncio
import sys
import os

# AutoGen imports
from autogen_agentchat.ui import Console

# Local imports - 支持两种导入方式
try:
    # 作为模块运行时使用相对导入
    from .config import get_model_config, print_config
    from .agent_factory import create_research_team
    from .mcp_workbench import MCPWorkbenchManager
    from .task import get_research_task
    from .workflow import create_research_workflow
except ImportError:
    # 直接运行时使用绝对导入
    from autogen_graphflow.config import get_model_config, print_config
    from autogen_graphflow.agent_factory import create_research_team
    from autogen_graphflow.mcp_workbench import MCPWorkbenchManager
    from autogen_graphflow.task import get_research_task
    from autogen_graphflow.workflow import create_research_workflow

async def run_research(task: str):
    """运行研究流程"""
    print(f"🚀 智能研究系统")
    print_config()

    workbench_manager = MCPWorkbenchManager()

    async with workbench_manager.get_workbenches() as workbenches:
        agents = create_research_team(get_model_config()["api_key"], workbenches)
        team = create_research_workflow(agents)

        task_description = get_research_task(task)

        await Console(team.run_stream(task=task_description))
        print(f"✅ 研究完成")


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("❌ 用法: python main.py <研究任务>")
        print("   示例: python main.py '分析贵州茅台的投资价值'")
        return

    task = sys.argv[1]
    asyncio.run(run_research(task))


if __name__ == "__main__":
    main()