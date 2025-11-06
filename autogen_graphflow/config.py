#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""配置模块"""
import os
import sys
import threading
from typing import List, Dict, Any, Optional
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 从主配置导入API密钥
from config.config import GEMINI_API_KEYS

# API Key 轮换管理器
class APIKeyRotator:
    """API Key 轮换管理器 - 确保每次使用不同的 key"""
    
    def __init__(self, api_keys: List[str]):
        self.api_keys = api_keys
        self.current_index = 0
        self.lock = threading.Lock()
        self.failed_keys = set()  # 记录失败的 keys
    
    def get_next_key(self) -> str:
        """获取下一个 API key（轮换使用）"""
        with self.lock:
            # 从当前索引开始，找到一个未失败的 key
            start_index = self.current_index
            attempts = 0
            
            while attempts < len(self.api_keys):
                key = self.api_keys[self.current_index]
                self.current_index = (self.current_index + 1) % len(self.api_keys)
                
                if key not in self.failed_keys:
                    return key
                
                attempts += 1
                # 如果转了一圈，说明所有 key 都失败了，清除失败记录并重试
                if self.current_index == start_index:
                    self.failed_keys.clear()
                    return self.api_keys[self.current_index]
        
        # 如果所有 key 都失败，返回第一个
        return self.api_keys[0]
    
    def mark_key_failed(self, api_key: str):
        """标记某个 key 为失败（暂时不使用）"""
        with self.lock:
            self.failed_keys.add(api_key)
    
    def reset_failed_keys(self):
        """重置失败记录"""
        with self.lock:
            self.failed_keys.clear()

# 创建全局轮换器
_api_key_rotator = APIKeyRotator(GEMINI_API_KEYS)

# 模型配置 - 更新为 Gemini
MODEL_CONFIG = {
    "model": "gemini-2.5-flash",
    "base_url": "https://123asxcvh-gemini-94.deno.dev/v1",
    "timeout": 120.0,
    "max_retries": 1,  # 设置为1，因为我们会在外层处理重试和 key 轮换
    "temperature": 0.3,
    "model_info": {
        "vision": False,
        "function_calling": True,
        "json_output": True,
        "family": "Gemini",
        "structured_output": True,
    }
}

# 智能体配置 - 带质量评估循环的新架构
AGENT_NAMES = ["classifier", "research_brief", "supervisor", "research_agent_1", "research_agent_2", "research_agent_3", "investment_advisor"]
AGENT_ROLES = ["意图分类器", "研究简报员", "任务监督者", "研究代理1", "研究代理2", "研究代理3", "投资建议师"]

AGENTS_CONFIG = [
    {"name": name, "role": role, "max_tool_iterations": 10, "reflect_on_tool_use": True}
    for name, role in zip(AGENT_NAMES, AGENT_ROLES)
]

# MCP服务器配置 - 支持投资建议
MCP_SERVERS_CONFIG = [
    {
        "name": "exa",
        "command": "npx",
        "args": [
            "-y",
            "@smithery/cli@latest",
            "run",
            "exa",
            "--key",
            "d7f53aa9-5222-4b5c-8a39-cf8583851579",
            "--profile",
            "missing-scorpion-b6TrHE"
        ],
        "env": {},
        "agents": ["research_agent_1", "research_agent_2", "research_agent_3", "investment_advisor"]
    },
    {
        "name": "time",
        "command": "uvx",
        "args": ["mcp-server-time"],
        "env": {}
    }
]

# 项目配置
PROJECT_CONFIG = {
    "model": MODEL_CONFIG,
    "agents": AGENTS_CONFIG,
    "mcp_servers": MCP_SERVERS_CONFIG,
}

# 配置访问函数
def get_model_config(api_key: Optional[str] = None) -> Dict[str, Any]:
    """获取模型配置，自动轮换 API key"""
    config = PROJECT_CONFIG["model"].copy()
    
    # 如果提供了 api_key，使用提供的；否则从轮换器获取
    if api_key:
        config["api_key"] = api_key
    else:
        config["api_key"] = _api_key_rotator.get_next_key()
    
    return config

def get_next_api_key() -> str:
    """获取下一个 API key（用于轮换）"""
    return _api_key_rotator.get_next_key()

def mark_api_key_failed(api_key: str):
    """标记 API key 为失败"""
    _api_key_rotator.mark_key_failed(api_key)

def reset_failed_api_keys():
    """重置失败的 API keys"""
    _api_key_rotator.reset_failed_keys()

def get_agent_config(agent_name: str) -> Optional[Dict[str, Any]]:
    return next((agent for agent in AGENTS_CONFIG if agent["name"] == agent_name), None)

def get_mcp_servers() -> List[Dict[str, Any]]:
    return MCP_SERVERS_CONFIG

def print_config():
    config = MODEL_CONFIG
    print(f"📋 配置: {config['model']} | {config['base_url']} | 超时: {config['timeout']}s")
    print(f"   API Keys: {len(GEMINI_API_KEYS)}个（轮换使用）")
    print(f"   智能体: {len(AGENT_NAMES)}个 | MCP服务器: {len(MCP_SERVERS_CONFIG)}个")