#!/usr/bin/env python3
"""
创建必要的目录结构
在应用启动前运行此脚本确保所有目录存在
"""

import os
from pathlib import Path

def create_directories():
    """创建项目所需的目录结构"""

    # 项目根目录
    project_root = Path(__file__).parent

    # 需要创建的目录列表
    directories = [
        "data",
        "data/stocks",
        "data/cleaned_stocks",
        "data/ai_reports",
        "data/market_data",
        "data/index_data",
        "data/cache",
        "logs"
    ]

    print("🏗️  创建项目目录结构...")

    for dir_path in directories:
        full_path = project_root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"✅ {dir_path}")

    print("🎉 目录结构创建完成！")
    print(f"📁 项目根目录: {project_root}")

if __name__ == "__main__":
    create_directories()