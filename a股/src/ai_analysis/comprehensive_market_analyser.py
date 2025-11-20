#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
简化综合市场分析器
只保留核心功能
"""

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import asyncio
import aiofiles
import time
from typing import Dict, Any

from config import (
    config, MODEL_NAME,
    AsyncAIAnalyzerBase
)
from src.ai_analysis.prompts.prompt_manager import PromptManager


def get_config():
    return config.ai_reports_dir, MODEL_NAME

def run_main(main_func):
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    try:
        asyncio.run(main_func())
    except KeyboardInterrupt:
        print("用户中断操作")

class AsyncComprehensiveMarketAnalyzer(AsyncAIAnalyzerBase):
    """简化异步综合市场分析器"""

    # 市场分析类型显示名称映射
    MARKET_ANALYSIS_DISPLAY_NAMES = {
        "fund_flow_concept": "概念板块资金流向分析",
        "fund_flow_industry": "行业资金流向分析",
        "fund_flow_individual": "个股资金流向分析",
        "zt_pool": "涨停股票池分析",
        "news_main_cx": "财经新闻舆情分析",
        "market_activity_legu": "市场赚钱效应分析"
    }

    def __init__(self, model_name: str = None):
        super().__init__(model_name)
        self.reports_dir = config.ai_reports_dir / "market_analysis"
        # 确保目录存在
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        # 初始化prompt_manager
        from src.ai_analysis.prompts.prompt_manager import PromptManager
        self.prompt_manager = PromptManager()

    def _get_market_reports_dir(self, output_dir: str) -> Path:
        """
        获取市场分析报告目录

        Args:
            output_dir: 传入的输出目录

        Returns:
            市场分析报告的实际目录路径
        """
        # 如果传入的output_dir就是市场分析目录，直接使用
        output_path = Path(output_dir)
        if output_path.name == "market_analysis":
            return output_path

        # 如果传入的是ai_reports目录，添加market_analysis子目录
        if output_path.name == "ai_reports":
            return output_path / "market_analysis"

        # 其他情况，假设需要在当前目录下查找市场分析报告
        return output_path

    async def process_comprehensive_market_analysis(self, output_dir: str) -> Dict[str, Any]:
        """处理综合市场分析"""
        # 获取市场分析报告的实际目录
        market_reports_dir = self._get_market_reports_dir(output_dir)

        # 设置综合分析报告的输出路径
        output_path = market_reports_dir / "comprehensive.md"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        print(f"🏢 开始综合市场分析...")
        print(f"📂 市场报告目录: {market_reports_dir}")
        print(f"📄 综合报告输出: {output_path}")

        # 收集所有市场分析报告
        analysis_reports = await self._collect_market_analysis_reports(market_reports_dir)

        if not analysis_reports:
            print("❌ 未找到任何市场分析报告")
            return {
                "success": False,
                "output_path": str(output_path),
                "reports_used": [],
                "error": "未找到任何市场分析报告"
            }

        # 构建综合市场分析输入
        comprehensive_input = self._build_comprehensive_market_input(analysis_reports)
        print(f"📊 综合输入构建完成，长度: {len(comprehensive_input)} 字符")

        # 调用AI API进行综合市场分析
        system_prompt, user_prompt = self.prompt_manager.get_comprehensive_market_prompt()
        messages = [
            {"role": "system", "content": self.prompt_manager.get_market_system_prompt(system_prompt)}, 
            {"role": "user", "content": f"{user_prompt}\n\n{comprehensive_input}"}
        ]
        analysis_result = await self._call_ai_api_with_retry(messages) or f"❌ 综合市场分析失败"

        # 保存结果
        await self._save_analysis_result(output_path, analysis_result)
        
        return {
            "success": True,
            "output_path": str(output_path),
            "reports_used": list(analysis_reports.keys())
        }

    async def _collect_market_analysis_reports(self, market_reports_dir: Path) -> Dict[str, str]:
        """收集所有市场分析报告"""
        analysis_reports = {}
        analysis_types = config.supported_market_analysis_types
        found_reports = []

        print(f"📋 开始收集市场分析报告，支持类型: {', '.join(analysis_types)}")
        print(f"📂 搜索目录: {market_reports_dir}")

        for analysis_type in analysis_types:
            report_file = market_reports_dir / f"{analysis_type}.md"

            if not report_file.exists():
                print(f"⚠️ 报告文件不存在: {analysis_type}")
                continue

            try:
                async with aiofiles.open(report_file, 'r', encoding='utf-8') as f:
                    content = await f.read()
                    if content.strip():  # 确保文件不为空
                        analysis_reports[analysis_type] = content
                        found_reports.append(analysis_type)
                        display_name = self._get_market_analysis_display_name(analysis_type)
                        print(f"✅ 成功加载: {display_name}")
                    else:
                        print(f"⚠️ 报告文件为空: {analysis_type}")
            except Exception as e:
                print(f"⚠️ 读取报告文件失败 {analysis_type}: {e}")

        print(f"📈 总共收集到 {len(found_reports)} 份市场分析报告: {', '.join(found_reports)}")
        return analysis_reports

    def _build_comprehensive_market_input(self, analysis_reports: Dict[str, str]) -> str:
        """构建综合市场分析输入"""
        comprehensive_input = "=== 综合市场分析输入 ===\n\n"

        # 按逻辑分组市场分析报告
        sections = {
            "资金流向分析": [],
            "板块分析": [],
            "热点追踪": []
        }

        # 分类各个市场分析类型
        for analysis_type, content in analysis_reports.items():
            if analysis_type in ["fund_flow_individual", "fund_flow_industry", "fund_flow_concept"]:
                sections["资金流向分析"].append((analysis_type, content))
            elif analysis_type == "sector_fund_flow":
                sections["板块分析"].append((analysis_type, content))
            elif analysis_type == "zt_pool":
                sections["热点追踪"].append((analysis_type, content))

        # 构建结构化的综合输入
        for section_name, reports in sections.items():
            if reports:
                comprehensive_input += f"=== {section_name.upper()} ===\n\n"
                for analysis_type, content in reports:
                    display_name = self._get_market_analysis_display_name(analysis_type)
                    comprehensive_input += f"**{display_name}**\n{content}\n\n"
                comprehensive_input += "---\n\n"

        # 添加综合分析要求
        comprehensive_input += "\n=== 综合市场分析要求 ===\n"
        comprehensive_input += "基于以上所有市场分析报告，请提供以下内容的综合分析：\n"
        comprehensive_input += "1. 整体资金流向分析（大单、中单、小单资金动向）\n"
        comprehensive_input += "2. 行业和概念板块资金轮动分析\n"
        comprehensive_input += "3. 板块资金流向排名和热点板块识别\n"
        comprehensive_input += "4. 涨停股票池热点分析和市场情绪评估\n"
        comprehensive_input += "5. 基于资金流向的投资机会识别和风险提示\n"
        comprehensive_input += "6. 具体的投资策略建议（重点关注板块和个股）\n"

        return comprehensive_input

    def _get_market_analysis_display_name(self, analysis_type: str) -> str:
        """获取市场分析类型的显示名称"""
        return self.MARKET_ANALYSIS_DISPLAY_NAMES.get(analysis_type, analysis_type.upper())

    async def _save_analysis_result(self, output_path: Path, content: str):
        """保存分析结果到文件"""
        async with aiofiles.open(output_path, 'w', encoding='utf-8') as f:
            await f.write(content)

async def main():
    """主异步函数"""
    reports_dir, model_name = get_config()
    
    start_time = time.time()
    
    async with AsyncComprehensiveMarketAnalyzer(model_name) as analyzer:
        result = await analyzer.process_comprehensive_market_analysis(str(reports_dir))
        
        total_time = time.time() - start_time
        
        print(f"\n📈 综合市场分析完成!")
        print(f"   分析结果: {'✅ 成功' if result['success'] else '❌ 失败'}")
        print(f"   输出路径: {result['output_path']}")
        print(f"   总耗时: {total_time:.2f} 秒")
        if result['success']:
            print(f"   使用报告: {', '.join(result['reports_used'])}")

if __name__ == "__main__":
    run_main(main)