#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
MCP工作台管理器
管理MCP服务器 - 基于 AutoGen 0.4+ 正确API
基于官方文档的最佳实践
"""

import asyncio
from contextlib import asynccontextmanager
from typing import Dict, List, Optional, Any

# AutoGen 0.4+ 正确的导入路径
from autogen_ext.tools.mcp import McpWorkbench, StdioServerParams, mcp_server_tools
from autogen_agentchat.agents import AssistantAgent

from config import get_mcp_servers


class MCPWorkbenchManager:
    """MCP工作台管理器 - 基于 AutoGen 0.4+ 正确API"""

    def __init__(self):
        self.server_configs = {}
        self.workbenches = {}
        self._initialized = False

    async def initialize(self):
        """初始化MCP服务器配置"""
        mcp_servers = get_mcp_servers()
        
        for server_config in mcp_servers:
            server_name = server_config["name"]
            self.server_configs[server_name] = server_config
        
        self._initialized = True
        print(f"✅ MCP工作台管理器初始化完成 (AutoGen 0.4+) - {len(self.server_configs)} 个服务器配置")

    def create_server_params(self, server_config: Dict[str, Any]) -> StdioServerParams:
        """
        创建StdioServerParams - AutoGen 0.4+ 标准方式
        
        Args:
            server_config: 服务器配置字典
            
        Returns:
            StdioServerParams: 服务器参数
        """
        return StdioServerParams(
            command=server_config["command"],
            args=server_config["args"],
            env=server_config.get("env", {}),
            read_timeout_seconds=60,  # 增加超时时间
        )

    @asynccontextmanager
    async def get_workbenches(self) -> Dict[str, McpWorkbench]:
        """
        获取所有MCP工作台 - 使用正确的 AutoGen 0.4+ API

        Returns:
            Dict[str, McpWorkbench]: 服务器名称到工作台的映射
        """
        if not self._initialized:
            await self.initialize()

        workbenches = {}
        started_workbenches = []

        try:
            # 使用正确的 AutoGen 0.4+ API - 直接创建McpWorkbench
            for server_name, server_config in self.server_configs.items():
                try:
                    print(f"🔄 正在启动MCP服务器: {server_name}")
                    
                    # 创建服务器参数
                    server_params = self.create_server_params(server_config)
                    
                    # 直接创建 McpWorkbench 实例
                    workbench = McpWorkbench(server_params=server_params)
                    
                    workbenches[server_name] = workbench
                    started_workbenches.append(workbench)
                    print(f"✅ MCP服务器 {server_name} 配置成功")
                    
                except Exception as e:
                    print(f"❌ MCP服务器 {server_name} 配置失败: {e}")
                    # 继续尝试其他服务器
                    continue

            print(f"🔧 已配置MCP服务器数量: {len(workbenches)}/{len(self.server_configs)}")
            if workbenches:
                print(f"   可用服务器: {', '.join(workbenches.keys())}")

            yield workbenches

        finally:
            # 确保所有启动的工作台都被正确关闭
            for workbench in started_workbenches:
                try:
                    if hasattr(workbench, 'close'):
                        await workbench.close()
                    elif hasattr(workbench, 'stop'):
                        await workbench.stop()
                    print(f"🔄 已关闭MCP工作台")
                except Exception as e:
                    print(f"⚠️  关闭MCP工作台时出错: {e}")

    async def get_tools_for_server(self, server_name: str) -> List[Any]:
        """
        获取指定MCP服务器的工具列表 - 使用正确的 mcp_server_tools API

        Args:
            server_name: MCP服务器名称

        Returns:
            List[Any]: 工具列表
        """
        if not self._initialized:
            await self.initialize()

        if server_name not in self.server_configs:
            raise ValueError(f"未知的MCP服务器: {server_name}")

        try:
            print(f"🔄 正在获取MCP工具: {server_name}")
            server_config = self.server_configs[server_name]
            
            # 使用正确的 AutoGen 0.4+ API
            server_params = self.create_server_params(server_config)
            tools = await mcp_server_tools(server_params)
            
            print(f"✅ 成功获取 {len(tools)} 个工具 from {server_name}")
            return tools
            
        except Exception as e:
            print(f"❌ 获取MCP工具失败 {server_name}: {e}")
            return []

    async def create_agent_with_mcp_tools(
        self,
        agent_name: str,
        model_client,
        system_message: str,
        server_names: Optional[List[str]] = None
    ) -> AssistantAgent:
        """
        创建带有MCP工具的智能体 - 使用正确的 AutoGen 0.4+ API

        Args:
            agent_name: 智能体名称
            model_client: 模型客户端
            system_message: 系统消息
            server_names: 要使用的MCP服务器名称列表，None表示使用所有服务器

        Returns:
            AssistantAgent: 配置好MCP工具的智能体
        """
        if not self._initialized:
            await self.initialize()

        # 确定要使用的服务器
        if server_names is None:
            server_names = list(self.server_configs.keys())

        all_tools = []

        # 收集所有指定服务器的工具
        for server_name in server_names:
            if server_name in self.server_configs:
                try:
                    tools = await self.get_tools_for_server(server_name)
                    all_tools.extend(tools)
                    print(f"✅ 为 {agent_name} 添加了 {len(tools)} 个工具 from {server_name}")
                except Exception as e:
                    print(f"⚠️  无法从 {server_name} 获取工具: {e}")
            else:
                print(f"⚠️  未知服务器: {server_name}")

        # 创建智能体 - 使用正确的 AutoGen 0.4+ API
        agent = AssistantAgent(
            name=agent_name,
            model_client=model_client,
            tools=all_tools,  # 直接传递工具列表
            system_message=system_message,
        )

        print(f"✅ 智能体 {agent_name} 创建完成，总工具数: {len(all_tools)}")
        return agent

    async def test_mcp_connection(self, server_name: str) -> bool:
        """
        测试MCP服务器连接

        Args:
            server_name: 服务器名称

        Returns:
            bool: 连接是否成功
        """
        try:
            tools = await self.get_tools_for_server(server_name)
            return len(tools) > 0
        except Exception as e:
            print(f"❌ 测试MCP连接失败 {server_name}: {e}")
            return False

    async def list_available_tools(self) -> Dict[str, List[str]]:
        """
        列出所有可用的MCP工具

        Returns:
            Dict[str, List[str]]: 服务器名称到工具名称列表的映射
        """
        tools_by_server = {}
        
        for server_name in self.server_configs.keys():
            try:
                tools = await self.get_tools_for_server(server_name)
                tool_names = [getattr(tool, 'name', str(tool)) for tool in tools]
                tools_by_server[server_name] = tool_names
                print(f"📋 {server_name}: {len(tool_names)} 个工具")
            except Exception as e:
                print(f"⚠️  无法列出 {server_name} 的工具: {e}")
                tools_by_server[server_name] = []
        
        return tools_by_server

    @asynccontextmanager
    async def get_mcp_tools(self, server_name: str):
        """
        获取指定MCP服务器的工具列表 - 向后兼容方法

        Args:
            server_name: MCP服务器名称
        """
        tools = await self.get_tools_for_server(server_name)
        yield tools


# 便捷函数
async def create_mcp_manager() -> MCPWorkbenchManager:
    """
    创建并初始化MCP工作台管理器

    Returns:
        MCPWorkbenchManager: 初始化好的管理器
    """
    manager = MCPWorkbenchManager()
    await manager.initialize()
    return manager


async def test_all_mcp_servers() -> Dict[str, bool]:
    """
    测试所有MCP服务器连接

    Returns:
        Dict[str, bool]: 服务器名称到连接状态的映射
    """
    manager = await create_mcp_manager()
    results = {}
    
    for server_name in manager.server_configs.keys():
        results[server_name] = await manager.test_mcp_connection(server_name)
    
    return results