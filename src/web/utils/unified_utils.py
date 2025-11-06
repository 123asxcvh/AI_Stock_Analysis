#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
统一工具模块
整合所有常用的格式化、工具函数、数据处理、图表创建和系统功能
避免重复，提供统一的访问接口
"""

import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Union, Optional, Dict, Any, List
from functools import lru_cache
from pathlib import Path
import sys

# 添加项目根目录
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from config import config


# ==================== 格式化函数 ====================

def format_number(value: Union[int, float], precision: int = 2) -> str:
    """格式化数字（万/亿）"""
    if pd.isna(value) or value is None:
        return "N/A"

    try:
        abs_val = abs(value)
        if abs_val >= 1e8:
            return f"{value / 1e8:.{precision}f}亿"
        elif abs_val >= 1e4:
            return f"{value / 1e4:.{precision}f}万"
        else:
            return f"{value:.0f}"
    except:
        return "N/A"


def format_percentage(value: Union[int, float], precision: int = 2) -> str:
    """格式化百分比"""
    if pd.isna(value) or value is None:
        return "N/A"

    try:
        if abs(value) < 0.01:  # 如果是小数形式的百分比
            return f"{value * 100:.{precision}f}%"
        else:  # 如果已经是百分比形式
            return f"{value:.{precision}f}%"
    except:
        return "N/A"


def format_money(value: Union[int, float], unit: str = "元") -> str:
    """格式化金额"""
    formatted = format_number(value)
    return f"{formatted}{unit}" if formatted != "N/A" else "N/A"


def format_change(value: Union[int, float], prefix: str = "") -> str:
    """格式化变化量"""
    if pd.isna(value) or value is None:
        return "N/A"

    try:
        arrow = "📈" if value > 0 else "📉" if value < 0 else "➡️"
        if abs(value) >= 1:
            formatted = f"{value:+.1f}"
        else:
            formatted = f"{value:+.2f}"
        return f"{prefix}{arrow} {formatted}"
    except:
        return "N/A"


# ==================== 数据处理函数 ====================

def get_stock_file_path(stock_code: str, filename: str, cleaned: bool = True) -> Path:
    """获取股票文件路径"""
    stock_dir = config.get_stock_dir(stock_code, cleaned=cleaned)
    return stock_dir / filename


def load_csv(file_path: Path, **kwargs) -> pd.DataFrame:
    """加载CSV文件"""
    if not file_path.exists():
        return pd.DataFrame()

    try:
        df = pd.read_csv(file_path, **kwargs)

        # 处理日期列
        if '日期' in df.columns:
            df['日期'] = pd.to_datetime(df['日期'])
            df = df.set_index('日期')

        return df
    except Exception as e:
        print(f"加载文件失败 {file_path}: {e}")
        return pd.DataFrame()


def get_available_stocks() -> List[str]:
    """获取可用股票列表"""
    stocks = []
    stocks_dir = config.cleaned_stocks_dir

    if stocks_dir.exists():
        for stock_dir in stocks_dir.iterdir():
            if stock_dir.is_dir():
                quotes_file = stock_dir / "historical_quotes.csv"
                if quotes_file.exists():
                    stocks.append(stock_dir.name)

    return sorted(stocks)


def get_stock_name(stock_code: str) -> Optional[str]:
    """获取股票名称"""
    try:
        profile_file = get_stock_file_path(stock_code, "company_profile.csv")
        if profile_file.exists():
            df = load_csv(profile_file)
            if not df.empty and '公司名称' in df.columns:
                return df.iloc[0]['公司名称']
    except:
        pass
    return None


# ==================== Streamlit UI组件 ====================

def display_metric(title: str, value: Union[str, float], delta: Optional[Union[str, float]] = None,
                   icon: str = "", help_text: str = ""):
    """显示指标卡片"""
    if delta is not None:
        st.metric(title, value, delta, help=help_text)
    else:
        st.metric(title, value, help=help_text)


def display_info_box(title: str, content: str, icon: str = "", box_type: str = "info"):
    """显示信息框"""
    if box_type == "info":
        st.info(f"{icon} {title}: {content}")
    elif box_type == "warning":
        st.warning(f"{icon} {title}: {content}")
    elif box_type == "error":
        st.error(f"{icon} {title}: {content}")
    elif box_type == "success":
        st.success(f"{icon} {title}: {content}")
    else:
        st.info(f"{icon} {title}: {content}")


def create_expandable_section(title: str, content_func, expanded: bool = False):
    """创建可展开的区域"""
    with st.expander(title, expanded=expanded):
        content_func()


def create_page_header(title: str, subtitle: str = ""):
    """创建页面标题"""
    if subtitle:
        st.markdown(f"## {title}\n\n{subtitle}\n")
    else:
        st.markdown(f"## {title}\n")


def create_section_header(title: str):
    """创建章节标题"""
    st.markdown(f"### {title}")


def create_columns_layout(n_cols: int):
    """创建多列布局"""
    return st.columns(n_cols)


# ==================== 图表函数 ====================

def create_candlestick_chart(df: pd.DataFrame, title: str = "K线图",
                            show_volume: bool = True, ma_periods: List[int] = [5, 10, 20]) -> go.Figure:
    """创建K线图"""
    if df.empty:
        return go.Figure()

    rows = 2 if show_volume and '成交量' in df.columns else 1
    subplot_titles = ["价格走势", "成交量"] if show_volume else ["价格走势"]

    fig = make_subplots(
        rows=rows, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        subplot_titles=subplot_titles,
        row_width=[0.2, 0.7] if show_volume else [0.2]
    )

    # K线图
    candlestick = go.Candlestick(
        x=df.index,
        open=df['开盘'],
        high=df['最高'],
        low=df['最低'],
        close=df['收盘'],
        name="K线",
        increasing_line_color='#ef4444',
        decreasing_line_color='#10b981'
    )
    fig.add_trace(candlestick, row=1, col=1)

    # 移动平均线
    colors = ['#FFD700', '#1E90FF', '#FF6B6B']
    for i, period in enumerate(ma_periods):
        if len(df) >= period:
            ma_col = f'MA{period}'
            df[ma_col] = df['收盘'].rolling(window=period).mean()
            fig.add_trace(
                go.Scatter(
                    x=df.index, y=df[ma_col], mode='lines',
                    name=ma_col, line=dict(color=colors[i], width=2)
                ),
                row=1, col=1
            )

    # 成交量
    if show_volume and '成交量' in df.columns:
        colors = ['#ef4444' if close >= open else '#10b981'
                 for close, open in zip(df['收盘'], df['开盘'])]

        volume_bar = go.Bar(
            x=df.index, y=df['成交量'],
            name="成交量", marker_color=colors, opacity=0.7
        )
        fig.add_trace(volume_bar, row=2, col=1)

    fig.update_layout(
        title=title,
        xaxis_rangeslider_visible=False,
        template="plotly_dark",
        height=600 if show_volume else 400
    )

    return fig


def create_line_chart(df: pd.DataFrame, title: str = "折线图",
                      y_column: str = None) -> go.Figure:
    """创建折线图"""
    if df.empty:
        return go.Figure()

    if y_column is None:
        # 使用第一个数值列
        numeric_cols = df.select_dtypes(include=['number']).columns
        if numeric_cols.empty:
            return go.Figure()
        y_column = numeric_cols[0]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df.index, y=df[y_column],
        mode='lines', name=y_column,
        line=dict(color='#FFD700', width=2)
    ))

    fig.update_layout(
        title=title,
        template="plotly_dark",
        height=400
    )

    return fig


def create_volume_chart(df: pd.DataFrame, title: str = "成交量图") -> go.Figure:
    """创建成交量图"""
    if df.empty or '成交量' not in df.columns:
        return go.Figure()

    colors = ['#ef4444' if close >= open else '#10b981'
             for close, open in zip(df['收盘'], df['开盘'])]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df.index, y=df['成交量'],
        marker_color=colors, opacity=0.7,
        name="成交量"
    ))

    fig.update_layout(
        title=title,
        template="plotly_dark",
        height=300
    )

    return fig


def create_simple_line_chart(df: pd.DataFrame, title: str = "折线图", y_column: str = None) -> go.Figure:
    """创建简单折线图（不包含特殊格式化）"""
    if df.empty:
        return go.Figure()

    if y_column is None:
        numeric_cols = df.select_dtypes(include=['number']).columns
        if numeric_cols.empty:
            return go.Figure()
        y_column = numeric_cols[0]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df.index, y=df[y_column],
        mode='lines', name=y_column,
        line=dict(color='#FFD700', width=2)
    ))

    fig.update_layout(title=title, height=300)
    return fig


# ==================== 技术指标计算函数 ====================

def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    """计算RSI指标"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


def calculate_macd(prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, pd.Series]:
    """计算MACD指标"""
    ema_fast = prices.ewm(span=fast).mean()
    ema_slow = prices.ewm(span=slow).mean()
    macd = ema_fast - ema_slow
    signal_line = macd.ewm(span=signal).mean()
    histogram = macd - signal_line

    return {
        'MACD': macd,
        'Signal': signal_line,
        'Histogram': histogram
    }


def calculate_ma(prices: pd.Series, periods: List[int]) -> Dict[str, pd.Series]:
    """计算移动平均线"""
    ma_dict = {}
    for period in periods:
        if len(prices) >= period:
            ma_dict[f'MA{period}'] = prices.rolling(window=period).mean()
    return ma_dict


# ==================== 数据验证函数 ====================

def validate_data(df: pd.DataFrame, required_columns: List[str] = None) -> bool:
    """验证数据完整性"""
    if df.empty:
        return False

    if required_columns:
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            print(f"缺少必要列: {missing_cols}")
            return False

    return True


def safe_get_value(df: pd.DataFrame, column: str, default: Any = None) -> Any:
    """安全获取DataFrame中的值"""
    if df.empty or column not in df.columns:
        return default
    return df[column].iloc[-1] if not df[column].empty else default


# ==================== 缓存和性能函数 ====================

def clear_cache():
    """清除缓存"""
    if hasattr(st, 'cache_data'):
        st.cache_data.clear()


def get_cache_key(*args) -> str:
    """生成缓存键"""
    return "_".join(str(arg) for arg in args)


# ==================== 错误处理函数 ====================

def handle_error(func):
    """错误处理装饰器"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            st.error(f"操作失败: {e}")
            return None
    return wrapper


def display_error(message: str, title: str = "错误"):
    """显示错误信息"""
    st.error(f"**{title}**: {message}")


def display_warning(message: str, title: str = "警告"):
    """显示警告信息"""
    st.warning(f"**{title}**: {message}")


def display_success(message: str, title: str = "成功"):
    """显示成功信息"""
    st.success(f"**{title}**: {message}")


# ==================== 数据加载类 ====================

@st.cache_data(ttl=30, show_spinner="正在扫描股票数据...")
def _get_available_stocks_cached() -> List[str]:
    """获取可用的股票列表 - 缓存版本"""
    try:
        default_stocks = config.target_stocks
        available_stocks = set()

        # 检查默认股票
        for stock in default_stocks:
            if config.get_stock_dir(stock, cleaned=True).exists():
                available_stocks.add(stock)

        # 扫描目录
        cleaned_stocks_root = config.cleaned_stocks_dir
        if cleaned_stocks_root.exists():
            available_stocks.update({
                d.name for d in cleaned_stocks_root.iterdir()
                if d.is_dir() and d.name.isdigit()
            })

        return sorted(list(available_stocks), key=lambda x: (x not in default_stocks, x))
    except Exception as e:
        st.error(f"获取股票列表失败: {e}")
        return []


class UnifiedDataLoader:
    """统一数据加载器 - 整合所有数据加载功能"""

    def get_available_stocks(self) -> List[str]:
        """获取可用的股票列表"""
        return _get_available_stocks_cached()

    def get_stock_name(self, stock_code: str) -> str:
        """获取股票名称"""
        try:
            profile_path = config.get_stock_file_path(stock_code, "company_profile.csv", cleaned=True)
            if profile_path.exists():
                df = pd.read_csv(profile_path)
                if not df.empty:
                    # 处理键值对格式
                    if '字段名' in df.columns and '字段值' in df.columns:
                        profile_dict = dict(zip(df['字段名'], df['字段值']))
                        return profile_dict.get("A股简称", "")
                    # 处理标准格式
                    elif 'A股简称' in df.columns:
                        return df.iloc[0]['A股简称']
                    elif '公司名称' in df.columns:
                        return df.iloc[0]['公司名称']
        except Exception:
            pass
        return ""

    @lru_cache(maxsize=32)
    def load_stock_data(self, stock_code: str) -> Dict[str, pd.DataFrame]:
        """加载单个股票的所有数据"""
        data = {"stock_code": stock_code}
        stock_dir = config.get_stock_dir(stock_code, cleaned=True)

        if not stock_dir.exists():
            return data

        # 数据文件映射
        file_mappings = {
            "historical_quotes": "historical_quotes.csv",
            "company_profile": "company_profile.csv",
            "main_business_composition": "main_business_composition.csv",
            "balance_sheet": "balance_sheet.csv",
            "income_statement": "income_statement.csv",
            "cash_flow_statement": "cash_flow_statement.csv",
            "financial_indicators": "financial_indicators.csv",
            "stock_valuation": "stock_valuation.csv",
            "bid_ask": "bid_ask.csv",
            "trading_signals": "trading_signals.csv"
        }

        # 加载所有数据文件
        for key, filename in file_mappings.items():
            file_path = stock_dir / filename
            if file_path.exists():
                try:
                    df = pd.read_csv(file_path)
                    if '日期' in df.columns:
                        df['日期'] = pd.to_datetime(df['日期'])
                        df = df.set_index('日期')
                    data[key] = df
                except Exception as e:
                    print(f"加载文件失败 {file_path}: {e}")
                    data[key] = pd.DataFrame()

        return data

    @lru_cache(maxsize=16)
    def load_market_data(self, symbol: str = "sh000001") -> Optional[pd.DataFrame]:
        """加载指数数据"""
        path = config.market_data_dir / f"index_{symbol.lower()}.csv"
        if not path.exists():
            return None

        try:
            df = pd.read_csv(path)
            # 标准化列名
            if "日期" in df.columns:
                df["日期"] = pd.to_datetime(df["日期"])
                df = df.set_index("日期")
            else:
                if "date" in df.columns:
                    df["日期"] = pd.to_datetime(df["date"])
                    df = df.set_index("date")
                    if "close" in df.columns:
                        df["收盘"] = df["close"]
                    else:
                        return None

            # 确保有收盘价列
            if "收盘" in df.columns:
                return df.dropna(subset=["收盘"])
            return None
        except Exception:
            return None


class UnifiedAIReportManager:
    """统一AI报告管理器 - 整合AI报告功能"""

    def load_reports(self, stock_code: str, report_type: str = "stock") -> Dict[str, str]:
        """加载AI分析报告"""
        reports = {}

        # 确定目录
        if report_type == "market" or stock_code == "market_analysis":
            base_dir = config.ai_reports_dir / "market_analysis"
        else:
            base_dir = config.ai_reports_dir / stock_code

        if base_dir.exists():
            for fpath in base_dir.iterdir():
                if fpath.suffix == ".md":
                    try:
                        with open(fpath, encoding="utf-8") as f:
                            content = f.read()
                            if content.strip():
                                reports[fpath.name] = content
                    except Exception:
                        pass

        return reports

    def clear_cache(self):
        """清除报告缓存"""
        # Streamlit的缓存已移除，这个方法保留用于向后兼容
        pass

    def display_single_report(self, report_type: str, report_subtype: str = None):
        """直接显示单个AI分析报告，不使用tab选择"""
        import streamlit as st

        try:
            # 确定报告目录和文件名
            if report_type == "market_analysis":
                base_dir = config.ai_reports_dir / "market_analysis"
                if report_subtype:
                    # 使用具体的报告文件名
                    report_filename = f"{report_subtype}.md"
                else:
                    # 默认使用综合市场分析
                    report_filename = "comprehensive_market.md"
            else:
                base_dir = config.ai_reports_dir / report_type
                report_filename = "comprehensive_analysis.md"  # 默认文件名

            # 构建完整文件路径
            report_path = base_dir / report_filename

            # 尝试读取报告文件
            if report_path.exists():
                try:
                    with open(report_path, encoding="utf-8") as f:
                        content = f.read()

                    if content.strip():
                        # 检查是否是错误信息
                        if content.startswith("❌") or "AI分析失败" in content:
                            st.warning(f"🤖 AI分析报告暂未生成")
                            st.caption(f"报告文件: {report_filename}")
                        else:
                            st.markdown(content)
                    else:
                        st.warning(f"🤖 AI分析报告暂未生成")
                        st.caption(f"报告文件: {report_filename}")
                except Exception as e:
                    st.warning(f"🤖 AI分析报告读取失败")
                    st.caption(f"报告文件: {report_filename}")
            else:
                st.warning(f"🤖 AI分析报告暂未生成")
                st.caption(f"报告文件: {report_filename}")

        except Exception as e:
            st.warning(f"🤖 AI分析报告加载失败")
            st.caption(f"错误信息: {str(e)}")

    def display_reports_tabs(self, stock_code: str, analysis_type: str):
        """显示AI分析报告的tab界面"""
        import streamlit as st

        try:
            # 加载AI报告
            reports = self.load_reports(stock_code, "stock")

            if reports:
                # 创建tab
                report_names = []
                report_contents = []

                for filename, content in reports.items():
                    name = filename.replace(".md", "").replace("_", " ").title()
                    report_names.append(name)
                    report_contents.append(content)

                if report_names:
                    tabs = st.tabs(report_names)
                    for i, (tab, content) in enumerate(zip(tabs, report_contents)):
                        with tab:
                            if content.startswith("❌"):
                                st.error(f"AI分析失败: {content}")
                            else:
                                st.markdown(content)
                else:
                    st.info("暂无AI分析报告")
            else:
                st.info("AI分析报告暂未加载")

        except Exception as e:
            st.error(f"加载AI报告时出错: {str(e)}")
            st.info("AI分析报告暂未加载")


class UnifiedValidator:
    """统一验证器 - 整合所有验证功能"""

    @staticmethod
    def validate_data(data: Dict[str, Any], key: str, message: str = None) -> bool:
        """验证数据存在性"""
        if key not in data or data[key] is None:
            if message:
                UnifiedValidator.show_no_data_message(message)
            return False

        if isinstance(data[key], pd.DataFrame) and data[key].empty:
            if message:
                UnifiedValidator.show_no_data_message(message)
            return False

        return True

    @staticmethod
    def get_stock_code(data: Dict[str, Any], default: str = "未知") -> str:
        """获取股票代码"""
        return data.get("stock_code", default) if data else default

    @staticmethod
    def show_no_data_message(message: str = "暂无相关数据"):
        """显示无数据消息"""
        st.info(f"📊 {message}")

    @staticmethod
    def safe_get_value(data_dict: Dict, key: str, default: Any = "") -> Any:
        """安全获取字典值"""
        return data_dict.get(key, default) or default

    @staticmethod
    def validate_dataframe(df: pd.DataFrame, required_columns: List[str] = None) -> bool:
        """验证DataFrame"""
        if df.empty:
            return False

        if required_columns:
            missing_cols = [col for col in required_columns if col not in df.columns]
            if missing_cols:
                print(f"缺少必要列: {missing_cols}")
                return False

        return True

    @staticmethod
    def validate_financial_data(data: Dict[str, Any]) -> bool:
        """验证财务数据完整性"""
        required_files = [
            "balance_sheet", "income_statement", "cash_flow_statement"
        ]

        for file_key in required_files:
            if not UnifiedValidator.validate_data(data, file_key):
                return False

        return True


# 创建全局实例
data_loader = UnifiedDataLoader()
ai_report_manager = UnifiedAIReportManager()
validator = UnifiedValidator()

# 提供对常用方法的直接访问
validate_dataframe = validator.validate_dataframe
validate_financial_data = validator.validate_financial_data
show_no_data_message = validator.show_no_data_message
get_stock_code = validator.get_stock_code
safe_get_value = validator.safe_get_value

# AI报告管理器方法
display_reports_tabs = ai_report_manager.display_reports_tabs

# 移除的方法
create_benchmark_portfolio = None


# 导出所有功能
__all__ = [
    # 格式化函数
    'format_number', 'format_percentage', 'format_money', 'format_change',

    # 数据处理
    'get_stock_file_path', 'load_csv', 'get_available_stocks', 'get_stock_name',

    # UI组件
    'display_metric', 'display_info_box', 'create_expandable_section',
    'create_page_header', 'create_section_header', 'create_columns_layout',
    'display_error', 'display_warning', 'display_success',

    # 图表函数
    'create_candlestick_chart', 'create_line_chart', 'create_volume_chart',
    'create_simple_line_chart',

    # 技术指标
    'calculate_rsi', 'calculate_macd', 'calculate_ma',

    # 数据验证
    'validate_data', 'safe_get_value',

    # 缓存和性能
    'clear_cache', 'get_cache_key',

    # 错误处理
    'handle_error',

    # 数据加载器
    'data_loader', 'UnifiedDataLoader',

    # AI报告管理器
    'ai_report_manager', 'UnifiedAIReportManager',

    # 验证器
    'validator', 'UnifiedValidator',
    'validate_dataframe', 'validate_financial_data',
    'show_no_data_message', 'get_stock_code', 'safe_get_value',

    # AI报告管理器方法
    'display_reports_tabs',

    # 移除的方法
    'create_benchmark_portfolio'
]