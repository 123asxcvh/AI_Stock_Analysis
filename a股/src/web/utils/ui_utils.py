#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
简化的统一工具模块
移除重复函数，整合功能
"""

import pandas as pd
import streamlit as st
import re
import sys
from pathlib import Path
from typing import Union, Optional, Dict, Any, List
from functools import lru_cache

# 添加项目根目录
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from config import config


# ==================== 核心格式化函数 ====================

def format_with_unit(value: Union[int, float, None], unit: str = "", precision: int = 2) -> str:
    """统一的数值格式化函数，支持单位"""
    if value is None or pd.isna(value):
        return "N/A"

    try:
        # 处理符号
        sign = "+" if value > 0 else ""
        abs_val = abs(value)

        # 根据数值大小自动选择单位
        if unit == "auto":
            if abs_val >= 1e8:
                formatted = f"{sign}{value/1e8:.{precision}f}亿"
            elif abs_val >= 1e4:
                formatted = f"{sign}{value/1e4:.{precision}f}万"
            else:
                formatted = f"{sign}{value:.0f}"
        elif unit == "%":
            formatted = f"{value:.{precision}f}%"
        elif unit in ["元", "万元", "亿元"]:
            formatted = f"{value:,.{precision}f}{unit}"
        else:
            formatted = f"{value:,.{precision}f}{unit}"

        return formatted
    except:
        return "N/A"


# ==================== 简化的单位管理器 ====================

class UnitManager:
    """统一的数值单位管理器 - 简化版本"""

    @staticmethod
    def get_optimal_unit(values: List[float]) -> str:
        """根据数值大小获取最优单位"""
        if not values:
            return "元"
        max_value = max(abs(v) for v in values if v is not None)
        if max_value >= 1e8:
            return "亿元"
        elif max_value >= 1e4:
            return "万元"
        else:
            return "元"

    @staticmethod
    def get_factor_and_label(unit: str) -> tuple[float, str]:
        """获取单位的转换因子和显示标签"""
        factors = {
            "亿元": (1e8, "亿元"),
            "万": (1e4, "万元"),
            "元": (1, "元"),
            "亿": (1e8, "亿元"),
            "千": (1e3, "千元")
        }
        return factors.get(unit, (1, "元"))

    @staticmethod
    def convert_dataframe_to_unit(df: pd.DataFrame, columns: List[str], unit: str) -> pd.DataFrame:
        """将DataFrame的指定列转换为指定单位"""
        result_df = df.copy()
        factor, _ = UnitManager.get_factor_and_label(unit)

        for col in columns:
            if col in result_df.columns:
                result_df[col] = result_df[col] / factor

        return result_df

    @staticmethod
    def analyze_columns_for_unit(df: pd.DataFrame, columns: List[str]) -> dict:
        """分析指定列，返回最优单位信息"""
        all_values = []
        for col in columns:
            if col in df.columns:
                all_values.extend(df[col].dropna().tolist())

        if not all_values:
            return {'unit': '元', 'factor': 1, 'label': '元', 'has_data': False}

        optimal_unit = UnitManager.get_optimal_unit(all_values)
        factor, label = UnitManager.get_factor_and_label(optimal_unit)

        return {
            'unit': optimal_unit,
            'factor': factor,
            'label': label,
            'has_data': True
        }

    @staticmethod
    def format_value_with_unit(value: float, unit: str, precision: int = 2) -> str:
        """格式化数值并添加单位"""
        if value is None:
            return "无数据"

        _, label = UnitManager.get_factor_and_label(unit)

        if abs(value) >= 1e6:
            return f"{value:,.{precision}f}{label}"
        elif abs(value) >= 1e3:
            return f"{value:,.{precision}f}{label}"
        else:
            return f"{value:.{precision}f}{label}"

    @staticmethod
    def create_hover_text(values: List[float], unit: str, precision: int = 2) -> List[str]:
        """为数值列表创建格式化的悬停文本"""
        return [UnitManager.format_value_with_unit(v, unit, precision) if v is not None else "无数据" for v in values]


# ==================== 金额转换 ====================

def convert_money(money_str: str) -> float:
    """转换金额字符串为数字"""
    if not money_str or money_str in [None, '', 'N/A']:
        return 0.0

    try:
        clean_str = re.sub(r'[^\d.-]', '', str(money_str))
        if clean_str in ['', '-', '.']:
            return 0.0

        # 处理中文单位
        if '亿' in str(money_str):
            return float(clean_str) * 100000000
        elif '万' in str(money_str):
            return float(clean_str) * 10000
        elif '千' in str(money_str):
            return float(clean_str) * 1000
        else:
            return float(clean_str)
    except:
        return 0.0


# ==================== 简化的UI组件 ====================

def display_metric(title: str, value: Union[str, float], delta: Optional[Union[str, float]] = None,
                  help_text: Optional[str] = None, delta_color: str = "normal") -> None:
    """显示指标卡片"""
    try:
        if delta is not None:
            # 确保delta_color是有效值
            if delta_color not in ["normal", "inverse", "off"]:
                delta_color = "normal"
            # 正确的参数顺序：label, value, delta, delta_color, help
            st.metric(title, value, delta=delta, delta_color=delta_color, help=help_text)
        else:
            st.metric(title, value, delta=delta, help=help_text)
    except Exception as e:
        st.error(f"显示指标失败: {e}")


def section_header(title: str, icon: str = "", level: int = 2):
    """创建章节标题（带图标）"""
    if level == 1:
        st.markdown(f"# {icon} {title}" if icon else f"# {title}")
    else:
        st.markdown(f"{'#' * level} {icon} {title}" if icon else f"{'#' * level} {title}")


# ==================== 数据处理 ====================

def display_comparison_table(df: pd.DataFrame, stock_code: str, analysis_type: str, metric_name: str):
    """显示对比表格 - 简化版本"""
    try:
        if df.empty:
            st.info(f"暂无{metric_name}对比数据")
            return

        if stock_code not in df.index and stock_code not in df.get('股票代码', []):
            return

        st.markdown(f"##### 📊 {metric_name} 对比分析")

        display_df = df.copy()
        numeric_cols = display_df.select_dtypes(include=['number']).columns
        for col in numeric_cols:
            if display_df[col].dtype in ['float64', 'int64']:
                display_df[col] = display_df[col].round(2)

        def highlight_target_stock(row):
            if stock_code in row.values:
                return ['background-color: rgba(255, 215, 0, 0.2)'] * len(row)
            return [''] * len(row)

        styled_df = display_df.style.apply(highlight_target_stock, axis=1)
        st.dataframe(styled_df, width="stretch")

    except Exception as e:
        print(f"显示对比表格失败: {e}")
        st.error(f"对比表格显示失败: {e}")


def get_numeric_value(data: Dict[str, Any], key_list: List[str]) -> float:
    """获取数值，支持字符串转换"""
    for key in key_list:
        if key in data:
            value = data[key]
            if value is None or value == "":
                continue
            try:
                if isinstance(value, str):
                    return convert_money(value.replace(',', '').replace(' ', ''))
                return float(value)
            except (ValueError, TypeError):
                continue
    return 0.0


def safe_get_year(df):
    """安全获取DataFrame的年份"""
    if isinstance(df, pd.Index):
        if isinstance(df, pd.DatetimeIndex):
            return df.year
        return pd.Series([], dtype=int)

    if df.empty:
        return pd.Series([], dtype=int)

    if isinstance(df.index, pd.DatetimeIndex):
        return df.index.year

    if '日期' in df.columns:
        try:
            dates = pd.to_datetime(df['日期'], errors='coerce')
            return dates.dt.year
        except:
            pass

    # 尝试其他可能的日期列
    for col in df.columns:
        if 'date' in col.lower() or '时间' in col:
            try:
                dates = pd.to_datetime(df[col], errors='coerce')
                return dates.dt.year
            except:
                continue

    return pd.Series([2024] * len(df), index=df.index)


def filter_annual_data(df: pd.DataFrame) -> pd.DataFrame:
    """过滤年度数据"""
    if df is None or df.empty:
        return df

    try:
        df = df.copy()

        if '日期' in df.columns:
            df['日期'] = pd.to_datetime(df['日期'], errors='coerce')
            df = df.dropna(subset=['日期'])
            if df.empty:
                return df

            df['年份'] = df['日期'].dt.year
            year_end_data = []

            for year in df['年份'].unique():
                year_data = df[df['年份'] == year]
                if not year_data.empty:
                    last_day = year_data['日期'].max()
                    last_day_data = year_data[year_data['日期'] == last_day]
                    if not last_day_data.empty:
                        year_end_data.append(last_day_data.iloc[0])

            if year_end_data:
                result = pd.DataFrame(year_end_data)
                result = result.sort_values('日期')
                if '年份' not in result.columns:
                    result['年份'] = result['日期'].dt.year.astype(int)
                return result

        return df
    except Exception as e:
        print(f"筛选年度数据失败: {e}")
        return df


# ==================== 缓存的股票管理 ====================

@lru_cache(maxsize=128)
def get_available_stocks() -> List[str]:
    """获取可用的股票列表"""
    try:
        stocks_dir = config.cleaned_stocks_dir
        if not stocks_dir.exists():
            return []
        return [d.name for d in stocks_dir.iterdir() if d.is_dir()]
    except Exception as e:
        print(f"获取股票列表失败: {e}")
        return []


def get_stock_file_path(stock_code: str, filename: str, cleaned: bool = True) -> Path:
    """获取股票文件路径"""
    if cleaned:
        return config.get_stock_dir(stock_code, cleaned=True) / filename
    else:
        return config.get_stock_dir(stock_code, cleaned=False) / filename


def load_csv(file_path: Path, **kwargs) -> pd.DataFrame:
    """加载CSV文件"""
    try:
        encodings = ['utf-8-sig', 'utf-8', 'gbk', 'gb2312', 'latin-1']

        for encoding in encodings:
            try:
                df = pd.read_csv(file_path, encoding=encoding, **kwargs)
                
                # 自动转换日期列
                date_columns = ['日期', 'date', '时间', '报告期', '报告日期']
                for col in date_columns:
                    if col in df.columns:
                        try:
                            df[col] = pd.to_datetime(df[col], errors='coerce')
                        except:
                            pass
                
                return df
            except UnicodeDecodeError:
                continue
            except Exception as e:
                if encoding == encodings[0]:
                    print(f"加载CSV失败 {file_path}: {e}")
                raise
        
        return pd.DataFrame()
    except Exception as e:
        print(f"加载CSV失败 {file_path}: {e}")
        return pd.DataFrame()


def validate_data(data: pd.DataFrame, required_columns: List[str] = None) -> bool:
    """验证数据有效性 - 简化版本"""
    if data is None or data.empty:
        return False

    if required_columns:
        missing_columns = [col for col in required_columns if col not in data.columns]
        if missing_columns:
            print(f"缺少必需的列: {missing_columns}")
            return False

    return True


# ==================== 数据加载器 ====================

class UnifiedDataLoader:
    """统一数据加载器 - 简化版本"""

    def get_available_stocks(self) -> List[str]:
        """获取可用的股票列表"""
        return get_available_stocks()

    def get_stock_name(self, stock_code: str) -> str:
        """获取股票名称"""
        try:
            profile_path = get_stock_file_path(stock_code, "company_profile.csv")
            if profile_path.exists():
                df = pd.read_csv(profile_path)
                if not df.empty:
                    if '字段名' in df.columns and '字段值' in df.columns:
                        profile_dict = dict(zip(df['字段名'], df['字段值']))
                        return profile_dict.get("A股简称", "") or profile_dict.get("公司名称", "")
                    elif 'A股简称' in df.columns:
                        return df.iloc[0]['A股简称']
            return stock_code
        except:
            return stock_code

    def load_stock_data(self, stock_code: str) -> Dict[str, Any]:
        """加载股票数据"""
        try:
            data = {'stock_code': stock_code}

            data_files = {
                'historical_quotes': 'historical_quotes.csv',
                'income_statement': 'income_statement.csv',
                'balance_sheet': 'balance_sheet.csv',
                'cash_flow_statement': 'cash_flow_statement.csv',
                'financial_indicators': 'financial_indicators.csv',
                'company_profile': 'company_profile.csv',
                'bid_ask': 'bid_ask.csv',
                'main_business_composition': 'main_business_composition.csv',
                'stock_valuation': 'stock_valuation.csv',
                'stock_belong_boards': 'stock_belong_boards.csv',
            }

            loaded_count = 0
            for key, filename in data_files.items():
                file_path = get_stock_file_path(stock_code, filename)
                if file_path.exists():
                    df = load_csv(file_path)
                    if not df.empty:
                        data[key] = df
                        loaded_count += 1

            if loaded_count == 0:
                print(f"⚠️ 警告: 股票 {stock_code} 没有加载到任何数据文件")

            return data
        except Exception as e:
            print(f"❌ 加载股票数据失败 {stock_code}: {e}")
            return {'stock_code': stock_code}


# ==================== AI报告管理器 ====================

class AIReportManager:
    """AI报告管理器 - 简化版本"""

    def __init__(self):
        self.cache = {}

    def load_reports(self, stock_code: str, report_type: str = "stock") -> Dict[str, str]:
        """加载AI报告"""
        cache_key = f"{stock_code}_{report_type}"

        if cache_key in self.cache:
            return self.cache[cache_key]

        reports = {}
        try:
            if report_type == "stock":
                report_dir = config.ai_reports_dir / stock_code
            else:
                report_dir = config.ai_reports_dir / report_type / stock_code
                
            if report_dir.exists():
                for report_file in report_dir.glob("*.md"):
                    with open(report_file, 'r', encoding='utf-8') as f:
                        reports[report_file.name] = f.read()

            self.cache[cache_key] = reports
        except Exception as e:
            print(f"加载AI报告失败 {stock_code}: {e}")

        return reports

    def clear_cache(self):
        """清除缓存"""
        self.cache.clear()


# ==================== 全局实例 ====================

# 创建全局实例
ai_report_manager = AIReportManager()
data_loader = UnifiedDataLoader()

# ==================== 统一的格式化函数 ====================

def format_chart_value(value: Union[int, float, None], unit: str = "auto", precision: int = 2) -> str:
    """统一的图表数值格式化函数"""
    if value is None or pd.isna(value):
        return "无数据"

    try:
        # 如果指定了单位，直接使用
        if unit != "auto":
            factor, label = UnitManager.get_factor_and_label(unit)
            converted_value = value / factor
            return f"{converted_value:,.{precision}f}{label}"

        # 自动选择最优单位
        if isinstance(value, (list, tuple)):
            all_values = [v for v in value if v is not None and not pd.isna(v)]
        else:
            all_values = [value]

        if all_values:
            optimal_unit = UnitManager.get_optimal_unit(all_values)
            factor, label = UnitManager.get_factor_and_label(optimal_unit)
            converted_value = value / factor
            return f"{converted_value:,.{precision}f}{label}"
        else:
            return "0.00"
    except:
        return "无数据"


def format_chart_values(values: List[Union[int, float, None]], unit: str = "auto", precision: int = 2) -> List[str]:
    """批量格式化图表数值"""
    return [format_chart_value(v, unit, precision) for v in values]


def get_chart_unit_and_factor(values: List[Union[int, float, None]], unit: str = "auto") -> tuple:
    """获取图表的单位转换因子和标签"""
    if not values:
        return 1, "元"

    # 过滤有效值
    valid_values = [v for v in values if v is not None and not pd.isna(v)]

    if not valid_values:
        return 1, "元"

    if unit == "auto":
        optimal_unit = UnitManager.get_optimal_unit(valid_values)
    else:
        optimal_unit = unit

    factor, label = UnitManager.get_factor_and_label(optimal_unit)
    return factor, label


def create_chart_hover_text(values: List[Union[int, float, None]], unit: str = "auto", precision: int = 2) -> List[str]:
    """创建图表的悬停文本"""
    return [format_chart_value(v, unit, precision) for v in values]


def create_chart_hover_text_no_unit(values: List[Union[int, float, None]], precision: int = 2) -> List[str]:
    """创建图表的悬停文本（不包含单位）"""
    result = []
    for v in values:
        if v is None or pd.isna(v):
            result.append("无数据")
        else:
            result.append(f"{v:,.{precision}f}")
    return result


# 向后兼容的别名
format_number = lambda v, precision=2: format_with_unit(v, "auto", precision)
format_percentage = lambda v, precision=2: format_with_unit(v, "%", precision)
format_money = lambda v, unit="元": format_with_unit(v, unit)
convert_money_to_number = convert_money
get_appropriate_unit = UnitManager.get_optimal_unit
get_unit_factor_and_suffix = UnitManager.get_factor_and_label


# ==================== fundamental_analysis_page需要的函数 ====================

def safe_get_date_column(df):
    """安全获取日期列"""
    if '日期' in df.columns:
        return '日期'
    elif 'date' in df.columns:
        return 'date'
    elif '时间' in df.columns:
        return '时间'
    elif isinstance(df.index, pd.DatetimeIndex):
        return None  # 使用索引
    return None


def filter_semi_annual_data(df: pd.DataFrame) -> pd.DataFrame:
    """过滤出0630和1231的半年度数据"""
    return filter_data_by_date(df, [(6, 30), (12, 31)])


def filter_data_by_date(df: pd.DataFrame, month_day_tuples) -> pd.DataFrame:
    """通用日期过滤方法"""
    if df is None or df.empty:
        return df

    df = df.copy()

    # 统一处理month_day_tuples参数
    if isinstance(month_day_tuples, int):
        month_day_tuples = [(month_day_tuples, 31)] if month_day_tuples != 6 else [(month_day_tuples, 30)]
    elif isinstance(month_day_tuples, tuple) and len(month_day_tuples) == 2:
        month_day_tuples = [month_day_tuples]

    # 获取日期列
    date_col = "日期" if "日期" in df.columns else None

    if date_col:
        df[date_col] = pd.to_datetime(df[date_col])
        mask = create_date_mask(df[date_col], month_day_tuples)
        filtered_df = df[mask].reset_index(drop=True)
        return filtered_df.sort_values(date_col)
    else:
        if not isinstance(df.index, pd.DatetimeIndex):
            return df
        date_series = df.index
        mask = create_date_mask(date_series, month_day_tuples)
        return df[mask].sort_index()


def create_date_mask(date_series, month_day_tuples):
    """创建日期过滤掩码"""
    if not isinstance(date_series, pd.Series):
        date_series = pd.Series(date_series)
    
    mask = pd.Series(False, index=date_series.index)
    for month, day in month_day_tuples:
        condition_mask = (date_series.dt.month == month) & (date_series.dt.day == day)
        mask = mask | condition_mask
    return mask


def get_year_end_data(df: pd.DataFrame) -> pd.DataFrame:
    """获取每年最后一天的数据"""
    if df.empty:
        return df

    try:
        df = df.copy()
        
        if '日期' in df.columns:
            df['日期'] = pd.to_datetime(df['日期'], errors='coerce')
            df = df.dropna(subset=['日期'])
            if df.empty:
                return df
            
            df['年份'] = df['日期'].dt.year
            year_end_data = []
            
            for year in df['年份'].unique():
                year_data = df[df['年份'] == year]
                if not year_data.empty:
                    last_day = year_data['日期'].max()
                    last_day_data = year_data[year_data['日期'] == last_day]
                    if not last_day_data.empty:
                        year_end_data.append(last_day_data.iloc[0])
            
            if year_end_data:
                result = pd.DataFrame(year_end_data)
                result = result.sort_values('日期')
                if '年份' not in result.columns:
                    result['年份'] = result['日期'].dt.year.astype(int)
                else:
                    result['年份'] = result['年份'].astype(int)
                return result
        elif isinstance(df.index, pd.DatetimeIndex):
            df['日期'] = df.index
            return get_year_end_data(df)
        else:
            return df

    except Exception as e:
        print(f"筛选年末数据失败: {e}")
        return df


def get_financial_metric_descriptions():
    """获取财务指标说明字典"""
    return {
        "盈利能力": {
            "净资产收益率": {
                "name": "净资产收益率 (ROE)",
                "description": "衡量股东权益的投资回报率",
                "calculation": "净利润 / 平均净资产 × 100%",
                "standard": ">15%优秀，10-15%良好",
                "icon": "💰"
            },
            "销售净利率": {
                "name": "销售净利率",
                "description": "每元销售收入的净利润",
                "calculation": "净利润 / 营业收入 × 100%",
                "standard": ">20%优秀，10-20%良好",
                "icon": "📊"
            }
        },
        "偿债能力": {
            "流动比率": {
                "name": "流动比率",
                "description": "流动资产与流动负债的比值",
                "calculation": "流动资产 / 流动负债",
                "standard": ">2优秀，1.5-2良好",
                "icon": "💵"
            },
            "资产负债率": {
                "name": "资产负债率",
                "description": "总负债与总资产的比值",
                "calculation": "总负债 / 总资产 × 100%",
                "standard": "<30%优秀，30-50%良好",
                "icon": "🏦"
            }
        }
    }