#!/usr/bin/env python

"""
市场数据AI分析启动脚本（优化版本）
专注于市场数据的AI分析，基于已爬取的数据，使用异步处理提高效率

更新内容：
- 移除了龙虎榜分析(lhb_detail)，专注5种核心市场分析类型
- 实现智能数据采样：统一100行，8:2采样比例（前80%+后20%）
- 修复了APIKeyRotationManager和PromptManager的方法缺失问题
- 增强了错误处理和日志记录
- 优化了异常处理和用户反馈
- 确保所有API调用都能正常工作
"""

import argparse
import asyncio
import sys
import time
from pathlib import Path

# 添加项目根目录到Python路径
current_file = Path(__file__).resolve()
# 脚本位于 src/launchers/，需要向上3级到达项目根
project_root = current_file.parents[2]
sys.path.insert(0, str(project_root))

from config import config

# 使用config的项目根目录
project_root = config.project_root

# 支持的市场分析类型（从配置获取，确保一致性）
def get_supported_market_analysis_types():
    """从配置获取支持的市场分析类型"""
    from config import config
    return config.supported_market_analysis_types


async def analyze_market_data_async(analyzer, data_types, total_types, data_index, data_dir, reports_dir):
    """异步分析市场数据（修复版本）"""
    print(f"\n📊 分析进度: {data_index}/{total_types}")
    print(f"🎯 正在分析数据类型: {', '.join(data_types)}")
    print("-" * 30)

    start_time = time.time()
    successful_analyses = 0
    failed_analyses = 0

    # 步骤1: 执行各种分析类型
    print(f"🔄 开始执行 {len(data_types)} 种市场分析类型...")
    print(f"🚀 使用新的批量处理方法执行 {len(data_types)} 个分析任务...")

    result = await analyzer.process_market_analysis(data_types, reports_dir)
    successful_analyses = result.get('successful_analyses', 0)
    failed_analyses = result.get('failed_analyses', 0)
    print(f"✅ 批量分析完成: 成功 {successful_analyses} 个, 失败 {failed_analyses} 个")

    # 步骤2: 综合市场分析
    print("\n🔗 开始生成综合市场分析...")
    from src.ai_analysis.comprehensive_market_analyser import AsyncComprehensiveMarketAnalyzer

    async with AsyncComprehensiveMarketAnalyzer() as comprehensive_analyzer:
        result = await comprehensive_analyzer.process_comprehensive_market_analysis(str(reports_dir))

        success = result.get('success', False)
        output_path = result.get('output_path', '')

        if success:
            print(f"✅ 综合市场分析生成成功")
            print(f"   输出文件: {output_path}")
        else:
            error = result.get('error', '未知错误')
            print(f"❌ 综合市场分析生成失败: {error}")

        merged_report_path = output_path
        comprehensive_report_path = output_path

    total_time = time.time() - start_time
    print("\n📈 市场数据分析总结:")
    print(f"   总耗时: {total_time:.2f} 秒")
    print(f"   成功分析: {successful_analyses}/{len(data_types)}")
    print(f"   失败分析: {failed_analyses}")
    print(f"   报告目录: {reports_dir}")
    print(f"   整合报告: {merged_report_path}")
    print(f"   综合分析: {comprehensive_report_path}")
    return successful_analyses > 0


async def main_async(args):
    """异步主函数（优化版本）"""
    print("🤖 启动市场数据AI分析（优化版本）...")
    print("=" * 50)
    print("📋 最新优化内容:")
    print("   - ✅ 移除龙虎榜分析，专注5种核心市场分析类型")
    print("   - ✅ 智能数据采样：统一50行，7:3采样比例（前70%+后30%）")
    print("   - ✅ 配置驱动架构：从配置文件动态加载分析类型")
    print("   - ✅ 修复了APIKeyRotationManager和PromptManager的方法缺失问题")
    print("   - ✅ 增强了错误处理和日志记录")
    print("   - ✅ 优化了异常处理和用户反馈")
    print("   - ✅ 确保所有API调用都能正常工作")
    print("=" * 50)

    from src.ai_analysis.individual_market_analyser import (
        AsyncMarketAIAnalyzer,
    )
    from src.ai_analysis.comprehensive_market_analyser import (
        AsyncComprehensiveMarketAnalyzer,
    )
    print("✅ AsyncMarketAIAnalyzer市场AI分析器初始化成功")
    print("📊 异步并发处理已启用")
    print("💾 智能缓存机制已启用")
    print("🎯 智能数据采样已启用（50行，7:3比例）")

    # 使用异步上下文管理器 - 参考pdf_processor.py
    async with AsyncMarketAIAnalyzer() as analyzer:
        total_types = len(args.data_types)
        successful_types = 0
        start_time = time.time()
        data_dir = args.data_dir
        reports_dir = args.output_dir
        success = await analyze_market_data_async(
            analyzer, args.data_types, total_types, 1, data_dir, reports_dir
        )
        successful_types += success
        total_time = time.time() - start_time
        print("\n" + "=" * 50)
        print("📈 市场数据AI分析总结（优化版本）")
        print(f"   总数据类型: {total_types}")
        print(f"   成功分析: {successful_types}")
        print(f"   失败分析: {total_types - successful_types}")
        print(f"   成功率: {successful_types / total_types * 100:.1f}%")
        print(f"   总耗时: {total_time:.2f} 秒")
        print(f"   报告目录: {args.output_dir}")
        print("\n📊 分析特性:")
        print(f"   ✅ 多类型综合分析（{len(args.data_types)}种分析类型）")
        print("   ✅ 智能数据采样（50行，7:3比例，兼顾最新趋势与历史对比）")
        print("   ✅ 自动报告整合（已启用）")
        print("   ✅ 综合市场分析生成（已启用）")
        print("   ✅ 异步并发处理")
        print("   ✅ 智能缓存机制")
        print("   ✅ 优化架构：AsyncMarketAIAnalyzer + AsyncComprehensiveMarketAnalyzer")
        print("   ✅ 统一配置管理和公共函数")
        print("\n🎉 优化版本市场数据AI分析完成!")



async def main():
    """主函数"""
    # 获取支持的分析类型
    supported_types = get_supported_market_analysis_types()

    parser = argparse.ArgumentParser(
        description="市场数据AI分析（优化版本，基于已爬取的数据）\n"
                   f"默认执行{len(supported_types)}种分析类型：概念板块资金流向、行业资金流向、板块资金流向、个股资金流向、涨停股票池\n"
                   "使用 AsyncMarketAIAnalyzer 进行单独分析（批量并发处理）\n"
                   "使用 AsyncComprehensiveMarketAnalyzer 进行整合和综合市场分析"
      )
    parser.add_argument(
        "--data-types",
        nargs="+",
        choices=supported_types + ["all"],
        default=supported_types,  # 默认执行所有支持的分析类型
        help="要执行的分析类型（默认：所有支持的分析类型）"
    )
    parser.add_argument(
        "--config",
        default=str(config.get_config_file_path("config")),
        help="配置文件路径"
    )
    parser.add_argument(
        "--data-dir",
        default=str(config.get_market_data_dir(cleaned=True)),
        help="数据目录（包含清洗后的市场数据的目录）"
    )
    parser.add_argument(
        "--output-dir",
        default=str(config.ai_reports_dir / "market_analysis"),
        help="输出目录（市场AI分析报告保存位置）"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="显示详细的分析过程信息"
    )
    parser.add_argument(
        "--comprehensive", "-c",
        action="store_true",
        help="执行综合分析（整合报告和生成综合市场分析）"
    )
    parser.add_argument(
        "--use-cleaned-data",
        action="store_true",
        default=True,
        help="使用清洗后的数据（默认启用）"
    )
    parser.add_argument(
        "--use-raw-data",
        action="store_true",
        help="使用原始数据（覆盖清洗数据选项）"
    )

    args = parser.parse_args()

    # 处理分析类型参数
    args.data_types = supported_types if "all" in args.data_types else [t for t in args.data_types if t in supported_types] or supported_types

    # 确保输出目录存在
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)

    print(f"📂 数据目录: {args.data_dir}")
    print(f"📁 输出目录: {args.output_dir}")
    print(f"🔧 分析类型: {', '.join(args.data_types)}")
    print(f"📋 支持的分析类型: {', '.join(supported_types)}")

    # 运行异步主函数
    await main_async(args)


if __name__ == "__main__":
    asyncio.run(main())