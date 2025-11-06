#!/usr/bin/env python3
# -*- coding: utf-8 -*-



import os
import sys
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from config import config


class IndexStocksCleaner:
    """指数成份股数据清洗器"""
    
    def __init__(self):
        """初始化清洗器"""
        self.concept_dir = config.get_concept_stocks_dir()
        self.industry_dir = config.get_industry_stocks_dir()
        
        # 确保目录存在
        self.concept_dir.mkdir(parents=True, exist_ok=True)
        self.industry_dir.mkdir(parents=True, exist_ok=True)
        
    def clean_index_stocks_data(self, file_path: Path) -> Optional[pd.DataFrame]:
        """
        清洗单个成份股数据文件
        
        Args:
            file_path: 数据文件路径
        
        Returns:
            清洗后的DataFrame
        """
        # 读取数据
        df = pd.read_csv(file_path, encoding='utf-8-sig')
        
        if df.empty:
            return None
        
        # 数据清洗步骤
        df = self._clean_data_structure(df)
        df = self._clean_numeric_columns(df)
        df = self._sort_by_turnover(df)
        df = self._add_ranking(df)
        
        return df
    
    def _clean_data_structure(self, df: pd.DataFrame) -> pd.DataFrame:
        """清洗数据结构"""
        # 删除全空行
        df = df.dropna(how='all')
        
        # 重置索引
        df = df.reset_index(drop=True)
        
        # 删除序号列（如果有的话）
        if '序号' in df.columns:
            df = df.drop('序号', axis=1)
        
        return df
    
    def _clean_numeric_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """清洗数值列"""
        # 定义需要转换为数值的列
        numeric_columns = [
            '最新价', '涨跌幅', '涨跌额', '成交量', '成交额', '振幅',
            '最高', '最低', '今开', '昨收', '换手率', '市盈率-动态', '市净率'
        ]
        
        for col in numeric_columns:
            if col in df.columns:
                # 转换为数值类型，无法转换的变为NaN
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # 删除关键字段为空的记录
        if '成交额' in df.columns:
            df = df.dropna(subset=['成交额'])
        
        return df
    
    def _sort_by_turnover(self, df: pd.DataFrame) -> pd.DataFrame:
        """按成交额倒序排列"""
        if '成交额' in df.columns:
            df = df.sort_values('成交额', ascending=False)
        else:
            pass
        
        return df
    
    def _add_ranking(self, df: pd.DataFrame) -> pd.DataFrame:
        """添加排名列"""
        # 重置索引
        df = df.reset_index(drop=True)
        
        # 如果排名列已存在，先删除
        if '排名' in df.columns:
            df = df.drop('排名', axis=1)
        
        # 添加新的排名列
        df.insert(0, '排名', range(1, len(df) + 1))
        
        return df
    
    def clean_concept_stocks(self) -> Dict[str, bool]:
        """清洗所有概念板块数据"""
        results = {}
        concept_files = list(self.concept_dir.glob('*.csv'))
        
        if not concept_files:
            return results
        
        for file_path in concept_files:
            # 清洗数据
            cleaned_df = self.clean_index_stocks_data(file_path)
            
            if cleaned_df is not None and not cleaned_df.empty:
                # 替换原文件
                cleaned_df.to_csv(file_path, index=False, encoding='utf-8-sig')
                results[file_path.name] = True
            else:
                results[file_path.name] = False
        
        return results
    
    def clean_industry_stocks(self) -> Dict[str, bool]:
        """清洗所有行业板块数据"""
        results = {}
        industry_files = list(self.industry_dir.glob('*.csv'))
        
        if not industry_files:
            return results
        
        for file_path in industry_files:
            # 清洗数据
            cleaned_df = self.clean_index_stocks_data(file_path)
            
            if cleaned_df is not None and not cleaned_df.empty:
                # 替换原文件
                cleaned_df.to_csv(file_path, index=False, encoding='utf-8-sig')
                results[file_path.name] = True
            else:
                results[file_path.name] = False
        
        return results
    
    def clean_all_index_stocks(self) -> Dict[str, Dict[str, bool]]:
        """清洗所有指数成份股数据"""
        results = {
            'concept': self.clean_concept_stocks(),
            'industry': self.clean_industry_stocks()
        }
        
        return results


def main():
    """主函数"""
    cleaner = IndexStocksCleaner()
    results = cleaner.clean_all_index_stocks()
    
    # 输出结果摘要
    print("\n🎉 成份股数据清洗完成！")
    for category, files in results.items():
        success_count = sum(files.values())
        total_count = len(files)
        print(f"{'💡 概念板块' if category == 'concept' else '🏭 行业板块'}: {success_count}/{total_count} 个文件成功")


if __name__ == "__main__":
    main()