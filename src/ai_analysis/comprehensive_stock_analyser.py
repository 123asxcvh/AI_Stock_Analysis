#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
简化综合分析器
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

class AsyncComprehensiveAnalyzer(AsyncAIAnalyzerBase):
    """简化异步综合分析器"""

    # 基本面分析类型配置
    FUNDAMENTAL_ANALYSIS_TYPES = [
        "balance_sheet_analysis",
        "income_statement_analysis",
        "cash_flow_analysis",
        "financial_indicators_analysis"
    ]

    # 分析类型显示名称映射
    ANALYSIS_DISPLAY_NAMES = {
        "company_profile": "公司概况分析",
        "balance_sheet_analysis": "资产负债表分析",
        "income_statement_analysis": "利润表分析",
        "cash_flow_analysis": "现金流量表分析",
        "financial_indicators_analysis": "财务指标分析",
        "technical_analysis": "技术分析",
        "intraday_trading": "日内交易分析"
    }

    # 分析类型分组配置
    ANALYSIS_SECTIONS = {
        "公司概况": ["company_profile"],
        "基本面分析": FUNDAMENTAL_ANALYSIS_TYPES,
        "技术面分析": ["technical_analysis", "intraday_trading"]
    }

    # 分析类型优先级排序
    ANALYSIS_PRIORITY = [
        "company_profile",
        *FUNDAMENTAL_ANALYSIS_TYPES,
        "technical_analysis",
        "intraday_trading"
    ]

    def __init__(self, model_name: str = None):
        super().__init__(model_name)
        self.prompt_manager = PromptManager()
        self.reports_dir = config.ai_reports_dir

    async def process_comprehensive_analysis(self, stock_code: str, output_dir: str) -> Dict[str, Any]:
        """处理单个股票的综合分析"""
        # 从配置获取分析类型
        analysis_types = config.supported_stock_analysis_types
        
        # 创建输出路径
        output_path = Path(output_dir) / stock_code / "comprehensive.md"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 收集所有分析报告
        analysis_reports = await self._collect_analysis_reports(stock_code, analysis_types)

        # 构建综合分析输入
        comprehensive_input = self._build_comprehensive_input(stock_code, analysis_reports)

        # 调用AI API进行综合分析
        analysis_result = await self._call_comprehensive_ai_analysis(stock_code, comprehensive_input)

        # 保存结果
        await self._save_analysis_result(output_path, analysis_result)
        
        return {
            "success": True,
            "stock_code": stock_code,
            "output_path": str(output_path)
        }
    
    async def _collect_analysis_reports(self, stock_code: str, analysis_types: list) -> Dict[str, str]:
        """收集所有分析报告"""
        analysis_reports = {}
        found_reports = []

        print(f"🔄 正在整合 {stock_code} 的分析报告...")

        for analysis_type in analysis_types:
            report_file = self.reports_dir / stock_code / f"{analysis_type}.md"
            if not report_file.exists():
                print(f"   ⚠️ 缺少报告: {self._get_analysis_display_name(analysis_type)}")
                continue

            try:
                async with aiofiles.open(report_file, 'r', encoding='utf-8') as f:
                    content = await f.read()
                    if content.strip():  # 确保文件不为空
                        analysis_reports[analysis_type] = content
                        found_reports.append(analysis_type)
                        print(f"   ✅ 已加载: {self._get_analysis_display_name(analysis_type)}")
                    else:
                        print(f"   ⚠️ 报告为空: {self._get_analysis_display_name(analysis_type)}")
            except Exception as e:
                print(f"   ❌ 读取失败: {self._get_analysis_display_name(analysis_type)}")

        # 特别处理新的基本面分析类型
        available_fundamental = [t for t in self.FUNDAMENTAL_ANALYSIS_TYPES if t in found_reports]
        if available_fundamental:
            fundamental_names = [self._get_analysis_display_name(t) for t in available_fundamental]
            print(f"   💰 基本面分析: {len(available_fundamental)} 份 ({', '.join(fundamental_names)})")

        technical_count = len([t for t in ['technical_analysis', 'intraday_trading'] if t in found_reports])
        if technical_count > 0:
            print(f"   📈 技术面分析: {technical_count} 份")

        print(f"   📋 整合报告: {len(found_reports)} 份分析完成")

        if not analysis_reports:
            print(f"❌ {stock_code} 没有任何可用的分析报告")

        return analysis_reports
    
    def _build_comprehensive_input(self, stock_code: str, analysis_reports: Dict[str, str]) -> str:
        """构建综合分析输入"""
        comprehensive_input = f"=== {stock_code} 综合分析输入 ===\n\n"

        # 将分析报告分组（使用类配置）
        sections = {section_name: [] for section_name in self.ANALYSIS_SECTIONS.keys()}

        # 使用配置优先级和分组进行分类
        for analysis_type in self.ANALYSIS_PRIORITY:
            if analysis_type in analysis_reports:
                content = analysis_reports[analysis_type]

                # 找到该分析类型所属的分组
                for section_name, types_in_section in self.ANALYSIS_SECTIONS.items():
                    if analysis_type in types_in_section:
                        sections[section_name].append((analysis_type, content))
                        break

        # 构建结构化的综合输入
        for section_name, reports in sections.items():
            if reports:
                comprehensive_input += f"=== {section_name.upper()} ===\n\n"
                for analysis_type, content in reports:
                    display_name = self._get_analysis_display_name(analysis_type)
                    comprehensive_input += f"**{display_name}**\n{content}\n\n"
                comprehensive_input += "---\n\n"

        # 添加总结说明
        comprehensive_input += f"\n=== 综合投资决策要求 ===\n"
        comprehensive_input += f"基于以上所有分析报告，请提供以下内容的综合分析：\n"
        comprehensive_input += f"1. 投资价值评估（公司基本面、财务状况、估值水平）\n"
        comprehensive_input += f"2. 技术面分析与操作建议\n"
        comprehensive_input += f"3. 风险因素识别与应对策略\n"
        comprehensive_input += f"4. 明确的投资建议（买入/增持/持有/减持/卖出）及理由\n"

        return comprehensive_input

    def _get_analysis_display_name(self, analysis_type: str) -> str:
        """获取分析类型的显示名称"""
        return self.ANALYSIS_DISPLAY_NAMES.get(analysis_type, analysis_type.upper())

    async def _call_comprehensive_ai_analysis(self, stock_code: str, comprehensive_input: str) -> str:
        """调用AI API进行综合分析"""
        comprehensive_system_prompt, comprehensive_user_prompt = self.prompt_manager.get_comprehensive_prompt(stock_code)
        system_content = self.prompt_manager.get_system_prompt(comprehensive_system_prompt)
        full_user_prompt = f"{comprehensive_user_prompt}\n\n{comprehensive_input}"
        
        messages = [
            {"role": "system", "content": system_content}, 
            {"role": "user", "content": full_user_prompt}
        ]
        return await self._call_ai_api_with_retry(messages) or f"❌ {stock_code} 综合分析失败"
    
    async def _save_analysis_result(self, output_path: Path, analysis_result: str) -> None:
        """保存分析结果"""
        async with aiofiles.open(output_path, 'w', encoding='utf-8') as f:
            await f.write(analysis_result)

async def main():
    """主异步函数"""
    output_dir, model_name = get_config()
    
    if len(sys.argv) < 2:
        print("❌ 用法: python comprehensive_stock_analyser.py <股票代码>")
        return
    
    stock_code = sys.argv[1].strip()
    start_time = time.time()
    
    async with AsyncComprehensiveAnalyzer(model_name) as analyzer:
        result = await analyzer.process_comprehensive_analysis(stock_code, str(output_dir))
        
        total_time = time.time() - start_time
        print(f"\n🎉 {stock_code} 综合报告生成完成!")
        print(f"   ✅ 整合报告: {result['output_path']}")
        print(f"   ⏱️  处理耗时: {total_time:.2f}s")

if __name__ == "__main__":
    run_main(main)