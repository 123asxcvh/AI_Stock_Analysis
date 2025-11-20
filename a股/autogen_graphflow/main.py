#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
主程序入口
基于 AutoGen 0.4+ 最新API - 修复重复问题，简化流程
"""

import asyncio
import argparse
import sys
import os
from datetime import datetime

# 添加路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from config import get_model_config, print_config
from agent_factory import create_simple_analysis_team, create_full_analysis_team
from workflow import create_analysis_workflow
from task import get_stock_analysis_task
from report_saver import ReportSaver


async def run_stock_analysis(stock_code: str):
    """运行股票分析

    Args:
        stock_code: 股票代码
    """
    try:
        print("📋 AutoGen 0.4+ 股票分析系统 (顺序工作流)")
        print_config()

        # 创建完整的8智能体团队
        model_config = get_model_config()
        agents = await create_full_analysis_team(model_config)
        print("\n🔄 使用完整顺序工作流 (8个智能体)")

        # 创建顺序工作流
        from workflow import create_analysis_workflow
        team = await create_analysis_workflow(agents)

        # 执行分析
        task_description = get_stock_analysis_task(stock_code)
        
        print(f"\n🚀 开始分析: {stock_code}")
        print("   📝 使用 GraphFlow 流式处理")
        print("   🤖 智能体团队协作分析中...")
        
        # 使用新的ReportSaver处理流
        report_saver = ReportSaver()

        # 设置用户请求信息
        report_saver.set_user_request(task_description)

        # 处理流并收集结果
        agent_results = await report_saver.process_stream(team.run_stream(task=task_description), stock_code)

        if agent_results:
            print(f"\n✅ 分析完成！智能体数量: {len(agent_results)}")
            print(f"   📁 报告已保存到 reports/ 目录")
        else:
            print("\n⚠️ 未收到任何分析结果")
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


async def test_setup():
    """测试设置"""
    print("🧪 测试 AutoGen 0.4+ 设置...")
    
    try:
        # 测试模型配置
        model_config = get_model_config()
        print(f"✅ 模型配置: {model_config['name']}")
        
        # 测试完整团队创建
        full_agents = await create_full_analysis_team(model_config)
        print(f"✅ 完整团队创建: {len(full_agents)} 个智能体")

        # 测试工作流创建
        from workflow import create_analysis_workflow

        sequential_flow = await create_analysis_workflow(full_agents)
        print(f"✅ 顺序工作流创建: 8个智能体顺序执行")
        
        print("🎉 测试完成！")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="AutoGen 0.4+ 股票分析系统 (8智能体顺序执行)",
        epilog="""
示例:
  python main.py 600519                  # 分析贵州茅台
  python main.py --test                  # 测试系统设置
        """
    )

    parser.add_argument("stock_code", nargs="?", help="股票代码")
    parser.add_argument("--test", action="store_true", help="测试设置")

    args = parser.parse_args()

    if args.test:
        asyncio.run(test_setup())
    elif args.stock_code:
        asyncio.run(run_stock_analysis(args.stock_code.upper()))
    else:
        parser.print_help()
        print("\n💡 系统特性:")
        print("   • 8个专业智能体顺序执行")
        print("   • 协调者制定分析策略")
        print("   • 完整的股票分析流程")
        print("   • 使用 DiGraphBuilder 正确API")
        print("   • 纯AutoGen 0.4+架构")
        print("\n🎯 智能体团队:")
        print("   coordinator_agent - 协调者")
        print("   company_analyst - 公司基本面分析")
        print("   financial_analyst - 财务数据分析")
        print("   industry_analyst - 行业分析")
        print("   market_analyst - 市场分析")
        print("   news_analyst - 新闻舆情分析")
        print("   technical_analyst - 技术分析")
        print("   strategy_advisor - 投资策略建议")
        print("\n🚀 顺序执行，避免重复，提高分析质量！")


if __name__ == "__main__":
    main()