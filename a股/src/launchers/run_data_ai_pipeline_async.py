#!/usr/bin/env python

"""
个股AI分析启动脚本（优化版本）
专注于个股数据的AI分析，基于已爬取的数据，使用异步处理提高效率

更新内容：
- 使用优化后的 AsyncStockAIAnalyzer 和 AsyncComprehensiveAnalyzer
- 支持多种分析类型：基本面、技术面、公司档案、新闻、估值、日内交易
- 批量并发处理，提高效率
- 自动整合报告并生成综合投资建议
- 优化异步处理流程
- 清晰的职责分离：单独分析 vs 整合分析
- 统一的配置管理和公共函数
"""

import argparse
import asyncio
import sys
import time
from pathlib import Path

# 添加项目根目录到Python路径

# 获取项目根目录
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 使用统一路径管理
from config import config

# 支持的分析类型（从配置获取，确保一致性）
def get_supported_analysis_types():
    """从配置获取支持的分析类型"""
    from config import config
    return config.supported_stock_analysis_types


async def generate_comprehensive_analysis(stock_code: str, reports_dir: str) -> tuple:
    """生成综合分析报告"""
    from src.ai_analysis.comprehensive_stock_analyser import AsyncComprehensiveAnalyzer
    
    async with AsyncComprehensiveAnalyzer() as comprehensive_analyzer:
        investment_result = await comprehensive_analyzer.process_comprehensive_analysis(
            stock_code=stock_code,
            output_dir=str(reports_dir)
        )
        
        output_path = investment_result.get('output_path', '')
        print(f"✅ 综合投资建议生成成功")
        print(f"   输出路径: {output_path}")
        return output_path, output_path


async def analyze_stock_async(analyzer, stock_code, stock_index, total_stocks, data_dir, reports_dir, analysis_types):
    """异步分析单个股票"""
    print(f"\n📊 分析进度: {stock_index}/{total_stocks}")
    print(f"🎯 正在分析股票: {stock_code}")
    print("-" * 30)

    start_time = time.time()

    # 步骤1: 执行所有分析类型
    print(f"🔄 开始执行所有 {len(analysis_types)} 种分析类型...")
    result = await analyzer.process_stock_analysis(
        stock_code=stock_code,
        analysis_types=analysis_types,
        data_dir=str(data_dir),
        output_dir=str(reports_dir)
    )
    
    successful_analyses = result.get('successful_analyses', 0)
    failed_analyses = result.get('failed_analyses', 0)
    print(f"✅ 批量分析完成: 成功 {successful_analyses} 个, 失败 {failed_analyses} 个")

    # 步骤2: 综合投资建议
    print("\n🔗 开始生成综合投资建议...")
    merged_report_path, investment_report_path = await generate_comprehensive_analysis(stock_code, reports_dir)

    # 总结
    total_time = time.time() - start_time
    print(f"\n📈 {stock_code} 分析总结:")
    print(f"   总耗时: {total_time:.2f} 秒")
    print(f"   成功分析: {successful_analyses}/{len(analysis_types)}")
    print(f"   失败分析: {failed_analyses}")
    print(f"   报告目录: {reports_dir}/{stock_code}")
    print(f"   整合报告: {merged_report_path}")
    print(f"   投资建议: {investment_report_path}")
    return successful_analyses > 0

async def main_async(args):
    """异步主函数"""
    print("🤖 启动个股AI分析（优化版本）...")
    print("=" * 50)
    print("📋 更新内容:")
    print("   - 使用优化后的 AsyncStockAIAnalyzer 和 AsyncComprehensiveAnalyzer")
    print("   - 默认执行所有8种分析类型：公司概况、资产负债表、利润表、现金流量表、财务指标、技术面、新闻、日内交易")
    print("   - 批量并发处理，提高效率")
    print("   - 自动整合报告并生成综合投资建议（已启用）")
    print("   - 优化异步处理流程")
    print("   - 清晰的职责分离：单独分析 vs 整合分析")
    print("   - 统一的配置管理和公共函数")
    print("=" * 50)

    from src.ai_analysis.individual_stock_analyser import (
        AsyncStockAIAnalyzer,
    )
    from src.ai_analysis.comprehensive_stock_analyser import (
        AsyncComprehensiveAnalyzer,
    )
    print("✅ AsyncStockAIAnalyzer个股AI分析器初始化成功")
    print("📊 异步并发处理已启用")
    print("💾 缓存功能已启用")

    # 使用异步上下文管理器 - 参考pdf_processor.py
    async with AsyncStockAIAnalyzer() as analyzer:
        total_stocks = len(args.stock_codes)
        successful_stocks = 0
        start_time = time.time()
        for i, stock_code in enumerate(args.stock_codes, 1):
            data_dir = config.get_stock_dir(stock_code, cleaned=True)
            success = await analyze_stock_async(
                analyzer, stock_code, i, total_stocks, str(data_dir), str(args.output_dir), args.analysis_types
            )
            successful_stocks += success
        total_time = time.time() - start_time
        print("\n" + "=" * 50)
        print("📈 个股AI分析总结（优化版本）")
        print(f"   总股票数: {total_stocks}")
        print(f"   成功分析: {successful_stocks}")
        print(f"   失败分析: {total_stocks - successful_stocks}")
        print(f"   成功率: {successful_stocks / total_stocks * 100:.1f}%")
        print(f"   总耗时: {total_time:.2f} 秒")
        print(f"   报告目录: {args.output_dir}")
        print("\n📊 分析特性:")
        print(f"   ✅ 多类型综合分析（{len(args.analysis_types)}种分析类型）")
        print("   ✅ 自动报告整合（已启用）")
        print("   ✅ 综合投资建议生成（已启用）")
        print("   ✅ 异步并发处理")
        print("   ✅ 智能缓存机制")
        print("   ✅ 优化架构：AsyncStockAIAnalyzer + AsyncComprehensiveAnalyzer")
        print("   ✅ 统一配置管理和公共函数")
        print("\n🎉 优化版本个股AI分析完成!")



async def main():
    """主函数"""
    # 获取支持的分析类型
    supported_types = get_supported_analysis_types()

    parser = argparse.ArgumentParser(
        description="个股AI分析（优化版本，基于已爬取的数据）\n"
                   f"默认执行所有{len(supported_types)}种分析类型：公司概况、资产负债表、利润表、现金流量表、财务指标、技术面、新闻、日内交易\n"
                   "使用 AsyncStockAIAnalyzer 进行单独分析（批量并发处理）\n"
                   "使用 AsyncComprehensiveAnalyzer 进行整合和综合投资建议"
    )
    parser.add_argument("stock_codes", nargs="+", help="股票代码列表")
    parser.add_argument(
        "--config",
        default=str(config.get_config_file_path("config")),
        help="配置文件路径"
    )
    parser.add_argument(
        "--data-dir",
        default=str(config.get_stocks_dir(cleaned=True)),
        help="数据目录（包含股票数据的目录）"
    )
    parser.add_argument(
        "--output-dir",
        default=str(config.ai_reports_dir),
        help="输出目录"
    )
    # 获取支持的分析类型
    supported_types = get_supported_analysis_types()

    parser.add_argument(
        "--analysis-types",
        nargs="+",
        choices=supported_types + ["all"],
        default=supported_types,  # 默认执行所有支持的分析类型
        help="要执行的分析类型（默认：所有支持的分析类型）"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="显示详细的分析过程信息"
    )

    args = parser.parse_args()

    # 处理分析类型参数
    supported_types = get_supported_analysis_types()
    args.analysis_types = supported_types if "all" in args.analysis_types else [t for t in args.analysis_types if t in supported_types] or supported_types

    # 确保输出目录存在
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)

    # 检查数据目录是否存在
    Path(args.data_dir).exists() or print(f"❌ 数据目录不存在: {args.data_dir}")

    print(f"📂 数据目录: {args.data_dir}")
    print(f"📁 输出目录: {args.output_dir}")
    print(f"🔧 分析类型: {', '.join(args.analysis_types)}")

    # 运行异步主函数
    await main_async(args)


if __name__ == "__main__":
    asyncio.run(main())
