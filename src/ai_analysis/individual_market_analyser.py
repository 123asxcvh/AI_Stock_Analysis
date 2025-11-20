#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
简化市场AI分析器
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
    config, MODEL_NAME, MAX_CONCURRENCY,
    AsyncAIAnalyzerBase, DataProcessor
)
from src.ai_analysis.prompts.prompt_manager import PromptManager


def get_market_default_config():
    """获取市场分析的默认配置参数"""
    # 从配置系统获取市场分析类型
    supported_market_analysis_types = config.supported_market_analysis_types
    return (
        config.market_data_dir,
        config.ai_reports_dir,
        supported_market_analysis_types,
        MODEL_NAME
    )

def run_main(main_func):
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    try:
        asyncio.run(main_func())
    except KeyboardInterrupt:
        print("用户中断操作")

class AsyncMarketAIAnalyzer(AsyncAIAnalyzerBase):
    """简化异步市场AI分析器"""

    # 数据采样限制配置
    DATA_LIMITS = {
        "fund_flow_concept": 100,      # 概念板块资金流向
        "fund_flow_industry": 50,      # 行业资金流向
        "fund_flow_individual": 50,    # 个股资金流向
        "zt_pool": 50,                 # 涨停股票池
        "news_main_cx": 30,            # 财经新闻（最近1个月）
        "market_activity_legu": 12     # 市场活跃度（全部数据）
    }

    # 智能采样配置 - 对fund_flow_concept和fund_flow_individual进行采样
    SAMPLING_CONFIG = {
        "fund_flow_concept": {"first_percent": 0.7, "last_percent": 0.3, "min_rows": 70},      # 概念板块资金流向需要采样，100行
        "fund_flow_individual": {"first_percent": 0.7, "last_percent": 0.3, "min_rows": 35},  # 个股资金流向需要采样，50行
        "news_main_cx": {"first_percent": 1.0, "last_percent": 0.0, "min_rows": 30},          # 新闻按时间顺序取最新
        "market_activity_legu": {"first_percent": 1.0, "last_percent": 0.0, "min_rows": 12}    # 市场活跃度取全部
    }

    def __init__(self, model_name: str = None):
        super().__init__(model_name)
        self.data_dir = config.data_dir / "cleaned_market_data"
        config.ensure_dir(self.data_dir)
        # 立即初始化prompt_manager，不依赖异步上下文
        from src.ai_analysis.prompts.prompt_manager import PromptManager
        self.prompt_manager = PromptManager()

    def _smart_sample_data(self, df: pd.DataFrame, analysis_type: str) -> pd.DataFrame:
        """
        智能数据采样策略
        - 对于大容量数据，采用前N% + 后M%的策略
        - 既保证包含最新数据，又保留历史数据进行对比

        Args:
            df: 原始数据DataFrame
            analysis_type: 分析类型

        Returns:
            采样后的DataFrame
        """
        total_rows = len(df)
        max_limit = self.DATA_LIMITS.get(analysis_type, 100)

        # 如果数据量不超过限制，直接返回
        if total_rows <= max_limit:
            return df

        # 获取采样配置
        sampling_config = self.SAMPLING_CONFIG.get(analysis_type,
                                                 {"first_percent": 0.6, "last_percent": 0.4, "min_rows": 30})

        first_percent = sampling_config["first_percent"]
        last_percent = sampling_config["last_percent"]
        min_rows = sampling_config["min_rows"]

        # 计算采样行数
        first_rows = int(max_limit * first_percent)
        last_rows = max_limit - first_rows

        # 确保至少有最小行数
        if first_rows < min_rows:
            first_rows = min_rows
            last_rows = max_limit - first_rows

        # 采样数据：前N行 + 后M行
        df_first = df.head(first_rows)
        df_last = df.tail(last_rows)

        # 合并数据
        df_sampled = pd.concat([df_first, df_last], ignore_index=True)

        print(f"📊 {analysis_type}: 智能采样完成 - 原始{total_rows}行 → 采样{len(df_sampled)}行 (前{first_rows}+后{last_rows}行)")

        return df_sampled

    async def process_market_analysis(self, analysis_types: List[str], output_dir: str) -> Dict[str, Any]:
        """处理所有市场分析类型 - 使用信号量控制并发"""
        # 创建输出目录
        market_reports_dir = Path(output_dir)
        market_reports_dir.mkdir(parents=True, exist_ok=True)

        # 创建结果跟踪
        completed_tasks = {"successful": 0, "failed": 0}
        
        # 使用信号量控制并发数（从配置获取最大并发数）
        semaphore = asyncio.Semaphore(MAX_CONCURRENCY)

        async def process_analysis_with_semaphore(analysis_type: str):
            """异步处理单个分析类型，使用信号量控制并发"""
            async with semaphore:
                try:
                    # 从AI配置管理器获取文件映射
                    market_analysis_file_mapping = config.market_analysis_file_mapping
                    required_files = market_analysis_file_mapping[analysis_type]

                    # 读取文件数据（使用智能采样）
                    file_data = {}
                    for filename in required_files:
                        df = await DataProcessor.read_csv_file_async(str(self.data_dir / filename))
                        if df is not None:
                            # 应用智能数据采样
                            original_rows = len(df)
                            df_sampled = self._smart_sample_data(df, analysis_type)
                            print(f"📊 {analysis_type} - {filename}: 原始数据 {original_rows} 行 → 采样后 {len(df_sampled)} 行")
                            file_data[filename] = df_sampled

                    # 构建数据摘要
                    if not file_data:
                        data_summary = f"暂无{analysis_type}的具体数据，请基于市场常识和专业知识进行分析。"
                        print(f"⚠️  {analysis_type} 未读取到数据文件")
                        return True
                    
                    summary_parts = [f"=== {analysis_type.upper()} 市场数据分析 ==="]

                    # 添加采样说明
                    sampling_config = self.SAMPLING_CONFIG.get(analysis_type,
                                                             {"first_percent": 0.6, "last_percent": 0.4})
                    first_percent = int(sampling_config["first_percent"] * 100)
                    last_percent = int(sampling_config["last_percent"] * 100)
                    summary_parts.append(f"**数据说明**: 已应用智能采样策略，选取前{first_percent}% + 后{last_percent}%的数据以兼顾最新趋势和历史对比")
                    summary_parts.append("")

                    total_rows = 0
                    for filename, df in file_data.items():
                        summary_parts.append(f"=== {filename} ===")
                        total_rows += len(df)

                        # 数据已经过智能采样
                        summary_parts.append(f"采样数据行数: {len(df)}")
                        rows_data = df.to_dict('records')
                        for row in rows_data:
                            row_info = " | ".join([f"{col}: {val}" for col, val in row.items() if pd.notna(val)])
                            summary_parts.append(row_info)
                        summary_parts.append("")
                    data_summary = "\n".join(summary_parts)
                    print(f"✅ {analysis_type} 数据准备完成，摘要长度: {len(data_summary)} 字符，采样数据总行数: {total_rows}，文件数: {len(file_data)}")

                    # 调用AI API进行分析
                    prompt_config = self.prompt_manager.get_market_prompt(analysis_type)
                    system_content = self.prompt_manager.get_market_system_prompt(
                        prompt_config.get("market_system_prompt", "market_strategist")
                    )
                    user_prompt = prompt_config.get("market_user_prompt", "请对以下市场数据进行专业分析。")
                    
                    messages = [
                        {"role": "system", "content": system_content},
                        {"role": "user", "content": f"{user_prompt}\n\n**数据输入：**\n{data_summary}"}
                    ]
                    
                    print(f"🔄 {analysis_type} 正在调用AI API...")
                    analysis_result = await self._call_ai_api_with_retry(messages)
                    
                    # 统一处理API调用结果
                    success, processed_result = self._process_api_result(analysis_result, analysis_type)
                    if success:
                        completed_tasks["successful"] += 1
                    else:
                        completed_tasks["failed"] += 1

                    # 保存结果
                    output_path = market_reports_dir / f"{analysis_type}.md"
                    await self._write_analysis_result(output_path, processed_result)
                    
                    print(f"✅ 市场分析 {analysis_type} 处理完成")
                    return True
                except Exception as e:
                    print(f"❌ 市场分析 {analysis_type} 异常: {e}")
                    import traceback
                    traceback.print_exc()
                    completed_tasks["failed"] += 1

                    # 保存错误信息（静默失败）
                    error_content = f"❌ 市场分析 {analysis_type} 异常: {str(e)}\n\n详细错误:\n{traceback.format_exc()}"
                    await self._write_analysis_result_safe(market_reports_dir / f"{analysis_type}.md", error_content)
                    return True

        # 创建并发任务（使用信号量控制，不再使用固定延迟）
        tasks = [
            asyncio.create_task(process_analysis_with_semaphore(analysis_type))
            for analysis_type in analysis_types
        ]

        # 等待所有任务完成
        await asyncio.gather(*tasks, return_exceptions=True)

        # 统计结果
        successful_analyses = completed_tasks["successful"]
        failed_analyses = completed_tasks["failed"]
        
        return {
            "success": True,
            "successful_analyses": successful_analyses,
            "failed_analyses": failed_analyses,
            "total_analyses": len(analysis_types),
            "output_dir": str(market_reports_dir)
        }

    async def _write_analysis_result(self, output_path: str, content: str):
        """异步写入分析结果到文件"""
        async with aiofiles.open(output_path, 'w', encoding='utf-8') as f:
            await f.write(content)

    async def _write_analysis_result_safe(self, output_path: str, content: str):
        """安全写入分析结果到文件（静默失败）"""
        try:
            await self._write_analysis_result(output_path, content)
        except Exception:
            pass

    def _process_api_result(self, analysis_result: str, analysis_type: str) -> tuple[bool, str]:
        """处理API调用结果，返回(成功状态, 处理后结果)"""
        if analysis_result:
            print(f"✅ {analysis_type} API调用成功")
            return True, analysis_result
        else:
            error_result = f"❌ {analysis_type} AI分析失败 - API返回空结果"
            print(f"❌ {analysis_type} API调用返回空结果")
            return False, error_result

async def main():
    """主异步函数"""
    data_dir, output_dir, analysis_types, model_name = get_market_default_config()
    
    start_time = time.time()
    
    print(f"🤖 启动市场AI分析...")
    print(f"📂 数据目录: {data_dir}")
    print(f"📁 输出目录: {output_dir}")
    print(f"🔧 分析类型: {', '.join(analysis_types)}")
    print("=" * 50)
    
    async with AsyncMarketAIAnalyzer(model_name) as analyzer:
        result = await analyzer.process_market_analysis(analysis_types, str(output_dir))
        
        total_time = time.time() - start_time
        
        print("\n" + "=" * 50)
        print("📈 市场AI分析总结")
        print(f"   总分析数: {result['total_analyses']}")
        print(f"   成功分析: {result['successful_analyses']}")
        print(f"   失败分析: {result['failed_analyses']}")
        print(f"   成功率: {result['successful_analyses'] / result['total_analyses'] * 100:.1f}%")
        print(f"   总耗时: {total_time:.2f} 秒")
        print(f"   报告目录: {result['output_dir']}")

if __name__ == "__main__":
    run_main(main)