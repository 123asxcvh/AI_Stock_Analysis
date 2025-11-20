#!/usr/bin/env python

"""
异步市场数据处理流水线
功能：市场数据爬取 -> 数据清洗
"""

import argparse
import subprocess
import sys
import time
from datetime import datetime
import os
from pathlib import Path

# 添加项目根目录到Python路径
current_file = Path(__file__).resolve()
# 脚本位于 src/launchers/，需要向上3级到达项目根
project_root = current_file.parents[2]
sys.path.insert(0, str(project_root))

from config import config

# 使用config的项目根目录
PROJECT_ROOT = config.project_root

def run_market_data_collection():
    """执行市场数据爬取"""
    print("\n🔄 步骤1: 市场数据爬取")
    start_time = time.time()
    subprocess.run(["python", "-m", "src.crawling.market_data_collector"], cwd=str(PROJECT_ROOT))
    duration = time.time() - start_time
    print(f"✅ 市场数据爬取完成，耗时: {duration:.2f}秒")
    return duration


def run_market_data_cleaning():
    """执行市场数据清洗"""
    print("\n🔄 步骤2: 市场数据清洗")
    start_time = time.time()
    subprocess.run(["python", "-m", "src.cleaning.market_data_cleaner"], cwd=str(PROJECT_ROOT))
    duration = time.time() - start_time
    print(f"✅ 市场数据清洗完成，耗时: {duration:.2f}秒")
    return duration


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="异步市场数据处理流水线：市场数据爬取 -> 数据清洗",
        epilog="""
使用示例:
  python run_market_data_pipeline_async.py
  python run_market_data_pipeline_async.py --skip-cleaning
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("--skip-cleaning", action="store_true", help="跳过数据清洗步骤")

    args = parser.parse_args()

    print("========== 异步市场数据处理流水线 ==========")
    print(f"⏰ 启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔧 跳过清洗: {'是' if args.skip_cleaning else '否'}")
    print("-" * 50)

    total_start_time = time.time()

    # 步骤1: 市场数据爬取
    collection_time = run_market_data_collection()

    # 步骤2: 市场数据清洗（可选）
    cleaning_time = 0
    args.skip_cleaning and print("\n⏭️ 跳过市场数据清洗步骤") or (cleaning_time := run_market_data_cleaning())

    # 总结
    total_duration = time.time() - total_start_time

    print("\n" + "=" * 60)
    print("📈 异步市场数据处理流水线完成")
    print(f"   - 市场数据爬取: {collection_time:.2f}秒")
    args.skip_cleaning or print(f"   - 数据清洗: {cleaning_time:.2f}秒")
    print(f"   - 总耗时: {total_duration:.2f}秒")

    print("\n📁 数据保存位置:")
    print("   - 原始数据: data/market_data/")
    args.skip_cleaning or print("   - 清洗数据: data/cleaned_market_data/")

    print("\n📊 生成的数据文件:")
    [print(f"   - {csv_file}") for csv_file in [
        "fund_flow_industry.csv", "fund_flow_concept.csv",
        "fund_flow_individual.csv", "zt_pool.csv", "lhb_detail.csv",
        "news_main_cx.csv", "market_activity_legu.csv"
    ]]

    print("\n💡 后续操作:")
    print("   - 市场AI分析（异步）: python src/launchers/run_market_ai_pipeline_async.py --skip-data --concurrency 3")
    print("   - Web应用查看: python src/launchers/run_app.py")
    print("=" * 60)


if __name__ == "__main__":
    main()
