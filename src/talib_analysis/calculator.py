#!/usr/bin/env python3
"""
技术指标计算器
基于backtesting模块的指标计算器，提供命令行接口
"""

import sys
import argparse
from pathlib import Path
import pandas as pd

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.backtesting.core.indicators import indicator_calculator
from config import config


def calculate_technical_indicators(symbol: str):
    """
    为指定股票计算技术指标，直接在historical_quotes.csv文件上添加指标列

    Args:
        symbol: 股票代码
    """
    print(f"🔄 开始计算股票 {symbol} 的技术指标...")

    # 查找历史数据文件
    historical_file = config.get_stock_file_path(symbol, "historical_quotes.csv", cleaned=True)
    if not historical_file.exists():
        historical_file = config.get_stock_file_path(symbol, "historical_quotes.csv", cleaned=False)

    if not historical_file.exists():
        print(f"❌ 历史数据文件不存在: {historical_file}")
        return False

    try:
        # 读取历史数据
        df = pd.read_csv(historical_file)

        if df.empty:
            print(f"❌ 历史数据为空")
            return False

        print(f"📊 读取到 {len(df)} 条历史数据，当前列数: {len(df.columns)}")

        # 检查是否已经包含技术指标
        existing_indicators = [col for col in df.columns if any(ind in col for ind in ['MACD', 'KDJ', 'RSI', 'BOLL', 'BBI', 'ATR'])]
        if existing_indicators:
            print(f"⚠️ 检测到已有技术指标: {len(existing_indicators)} 个")
            print("   将重新计算所有技术指标...")
        else:
            print("   未检测到技术指标，将开始计算...")

        # 计算技术指标
        df_with_indicators = indicator_calculator.calculate_all(df)

        # 直接覆盖原历史数据文件（包含技术指标）
        df_with_indicators.to_csv(historical_file, index=False, encoding="utf-8-sig")

        print(f"✅ 技术指标计算完成，已更新文件: {historical_file}")
        print(f"   文件列数: {len(df_with_indicators.columns)} (增加了 {len(df_with_indicators.columns) - len(df.columns)} 个技术指标)")

        # 显示新增的技术指标
        new_indicators = [col for col in df_with_indicators.columns if col not in df.columns]
        print(f"   新增指标: {new_indicators}")

        return True

    except Exception as e:
        print(f"❌ 计算技术指标时出错: {e}")
        return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="技术指标计算器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python calculator.py 000001
  python calculator.py 603026
        """
    )

    parser.add_argument(
        "symbol",
        help="股票代码（6位数字）"
    )

    args = parser.parse_args()

    # 计算技术指标
    success = calculate_technical_indicators(args.symbol)

    if success:
        print(f"🎉 股票 {args.symbol} 技术指标计算完成")
        sys.exit(0)
    else:
        print(f"❌ 股票 {args.symbol} 技术指标计算失败")
        sys.exit(1)


if __name__ == "__main__":
    main()