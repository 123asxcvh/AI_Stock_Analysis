#!/usr/bin/env python3
"""
简化的回测工具模块
消除冗余，专注核心功能
"""

import pandas as pd
import numpy as np
import ast
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from functools import lru_cache

logger = logging.getLogger(__name__)

# 全局实例缓存
_data_manager_instance = None


# ==================== 实例管理 ====================

@lru_cache(maxsize=1)
def get_data_manager():
    """获取DataManager单例实例"""
    global _data_manager_instance
    if _data_manager_instance is None:
        from .data_manager import DataManager
        _data_manager_instance = DataManager()
    return _data_manager_instance


def clear_caches():
    """清理所有缓存"""
    global _data_manager_instance
    _data_manager_instance = None
    get_data_manager.cache_clear()


# ==================== 参数处理 ====================

def parse_param_string(param_str: str) -> List[Any]:
    """解析参数字符串为列表"""
    if not param_str or param_str == "[N/A]":
        return []

    try:
        parsed = ast.literal_eval(param_str)
        if isinstance(parsed, (list, tuple)):
            return list(parsed)
        elif isinstance(parsed, dict):
            return list(parsed.values())
        else:
            return [parsed]
    except:
        try:
            cleaned = param_str.strip("[](){}")
            if "," in cleaned:
                return [float(x.strip()) if x.replace('.', '').replace('-', '').isdigit() else x.strip()
                       for x in cleaned.split(",")]
            else:
                return [cleaned]
        except:
            return [param_str]


def normalize_params(strategy_name: str, params: Union[List, Dict]) -> Dict[str, float]:
    """标准化参数格式，将列表转换为字典"""
    if not params:
        return {}

    if isinstance(params, dict):
        return params

    if isinstance(params, (list, tuple)):
        from .config import STRATEGY_PARAM_GRIDS
        param_grid = STRATEGY_PARAM_GRIDS.get(strategy_name, {})
        param_keys = list(param_grid.keys())

        length = min(len(params), len(param_keys))
        result = {}
        for i in range(length):
            param_name = param_keys[i]
            param_value = params[i]

            # 对于周期类参数，转换为整数
            if any(keyword in param_name.lower() for keyword in ['period', 'window', 'length']):
                result[param_name] = int(float(param_value))
            else:
                result[param_name] = float(param_value)

        return result

    return {}


def apply_strategy_params(strategy, params: Dict[str, Any]):
    """将参数应用到策略实例 - 使用安全的方式"""
    if not params or not strategy:
        return

    try:
        if hasattr(strategy, 'set_params'):
            strategy.set_params(params)
        else:
            if hasattr(strategy, 'params') and isinstance(strategy.params, dict):
                strategy.params.update(params)
            else:
                logger.warning(f"策略 {strategy.__class__.__name__} 不支持安全的参数设置方法")
    except Exception as e:
        logger.error(f"设置策略参数失败: {e}")
        raise


def format_params_for_storage(strategy_name: str, params: Dict[str, float]) -> str:
    """按策略参数网格顺序将参数字典转换为列表字符串"""
    if not params:
        return "[N/A]"

    from .config import STRATEGY_PARAM_GRIDS
    import numpy as np

    grid = STRATEGY_PARAM_GRIDS.get(strategy_name)
    if grid:
        ordered_values = [params.get(key) for key in grid.keys()]
    else:
        ordered_values = list(params.values())

    # 清理numpy类型，转换为简单的Python类型
    clean_values = []
    for val in ordered_values:
        if val is None:
            clean_values.append(None)
        elif isinstance(val, np.integer):
            clean_values.append(int(val))
        elif isinstance(val, np.floating):
            clean_values.append(float(val))
        elif isinstance(val, (int, float, str)):
            clean_values.append(val)
        else:
            clean_values.append(str(val))

    return str(clean_values)


# ==================== 数据处理 ====================

def load_stock_data_with_validation(symbol: str) -> Optional[pd.DataFrame]:
    """加载股票数据并验证（不重新计算技术指标，避免覆盖已有数据）"""
    try:
        data_manager = get_data_manager()
        data = data_manager.load_stock_data(symbol, required_indicators=[])
        return data if data is not None and not data.empty else None
    except Exception as e:
        logger.error(f"加载股票 {symbol} 数据失败: {e}")
        return None


def extract_date_series(data: pd.DataFrame) -> List[str]:
    """从股票数据中提取日期序列"""
    # 优先使用中文列名，向后兼容英文列名
    date_col = '日期' if '日期' in data.columns else 'date'
    if date_col in data.columns:
        return data[date_col].dt.strftime('%Y-%m-%d').tolist()
    elif hasattr(data.index, 'strftime'):
        return data.index.strftime('%Y-%m-%d').tolist()
    else:
        return data.index.tolist()


def ensure_output_directory(symbol: str, subpath: str = None) -> Path:
    """确保输出目录存在"""
    base_dir = Path(f"data/cleaned_stocks/{symbol}/backtest_results")
    if subpath:
        base_dir = base_dir / subpath
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir


# ==================== 策略对比和结果处理 ====================

def read_optimized_parameters(symbol: str) -> Dict[str, Dict[str, float]]:
    """读取已有的最优参数"""
    comparison_file = Path(f"data/cleaned_stocks/{symbol}/backtest_results/strategy_comparison.csv")

    if not comparison_file.exists():
        return {}

    try:
        df = pd.read_csv(comparison_file, encoding='utf-8')
        optimized_params = {}

        for _, row in df.iterrows():
            if row['参数'] != '[N/A]':
                try:
                    parsed = parse_param_string(row['参数'])
                    params_dict = normalize_params(row['策略名称'], parsed)
                    optimized_params[row['策略名称']] = params_dict
                except Exception as e:
                    logger.warning(f"解析策略 {row['策略名称']} 参数失败: {e}")

        return optimized_params
    except Exception as e:
        logger.error(f"读取参数失败: {e}")
        return {}


def generate_total_trades_csv_unified(output_dir: Path, symbol: str, strategy_names: List[str]):
    """统一的total_trades.csv生成函数 - 只保留有信号的日期"""
    try:
        data = load_stock_data_with_validation(symbol)
        if data is None:
            return

        # 收集所有有信号的日期
        signal_dates = set()
        strategy_signals = {}

        for strategy_name in strategy_names:
            strategy_dir = output_dir / strategy_name
            trades_path = strategy_dir / "trades.csv"

            strategy_signals[strategy_name] = {}

            if trades_path.exists():
                trades_df = pd.read_csv(trades_path, encoding='utf-8')

                for _, trade in trades_df.iterrows():
                    trade_date = str(trade['日期'])
                    trade_type = str(trade['类型']).lower()
                    signal_dates.add(trade_date)
                    strategy_signals[strategy_name][trade_date] = trade_type

        # 如果没有信号，创建空的DataFrame
        if not signal_dates:
            empty_df = pd.DataFrame(columns=['日期', '收盘价'] + strategy_names)
            empty_df.to_csv(output_dir / "total_trades.csv", index=False, encoding='utf-8')
            return

        # 只创建有信号的日期的DataFrame
        sorted_dates = sorted(signal_dates, reverse=True)  # 降序排列
        close_col = '收盘' if '收盘' in data.columns else 'close'
        close_prices = {}
        for date in sorted_dates:
            # 找到对应日期的收盘价
            date_mask = data['日期'].astype(str) == date
            if date_mask.any():
                close_prices[date] = data.loc[date_mask, close_col].iloc[0]
            else:
                close_prices[date] = None

        # 构建结果DataFrame
        result_data = []
        for date in sorted_dates:
            row = {
                '日期': date,
                '收盘价': close_prices[date]
            }

            # 为每个策略添加信号
            for strategy_name in strategy_names:
                row[strategy_name] = strategy_signals[strategy_name].get(date, '')

            result_data.append(row)

        result_df = pd.DataFrame(result_data)
        result_df.to_csv(output_dir / "total_trades.csv", index=False, encoding='utf-8')

    except Exception as e:
        logger.error(f"生成total_trades.csv失败: {e}")
        import traceback
        traceback.print_exc()


def create_strategy_comparison_csv(symbol: str, sorted_results: List,
                                  optimized_params: Dict[str, Dict[str, float]]):
    """创建策略对比CSV文件"""
    comparison_file = Path(f"data/cleaned_stocks/{symbol}/backtest_results/strategy_comparison.csv")

    # 性能指标配置
    metrics = [
        ('总收益率', 'total_return', ':.2f%'),
        ('年化收益率', 'annual_return', ':.2f%'),
        ('夏普比率', 'sharpe_ratio', ':.3f'),
        ('卡尔玛比率', 'calmar_ratio', ':.3f'),
        ('最大回撤', 'max_drawdown', ':.2f%'),
        ('年化波动率', 'volatility', ':.2f%'),
        ('总交易次数', 'total_trades', ':.0f'),
        ('胜率', 'win_rate', ':.1f%'),
        ('盈亏比', 'profit_loss_ratio', ':.2f'),
        ('止损次数', 'stop_loss_count', ':.0f'),
        ('止损率', 'stop_loss_rate', ':.2f%'),
        ('初始资金', 'initial_capital', ':,.0f'),
        ('最终资金', 'final_capital', ':,.0f'),
        ('总盈利', 'total_profit', ':,.0f'),
        ('总亏损', 'total_loss', ':,.0f'),
        ('执行时间(s)', 'execution_time', ':.2f')
    ]

    rows = []
    for rank, (strategy, result) in enumerate(sorted_results, 1):
        perf = result.get("performance", {})
        execution_time = result.get('execution_time', 0)
        params_str = format_params_for_storage(strategy, optimized_params.get(strategy))

        row = {
            "排名": rank,
            "策略名称": strategy,
            "参数": params_str,
            "执行时间(s)": f"{execution_time:.2f}"
        }

        for label, key, fmt in metrics:
            if key == 'execution_time':
                row[label] = f"{execution_time:.2f}"
            else:
                value = perf.get(key, 0)
                try:
                    if fmt.endswith('%'):
                        row[label] = f"{float(value):.2f}%"
                    elif fmt.endswith(',.0f'):
                        row[label] = f"{int(float(value)):,}"
                    else:
                        row[label] = f"{float(value):{fmt.replace(':', '.')}}"
                except:
                    row[label] = str(value)

        rows.append(row)

    df = pd.DataFrame(rows)
    df.to_csv(comparison_file, index=False, encoding='utf-8')




# ==================== 性能分析 ====================

def validate_performance_data(performance: Dict[str, Any]) -> bool:
    """验证性能数据的完整性和有效性"""
    required_fields = ['total_return', 'sharpe_ratio', 'max_drawdown', 'win_rate', 'total_trades']

    for field in required_fields:
        if field not in performance:
            return False
        try:
            float(performance[field])
        except (ValueError, TypeError):
            return False
    return True


def format_performance_metrics(performance: Dict[str, Any]) -> Dict[str, str]:
    """格式化性能指标用于显示"""
    formatters = {
        'total_return': f"{float(performance.get('total_return', 0)):.2f}%",
        'annual_return': f"{float(performance.get('annual_return', 0)):.2f}%",
        'sharpe_ratio': f"{float(performance.get('sharpe_ratio', 0)):.3f}",
        'calmar_ratio': f"{float(performance.get('calmar_ratio', 0)):.3f}",
        'max_drawdown': f"{float(performance.get('max_drawdown', 0)):.2f}%",
        'volatility': f"{float(performance.get('volatility', 0)):.2f}%",
        'win_rate': f"{float(performance.get('win_rate', 0)):.1f}%",
        'profit_loss_ratio': f"{float(performance.get('profit_loss_ratio', 0)):.2f}",
        'stop_loss_rate': f"{float(performance.get('stop_loss_rate', 0)):.2f}%",
        'total_trades': f"{int(float(performance.get('total_trades', 0))):,}",
        'stop_loss_count': f"{int(float(performance.get('stop_loss_count', 0))):,}",
        'initial_capital': f"{int(float(performance.get('initial_capital', 0))):,}",
        'final_capital': f"{int(float(performance.get('final_capital', 0))):,}",
        'total_profit': f"{int(float(performance.get('total_profit', 0))):,}",
        'total_loss': f"{int(float(performance.get('total_loss', 0))):,}"
    }

    return {key: formatters.get(key, str(value)) for key, value in performance.items()}


def calculate_strategy_rating(performance: Dict[str, Any]) -> float:
    """计算策略综合评分 (0-100分)"""
    try:
        sharpe = float(performance.get('sharpe_ratio', 0))
        return_rate = float(performance.get('total_return', 0))
        max_dd = float(performance.get('max_drawdown', 100))
        win_rate = float(performance.get('win_rate', 0))

        # 综合评分公式
        sharpe_score = min(sharpe * 20, 40)      # 夏普比率 40%
        return_score = min(abs(return_rate) / 5, 20)  # 收益率 20%
        dd_score = max(20 - max_dd * 0.4, 0)      # 回撤控制 20%
        win_score = min(win_rate * 0.25, 20)      # 胜率 20%

        return min(max(sharpe_score + return_score + dd_score + win_score, 0), 100)
    except (ValueError, TypeError):
        return 0.0


# ==================== 通用工具 ====================

def format_strategy_results_display(sorted_results: List,
                                   show_execution_time: bool = False,
                                   show_params: bool = False,
                                   max_display: int = 10) -> str:
    """格式化策略结果显示"""
    display_lines = []

    for i, (strategy, result) in enumerate(sorted_results[:max_display], 1):
        perf = result.get("performance", {}) if isinstance(result, dict) else \
              getattr(result, 'performance', {})

        line_parts = [
            f"{i:2d}.",
            f"{strategy:20s}",
            f"夏普:{perf.get('sharpe_ratio', 0):6.3f}",
            f"收益:{perf.get('total_return', 0):7.2f}%",
            f"胜率:{perf.get('win_rate', 0):5.1f}%"
        ]

        if show_execution_time:
            execution_time = result.get('execution_time', 0) if isinstance(result, dict) else \
                             getattr(result, 'execution_time', 0)
            if execution_time > 0:
                line_parts.append(f"时间:{execution_time:5.1f}s")

        if show_params and isinstance(result, dict) and 'params' in result:
            line_parts.append(f"参数:{result['params']}")

        display_lines.append(" ".join(line_parts))

    return "\n".join(display_lines)


def validate_symbol_list(symbols: List[str]) -> List[str]:
    """验证股票代码列表"""
    if not symbols:
        return []

    valid_symbols = []
    for symbol in symbols:
        symbol = symbol.strip()
        if symbol and (symbol.isdigit() or len(symbol) == 6):
            valid_symbols.append(symbol)

    return valid_symbols


def parse_strategy_list(strategy_str: Optional[str]) -> Optional[List[str]]:
    """解析策略列表字符串"""
    if not strategy_str:
        return None

    strategies = [s.strip() for s in strategy_str.split(",") if s.strip()]
    return strategies if strategies else None


# ==================== 导出接口 ====================

__all__ = [
    # 实例管理
    'get_data_manager',
    'clear_caches',

    # 参数处理
    'parse_param_string',
    'normalize_params',
    'apply_strategy_params',
    'format_params_for_storage',

    # 数据处理
    'load_stock_data_with_validation',
    'extract_date_series',
    'ensure_output_directory',

    # 策略对比和结果处理
    'read_optimized_parameters',
    'generate_total_trades_csv_unified',
    'create_strategy_comparison_csv',
    'save_enhanced_comparison_summary',

    # 性能分析
    'validate_performance_data',
    'format_performance_metrics',
    'calculate_strategy_rating',

    # 通用工具
    'format_strategy_results_display',
    'validate_symbol_list',
    'parse_strategy_list',
]