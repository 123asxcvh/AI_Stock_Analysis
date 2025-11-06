#!/usr/bin/env python3
"""
指数成份股数据处理流水线脚本
功能：成份股数据爬取 -> 数据清洗
包含：概念板块和行业板块成份股数据收集、数据清洗（按成交额排序、添加排名）
作者：AI Assistant
创建时间：2025年
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path
import os

# 使用统一路径管理 - 不依赖sys.path操作
def get_project_paths():
    """获取项目路径，使用与paths.py相同的逻辑"""
    current_file = Path(__file__).resolve()
    
    # 从当前文件向上查找项目根目录
    for parent in [current_file.parent, *current_file.parents]:
        if (parent / 'pyproject.toml').exists():
            return parent
        if (parent / '.git').exists():
            return parent
        # 检查是否是项目根目录（包含src目录）
        if (parent / 'src').exists() and (parent / 'data').exists():
            return parent
    
    # fallback: 返回当前文件的上上级目录
    return current_file.parents[2]

# 添加项目根目录到Python路径
project_root = get_project_paths()
sys.path.insert(0, str(project_root))

from config import config


def check_existing_files(symbols, collection_type="concept"):
    """
    检查哪些文件已存在，返回需要收集的板块列表
    
    Args:
        symbols (list): 板块名称列表
        collection_type (str): 板块类型，'concept' 或 'industry'
    
    Returns:
        tuple: (需要收集的板块列表, 已存在的板块列表)
    """
    index_stocks_dir = config.get_index_stocks_dir()
    
    if collection_type == "concept":
        target_dir = index_stocks_dir / "concept"
    else:
        target_dir = index_stocks_dir / "industry"
    
    # 确保目录存在
    target_dir.mkdir(parents=True, exist_ok=True)
    
    symbols_to_collect = []
    existing_symbols = []
    
    for symbol in symbols:
        file_path = target_dir / f"{symbol}.csv"
        if file_path.exists():
            existing_symbols.append(symbol)
            print(f"✅ {symbol}: 文件已存在，跳过收集")
        else:
            symbols_to_collect.append(symbol)
            print(f"🔄 {symbol}: 文件不存在，需要收集")
    
    return symbols_to_collect, existing_symbols


def run_index_pipeline(symbols, collection_type="concept", skip_data_collection=False, max_concurrent=3, force=False):
    """
    运行指数成份股数据处理流水线

    Args:
        symbols (list): 板块名称列表
        collection_type (str): 板块类型，'concept' 或 'industry'
        skip_data_collection (bool): 是否跳过数据收集步骤
        max_concurrent (int): 最大并发数
    """
    print("🚀 启动指数成份股数据处理流水线")
    print("=" * 50)
    print(f"📋 板块类型: {collection_type}")
    print(f"📋 板块名称: {', '.join(symbols)}")
    print(f"📋 最大并发数: {max_concurrent}")
    print("=" * 50)
    
    # 检查文件存在性
    if force:
        print("\n🔄 强制模式: 将重新收集所有数据")
        symbols_to_collect = symbols
        existing_symbols = []
    else:
        print("\n🔍 检查文件存在性...")
        symbols_to_collect, existing_symbols = check_existing_files(symbols, collection_type)
        
        if existing_symbols:
            print(f"📁 已存在文件: {len(existing_symbols)} 个")
        if symbols_to_collect:
            print(f"📥 需要收集: {len(symbols_to_collect)} 个")
        
        # 精简：不做跳过分支判断，直接继续

    try:
        collection_time = 0  # 初始化收集时间

        if skip_data_collection or not symbols_to_collect:
            if skip_data_collection:
                print("\n⏭️ 跳过数据收集步骤（使用现有数据）")
            else:
                print("\n⏭️ 所有文件都已存在，跳过数据收集步骤")
        else:
            # 步骤1: 异步成份股数据收集
            print(f"\n🔄 步骤1: 异步成份股数据收集")
            print(f"   将收集 {len(symbols_to_collect)} 个板块: {', '.join(symbols_to_collect)}")
            start_time = time.time()

            # 构建命令行参数 - 只收集不存在的文件
            symbols_str = ",".join(symbols_to_collect)
            cmd = [
                sys.executable, 
                "src/crawling/index_stocks_collector.py",
                symbols_str,
                "--type", collection_type,
                "--max-concurrent", str(max_concurrent)
            ]

            # 调用异步成份股数据收集
            result = subprocess.run(
                cmd,
                cwd=str(config.project_root),
                capture_output=True,
                text=True,
                env=dict(os.environ, PYTHONPATH=f"{config.project_root}:{os.environ.get('PYTHONPATH', '')}")
            )

            # 精简：不中断流程

            collection_time = time.time() - start_time
            print(f"✅ 成份股数据收集完成，耗时: {collection_time:.2f}秒")
            print(f"   收集了 {len(symbols_to_collect)} 个{collection_type}板块的成份股数据")

        # 步骤2: 数据清洗
        print("\n🔄 步骤2: 数据清洗")
        start_time = time.time()

        # 调用数据清洗
        result = subprocess.run(
            [sys.executable, "-m", "src.cleaning.index_stocks_cleaner"],
            cwd=str(config.project_root),
            capture_output=True,
            text=True,
            env=dict(os.environ, PYTHONPATH=str(config.project_root))
        )

        # 精简：不中断流程

        clean_time = time.time() - start_time
        print(f"✅ 数据清洗完成，耗时: {clean_time:.2f}秒")
        print("   包含: 按成交额排序、添加排名列、删除空行等")

        # 计算总耗时
        total_time = collection_time + clean_time

        print(f"\n🎉 指数成份股数据处理完成！")
        print(f"   总耗时: {total_time:.2f}秒")
        if not skip_data_collection:
            print(f"   - 数据收集: {collection_time:.2f}秒")
        else:
            print("   - 数据收集: 跳过")
        print(f"   - 数据清洗: {clean_time:.2f}秒")
        
        # 显示数据保存位置
        index_stocks_dir = config.get_index_stocks_dir()
        concept_dir = index_stocks_dir / "concept"
        industry_dir = index_stocks_dir / "industry"
        
        print(f"\n📁 数据保存位置:")
        print(f"   - 概念板块: {concept_dir}")
        print(f"   - 行业板块: {industry_dir}")
        
        # 显示收集到的文件
        if collection_type == "concept" and concept_dir.exists():
            concept_files = list(concept_dir.glob("*.csv"))
            print(f"   - 概念板块文件: {len(concept_files)} 个")
            for file in concept_files[:5]:  # 显示前5个
                print(f"     * {file.name}")
            if len(concept_files) > 5:
                print(f"     ... 还有 {len(concept_files) - 5} 个文件")
                
        elif collection_type == "industry" and industry_dir.exists():
            industry_files = list(industry_dir.glob("*.csv"))
            print(f"   - 行业板块文件: {len(industry_files)} 个")
            for file in industry_files[:5]:  # 显示前5个
                print(f"     * {file.name}")
            if len(industry_files) > 5:
                print(f"     ... 还有 {len(industry_files) - 5} 个文件")

        return True

    except Exception as e:
        print(f"❌ 指数成份股数据处理失败: {e}")
        return False


def main():
    """
    主函数
    """
    parser = argparse.ArgumentParser(
        description="指数成份股数据处理流水线：成份股数据爬取 -> 数据清洗",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python run_index_pipeline_async.py "人工智能"
  python run_index_pipeline_async.py "人工智能,5G概念" --type concept
  python run_index_pipeline_async.py "半导体,银行" --type industry
  python run_index_pipeline_async.py "人工智能" --skip-data-collection
  python run_index_pipeline_async.py "人工智能" --max-concurrent 5
  python run_index_pipeline_async.py "人工智能" --force

流程说明:
  1. 成份股数据收集: 异步收集概念板块或行业板块的成份股数据
  2. 数据清洗: 按成交额排序、添加排名列、删除空行等处理

参数说明:
  --type: 板块类型，可选 concept(概念板块) 或 industry(行业板块)，默认为 concept
  --skip-data-collection: 跳过数据收集步骤，直接清洗现有数据
  --max-concurrent: 最大并发数，默认为 3
        """,
    )

    parser.add_argument("symbols", help="板块名称，多个用逗号分隔，如：人工智能,5G概念")

    parser.add_argument("--type", choices=["concept", "industry"], default="concept",
                        help="板块类型：concept(概念板块) 或 industry(行业板块)，默认为concept")

    parser.add_argument("--skip-data-collection", action="store_true",
                        help="跳过数据收集步骤，直接使用现有数据进行清洗")

    parser.add_argument("--max-concurrent", type=int, default=3,
                        help="最大并发数，默认为3")

    parser.add_argument("--force", action="store_true",
                        help="强制重新收集所有数据，忽略已存在的文件")

    args = parser.parse_args()

    # 处理板块名称参数
    symbols = [s.strip() for s in args.symbols.split(',') if s.strip()]

    if not symbols:
        print("❌ 请提供至少一个板块名称")
        parser.print_help()
        sys.exit(1)

    print(f"📋 待处理板块: {', '.join(symbols)}")

    if args.skip_data_collection:
        print("⏭️ 将跳过数据收集步骤")

    # 运行指数成份股流水线
    success = run_index_pipeline(
        symbols=symbols,
        collection_type=args.type,
        skip_data_collection=args.skip_data_collection,
        max_concurrent=args.max_concurrent,
        force=args.force
    )

    if success:
        print("\n🏁 指数成份股数据处理流水线执行完成！")
        print("=" * 50)
    else:
        print("\n❌ 指数成份股数据处理流水线执行失败！")
        sys.exit(1)


if __name__ == "__main__":
    main()
