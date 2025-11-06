#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
MCP工作台管理器 - 简化版
基于AutoGen最佳实践
"""

from contextlib import asynccontextmanager, AsyncExitStack

# AutoGen imports
from autogen_ext.tools.mcp import McpWorkbench, StdioServerParams

# Local imports - 支持两种导入方式
try:
    from .config import get_mcp_servers
except ImportError:
    from autogen_graphflow.config import get_mcp_servers


class SimpleMCPManager:
    def __init__(self):
        self.servers = get_mcp_servers()

    @asynccontextmanager
    async def get_workbenches(self):
        """获取MCP工作台"""
        stack = AsyncExitStack()
        workbenches = {}

        for server in self.servers:
            try:
                params = StdioServerParams(
                    command=server["command"],
                    args=server["args"],
                    env=server["env"]
                )
                workbench = await stack.enter_async_context(McpWorkbench(params))
                workbenches[server["name"]] = workbench
                print(f"✅ MCP工作台: {server['name']}")
            except Exception as e:
                print(f"⚠️ MCP工作台 {server['name']} 跳过: {e}")

        try:
            yield workbenches
        finally:
            await stack.aclose()


# 向后兼容
MCPWorkbenchManager = SimpleMCPManager
            

