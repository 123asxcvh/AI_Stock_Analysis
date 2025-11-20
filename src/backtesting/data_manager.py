#!/usr/bin/env python3

"""
统一数据管理模块
整合数据加载、缓存和预处理功能
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import logging
from functools import lru_cache
import pickle
import json
from datetime import datetime, timedelta

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



class DataManager:
    """
    统一数据管理器
    负责数据的加载、缓存、预处理和指标计算
    """

    def __init__(self, cache_dir: str = "./data_cache", max_cache_size: int = 100):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.max_cache_size = max_cache_size
        self._memory_cache = {}
        self._cache_access_count = {}

        # 每次初始化时清理磁盘缓存，确保获取最新数据
        self._clear_disk_cache()

    
    def load_stock_data(self, symbol: str, cleaned: bool = True, required_indicators: List[str] = None) -> pd.DataFrame:
        """
        加载股票数据

        Args:
            symbol: 股票代码
            cleaned: 是否使用清理后的数据
            required_indicators: 策略需要的指标列表，如果为None则计算所有常用指标

        Returns:
            包含技术指标的股票数据
        """
        cache_key = f"{symbol}_cleaned_{cleaned}"

        # 检查内存缓存
        if cache_key in self._memory_cache:
            self._cache_access_count[cache_key] = self._cache_access_count.get(cache_key, 0) + 1
            logger.info(f"从内存缓存加载数据: {symbol}")
            cached_data = self._memory_cache[cache_key].copy()
            # 如果指定了需要的指标，确保这些指标存在
            if required_indicators and 'ALL' not in required_indicators:
                cached_data = self._ensure_indicators(cached_data, required_indicators)
            return cached_data

        # 从项目数据目录加载
        data = self._load_from_project_data(symbol, cleaned)
        if data is None:
            raise FileNotFoundError(f"未找到股票数据: {symbol}")

        # 确保数据按日期排序
        data = self._sort_by_date(data)

        # 计算所有必需的指标
        if required_indicators is not None and 'ALL' not in required_indicators:
            # 如果指定了指标列表（包括空列表），只计算指定的指标
            data = self._add_required_indicators(data, required_indicators)
            # 只有当计算了指标时才保存回文件
            if required_indicators:  # 非空列表才保存
                self._save_indicators_to_file(data, symbol, cleaned)
        else:
            # 如果没有指定指标或指定了ALL，计算所有策略可能用到的指标
            all_indicators = self._get_all_required_indicators()
            data = self._add_required_indicators(data, all_indicators)
            # 将包含技术指标的数据保存回原始文件（如果需要）
            self._save_indicators_to_file(data, symbol, cleaned)

        # 缓存数据
        self._cache_data(cache_key, data)
        logger.info(f"成功加载并缓存数据: {symbol} ({len(data)} 行)")
        return data.copy()

    def _load_from_project_data(self, symbol: str, cleaned: bool) -> Optional[pd.DataFrame]:
        """从项目数据目录加载数据"""
        possible_paths = [
            f"data/cleaned_stocks/{symbol}/historical_quotes.csv",
            f"data/cleaned_stocks/{symbol}/cleaned_data.csv",
            f"data/historical_quotes/{symbol}.csv",
            f"data/processed_stocks/{symbol}/processed_data.csv",
            f"data/cleaned_stocks/{symbol}.csv"
        ]

        for path in possible_paths:
            file_path = Path(path)
            if file_path.exists():
                data = pd.read_csv(file_path)
                if self._validate_data_columns(data):
                    return data
                logger.warning(f"数据格式不正确: {path}")

        return None

    def _sort_by_date(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        确保数据按日期升序排列

        Args:
            data: 股票数据

        Returns:
            按日期排序的数据
        """
        # 确保日期列是datetime类型
        if not pd.api.types.is_datetime64_any_dtype(data['日期']):
            data['日期'] = pd.to_datetime(data['日期'])

        # 按日期升序排列
        data = data.sort_values('日期').reset_index(drop=True)

        logger.info(f"数据已按日期排序，范围: {data['日期'].min()} 到 {data['日期'].max()}")
        return data

    def _get_all_required_indicators(self) -> List[str]:
        """
        收集所有策略可能需要的指标

        Returns:
            所有必需的指标列表
        """
        all_indicators = set()

        # 基础价格指标（与数据流水线完全一致）
        basic_indicators = [
            # 移动平均线
            'MA5', 'MA10', 'MA20', 'MA30', 'MA60', 'MA120',
            # EMA指标（用于MACD）
            'EMA12', 'EMA26',
            # 成交量均线
            'VOLUME_MA5', 'VOLUME_MA10', 'VOLUME_MA20',
            # 核心技术指标
            'RSI',
            # MACD完整指标组
            'MACD_DIF', 'MACD_DEA', 'MACD_HIST',
            # 日线KDJ指标组
            'DAILY_KDJ_K', 'DAILY_KDJ_D', 'DAILY_KDJ_J',
            # 布林带指标组
            'BOLL_UPPER', 'BOLL_MIDDLE', 'BOLL_LOWER',
            # ATR指标
            'ATR',
            # BBI指标（Web界面需要）
            'BBI',
            # 额外补充指标（策略可能用到）
            'CCI',
            'WR',  # 威廉指标
            'MTM',  # 动量指标
            'OBV'   # 能量潮指标
        ]

        all_indicators.update(basic_indicators)

        # 从所有策略中收集必需的指标
        try:
            from .strategies import strategy_registry
            strategies = strategy_registry.list_all()

            for strategy_name in strategies:
                strategy = strategy_registry.get(strategy_name)
                if strategy and hasattr(strategy, 'get_required_indicators'):
                    required = strategy.get_required_indicators()
                    all_indicators.update(required)
        except Exception as e:
            logger.warning(f"收集策略指标时出错: {e}")

        logger.info(f"收集到 {len(all_indicators)} 个必需指标")
        return list(all_indicators)

    def _validate_data_columns(self, data: pd.DataFrame) -> bool:
        """验证数据列是否完整"""
        # 检查中文列名
        required_columns = ["日期", "开盘", "最高", "最低", "收盘", "成交量"]
        return all(col in data.columns for col in required_columns)

    def _add_required_indicators(self, data: pd.DataFrame, required_indicators: List[str]) -> pd.DataFrame:
        """
        添加所有必需的技术指标（检查是否已存在，只计算缺失的指标）

        Args:
            data: 原始数据
            required_indicators: 需要的指标列表，例如: ["MA5", "MA20", "RSI", "MACD_DIF"]

        Returns:
            包含所需指标的数据
        """
        from .indicators import indicator_calculator

        data = data.copy()

        if not required_indicators:
            return data

        # 检查哪些指标已经存在
        existing_indicators = set(data.columns)
        missing_indicators = [ind for ind in required_indicators if ind not in existing_indicators]

        if not missing_indicators:
            logger.info(f"所有技术指标都已存在，无需重新计算")
            return data

        logger.info(f"需要计算 {len(missing_indicators)} 个缺失的技术指标: {missing_indicators}")

        # 计算MACD相关指标
        if any(ind.startswith("MACD_") for ind in missing_indicators):
            macd_data = indicator_calculator.calculate_macd(data["收盘"])
            for key, values in macd_data.items():
                if key in missing_indicators:
                    data[key] = values

        # 计算KDJ相关指标
        if any(ind.startswith("DAILY_KDJ_") for ind in missing_indicators):
            kdj_data = indicator_calculator.calculate_kdj(data["最高"], data["最低"], data["收盘"])
            for key, values in kdj_data.items():
                # KDJ计算器已经返回了DAILY_开头的键名，直接使用
                if key in missing_indicators:
                    data[key] = values

        # 计算RSI指标
        if "RSI" in missing_indicators:
            data["RSI"] = indicator_calculator.calculate_rsi(data["收盘"])

        # 计算布林带指标
        if any(ind.startswith("BOLL_") for ind in missing_indicators):
            boll_data = indicator_calculator.calculate_bollinger_bands(data["收盘"])
            for key, values in boll_data.items():
                if key in missing_indicators:
                    data[key] = values

        # 计算ATR指标
        if "ATR" in missing_indicators:
            data["ATR"] = indicator_calculator.calculate_atr(data["最高"], data["最低"], data["收盘"])

        # 计算CCI指标
        if "CCI" in missing_indicators:
            data["CCI"] = indicator_calculator.calculate_cci(data["最高"], data["最低"], data["收盘"])

        # 计算移动平均线（MA）
        ma_indicators = [ind for ind in missing_indicators if ind.startswith("MA") and ind[2:].isdigit()]
        if ma_indicators:
            # 合并相同周期的MA，避免重复计算
            periods = set()
            for ma_ind in ma_indicators:
                period = int(ma_ind[2:])
                periods.add(period)

            for period in sorted(periods):
                ma_values = indicator_calculator.calculate_sma(data["收盘"], period)
                ma_col = f"MA{period}"
                if ma_col in missing_indicators:
                    data[ma_col] = ma_values

        # 计算EMA
        ema_indicators = [ind for ind in missing_indicators if ind.startswith("EMA") and ind[3:].isdigit()]
        if ema_indicators:
            # 合并相同周期的EMA，避免重复计算
            periods = set()
            for ema_ind in ema_indicators:
                period = int(ema_ind[3:])
                periods.add(period)

            for period in sorted(periods):
                ema_values = indicator_calculator.calculate_ema(data["收盘"], period)
                ema_col = f"EMA{period}"
                if ema_col in missing_indicators:
                    data[ema_col] = ema_values

        # 计算成交量均线
        vol_indicators = [ind for ind in missing_indicators if ind.startswith("VOLUME_MA")]
        if vol_indicators:
            # 合并相同周期的成交量均线，避免重复计算
            periods = set()
            for vol_ind in vol_indicators:
                period = int(vol_ind.split("_")[-1].replace("MA", ""))
                periods.add(period)

            for period in sorted(periods):
                vol_ma_values = indicator_calculator.calculate_sma(data["成交量"], period)
                vol_ma_col = f"VOLUME_MA{period}"
                if vol_ma_col in missing_indicators:
                    data[vol_ma_col] = vol_ma_values

        # 计算BBI指标
        if "BBI" in missing_indicators:
            data["BBI"] = indicator_calculator.calculate_bbi(data["收盘"])

        
        # 计算威廉指标
        if "WR" in missing_indicators:
            data["WR"] = indicator_calculator.calculate_williams_r(data["最高"], data["最低"], data["收盘"])

        # 计算动量指标
        if "MTM" in missing_indicators:
            data["MTM"] = indicator_calculator.calculate_mtm(data["收盘"])

        # 计算能量潮指标
        if "OBV" in missing_indicators:
            data["OBV"] = indicator_calculator.calculate_obv(data["收盘"], data["成交量"])

        logger.info(f"指标计算完成，总列数: {len(data.columns)}")
        return data
    
    def _ensure_indicators(self, data: pd.DataFrame, required_indicators: List[str]) -> pd.DataFrame:
        """确保数据中包含所需的指标，如果缺失则计算"""
        missing = [ind for ind in required_indicators if ind not in data.columns]
        if missing:
            return self._add_required_indicators(data, missing)
        return data

    def _cache_data(self, cache_key: str, data: pd.DataFrame):
        """缓存数据到内存和磁盘"""
        # 内存缓存
        self._memory_cache[cache_key] = data.copy()
        self._cache_access_count[cache_key] = 1

        # 磁盘缓存
        try:
            cache_file = self.cache_dir / f"{cache_key}.pkl"
            with open(cache_file, 'wb') as f:
                pickle.dump(data, f)
        except Exception as e:
            logger.warning(f"磁盘缓存失败: {e}")

        # 清理缓存
        self._cleanup_cache()

    def _cleanup_cache(self):
        """清理过多的缓存"""
        if len(self._memory_cache) > self.max_cache_size:
            # 按访问次数排序，删除最少使用的
            sorted_items = sorted(
                self._cache_access_count.items(),
                key=lambda x: x[1]
            )

            for cache_key, _ in sorted_items[:len(self._memory_cache) - self.max_cache_size]:
                if cache_key in self._memory_cache:
                    del self._memory_cache[cache_key]
                if cache_key in self._cache_access_count:
                    del self._cache_access_count[cache_key]

    def _clear_disk_cache(self):
        """清空磁盘缓存"""
        try:
            for cache_file in self.cache_dir.glob("*.pkl"):
                cache_file.unlink()
            logger.info("磁盘缓存已清空")
        except Exception as e:
            logger.warning(f"清空磁盘缓存失败: {e}")

    def clear_cache(self):
        """清空所有缓存"""
        self._memory_cache.clear()
        self._cache_access_count.clear()

        # 清空磁盘缓存
        self._clear_disk_cache()

    def get_cache_info(self) -> Dict[str, Any]:
        """获取缓存信息"""
        return {
            "memory_cache_size": len(self._memory_cache),
            "disk_cache_files": len(list(self.cache_dir.glob("*.pkl"))),
            "cache_dir": str(self.cache_dir),
            "max_cache_size": self.max_cache_size
        }

    def list_available_symbols(self) -> List[str]:
        """列出所有可用的股票代码"""
        symbols = []

        # 搜索多个可能的数据目录
        search_dirs = [
            Path("data/cleaned_stocks"),
            Path("data/historical_quotes"),
            Path("data/processed_stocks")
        ]

        for search_dir in search_dirs:
            if search_dir.exists():
                # 首先检查子目录（每个股票代码一个目录）
                for subdir in search_dir.iterdir():
                    if subdir.is_dir() and subdir.name.isdigit() and len(subdir.name) == 6:
                        # 这是股票代码目录
                        if subdir.name not in symbols:
                            symbols.append(subdir.name)

                # 然后检查直接的CSV文件（兼容旧格式）
                for file_path in search_dir.glob("*.csv"):
                    symbol = file_path.stem
                    # 只添加看起来像股票代码的文件名（6位数字）
                    if symbol.isdigit() and len(symbol) == 6 and symbol not in symbols:
                        symbols.append(symbol)

        return sorted(symbols)

  
    def get_stock_info(self, symbol: str) -> Dict[str, Any]:
        """获取股票基本信息"""
        try:
            data = self.load_stock_data(symbol, required_indicators=[])

            if data.empty:
                return {}

            return {
                "symbol": symbol,
                "data_points": len(data),
                "date_range": {
                    "start": data["日期"].min().strftime("%Y-%m-%d"),
                    "end": data["日期"].max().strftime("%Y-%m-%d")
                },
                "price_info": {
                    "current": float(data["收盘"].iloc[-1]),
                    "min": float(data["收盘"].min()),
                    "max": float(data["收盘"].max()),
                    "avg": float(data["收盘"].mean())
                },
                "volume_info": {
                    "current": int(data["成交量"].iloc[-1]),
                    "avg": int(data["成交量"].mean()),
                    "total": int(data["成交量"].sum())
                }
            }
        except Exception as e:
            logger.error(f"获取股票信息失败 {symbol}: {e}")
            return {}

    def save_data_summary(self, output_path: str = "data_summary.json"):
        """保存数据摘要"""
        symbols = self.list_available_symbols()
        summary = {
            "total_symbols": len(symbols),
            "symbols_info": {},
            "cache_info": self.get_cache_info(),
            "generated_at": datetime.now().isoformat()
        }

        for symbol in symbols[:20]:  # 限制前20只股票
            summary["symbols_info"][symbol] = self.get_stock_info(symbol)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        logger.info(f"数据摘要已保存到: {output_path}")

    def _save_indicators_to_file(self, data: pd.DataFrame, symbol: str, cleaned: bool):
        """将包含技术指标的数据保存回原始CSV文件，避免覆盖有效数据"""
        try:
            # 确定要保存的文件路径
            file_path = Path(f"data/cleaned_stocks/{symbol}/historical_quotes.csv")

            if not file_path.exists():
                logger.warning(f"原始数据文件不存在: {file_path}")
                return

            # 读取现有文件，检查是否已存在有效的指标数据
            existing_data = pd.read_csv(file_path)

            # 合并数据：优先保留现有数据中有效的指标值
            merged_data = data.copy()

            for column in existing_data.columns:
                if column not in merged_data.columns:
                    # 如果现有数据有新列，添加进来
                    merged_data[column] = existing_data[column]
                elif column not in ["日期", "开盘", "收盘", "最高", "最低", "成交量"]:
                    # 对于指标列，检查现有数据是否有更多有效值
                    existing_valid = existing_data[column].notna().sum()
                    new_valid = merged_data[column].notna().sum()

                    if existing_valid > new_valid:
                        # 现有数据的有效值更多，保留现有数据
                        merged_data[column] = existing_data[column]
                    elif existing_valid > 0 and new_valid > 0:
                        # 两边都有有效值，逐行选择非空值
                        for idx in range(len(merged_data)):
                            if pd.isna(merged_data.iloc[idx][column]) and not pd.isna(existing_data.iloc[idx][column]):
                                merged_data.iloc[idx, merged_data.columns.get_loc(column)] = existing_data.iloc[idx][column]

            # 对数据进行倒序排列（最新的数据在前面，便于查看）
            if '日期' in merged_data.columns:
                merged_data['日期'] = pd.to_datetime(merged_data['日期'], errors='coerce')
                merged_data = merged_data.sort_values('日期', ascending=False)

            # 保存合并后的数据
            merged_data.to_csv(file_path, index=False, encoding='utf-8')

            # 统计指标列数量
            basic_columns = {"日期", "开盘", "收盘", "最高", "最低", "成交量"}
            indicator_columns = [col for col in merged_data.columns if col not in basic_columns]
            logger.info(f"技术指标已保存到原始文件: {file_path} (共 {len(indicator_columns)} 个技术指标)")

        except Exception as e:
            logger.error(f"保存技术指标到文件失败: {e}")


# 全局数据管理器实例
data_manager = DataManager()