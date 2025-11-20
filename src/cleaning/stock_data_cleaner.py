#!/usr/bin/env python
"""
精简版增强数据清洗模块
只保留主流程和必要辅助方法
"""

import warnings
from pathlib import Path
from typing import Union

import numpy as np
import pandas as pd


warnings.filterwarnings("ignore")

# 导入统一路径管理
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))
from config import config


class EnhancedDataCleaner:
    def __init__(self, data_root_dir: Union[str, Path] = None):
        # 使用现代路径管理
        if data_root_dir is None:
            data_root_dir = str(config.data_dir)

        self.data_root_dir = Path(data_root_dir)
        self.stocks_dir = config.get_stocks_dir()
        self.cleaned_dir = self.data_root_dir / "cleaned_stocks"

        # 加载基本配置
        self._load_external_configs()

        # 定义需要清洗的文件类型
        self.cleaning_config = {
            "balance_sheet.csv": {
                "description": "资产负债表数据",
                "required_columns": ["日期"],
            },
            "income_statement.csv": {
                "description": "利润表数据",
                "required_columns": ["日期"],
            },
            "cash_flow_statement.csv": {
                "description": "现金流量表数据",
                "required_columns": ["日期"],
            },
            "main_business_composition.csv": {
                "description": "主营构成数据",
                "required_columns": ["日期", "主营收入", "主营成本"],
            },
            "financial_indicators.csv": {
                "description": "财务指标数据",
                "required_columns": ["日期", "净资产收益率", "资产负债率"],
            },
              "stock_belong_boards.csv": {
                "description": "股票所属版块数据",
                "required_columns": ["股票名称", "股票代码", "板块代码", "板块名称"],
            },
            "intraday_data.csv": {
                "description": "分时数据",
                "required_columns": ["日期", "开盘", "收盘", "最高", "最低"],
            },
            "company_profile.csv": {
                "description": "公司概况数据",
                "required_columns": ["字段名", "字段值"],
            },
            "bid_ask.csv": {
                "description": "盘口数据",
                "required_columns": ["字段名", "字段值"],
            },
            "peer_growth_comparison.csv": {
                "description": "同行成长性比较数据",
                "required_columns": ["代码", "简称"],
            },
            "peer_valuation_comparison.csv": {
                "description": "同行估值比较数据",
                "required_columns": ["代码", "简称"],
            },
            "peer_dupont_comparison.csv": {
                "description": "同行杜邦分析比较数据",
                "required_columns": ["代码", "简称"],
            },
            "peer_scale_comparison.csv": {
                "description": "同行公司规模比较数据",
                "required_columns": ["代码", "简称"],
            },
        }
        self.cleaner_mapping = {
            "company_profile.csv": self._clean_company_profile,
            "stock_belong_boards.csv": self._clean_stock_belong_boards,
            "main_business_composition.csv": self._clean_main_business_composition,
            "intraday_data.csv": self._clean_intraday_data,
            "bid_ask.csv": self._clean_bid_ask,
            "balance_sheet.csv": self._clean_financial_data,
            "income_statement.csv": self._clean_financial_data,
            "cash_flow_statement.csv": self._clean_financial_data,
            "financial_indicators.csv": self._clean_financial_data,
            "peer_growth_comparison.csv": self._clean_peer_comparison_data,
            "peer_valuation_comparison.csv": self._clean_peer_comparison_data,
            "peer_dupont_comparison.csv": self._clean_peer_comparison_data,
            "peer_scale_comparison.csv": self._clean_peer_comparison_data,
        }
        self.date_column_mapping = {
            "报告期": "日期",
            "数据日期": "日期",
            "交易日期": "日期",
            "date": "日期",
            "Date": "日期",
        }

    def _load_external_configs(self):
        """加载基本配置"""
        self.filter_start_date = "2022-01-01"

    def clean_stock_data(self, symbol: str):
        """
        清洗股票数据

        Args:
            symbol: 股票代码
        """
        print(f"🧹 开始数据清洗股票 {symbol} 的数据...")

        stock_dir = self.stocks_dir / symbol
        cleaned_stock_dir = self.cleaned_dir / symbol

        if not stock_dir.exists():
            print(f"❌ 股票数据目录不存在: {stock_dir}")
            return False

        cleaned_stock_dir.mkdir(parents=True, exist_ok=True)
        print(f"📁 创建清洗目录: {cleaned_stock_dir}")

        # 正常清洗模式：从原始数据清洗到目标目录
        csv_files = [f.name for f in stock_dir.glob("*.csv")]
        print(f"📊 发现 {len(csv_files)} 个CSV文件需要清洗")

        success_count = 0
        for i, file_name in enumerate(csv_files, 1):
            print(f"   🔄 [{i}/{len(csv_files)}] 正在清洗: {file_name}")
            raw_file_path = stock_dir / file_name
            cleaned_file_path = cleaned_stock_dir / file_name

            self._clean_file(raw_file_path, cleaned_file_path, file_name)
            success_count += 1

        print(f"✅ 数据清洗完成: {success_count}/{len(csv_files)} 个文件成功")

        # 步骤：对除了historical_quotes.csv之外的所有文件进行倒序排列
        print(f"🔄 对非historical_quotes文件进行倒序处理...")
        files_to_descend = [f for f in csv_files if f != "historical_quotes.csv"]
        descend_success = 0

        for file_name in files_to_descend:
            file_path = cleaned_stock_dir / file_name
            if file_path.exists():
                if self._sort_file_descending(file_path):
                    descend_success += 1
                    print(f"   ✅ {file_name} 倒序完成")
                else:
                    print(f"   ⚠️ {file_name} 倒序失败")

        print(f"✅ 倒序处理完成: {descend_success}/{len(files_to_descend)} 个文件成功")
        return success_count == len(csv_files)

    def clean_stock_data_skip_historical_quotes(self, symbol: str):
        """
        清洗股票数据，但跳过historical_quotes.csv文件（避免与技术指标准备冲突）
        Args:
            symbol: 股票代码
        """
        print(f"🧹 开始清洗股票 {symbol} 的数据（跳过行情数据）...")
        stock_dir = self.stocks_dir / symbol
        cleaned_stock_dir = self.cleaned_dir / symbol

        if not stock_dir.exists():
            print(f"❌ 股票数据目录不存在: {stock_dir}")
            return False

        cleaned_stock_dir.mkdir(parents=True, exist_ok=True)
        print(f"📁 创建清洗目录: {cleaned_stock_dir}")

        csv_files = [f.name for f in stock_dir.glob("*.csv")]
        # 跳过historical_quotes.csv文件
        csv_files = [f for f in csv_files if f != "historical_quotes.csv"]

        print(f"📊 发现 {len(csv_files)} 个CSV文件需要清洗（已跳过historical_quotes.csv）")
        success_count = 0

        for i, file_name in enumerate(csv_files, 1):
            print(f"   🔄 [{i}/{len(csv_files)}] 正在清洗: {file_name}")
            raw_file_path = stock_dir / file_name
            cleaned_file_path = cleaned_stock_dir / file_name

            self._clean_file(raw_file_path, cleaned_file_path, file_name)
            success_count += 1

        print(f"✅ 数据清洗完成: {success_count}/{len(csv_files)} 个文件成功")
        return success_count == len(csv_files)

    def _clean_file(self, raw_file_path, cleaned_file_path, file_name):
        """调度文件到对应的清洗函数"""
        df = pd.read_csv(raw_file_path)
        if df.empty:
            print(f"   ⚠️ {file_name} 为空文件，跳过清洗。")
            return

        # 根据文件名获取对应的清洗函数，若无特定函数则使用通用函数
        clean_function = self.cleaner_mapping.get(
            file_name, self._clean_generic_file
        )

        # 传递文件名给部分需要它的函数
        if clean_function in [self._clean_financial_data, self._clean_generic_file, self._clean_peer_comparison_data]:
            cleaned_df = clean_function(df, file_name)
        else:
            cleaned_df = clean_function(df)

        if cleaned_df is not None and not cleaned_df.empty:
            cleaned_df.to_csv(cleaned_file_path, index=False, encoding="utf-8-sig")
            print(f"   ✅ {file_name} 清洗完成: {len(cleaned_df)} 条记录")
        else:
            print(f"   ℹ️ {file_name} 清洗后无数据，不保存。")



    def _clean_generic_file(self, df: pd.DataFrame, file_name: str) -> pd.DataFrame:
        """通用数据清洗流程"""
        # 历史报价数据的列名映射
        historical_quotes_mapping = {
            "open": "开盘",
            "close": "收盘",
            "high": "最高",
            "low": "最低",
            "amount": "成交量"
        }

        # 财务指标的列名映射
        financial_indicator_mapping = {
            "净资产收益率(%)": "净资产收益率",
            "资产负债率(%)": "资产负债率",
            "PE(TTM)": "市盈率",
            "PE(静)": "市盈率(静)",
            "市净率(PB)": "市净率",
        }

        # 应用列名映射
        if file_name == "historical_quotes.csv":
            df = df.rename(columns=historical_quotes_mapping)
        elif (
            file_name == "financial_indicators.csv"
            or file_name == "stock_valuation.csv"
        ):
            df = df.rename(columns=financial_indicator_mapping)

        df = self._standardize_date_columns(df)
        df = df.dropna(how="all").drop_duplicates()
        df = self._remove_stock_code_column(df)

        if "日期" in df.columns:
            df["日期"] = pd.to_datetime(df["日期"], errors="coerce")
            df = df.dropna(subset=["日期"])
            df = self._filter_by_date(df, "日期", file_name)
            df = df.sort_values("日期", ascending=True)


        df = self._move_date_column_to_first(df)
        df = df.reset_index(drop=True)
        return df

    def _clean_stock_belong_boards(self, df: pd.DataFrame) -> pd.DataFrame:
        """清洗股票所属版块数据"""

        # 删除第一列（索引列）
        if df.columns[0] == df.index.name or df.columns[0].startswith('Unnamed'):
            df = df.iloc[:, 1:]  # 删除第一列

        # 确保必要列存在
        required_cols = ["股票名称", "股票代码", "板块代码", "板块名称"]
        available_cols = [col for col in required_cols if col in df.columns]

        if not available_cols:
            return pd.DataFrame()

        # 选择需要的列
        df = df[available_cols + [col for col in ["板块涨幅"] if col in df.columns]]

        # 删除重复行
        df = df.drop_duplicates()

        # 按板块涨幅排序（如果存在）
        if "板块涨幅" in df.columns:
            # 将涨幅转换为数值类型
            df["板块涨幅"] = pd.to_numeric(df["板块涨幅"], errors="coerce")
            # 排序，将NaN值放在最后
            df = df.sort_values("板块涨幅", ascending=False, na_position='last')

        df = df.reset_index(drop=True)
        return df

  
    def _clean_main_business_composition(self, df: pd.DataFrame) -> pd.DataFrame:
        """清洗主营构成数据"""
        # 1. 列重命名
        rename_dict = {
            "报告日期": "日期",
            "主营业务收入": "主营收入",
            "主营业务成本": "主营成本",
        }
        df = df.rename(columns=rename_dict)
        
        # 2. 删除股票代码列
        if "股票代码" in df.columns:
            df = df.drop(columns=["股票代码"])
        
        # 3. 处理分类类型
        if "分类类型" in df.columns:
            df["分类类型"] = df["分类类型"].fillna("按行业分类")
            df["分类类型"] = df["分类类型"].replace("", "按行业分类")

        # 4. 处理主营构成中的"其他"项
        if "主营构成" in df.columns:
            # 将包含"其他"的主营构成统一改为"其他"
            df["主营构成"] = df["主营构成"].apply(
                lambda x: "其他" if pd.notna(x) and "其他" in str(x) else x
            )

        # 5. 移动日期列到第一列
        df = self._move_date_column_to_first(df)
        
        # 5. 清理数据
        df = df.dropna(how="all").drop_duplicates()

        # 6. 处理日期列
        if "日期" in df.columns:
            df["日期"] = pd.to_datetime(df["日期"], errors="coerce")
            df = df.dropna(subset=["日期"])
            # 主营业务构成数据从2022年开始
            df = self._filter_by_date(df, "日期", "main_business_composition.csv")
            df = df.sort_values("日期", ascending=True)

        df = df.reset_index(drop=True)
        return df

    def _clean_intraday_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """清洗分时数据 - 参考baostock接口格式"""
        # 删除不需要的列：date, code, adjustflag
        columns_to_drop = ['date', 'code', 'adjustflag']
        df = df.drop(columns=[col for col in columns_to_drop if col in df.columns])

        # 重命名列为中文
        column_mapping = {
            'time': '日期',
            'open': '开盘',
            'high': '最高',
            'low': '最低',
            'close': '收盘',
            'volume': '成交量',
            'amount': '成交额'
        }
        df = df.rename(columns=column_mapping)

        # 处理时间格式：将time格式转换为日期时间
        if "日期" in df.columns:
            # baostock的time格式为：20251118144000000
            # 转换为标准datetime格式
            df["日期"] = df["日期"].astype(str)
            df["日期"] = pd.to_datetime(df["日期"], format='%Y%m%d%H%M%S%f', errors='coerce')
            df = df.dropna(subset=["日期"])

        # 基本清洗
        df = df.dropna(how="all").drop_duplicates()

        # 正常清洗时升序排列（为了技术指标计算）
        if "日期" in df.columns:
            df = df.sort_values("日期", ascending=True)

        # 将日期列移到第一列
        if "日期" in df.columns:
            cols = df.columns.tolist()
            cols.remove("日期")
            df = df[["日期"] + cols]

        df = df.reset_index(drop=True)
        return df

    def _clean_company_profile(self, df: pd.DataFrame) -> pd.DataFrame:
        """清洗公司概况数据 - 转换为纵向排列"""
        # 如果已经是纵向格式（有字段名和字段值列），直接返回
        if "字段名" in df.columns and "字段值" in df.columns:
            return df
        
        # 将横向数据转换为纵向格式
        if len(df) == 0:
            return pd.DataFrame()
        
        # 取第一行数据（通常只有一行）
        row_data = df.iloc[0]
        
        # 创建纵向格式的DataFrame
        vertical_data = []
        for column_name, value in row_data.items():
            if pd.notna(value) and str(value).strip() != "":
                vertical_data.append({
                    "字段名": column_name,
                    "字段值": str(value).strip()
                })
        
        vertical_data.append({
            "字段名": "数据清洗时间",
            "字段值": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        
        result_df = pd.DataFrame(vertical_data)
        
        return result_df

    def _clean_financial_data(self, df: pd.DataFrame, file_name: str) -> pd.DataFrame:
        """清洗财务报表数据 (资产负债表, 利润表, 现金流量表)"""
        # 1. 删除完全空白的列
        df = self._remove_empty_columns(df)

        # 2. 统一处理财务报表
        if file_name in ["balance_sheet.csv", "income_statement.csv", "cash_flow_statement.csv"]:
            df = self._clean_financial_statements(df, file_name)

        # 3. 清洗财务数值
        skip_columns = ["日期", "报告期", "报表核心指标", "报表全部指标"]
        for col in df.columns:
            if col in skip_columns:
                continue
            df[col] = df[col].apply(self._clean_financial_value)

        if "报告期" in df.columns:
            df["报告期"] = df["报告期"].apply(self._convert_year_to_date)
            df = df.rename(columns={"报告期": "日期"})

        if "日期" in df.columns:
            df["日期"] = pd.to_datetime(df["日期"], errors="coerce")
            df = df.dropna(subset=["日期"])
            df = self._filter_by_date(df, "日期", file_name)
            df = df.sort_values("日期", ascending=True)

        df = self._move_date_column_to_first(df)
        df = df.reset_index(drop=True)
        return df

    def _clean_financial_statements(self, df: pd.DataFrame, file_name: str) -> pd.DataFrame:
        """统一的财务报表清洗函数，按用户要求精确清洗"""
        columns_to_drop = []

        # 1. 首先删除全空的列（所有财务报表通用）
        empty_columns = []
        for col in df.columns:
            if col not in ["报告期", "日期"] and df[col].isnull().all():
                empty_columns.append(col)

        if empty_columns:
            columns_to_drop.extend(empty_columns)
            print(f"   🗑️ 删除空白列: {empty_columns}")

        # 2. 按文件类型进行特殊处理
        if file_name == "income_statement.csv":
            # 利润表特殊处理：按用户要求

            # 2.1 删除所有带*的列
            star_columns = [col for col in df.columns if col.startswith("*")]
            columns_to_drop.extend(star_columns)

            # 2.2 查找"五、净利润"列的位置，删除之后的所有列
            columns = [col for col in df.columns if col not in columns_to_drop]
            net_profit_index = None

            for i, col in enumerate(columns):
                if col == "五、净利润":
                    net_profit_index = i
                    print(f"   📍 找到五、净利润列在第 {i} 个位置")
                    break

            if net_profit_index is not None:
                # 删除五、净利润之后的所有列
                columns_after_net_profit = columns[net_profit_index + 1:]
                columns_to_drop.extend(columns_after_net_profit)
                print(f"   🗑️ 利润表删除净利润之后列: {len(columns_after_net_profit)} 个")

            # 2.3 重命名报告期为日期
            if "报告期" in df.columns:
                df = df.rename(columns={"报告期": "日期"})
                print(f"   🔄 重命名'报告期'为'日期'")

            # 显示删除的*列
            if star_columns:
                print(f"   🗑️ 删除带*列: {len(star_columns)} 个")
                if len(star_columns) <= 8:
                    print(f"      删除的列: {star_columns}")

        elif file_name == "balance_sheet.csv":
            # 资产负债表：删除带*的合计列和带"其中"的子项列
            for col in df.columns:
                if col not in ["报告期", "日期"]:
                    if col.startswith("*") or "其中" in col:
                        columns_to_drop.append(col)

        elif file_name == "cash_flow_statement.csv":
            # 现金流表：删除带*的合计列和带"其中"的子项列，以及净利润之后的列
            for col in df.columns:
                if col not in ["报告期", "日期"]:
                    if col.startswith("*") or "其中" in col:
                        columns_to_drop.append(col)

            # 查找净利润相关列并删除之后列
            columns = [col for col in df.columns if col not in columns_to_drop]
            net_profit_index = None

            for i, col in enumerate(columns):
                if "净利润" in col:
                    net_profit_index = i
                    break

            if net_profit_index is not None:
                columns_after_net_profit = columns[net_profit_index + 1:]
                columns_to_drop.extend(columns_after_net_profit)
                print(f"   🗑️ 现金流量表删除净利润及之后列: {len(columns_after_net_profit)} 个")

        # 3. 执行列删除
        if columns_to_drop:
            file_display_name = {
                "balance_sheet.csv": "资产负债表",
                "income_statement.csv": "利润表",
                "cash_flow_statement.csv": "现金流量表"
            }.get(file_name, file_name)

            remaining_cols = len(df.columns) - len(columns_to_drop)
            print(f"   🗑️ {file_display_name}删除特殊列: {len(columns_to_drop)} 个")
            print(f"      保留列数: {remaining_cols}")

            # 显示删除的列名（如果数量不多）
            if len(columns_to_drop) <= 10:
                print(f"      删除的列: {columns_to_drop}")

            df = df.drop(columns=columns_to_drop)

        return df

  
    def _clean_balance_sheet(self, df: pd.DataFrame) -> pd.DataFrame:
        """清洗资产负债表（保留兼容性）"""
        return self._clean_financial_statements(df, "balance_sheet.csv")

    def _clean_income_statement(self, df: pd.DataFrame) -> pd.DataFrame:
        """清洗利润表（保留兼容性）"""
        return self._clean_financial_statements(df, "income_statement.csv")

    def _remove_empty_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """删除完全空白的列"""
        # 保留日期列，即使它有空值
        date_columns = [col for col in df.columns if '日期' in col or 'date' in col.lower()]

        # 找出完全为空的列（除了日期列）
        empty_columns = []
        for col in df.columns:
            if col in date_columns:
                continue
            if df[col].isnull().all() or (df[col] == "").all():
                empty_columns.append(col)

        if empty_columns:
            print(f"   🗑️ 删除空白列: {empty_columns}")
            df = df.drop(columns=empty_columns)

        return df

    def _clean_cash_flow_statement(self, df: pd.DataFrame) -> pd.DataFrame:
        """清洗现金流量表，删除补充资料及之后的列"""
        # 查找净利润的位置（净利润是补充资料的开始）
        net_income_index = None
        for i, col in enumerate(df.columns):
            if col == "净利润":
                net_income_index = i
                break

        if net_income_index is not None:
            # 保留净利润之前的所有列
            columns_to_keep = df.columns[:net_income_index].tolist()
            columns_to_drop = df.columns[net_income_index:].tolist()

            print(f"   🗑️ 现金流量表删除补充资料列: {len(columns_to_drop)} 个")
            print(f"      保留列数: {len(columns_to_keep)}, 删除列数: {len(columns_to_drop)}")
            print(f"      从 '{columns_to_drop[0]}' 开始删除到最后")

            df = df.drop(columns=columns_to_drop)

        return df

    def _clean_financial_value(self, value):
        if pd.isna(value) or value == "" or value is None:
            return np.nan
        str_value = str(value).strip()
        if str_value.lower() in ["false", "true", "--", "-", ""]:
            return np.nan
        import re

        multiplier = 1
        if "万亿" in str_value:
            multiplier = 1e12
            str_value = str_value.replace("万亿", "")
        elif "千亿" in str_value:
            multiplier = 1e11
            str_value = str_value.replace("千亿", "")
        elif "百亿" in str_value:
            multiplier = 1e10
            str_value = str_value.replace("百亿", "")
        elif "十亿" in str_value:
            multiplier = 1e9
            str_value = str_value.replace("十亿", "")
        elif "亿" in str_value:
            multiplier = 1e8
            str_value = str_value.replace("亿", "")
        elif "万" in str_value:
            multiplier = 1e4
            str_value = str_value.replace("万", "")
        str_value = re.sub(r"[^\d.-]", "", str_value)
        if str_value == "" or str_value == "-":
            return np.nan
        numeric_value = float(str_value) * multiplier
        return numeric_value

    def _standardize_date_columns(self, df):
        for col, std_col in self.date_column_mapping.items():
            if col in df.columns and std_col != col:
                df[std_col] = df[col]
                df = df.drop(columns=[col])
        return df


    def _convert_year_to_date(self, value):
        value = str(value)
        if len(value) == 4 and value.isdigit():
            return f"{value}-12-31"
        return value

    def _filter_by_date(self, df, date_col, file_name=None):
            df[date_col] = pd.to_datetime(df[date_col], errors="coerce")

            if file_name and "talib" in file_name:
                filter_date = pd.to_datetime("2020-01-01")
                print(f"   📅 {file_name} 时间过滤: 保留从 {filter_date.strftime('%Y-%m-%d')} 开始的数据（技术指标需要更长历史）")
            elif file_name == "main_business_composition.csv":
                # 主营业务构成数据从2022年开始
                filter_date = pd.to_datetime("2022-01-01")
                print(f"   📅 {file_name} 时间过滤: 保留从 {filter_date.strftime('%Y-%m-%d')} 开始的数据")
            else:
                filter_date = pd.to_datetime(self.filter_start_date)
                print(f"   📅 {file_name} 时间过滤: 保留从 {filter_date.strftime('%Y-%m-%d')} 开始的数据")

            filtered_df = df[df[date_col] >= filter_date]
            return filtered_df

    def _remove_stock_code_column(self, df):
        stock_code_columns = ["股票代码", "stock_code", "code", "代码", "证券代码"]
        for col in stock_code_columns:
            if col in df.columns:
                sample_values = df[col].dropna().head(20).astype(str).tolist()
                if len(sample_values) == 0:
                    continue
                is_stock_code = True
                for value in sample_values:
                    if not (
                        value.isdigit()
                        and (len(value) == 6 or (len(value) == 1 and value == "1"))
                    ):
                        is_stock_code = False
                        break
                if is_stock_code:
                    df = df.drop(columns=[col])
                    break
        return df

    def _move_date_column_to_first(self, df):
        if "日期" in df.columns:
            cols = df.columns.tolist()
            cols.remove("日期")
            new_cols = ["日期"] + cols
            df = df[new_cols]
        return df


    def _clean_bid_ask(self, df: pd.DataFrame) -> pd.DataFrame:
        """清洗盘口行情数据 - 转换为纵向排列"""
        # 如果已经是纵向格式（有字段名和字段值列），直接返回
        if "字段名" in df.columns and "字段值" in df.columns:
            return df
        
        # 如果数据是item,value格式，转换为字段名,字段值格式
        if "item" in df.columns and "value" in df.columns:
            result_df = df.rename(columns={"item": "字段名", "value": "字段值"})
            
            return result_df
        
        # 将横向数据转换为纵向格式
        if len(df) == 0:
            return pd.DataFrame()
        
        # 取第一行数据（通常只有一行）
        row_data = df.iloc[0]
        
        # 创建纵向格式的DataFrame
        vertical_data = []
        for column_name, value in row_data.items():
            if pd.notna(value) and str(value).strip() != "":
                vertical_data.append({
                    "字段名": column_name,
                    "字段值": str(value).strip()
                })
        
        vertical_data.append({
            "字段名": "数据清洗时间",
            "字段值": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        
        result_df = pd.DataFrame(vertical_data)
        
        return result_df



    def _clean_peer_comparison_data(self, df: pd.DataFrame, file_name: str) -> pd.DataFrame:
        """清洗同行比较数据 - 基本清洗，保持原格式"""
        # 基本清洗：移除空行和重复行
        df = df.dropna(how="all").drop_duplicates()
        
        # 确保代码列是字符串格式
        if "代码" in df.columns:
            df["代码"] = df["代码"].astype(str)
        df["代码"] = df["代码"].apply(lambda x: str(x).zfill(6) if str(x).isdigit() and len(str(x)) < 6 else str(x))
        
        ranking_columns = [col for col in df.columns if "排名" in col]
        for col in ranking_columns:
            pass
        
        forecast_columns = [col for col in df.columns if any(suffix in col for suffix in ["25E", "26E", "27E"])]
        for col in forecast_columns:
            pass
        
        df = df.reset_index(drop=True)

        return df

    def _sort_file_descending(self, file_path: Path) -> bool:
        """
        将文件按日期倒序排列

        Args:
            file_path: 文件路径

        Returns:
            bool: 是否成功
        """
        try:
            # 使用utf-8-sig编码来处理BOM，并清理列名
            df = pd.read_csv(file_path, encoding='utf-8-sig')

            # 清理列名中的BOM字符和空白字符
            df.columns = df.columns.str.replace('\ufeff', '').str.strip()

            if '日期' in df.columns:
                df['日期'] = pd.to_datetime(df['日期'], errors='coerce')

                df = df.sort_values('日期', ascending=False)
                # 保存时不使用BOM，使用标准utf-8编码
                df.to_csv(file_path, index=False, encoding='utf-8')
                return True
            else:
                print(f"   ⚠️ {file_path.name} 未找到日期列，跳过排序")
                return False
        except Exception as e:
            print(f"   ❌ 处理 {file_path.name} 时出错: {e}")
            return False

    def sort_symbol_data_descending(self, symbol: str) -> bool:
        """
        将指定股票的所有数据文件按日期降序排列（最终排序步骤）

        Args:
            symbol: 股票代码

        Returns:
            bool: 是否成功
        """
        try:
            cleaned_stock_dir = self.cleaned_dir / symbol
            if not cleaned_stock_dir.exists():
                print(f"   ⚠️ 目录不存在: {cleaned_stock_dir}")
                return False

            print(f"   🔄 开始最终数据降序排序: {symbol}")

            # 需要排序的主要文件
            files_to_sort = [
                "historical_quotes.csv",
                "income_statement.csv",
                "balance_sheet.csv",
                "cash_flow_statement.csv",
                "financial_indicators.csv",
                "stock_valuation.csv",
                "intraday_data.csv",
                "main_business_composition.csv",
                  "stock_belong_boards.csv"
            ]

            success_count = 0
            total_files = 0

            for filename in files_to_sort:
                file_path = cleaned_stock_dir / filename
                if file_path.exists():
                    total_files += 1
                    if self._sort_file_descending(file_path):
                        success_count += 1

            print(f"   ✅ 最终数据排序完成: {success_count}/{total_files} 个文件成功")
            return total_files == 0 or success_count > 0

        except Exception as e:
            print(f"   ❌ 最终排序时出错: {e}")
            return False



if __name__ == "__main__":
    import argparse
    import sys

    # 创建参数解析器
    parser = argparse.ArgumentParser(description="数据清洗工具")
    parser.add_argument("stock_code", nargs="?", default="000001", help="股票代码")
    parser.add_argument("--post-backtest", action="store_true",
                       help="回测后模式：将数据按日期倒序排列")
    parser.add_argument("-p", "--post", action="store_true",
                       help="回测后模式的简写 (等同于 --post-backtest)")

    # 解析参数
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)

    args = parser.parse_args()
    stock_code = args.stock_code
    post_backtest_mode = args.post_backtest or args.post

    # 创建数据清洗器
    cleaner = EnhancedDataCleaner()

    # 执行清洗
    result = cleaner.clean_stock_data(stock_code, post_backtest_mode=post_backtest_mode)

    mode_text = "回测后数据倒序处理" if post_backtest_mode else "数据清洗"
    if result:
        print(f"✅ 股票 {stock_code} {mode_text}完成")
    else:
        print(f"❌ 股票 {stock_code} {mode_text}失败")