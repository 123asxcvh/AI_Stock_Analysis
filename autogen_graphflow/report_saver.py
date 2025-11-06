#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
简化报告保存模块
只保留核心功能
"""

import os
import sys
from datetime import datetime
from typing import AsyncGenerator, Dict, Any, Optional
from pathlib import Path

import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config import config

class ReportSaver:
    """简化报告保存器"""
    
    def __init__(self, stock_code: str, report_type: str = "stock"):
        self.stock_code = stock_code
        self.report_type = report_type
        self.agent_results = {}
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        base_dir = config.ai_reports_dir
        self.output_dir = base_dir / (stock_code if report_type == "stock" else "market_analysis")
        os.makedirs(self.output_dir, exist_ok=True)
    
    async def process_stream(self, stream: AsyncGenerator) -> Dict[str, str]:
        """处理流式消息"""
        async for message in stream:
            await self._process_message(message)
        
        if self.agent_results:
            await self._save_agent_results()
        
        return self.agent_results
    
    async def _process_message(self, message: Any):
        """处理单个消息"""
        content = message.content
        if content:
            print(f"\n---------- {message.source} ----------")
            print(content)
            print("-" * 60)
            
            content_str = '\n'.join(str(item) for item in content) if isinstance(content, list) else str(content)
            self.agent_results[message.source] = content_str
    
    async def _save_agent_results(self):
        """保存结果到Markdown文件"""
        filepath = self.output_dir / ("agent_report.md" if self.report_type == "stock" else "market_comprehensive_report.md")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            title = f"# {self.stock_code} 股票投资分析报告" if self.report_type == "stock" else "# 市场综合分析报告"
            stock_info = f"**股票代码**: {self.stock_code}\n\n" if self.report_type == "stock" else ""
            
            f.write(f"{title}\n\n**报告生成时间**: {self.timestamp}\n\n{stock_info}**数据来源**: AI分析 + 网络搜索\n\n{'=' * 80}\n\n")
            
            # 添加智能体结果
            for agent_key in ["coordinator_agent", "company_info_researcher", "industry_analyst", 
                            "porter_analyst", "macro_policy_analyst", "stock_analyst", "investment_advisor"]:
                if agent_key in self.agent_results:
                    f.write(f"{self.agent_results[agent_key]}\n\n{'=' * 80}\n\n")
            
            # 添加免责声明
            f.write(f"\n**注**：由于网络搜索工具暂时无法获取最新数据，本分析基于公司基本信息和行业特征进行。建议在实际投资决策前，获取最新的财务报表和行业研究报告进行补充分析。\n")
        
        print(f"📝 报告已保存: {filepath}")
        self._print_message_stats()
    
    def _print_message_stats(self):
        """打印统计信息"""
        print(f"\n📊 消息统计:")
        for agent, content in self.agent_results.items():
            print(f"   {agent}: {len(content)}字符")