#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
简化AI分析器
只保留核心功能
"""

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
import asyncio
import aiofiles
import time
from typing import Dict, Any, List
from datetime import datetime

from config import (
    config, cache_manager, MODEL_NAME, MAX_CONCURRENCY,
    AsyncAIAnalyzerBase, DataProcessor
)
from src.ai_analysis.prompts.prompt_manager import PromptManager

def get_config():
    # 从配置系统获取分析类型和映射
    supported_analysis_types = config.supported_stock_analysis_types
    return config.cleaned_stocks_dir, config.ai_reports_dir, supported_analysis_types, MODEL_NAME

def run_main(main_func):
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    try:
        asyncio.run(main_func())
    except KeyboardInterrupt:
        print("用户中断操作")

class AsyncStockAIAnalyzer(AsyncAIAnalyzerBase):
    """简化异步股票AI分析器"""

    # 缓存分析类型配置
    CACHEABLE_ANALYSIS_TYPES = [
        "company_profile",
        "balance_sheet_analysis",
        "income_statement_analysis",
        "cash_flow_analysis",
        "financial_indicators_analysis"
    ]

    # 数据采样限制配置
    DATA_LIMITS = {
        "technical_analysis": 100,
        "intraday_trading": 100
    }

    def __init__(self, model_name: str = None):
        super().__init__(model_name)
        # 立即初始化prompt_manager，不依赖异步上下文
        from src.ai_analysis.prompts.prompt_manager import PromptManager
        self.prompt_manager = PromptManager()

    async def _process_single_analysis_async(self, stock_code: str, analysis_type: str,
                                            data_dir: str, output_path: str) -> bool:
        """异步处理单个分析任务"""

        # 检查缓存
        if analysis_type in self.CACHEABLE_ANALYSIS_TYPES:
            analysis_result = await cache_manager.load_from_cache(stock_code, "multi_file_data", analysis_type)
            if analysis_result:
                await self._write_analysis_result(output_path, analysis_result)
                return True

        # 从AI配置管理器获取分析类型与文件的映射
        analysis_config = config
        analysis_file_mapping = analysis_config.analysis_file_mapping

        # AI分析需要的historical_quotes列
        HISTORICAL_QUOTES_AI_COLUMNS = [
            '日期', '开盘', '收盘', '最高', '最低', '成交量',
            'MACD_HIST', 'DAILY_KDJ_J', 'RSI', 'BBI', 'MA5', 'MA10'
        ]

        # 读取文件数据
        file_data = {}
        data_dir_path = Path(data_dir)  # 确保使用 Path 对象处理路径
        for filename in analysis_file_mapping[analysis_type]:
            file_path = str(data_dir_path / filename)  # 使用 Path 拼接，然后转为字符串
            df = await DataProcessor.read_csv_file_async(file_path)
            if df is not None:
                # 对于historical_quotes.csv，只读取AI分析需要的列
                if filename == 'historical_quotes.csv' and len(df.columns) > 12:
                    # 检查是否包含所有需要的列
                    available_columns = [col for col in HISTORICAL_QUOTES_AI_COLUMNS if col in df.columns]
                    if available_columns:
                        df = df[available_columns]
                        print(f"📊 {stock_code} historical_quotes.csv 已筛选为 {len(available_columns)} 个AI分析列")

                df_filtered = await DataProcessor.filter_data_by_time(df, filename)
                file_data[filename] = df_filtered

        # 构建数据摘要
        summary_parts = [f"=== {stock_code} {analysis_type.upper()} 数据分析 ==="]

        # 为所有分析类型添加公司上下文信息
        # 直接从CSV提取公司信息并拼接到prompt中
        company_info = await self._extract_company_info_csv(stock_code, data_dir)

        if company_info:
            # 直接将公司信息拼接到数据摘要中
            summary_parts.append("### 公司背景信息")
            summary_parts.append(f"公司名称：{company_info.get('公司名称', stock_code)}")
            summary_parts.append(f"股票代码：{stock_code}")
            summary_parts.append(f"所属行业：{company_info.get('所属行业', '未知')}")
            summary_parts.append(f"主营业务：{company_info.get('主营业务', '未知')}")
            summary_parts.append(f"公司简介：{company_info.get('机构简介', '暂无公司详细信息')}")
            summary_parts.append("")
            summary_parts.append("重要说明：请在分析报告中使用上述公司信息，不要显示为'未知'。")
            summary_parts.append("")

        # 使用类配置处理数据采样限制
        limit = None if analysis_type == "fundamental_analysis" else self.DATA_LIMITS.get(analysis_type)

        for filename, df in file_data.items():
            summary_parts.append(f"=== {filename} ===")
            
            if limit and len(df) > limit:
                df_sample = df.head(limit)
                summary_parts.append(f"数据总行数: {len(df)}, 显示最近{limit}行:")
            else:
                df_sample = df
            
            # 优化：使用 to_dict('records') 代替 iterrows()，性能更好
            rows_data = df_sample.to_dict('records')
            for row in rows_data:
                row_info = " | ".join([f"{col}: {val}" for col, val in row.items() if pd.notna(val)])
                summary_parts.append(row_info)
            summary_parts.append("")

        combined_summary = "\n".join(summary_parts)

        # 获取提示词并调用AI API
        system_prompt, user_prompt = self.prompt_manager.get_stock_prompt(analysis_type, stock_code)
        messages = [
            {"role": "system", "content": self.prompt_manager.get_system_prompt(system_prompt)},
            {"role": "user", "content": f"{user_prompt}\n\n{combined_summary}"}
        ]
        
        print(f"🔄 {stock_code} {analysis_type} 正在调用AI API...")
        analysis_result = await self._call_ai_api_with_retry(messages)

        # 统一处理API调用结果
        if not analysis_result:
            analysis_result = f"❌ {analysis_type} AI分析失败 - API返回空结果"
            self._log_api_result(stock_code, analysis_type, False)
        else:
            self._log_api_result(stock_code, analysis_type, True)

        # 保存缓存和写入文件
        if analysis_result:
            if analysis_type in self.CACHEABLE_ANALYSIS_TYPES:
                await cache_manager.save_to_cache(stock_code, "multi_file_data", analysis_type, analysis_result)
            await self._write_analysis_result(output_path, analysis_result)

        return bool(analysis_result)

    async def _write_analysis_result(self, output_path: str, analysis_result: str):
        """异步写入分析结果到文件"""
        async with aiofiles.open(output_path, 'w', encoding='utf-8') as f:
            await f.write(analysis_result)

    def _log_api_result(self, stock_code: str, analysis_type: str, success: bool):
        """记录API调用结果"""
        if success:
            print(f"✅ {stock_code} {analysis_type} API调用成功")
        else:
            print(f"❌ {stock_code} {analysis_type} API调用返回空结果")

    async def _extract_company_info_csv(self, stock_code: str, data_dir: str) -> dict:
        """直接从CSV提取公司信息"""
        try:
            import pandas as pd
            from io import StringIO
            import aiofiles

            company_info_file = Path(data_dir) / "company_profile.csv"
            if not company_info_file.exists():
                return {}

            async with aiofiles.open(company_info_file, 'r', encoding='utf-8') as f:
                content = await f.read()
                df = pd.read_csv(StringIO(content))

                if df.empty or '字段名' not in df.columns or '字段值' not in df.columns:
                    return {}

                # 提取关键字段
                company_info = dict(zip(df['字段名'], df['字段值']))

                # 返回关键字段
                return {
                    '公司名称': company_info.get('公司名称', stock_code),
                    '所属行业': company_info.get('所属行业', '未知'),
                    '主营业务': company_info.get('主营业务', '未知'),
                    '机构简介': company_info.get('机构简介', '暂无公司详细信息')
                }

        except Exception as e:
            print(f"⚠️ 提取公司信息失败 {stock_code}: {e}")
            return {}

    async def process_stock_analysis(self, stock_code: str, analysis_types: List[str],
                                   data_dir: str, output_dir: str) -> Dict[str, Any]:
        """处理单个股票的所有分析类型 - 使用信号量控制并发"""
        stock_reports_dir = Path(output_dir) / stock_code
        stock_reports_dir.mkdir(parents=True, exist_ok=True)

        # 创建结果跟踪
        completed_tasks = {"successful": 0, "failed": 0}
        
        # 使用信号量控制并发数（从配置获取最大并发数）
        semaphore = asyncio.Semaphore(MAX_CONCURRENCY)

        async def process_type_with_semaphore(analysis_type: str):
            """异步处理单个分析类型，使用信号量控制并发"""
            async with semaphore:
                result = await self._process_single_analysis_async(
                    stock_code, analysis_type, data_dir, 
                    str(stock_reports_dir / f"{analysis_type}.md")
                )
                status = "成功" if result else "失败"
                completed_tasks["successful" if result else "failed"] += 1
                print(f"{'✅' if result else '❌'} {stock_code} {analysis_type} 分析{status}")
                return result

        # 创建并发任务（使用信号量控制，不再使用固定延迟）
        tasks = [
            asyncio.create_task(process_type_with_semaphore(analysis_type))
            for analysis_type in analysis_types
        ]

        # 等待所有任务完成
        await asyncio.gather(*tasks, return_exceptions=True)

        return {
            "success": True,
            "stock_code": stock_code,
            "successful_analyses": completed_tasks["successful"],
            "failed_analyses": completed_tasks["failed"],
            "total_analyses": len(analysis_types),
            "output_dir": str(stock_reports_dir)
        }

async def main():
    """主异步函数"""
    data_base_dir, output_dir, analysis_types, model_name = get_config()

    if len(sys.argv) < 2:
        print("❌ 用法: python individual_stock_analyser.py <股票代码>")
        return

    stock_code = sys.argv[1].strip()
    start_time = time.time()

    # 构建正确的数据目录路径
    stock_data_dir = config.get_stock_dir(stock_code, cleaned=True)

    print(f"🤖 股票AI分析 | {stock_code}")
    print(f"📂 数据: {stock_data_dir}")
    print(f"📁 输出: {output_dir}")
    print("=" * 50)

    async with AsyncStockAIAnalyzer(model_name) as analyzer:
        result = await analyzer.process_stock_analysis(
            stock_code, analysis_types, str(stock_data_dir), str(output_dir)
        )
        
        total_time = time.time() - start_time
        print(f"\n📈 分析完成 | 成功率: {result['successful_analyses']}/{result['total_analyses']} | 耗时: {total_time:.2f}s")
        print(f"📁 报告目录: {result['output_dir']}")

if __name__ == "__main__":
    run_main(main)