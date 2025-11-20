#!/usr/bin/env python

"""
Market数据清洗模块
对market数据采集器生成的数据进行清洗和标准化处理
"""

import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from config import config


class MarketDataCleaner:
    """Market数据清洗器"""

    def __init__(
        self,
        data_dir: Path = None,
        cleaned_dir: Path = None,
    ):
        # 使用统一路径管理
        if data_dir is None:
            data_dir = config.get_market_data_dir(cleaned=False)
        if cleaned_dir is None:
            cleaned_dir = config.get_market_data_dir(cleaned=True)

        self.data_dir = Path(data_dir)
        self.cleaned_dir = Path(cleaned_dir)
        self.cleaned_dir.mkdir(parents=True, exist_ok=True)


    def load_market_data(self) -> Optional[Dict[str, List[Dict]]]:
        """从CSV文件加载market数据"""
        return self._load_from_csv_files()

    def _load_from_csv_files(self) -> Optional[Dict[str, List[Dict]]]:
        """从原始CSV文件加载数据"""
        market_data = {}

        # 定义数据文件映射
        csv_files = {
            "sector_fund_flow": "sector_fund_flow.csv",
            "fund_flow_industry": "fund_flow_industry.csv",
            "fund_flow_concept": "fund_flow_concept.csv",
            "fund_flow_individual": "fund_flow_individual.csv",  # 重新启用
            "zt_pool": "zt_pool.csv",
            "lhb_detail": "lhb_detail.csv",
            "realtime_quotes": "realtime_quotes.csv",
            "news_main_cx": "news_main_cx.csv",
            "market_activity_legu": "market_activity_legu.csv",
            # 指数日线（按缓存命名约定）
            "index_sh000001": "index_sh000001.csv",
            "index_sz399001": "index_sz399001.csv",
            "index_sh000300": "index_sh000300.csv",
        }

        for data_type, filename in csv_files.items():
            csv_path = self.data_dir / filename
            if csv_path.exists():
                df = pd.read_csv(csv_path)
                market_data[data_type] = df.to_dict("records")

        return market_data if market_data else None


    def _convert_financial_value(self, value):
        """将财务数值字符串转换为数值（参考个股清洗器）"""
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
        return float(str_value) * multiplier

    def _convert_percentage_to_number(self, value: str) -> float:
        """将百分比字符串转换为数值"""
        if pd.isna(value) or value == "":
            return 0.0

        value_str = str(value).strip()

        # 移除百分号
        if "%" in value_str:
            value_str = value_str.replace("%", "")

        return float(value_str)


    def clean_sector_fund_flow(self, data: List[Dict]) -> pd.DataFrame:
        """清洗板块资金流数据"""
        if not data:
            return pd.DataFrame()

        df = pd.DataFrame(data)

        # 数据清洗
        # 处理数值列
        numeric_columns = [
            "今日涨跌幅",
            "今日主力净流入-净额",
            "今日主力净流入-净占比",
            "今日超大单净流入-净额",
            "今日超大单净流入-净占比",
            "今日大单净流入-净额",
            "今日大单净流入-净占比",
            "今日中单净流入-净额",
            "今日中单净流入-净占比",
            "今日小单净流入-净额",
            "今日小单净流入-净占比",
        ]

        for col in numeric_columns:
            if col in df.columns:
                if "占比" in col or "涨跌幅" in col:
                    df[col] = df[col].apply(self._convert_percentage_to_number)
                else:
                    df[col] = df[col].apply(self._convert_financial_value)

        # 按涨跌幅倒序排列并重置排名
        if "今日涨跌幅" in df.columns:
            df = df.sort_values("今日涨跌幅", ascending=False).reset_index(
                drop=True
            )
            # 移除原序号列，新增排名列
            if "序号" in df.columns:
                df = df.drop("序号", axis=1)
            df.insert(0, "排名", range(1, len(df) + 1))


        return df

    def clean_fund_flow_industry(self, data: List[Dict]) -> pd.DataFrame:
        """清洗行业资金流数据"""
        if not data:
            return pd.DataFrame()

        df = pd.DataFrame(data)

        # 数据清洗
        # 处理数值列
        numeric_columns = ["涨跌幅", "流入资金", "流出资金", "净额", "成交额"]
        for col in numeric_columns:
            if col in df.columns:
                if col == "涨跌幅":
                    df[col] = df[col].apply(self._convert_percentage_to_number)
                else:
                    df[col] = df[col].apply(self._convert_financial_value)

        # 按涨跌幅倒序排列并重置排名
        sort_column = "行业-涨跌幅" if "行业-涨跌幅" in df.columns else "涨跌幅"
        if sort_column in df.columns:
            df = df.sort_values(sort_column, ascending=False).reset_index(drop=True)
            # 移除原序号列，新增排名列
            if "序号" in df.columns:
                df = df.drop("序号", axis=1)
            df.insert(0, "排名", range(1, len(df) + 1))


        return df

    def clean_fund_flow_concept(self, data: List[Dict]) -> pd.DataFrame:
        """清洗概念资金流数据"""
        if not data:
            return pd.DataFrame()

        df = pd.DataFrame(data)

        # 数据清洗
        # 处理数值列
        numeric_columns = ["涨跌幅", "流入资金", "流出资金", "净额", "成交额"]
        for col in numeric_columns:
            if col in df.columns:
                if col == "涨跌幅":
                    df[col] = df[col].apply(self._convert_percentage_to_number)
                else:
                    df[col] = df[col].apply(self._convert_financial_value)

        # 按涨跌幅倒序排列并重置排名
        sort_column = "行业-涨跌幅" if "行业-涨跌幅" in df.columns else "涨跌幅"
        if sort_column in df.columns:
            df = df.sort_values(sort_column, ascending=False).reset_index(drop=True)
            # 移除原序号列，新增排名列
            if "序号" in df.columns:
                df = df.drop("序号", axis=1)
            df.insert(0, "排名", range(1, len(df) + 1))


        return df

    def clean_fund_flow_individual(self, data: List[Dict]) -> pd.DataFrame:
        """清洗个股资金流数据"""
        if not data:
            return pd.DataFrame()

        df = pd.DataFrame(data)

        # 数据清洗
        # 处理股票代码列，使用zfill填充为6位数
        if "代码" in df.columns:
            df["代码"] = df["代码"].astype(str).apply(lambda x: x.zfill(6))

        # 处理股票名称列，确保不为空
        if "名称" in df.columns:
            df["名称"] = df["名称"].fillna("未知")

        # 处理数值列
        numeric_columns = [
            "最新价",
            "涨跌幅",
            "换手率",
            "流入资金",
            "流出资金",
            "净额",
            "成交额",
            "流通市值",
            "总市值",
            "市盈率",
            "市净率",
        ]

        for col in numeric_columns:
            if col in df.columns:
                if col in ["涨跌幅", "换手率"]:
                    df[col] = df[col].apply(self._convert_percentage_to_number)
                elif col in ["流入资金", "流出资金", "净额", "成交额", "流通市值", "总市值"]:
                    df[col] = df[col].apply(self._convert_financial_value)
                else:
                    df[col] = pd.to_numeric(df[col], errors="coerce")

        # 计算资金流向指标
        if all(col in df.columns for col in ["流入资金", "流出资金"]):
            # 计算净流入比例
            df["净流入比例"] = (df["净额"] / (df["流入资金"] + df["流出资金"]) * 100).round(2)
            # 填充NaN值
            df["净流入比例"] = df["净流入比例"].fillna(0)

        # 按涨跌幅倒序排列并重置排名
        if "涨跌幅" in df.columns:
            df = df.sort_values("涨跌幅", ascending=False).reset_index(drop=True)
            # 移除原序号列，新增排名列
            if "序号" in df.columns:
                df = df.drop("序号", axis=1)
            df.insert(0, "排名", range(1, len(df) + 1))


        return df

    def clean_zt_pool(self, data: List[Dict]) -> pd.DataFrame:
        """清洗涨停股池数据"""
        if not data:
            return pd.DataFrame()

        df = pd.DataFrame(data)

        # 数据清洗
        # 处理股票代码列，使用zfill填充为6位数
        if "代码" in df.columns:
            df["代码"] = df["代码"].astype(str).apply(lambda x: x.zfill(6))

        # 处理数值列
        numeric_columns = [
            "涨跌幅",
            "最新价",
            "成交额",
            "流通市值",
            "总市值",
            "换手率",
            "封板资金",
            "首次封板时间",
            "最后封板时间",
            "炸板次数",
            "连板数",
        ]

        for col in numeric_columns:
            if col in df.columns:
                if col in ["涨跌幅", "换手率"]:
                    df[col] = df[col].apply(self._convert_percentage_to_number)
                elif col in ["封板资金", "成交额", "流通市值", "总市值"]:
                    df[col] = df[col].apply(self._convert_financial_value)
                elif col in ["首次封板时间", "最后封板时间"]:
                    # 处理时间格式 (HHMMSS)
                    df[col] = pd.to_numeric(df[col], errors="coerce")
                else:
                    df[col] = pd.to_numeric(df[col], errors="coerce")

        # 按涨跌幅倒序排列并重置排名
        if "涨跌幅" in df.columns:
            df = df.sort_values("涨跌幅", ascending=False).reset_index(drop=True)
            # 移除原序号列，新增排名列
            if "序号" in df.columns:
                df = df.drop("序号", axis=1)
            df.insert(0, "排名", range(1, len(df) + 1))


        return df

    def clean_lhb_detail(self, data: List[Dict]) -> pd.DataFrame:
        """清洗龙虎榜详情数据"""
        if not data:
            return pd.DataFrame()

        df = pd.DataFrame(data)

        # 数据清洗
        # 处理股票代码列，使用zfill填充为6位数
        if "代码" in df.columns:
            df["代码"] = df["代码"].astype(str).apply(lambda x: x.zfill(6))

        # 处理数值列
        numeric_columns = [
            "收盘价",
            "涨跌幅",
            "龙虎榜净买额",
            "龙虎榜买入额",
            "龙虎榜卖出额",
            "龙虎榜成交额",
            "市场总成交额",
            "净买额占总成交比",
            "成交额占总成交比",
            "换手率",
            "流通市值",
            "上榜后1日",
            "上榜后2日",
            "上榜后5日",
            "上榜后10日",
        ]

        for col in numeric_columns:
            if col in df.columns:
                if col in [
                    "涨跌幅",
                    "换手率",
                    "净买额占总成交比",
                    "成交额占总成交比",
                    "上榜后1日",
                    "上榜后2日",
                    "上榜后5日",
                    "上榜后10日",
                ]:
                    df[col] = df[col].apply(self._convert_percentage_to_number)
                elif col in [
                    "龙虎榜净买额",
                    "龙虎榜买入额",
                    "龙虎榜卖出额",
                    "龙虎榜成交额",
                    "市场总成交额",
                    "流通市值",
                ]:
                    df[col] = df[col].apply(self._convert_financial_value)
                else:
                    df[col] = pd.to_numeric(df[col], errors="coerce")

        # 按涨跌幅倒序排列并重置排名
        if "涨跌幅" in df.columns:
            df = df.sort_values("涨跌幅", ascending=False).reset_index(drop=True)
            # 移除原序号列，新增排名列
            if "序号" in df.columns:
                df = df.drop("序号", axis=1)
            df.insert(0, "排名", range(1, len(df) + 1))


        return df

    def clean_realtime_quotes(self, data: List[Dict]) -> pd.DataFrame:
        """清洗实时行情数据"""
        if not data:
            return pd.DataFrame()

        df = pd.DataFrame(data)

        # 数据清洗
        # 处理股票代码列，使用zfill填充为6位数
        if "代码" in df.columns:
            df["代码"] = df["代码"].astype(str).apply(lambda x: x.zfill(6))

        # 处理数值列
        numeric_columns = [
            "最新价",
            "涨跌幅",
            "涨跌额",
            "成交量",
            "成交额",
            "振幅",
            "最高",
            "最低",
            "今开",
            "昨收",
            "量比",
            "换手率",
            "市盈率-动态",
            "市净率",
            "总市值",
            "流通市值",
            "涨速",
            "5分钟涨跌",
            "60日涨跌幅",
            "年初至今涨跌幅",
        ]

        for col in numeric_columns:
            if col in df.columns:
                if col in [
                    "涨跌幅",
                    "振幅",
                    "换手率",
                    "涨速",
                    "5分钟涨跌",
                    "60日涨跌幅",
                    "年初至今涨跌幅",
                ]:
                    df[col] = df[col].apply(self._convert_percentage_to_number)
                elif col in ["成交额", "总市值", "流通市值"]:
                    df[col] = df[col].apply(self._convert_financial_value)
                else:
                    df[col] = pd.to_numeric(df[col], errors="coerce")

        # 按涨跌幅倒序排列并重置排名
        if "涨跌幅" in df.columns:
            df = df.sort_values("涨跌幅", ascending=False).reset_index(drop=True)
            # 移除原序号列，新增排名列
            if "序号" in df.columns:
                df = df.drop("序号", axis=1)
            df.insert(0, "排名", range(1, len(df) + 1))


        return df

    def clean_news_main_cx(self, data: List[Dict]) -> pd.DataFrame:
        """清洗财联社主要新闻数据"""
        if not data:
            return pd.DataFrame()

        df = pd.DataFrame(data)

        # 列重命名：英文转中文
        column_mapping = {
            'tag': '标签',
            'summary': '摘要',
            'interval_time': '时间'
        }
        df = df.rename(columns=column_mapping)

        # 删除不需要的列：pub_time和url
        columns_to_drop = ['pub_time', 'url']
        for col in columns_to_drop:
            if col in df.columns:
                df = df.drop(columns=[col])

        # 数据清洗
        # 删除全空行
        df = df.dropna(how='all')

        # 重置索引
        df = df.reset_index(drop=True)

        # 处理时间列：转换为datetime并格式化为yy-mm-dd
        if '时间' in df.columns:
            # 将时间转换为datetime格式
            df['时间'] = pd.to_datetime(df['时间'], errors='coerce')
            # 删除时间无效的记录
            df = df.dropna(subset=['时间'])

            # 筛选最近1个月的数据
            from datetime import datetime, timedelta
            one_month_ago = datetime.now() - timedelta(days=30)
            df = df[df['时间'] >= one_month_ago]

            # 格式化日期为yyyy-mm-dd格式
            df['时间'] = df['时间'].dt.strftime('%Y-%m-%d')

            # 按时间倒序排列（最新的在前）
            df = df.sort_values('时间', ascending=False)

        # 处理缺失的标签
        if '标签' in df.columns:
            df['标签'] = df['标签'].fillna('无标签')

        # 重新排列列的顺序：时间作为第一列
        column_order = ['时间', '标签', '摘要']
        available_columns = [col for col in column_order if col in df.columns]
        df = df[available_columns]

        return df

    def clean_market_activity_legu(self, data: List[Dict]) -> pd.DataFrame:
        """清洗乐股市场活跃度数据"""
        if not data:
            return pd.DataFrame()

        df = pd.DataFrame(data)

        # 数据清洗
        # 删除全空行
        df = df.dropna(how='all')

        # 重置索引
        df = df.reset_index(drop=True)

        # 确保必要的列存在
        if '指标' in df.columns and '数值' in df.columns:
            # 处理数值列，确保为数值类型
            df['数值'] = pd.to_numeric(df['数值'], errors='coerce')

            # 按照常见顺序排列指标
            preferred_order = [
                '上涨', '涨停', '真实涨停', 'st st*涨停',
                '下跌', '跌停', '真实跌停', 'st st*跌停',
                '平盘', '停牌', '活跃度', '统计日期'
            ]

            # 重新排序：将已知的指标按preferred_order排列，未知指标保持在后面
            known_indicators = [ind for ind in preferred_order if ind in df['指标'].values]
            unknown_indicators = [ind for ind in df['指标'].values if ind not in preferred_order]
            final_order = known_indicators + unknown_indicators

            df = df.set_index('指标').loc[final_order].reset_index()

        return df

    def clean_all_market_data(self) -> Dict[str, pd.DataFrame]:
        """清洗所有market数据"""
        # 加载原始数据
        market_data = self.load_market_data()
        if not market_data:
            return {}

        # 清洗各类数据
        cleaned_data = {}

        cleaning_map = {
            "sector_fund_flow": self.clean_sector_fund_flow,
            "fund_flow_industry": self.clean_fund_flow_industry,
            "fund_flow_concept": self.clean_fund_flow_concept,
            "fund_flow_individual": self.clean_fund_flow_individual,
            "zt_pool": self.clean_zt_pool,
            "lhb_detail": self.clean_lhb_detail,
            "realtime_quotes": self.clean_realtime_quotes,
            "news_main_cx": self.clean_news_main_cx,
            "market_activity_legu": self.clean_market_activity_legu,
        }

        for data_type, cleaning_func in cleaning_map.items():
            if data_type in market_data:
                cleaned_data[data_type] = cleaning_func(market_data[data_type])

        # 保存清洗后的数据
        self.save_cleaned_data(cleaned_data)

        return cleaned_data

    def save_cleaned_data(self, cleaned_data: Dict[str, pd.DataFrame]):
        """保存清洗后的数据"""
        # 保存CSV文件，不添加日期后缀
        for data_type, df in cleaned_data.items():
            csv_file = self.cleaned_dir / f"{data_type}.csv"
            df.to_csv(csv_file, index=False, encoding="utf-8")


async def main():
    """主函数"""
    cleaner = MarketDataCleaner()
    cleaned_data = cleaner.clean_all_market_data()

    print("Market数据清洗完成！")
    print("数据统计:")
    for data_type, df in cleaned_data.items():
        print(f"  {data_type}: {len(df)}条记录")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())