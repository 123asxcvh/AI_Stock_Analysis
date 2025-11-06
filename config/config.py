#!/usr/bin/env python3
"""
统一配置文件 - 所有配置集中管理
使用Python原生格式，避免冗余
"""

from dataclasses import dataclass
from typing import List, Optional
from pathlib import Path
from datetime import datetime
import asyncio
import threading


# Gemini API Keys - 用于轮换
GEMINI_API_KEYS = [
    "AIzaSyCE_ElNSSTIQBpJzF6jlCQwjYcTryW6spI",
    "AIzaSyAShBvPYhIkp8-BUGEWeCoYUyRY2HkMMhA",
    "AIzaSyDN30ActMa4_4qR26zHaJbuH0stcvxSR8E",
    "AIzaSyDjenCVJ-dG44KnLNFp9RxB6NNDAdLvJw0",
    "AIzaSyAy2X5QX67wCkp0bIEI3i0hAvssskczVBA"
]

# API Key 轮换管理器
class APIKeyRotator:
    """API Key 轮换管理器 - 确保每次使用不同的 key"""
    
    def __init__(self, api_keys: List[str]):
        self.api_keys = api_keys
        self.current_index = 0
        self.lock = threading.Lock()
    
    def get_next_key(self) -> str:
        """获取下一个 API key（轮换使用）"""
        with self.lock:
            key = self.api_keys[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.api_keys)
            return key

# 创建全局轮换器
_api_key_rotator = APIKeyRotator(GEMINI_API_KEYS)


@dataclass
class Config:
    """统一配置类"""

    # Web配置
    web_host: str = "0.0.0.0"
    web_port: int = 8501
    web_debug: bool = False
    web_theme: str = "light"
    web_wide_mode: bool = True
    web_enable_caching: bool = True

    # 系统配置
    app_name: str = "A股分析系统"
    app_version: str = "2.0.0"
    target_stocks: List[str] = None
    request_delay: float = 2.0
    historical_start_date: str = "20210101"
    enable_parallel: bool = True
    max_workers: int = 3  # Mac系统推荐并发数为3，避免API限流

    # API配置
    api_key: str = ""  # 不再使用单一 key，通过轮换器获取
    api_base_url: str = "https://123asxcvh-gemini-94.deno.dev/v1"
    api_timeout: int = 90
    api_max_retries: int = 5  # 增加重试次数以支持 key 轮换

    # AI模型配置
    model_name: str = "gemini-2.5-flash"
    model_temperature: float = 0.2
    model_max_tokens: int = None

    # 回测配置
    initial_capital: float = 100000.0
    commission_rate: float = 0.0003
    slippage_rate: float = 0.001
    benchmark: str = "000300.SH"

    # 技术指标配置
    kdj_fastk_period: int = 9
    kdj_slowk_period: int = 3
    kdj_slowd_period: int = 3
    macd_fast_period: int = 12
    macd_slow_period: int = 26
    macd_signal_period: int = 9
    bbi_periods: List[int] = None
    boll_period: int = 20
    boll_nbdev: int = 2
    rsi_period: int = 14
    volume_ma_period: int = 20

    def __post_init__(self):
        """初始化后处理"""
        if self.target_stocks is None:
            self.target_stocks = ["000001", "000002", "000858", "002415", "600036", "600519"]
        if self.bbi_periods is None:
            self.bbi_periods = [3, 6, 12, 24]

    # 路径管理
    @property
    def project_root(self) -> Path:
        """项目根目录"""
        return Path(__file__).parent.parent

    @property
    def data_dir(self) -> Path:
        """数据目录"""
        return self.project_root / "data"

    @property
    def stocks_dir(self) -> Path:
        """股票数据目录"""
        return self.data_dir / "stocks"

    @property
    def cleaned_stocks_dir(self) -> Path:
        """清洗后股票数据目录"""
        return self.data_dir / "cleaned_stocks"

    @property
    def ai_reports_dir(self) -> Path:
        """AI报告目录"""
        return self.data_dir / "ai_reports"

    @property
    def cache_dir(self) -> Path:
        """缓存目录"""
        return self.data_dir / "cache"

    @property
    def market_data_dir(self) -> Path:
        """市场数据目录"""
        return self.data_dir / "market_data"

    def get_stock_dir(self, stock_code: str, cleaned: bool = False) -> Path:
        """获取股票目录"""
        base_dir = self.cleaned_stocks_dir if cleaned else self.stocks_dir
        return base_dir / stock_code

    def get_stock_quotes_csv(self, stock_code: str, cleaned: bool = False) -> Path:
        """获取股票行情CSV路径"""
        return self.get_stock_dir(stock_code, cleaned) / "historical_quotes.csv"

    def get_stock_file_path(self, stock_code: str, filename: str, cleaned: bool = False) -> Path:
        """获取股票数据文件路径"""
        return self.get_stock_dir(stock_code, cleaned) / filename

    def ensure_dir(self, path: Path) -> Path:
        """确保目录存在"""
        path.mkdir(parents=True, exist_ok=True)
        return path

    def get_stocks_dir(self, cleaned: bool = False) -> Path:
        """获取股票数据目录"""
        return self.cleaned_stocks_dir if cleaned else self.stocks_dir

    def get_ai_reports_dir(self) -> Path:
        """获取AI报告目录"""
        return self.ai_reports_dir

    def get_market_data_dir(self, cleaned: bool = False) -> Path:
        """获取市场数据目录"""
        if cleaned:
            return self.data_dir / "cleaned_market_data"
        return self.market_data_dir

    def get_index_stocks_dir(self) -> Path:
        """获取指数股票目录"""
        return self.data_dir / "index_stocks"

    def get_concept_stocks_dir(self) -> Path:
        """获取概念股票目录"""
        return self.data_dir / "concept_stocks"

    def get_industry_stocks_dir(self) -> Path:
        """获取行业股票目录"""
        return self.data_dir / "industry_stocks"

    def get_config_file_path(self, config_name: str = None) -> Path:
        """获取配置文件路径（向后兼容方法）"""
        return self.project_root / "config" / f"{config_name or 'config'}.py"

    # 回测结果路径管理
    def get_strategy_results_dir(self, stock_code: str, strategy_type: str, strategy_name: str) -> Path:
        """获取策略回测结果目录
        
        Args:
            stock_code: 股票代码
            strategy_type: 策略类型 (Single/Double/Triple)
            strategy_name: 策略名称
            
        Returns:
            策略结果目录路径
        """
        base_dir = self.get_stock_dir(stock_code, cleaned=True) / "results" / strategy_type / strategy_name
        return self.ensure_dir(base_dir)

    def get_strategy_type_dir(self, stock_code: str, strategy_type: str) -> Path:
        """获取策略类型目录
        
        Args:
            stock_code: 股票代码
            strategy_type: 策略类型 (Single/Double/Triple)
            
        Returns:
            策略类型目录路径
        """
        base_dir = self.get_stock_dir(stock_code, cleaned=True) / "results" / strategy_type
        return self.ensure_dir(base_dir)

    def get_stock_strategy_summary_path(self, stock_code: str) -> Path:
        """获取股票策略汇总文件路径
        
        Args:
            stock_code: 股票代码
            
        Returns:
            汇总文件路径
        """
        results_dir = self.get_stock_dir(stock_code, cleaned=True) / "results"
        self.ensure_dir(results_dir)
        return results_dir / "strategy_summary.csv"

    # AI分析配置
    @property
    def supported_stock_analysis_types(self) -> List[str]:
        """支持的个人股票分析类型"""
        return [
            "company_profile",
            "balance_sheet_analysis",      # 资产负债表分析
            "income_statement_analysis",    # 利润表分析
            "cash_flow_analysis",          # 现金流量表分析
            "financial_indicators_analysis", # 财务指标分析
            "technical_analysis",
            "intraday_trading",
            "news_data"
        ]

    @property
    def supported_market_analysis_types(self) -> List[str]:
        """支持的市场分析类型"""
        return [
            "fund_flow_concept",
            "fund_flow_industry",
            "sector_fund_flow",
            "fund_flow_individual",
            "zt_pool"
        ]

    @property
    def analysis_file_mapping(self) -> dict:
        """分析类型与数据文件的映射"""
        return {
            "company_profile": ["company_profile.csv", "main_business_composition.csv"],
            "balance_sheet_analysis": ["balance_sheet.csv"],      # 资产负债表分析
            "income_statement_analysis": ["income_statement.csv"],    # 利润表分析
            "cash_flow_analysis": ["cash_flow_statement.csv"],          # 现金流量表分析
            "financial_indicators_analysis": ["financial_indicators.csv"], # 财务指标分析
            "technical_analysis": ["historical_quotes.csv"],
            "intraday_trading": ["intraday_data.csv"],
            "news_data": ["news_data.csv"]
        }

    @property
    def market_analysis_file_mapping(self) -> dict:
        """市场分析类型与数据文件的映射"""
        return {
            "fund_flow_concept": ["fund_flow_concept.csv"],
            "fund_flow_industry": ["fund_flow_industry.csv"],
            "sector_fund_flow": ["sector_fund_flow.csv"],
            "fund_flow_individual": ["fund_flow_individual.csv"],
            "zt_pool": ["zt_pool.csv"]
        }


# 全局配置实例
config = Config()


# 便捷访问函数
def get_web_port() -> int:
    return config.web_port

def get_api_key() -> str:
    """获取下一个轮换的 API key"""
    return _api_key_rotator.get_next_key()

def get_target_stocks() -> List[str]:
    return config.target_stocks

def get_project_root() -> Path:
    return config.project_root

def get_data_dir() -> Path:
    return config.data_dir


# 策略配置（简化版）
class StrategyConfigs:
    """策略配置"""

    # KDJ策略
    kdj_j_buy_threshold = 0
    kdj_j_sell_threshold = 100
    kdj_signal_cooldown_days = 3

    # 周线KDJ策略
    weekly_kdj_j_buy_threshold = 10
    weekly_kdj_signal_cooldown_days = 5

    # RSI策略
    rsi_oversold = 30
    rsi_overbought = 70
    rsi_signal_cooldown_days = 3

    # MACD策略
    macd_signal_cooldown_days = 3

    # BBI策略
    bbi_signal_cooldown_days = 3

    # BOLL策略
    boll_signal_cooldown_days = 3

    # 成交量突破策略
    volume_multiplier = 2.0
    volume_signal_cooldown_days = 3

    # 混合策略
    hybrid_observation_timeout_days = 5
    hybrid_signal_cooldown_days = 5

    # 三指标策略
    triple_observation_timeout_days = 5
    triple_validation_timeout_days = 3
    triple_signal_cooldown_days = 5

    @classmethod
    def get_strategy_config(cls, strategy_name: str) -> dict:
        """获取策略配置"""
        # 基础配置模板
        base_daily_kdj = {
            "j_buy_threshold": cls.kdj_j_buy_threshold,
            "j_sell_threshold": cls.kdj_j_sell_threshold,
            "signal_cooldown_days": cls.kdj_signal_cooldown_days
        }
        base_weekly_kdj = {
            "j_buy_threshold": cls.weekly_kdj_j_buy_threshold,
            "j_sell_threshold": cls.kdj_j_sell_threshold,
            "signal_cooldown_days": cls.weekly_kdj_signal_cooldown_days
        }
        
        configs = {
            "Base_DailyKDJ": base_daily_kdj,
            "Base_WeeklyKDJ": base_weekly_kdj,
            "Base_RSI": {
                "rsi_oversold": cls.rsi_oversold,
                "rsi_overbought": cls.rsi_overbought,
                "signal_cooldown_days": cls.rsi_signal_cooldown_days
            },
            "Base_MACD": {
                "signal_cooldown_days": cls.macd_signal_cooldown_days
            },
            "Base_BBI": {
                "signal_cooldown_days": cls.bbi_signal_cooldown_days
            },
            "Base_BOLL": {
                "signal_cooldown_days": cls.boll_signal_cooldown_days
            },
            "Base_VolumeBreakout": {
                "volume_multiplier": cls.volume_multiplier,
                "signal_cooldown_days": cls.volume_signal_cooldown_days
            },
            # Hybrid 策略配置 (Double指标策略)
            "Hybrid_DailyKDJ_BBI": {
                **base_daily_kdj,
                "observation_timeout_days": cls.hybrid_observation_timeout_days,
                "signal_cooldown_days": cls.hybrid_signal_cooldown_days
            },
            "Hybrid_DailyKDJ_BOLL": {
                **base_daily_kdj,
                "observation_timeout_days": cls.hybrid_observation_timeout_days,
                "signal_cooldown_days": cls.hybrid_signal_cooldown_days
            },
            "Hybrid_DailyKDJ_MACD": {
                **base_daily_kdj,
                "observation_timeout_days": cls.hybrid_observation_timeout_days,
                "signal_cooldown_days": cls.hybrid_signal_cooldown_days
            },
            "Hybrid_DailyKDJ_RSI": {
                **base_daily_kdj,
                "rsi_oversold": cls.rsi_oversold,
                "rsi_overbought": cls.rsi_overbought,
                "observation_timeout_days": cls.hybrid_observation_timeout_days,
                "signal_cooldown_days": cls.hybrid_signal_cooldown_days
            },
            "Hybrid_DailyKDJ_Volume": {
                **base_daily_kdj,
                "volume_multiplier": cls.volume_multiplier,
                "observation_timeout_days": cls.hybrid_observation_timeout_days,
                "signal_cooldown_days": cls.hybrid_signal_cooldown_days
            },
            "Hybrid_WeeklyKDJ_BBI": {
                **base_weekly_kdj,
                "observation_timeout_days": cls.hybrid_observation_timeout_days,
                "signal_cooldown_days": cls.hybrid_signal_cooldown_days
            },
            "Hybrid_WeeklyKDJ_BOLL": {
                **base_weekly_kdj,
                "observation_timeout_days": cls.hybrid_observation_timeout_days,
                "signal_cooldown_days": cls.hybrid_signal_cooldown_days
            },
            "Hybrid_WeeklyKDJ_MACD": {
                **base_weekly_kdj,
                "observation_timeout_days": cls.hybrid_observation_timeout_days,
                "signal_cooldown_days": cls.hybrid_signal_cooldown_days
            },
            "Hybrid_WeeklyKDJ_RSI": {
                **base_weekly_kdj,
                "rsi_oversold": cls.rsi_oversold,
                "rsi_overbought": cls.rsi_overbought,
                "observation_timeout_days": cls.hybrid_observation_timeout_days,
                "signal_cooldown_days": cls.hybrid_signal_cooldown_days
            },
            "Hybrid_WeeklyKDJ_Volume": {
                **base_weekly_kdj,
                "volume_multiplier": cls.volume_multiplier,
                "observation_timeout_days": cls.hybrid_observation_timeout_days,
                "signal_cooldown_days": cls.hybrid_signal_cooldown_days
            },
            # Triple 策略配置 (三指标策略)
            "Triple_DailyKDJ_BOLL_RSI": {
                **base_daily_kdj,
                "rsi_oversold": cls.rsi_oversold,
                "rsi_overbought": cls.rsi_overbought,
                "observation_timeout_days": cls.triple_observation_timeout_days,
                "validation_timeout_days": cls.triple_validation_timeout_days,
                "signal_cooldown_days": cls.triple_signal_cooldown_days
            },
            "Triple_DailyKDJ_BOLL_MACD": {
                **base_daily_kdj,
                "observation_timeout_days": cls.triple_observation_timeout_days,
                "validation_timeout_days": cls.triple_validation_timeout_days,
                "signal_cooldown_days": cls.triple_signal_cooldown_days
            },
            "Triple_DailyKDJ_BBI_RSI": {
                **base_daily_kdj,
                "rsi_oversold": cls.rsi_oversold,
                "rsi_overbought": cls.rsi_overbought,
                "observation_timeout_days": cls.triple_observation_timeout_days,
                "validation_timeout_days": cls.triple_validation_timeout_days,
                "signal_cooldown_days": cls.triple_signal_cooldown_days
            },
            "Triple_DailyKDJ_BBI_MACD": {
                **base_daily_kdj,
                "observation_timeout_days": cls.triple_observation_timeout_days,
                "validation_timeout_days": cls.triple_validation_timeout_days,
                "signal_cooldown_days": cls.triple_signal_cooldown_days
            },
            "Triple_WeeklyKDJ_BOLL_RSI": {
                **base_weekly_kdj,
                "rsi_oversold": cls.rsi_oversold,
                "rsi_overbought": cls.rsi_overbought,
                "observation_timeout_days": cls.triple_observation_timeout_days,
                "validation_timeout_days": cls.triple_validation_timeout_days,
                "signal_cooldown_days": cls.triple_signal_cooldown_days
            },
            "Triple_WeeklyKDJ_BOLL_MACD": {
                **base_weekly_kdj,
                "observation_timeout_days": cls.triple_observation_timeout_days,
                "validation_timeout_days": cls.triple_validation_timeout_days,
                "signal_cooldown_days": cls.triple_signal_cooldown_days
            }
        }
        return configs.get(strategy_name, {})


# 策略配置实例
strategy_configs = StrategyConfigs()




# 缓存管理器
class CacheManager:
    """缓存管理器，用于管理股票分析的缓存"""

    def __init__(self, cache_dir: Path = None, cache_days: int = 7):
        """初始化缓存管理器"""
        if cache_dir is None:
            cache_dir = config.cache_dir
        self.cache_dir = cache_dir
        self.cache_days = cache_days
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._cleanup_expired_cache()

    def _generate_cache_key(self, symbol: str, filename: str, system_role: str) -> str:
        """生成缓存键"""
        import hashlib
        content = f"{symbol}_{filename}_{system_role}"
        return hashlib.md5(content.encode()).hexdigest()

    def _get_cache_file_path(self, symbol: str, cache_key: str) -> Path:
        """获取缓存文件路径，按股票代码分目录"""
        symbol_cache_dir = self.cache_dir / symbol
        symbol_cache_dir.mkdir(exist_ok=True)
        return symbol_cache_dir / f"{cache_key}.json"

    def _is_cache_valid(self, cache_file_path: Path) -> bool:
        """检查缓存是否有效"""
        if not cache_file_path.exists():
            return False

        file_mtime = datetime.fromtimestamp(cache_file_path.stat().st_mtime)
        cache_age = datetime.now() - file_mtime
        return cache_age.days < self.cache_days

    def _cleanup_expired_cache(self):
        """清理过期的缓存文件"""
        current_time = datetime.now()

        for symbol_dir in self.cache_dir.iterdir():
            if not symbol_dir.is_dir():
                continue

            for cache_file in symbol_dir.glob("*.json"):
                file_mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
                if (current_time - file_mtime).days >= self.cache_days:
                    cache_file.unlink()

    async def load_from_cache(self, symbol: str, filename: str, system_role: str):
        """从缓存加载数据（异步版本）"""
        import json
        import aiofiles
        
        cache_key = self._generate_cache_key(symbol, filename, system_role)
        cache_file_path = self._get_cache_file_path(symbol, cache_key)

        if not self._is_cache_valid(cache_file_path):
            return None

        try:
            async with aiofiles.open(cache_file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
                cached_data = json.loads(content)
                return cached_data.get("data", cached_data)
        except Exception as e:
            print(f"⚠️ 读取缓存失败 {cache_file_path}: {e}")
            return None

    async def save_to_cache(self, symbol: str, filename: str, system_role: str, data) -> bool:
        """保存数据到缓存（异步版本）"""
        import json
        import aiofiles
        
        cache_key = self._generate_cache_key(symbol, filename, system_role)
        cache_file_path = self._get_cache_file_path(symbol, cache_key)

        cache_data = {
            "symbol": symbol,
            "filename": filename,
            "system_role": system_role,
            "cached_at": datetime.now().isoformat(),
            "data": data
        }

        try:
            async with aiofiles.open(cache_file_path, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(cache_data, ensure_ascii=False, indent=2))
            return True
        except Exception as e:
            print(f"⚠️ 保存缓存失败 {cache_file_path}: {e}")
            return False

    def clear_cache(self, symbol: str = None):
        """清除缓存"""
        import shutil

        if symbol:
            symbol_cache_dir = self.cache_dir / symbol
            if symbol_cache_dir.exists():
                shutil.rmtree(symbol_cache_dir)
        else:
            shutil.rmtree(self.cache_dir)
            self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get_cache_stats(self):
        """获取缓存统计信息"""
        total_files = 0
        total_size = 0
        symbol_stats = {}

        for symbol_dir in self.cache_dir.iterdir():
            if not symbol_dir.is_dir():
                continue

            symbol_files = list(symbol_dir.glob("*.json"))
            symbol_size = sum(f.stat().st_size for f in symbol_files)

            symbol_stats[symbol_dir.name] = {
                "files_count": len(symbol_files),
                "size_bytes": symbol_size,
                "size_mb": round(symbol_size / (1024 * 1024), 2)
            }

            total_files += len(symbol_files)
            total_size += symbol_size

        return {
            "total_files": total_files,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "symbols_count": len(symbol_stats),
            "symbol_stats": symbol_stats
        }


# AI分析器基类
class AsyncAIAnalyzerBase:
    """异步AI分析器基类"""

    def __init__(self, model_name: str = None):
        self.model_name = model_name or config.model_name
        # 不再使用单一 api_key，通过轮换器在每次调用时获取
        self.api_key = None  # 保留此字段用于兼容性，但实际使用轮换器
        self.base_url = config.api_base_url
        self.timeout = config.api_timeout
        self.prompt_manager = None

    async def __aenter__(self):
        """异步上下文管理器入口"""
        from src.ai_analysis.prompts.prompt_manager import PromptManager
        self.prompt_manager = PromptManager()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        # 如果需要清理资源，在这里添加
        return False

    async def _call_ai_api_with_retry(self, messages):
        """调用AI API（带 API key 轮换的重试机制）"""
        import httpx
        import json

        request_body = {
            "model": self.model_name,
            "messages": messages,
            "temperature": config.model_temperature
        }

        max_retries = config.api_max_retries
        
        for attempt in range(max_retries):
            # 获取下一个 API key（轮换使用）
            current_api_key = _api_key_rotator.get_next_key()
            
            headers = {
                "Authorization": f"Bearer {current_api_key}",
                "Content-Type": "application/json"
            }

            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        f"{self.base_url}/chat/completions",
                        json=request_body,
                        headers=headers
                    )

                    if response.status_code == 200:
                        result = response.json()
                        if "choices" in result and len(result["choices"]) > 0:
                            return result["choices"][0]["message"]["content"]
                        else:
                            # 响应格式异常，换下一个 key 重试
                            if attempt < max_retries - 1:
                                await asyncio.sleep(1)
                                continue
                            return None
                    elif response.status_code == 401:
                        # 认证失败，换下一个 key 重试
                        if attempt < max_retries - 1:
                            await asyncio.sleep(1)
                            continue
                        return None
                    elif response.status_code == 429:
                        # 频率限制，换下一个 key 重试
                        if attempt < max_retries - 1:
                            await asyncio.sleep(3)
                            continue
                        return None
                    elif response.status_code >= 500:
                        # 服务器错误，换下一个 key 重试
                        if attempt < max_retries - 1:
                            await asyncio.sleep(2)
                            continue
                        return None
                    else:
                        # 其他错误，换下一个 key 重试
                        if attempt < max_retries - 1:
                            await asyncio.sleep(1)
                            continue
                        return None

            except (httpx.TimeoutException, httpx.ConnectError) as e:
                # 网络错误，换下一个 key 重试
                if attempt < max_retries - 1:
                    await asyncio.sleep(2)
                    continue
            except Exception as e:
                # 其他错误，换下一个 key 重试
                if attempt < max_retries - 1:
                    await asyncio.sleep(1)
                    continue

        return None

    async def test_api_connection(self):
        """测试API连接是否正常"""
        test_messages = [
            {"role": "user", "content": "测试连接，请回复'连接成功'"}
        ]

        print("🔍 测试API连接...")
        result = await self._call_ai_api_with_retry(test_messages)

        if result:
            print("✅ API连接测试成功")
            return True
        else:
            print("❌ API连接测试失败")
            return False


# 数据处理器
class DataProcessor:
    """数据处理器（通用版）"""

    @staticmethod
    async def read_csv_file_async(file_path: str):
        """异步读取CSV文件"""
        import aiofiles
        from io import StringIO
        import pandas as pd

        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
                return pd.read_csv(StringIO(content))
        except Exception as e:
            print(f"读取文件失败 {file_path}: {e}")
            return None

    @staticmethod
    async def filter_data_by_time(df, filename: str):
        """按时间过滤数据（简化版）"""
        return df

    @staticmethod
    def filter_industry_comparison_columns(df, filename: str):
        """过滤行业对比数据列（简化版）"""
        return df

    @staticmethod
    def filter_market_data_columns(df, filename: str):
        """过滤市场数据列（简化版）"""
        return df

    @staticmethod
    async def load_company_context(stock_code: str, data_dir: str, cache: dict):
        """加载公司上下文信息"""
        try:
            # 检查缓存
            cache_key = f"company_context_{stock_code}"
            if cache_key in cache:
                return cache[cache_key]

            # 尝试从公司概况文件加载
            import aiofiles
            import pandas as pd
            from pathlib import Path
            from io import StringIO

            company_info_file = Path(data_dir) / stock_code / "company_profile.csv"
            if company_info_file.exists():
                async with aiofiles.open(company_info_file, 'r', encoding='utf-8') as f:
                    content = await f.read()
                    # 读取CSV数据
                    df = pd.read_csv(StringIO(content))

                    # 提取关键公司信息
                    company_info = {}
                    if not df.empty and '字段名' in df.columns and '字段值' in df.columns:
                        # 处理键值对格式
                        company_info = dict(zip(df['字段名'], df['字段值']))
      
                    company_context = f"""
公司名称：{company_info.get('公司名称', stock_code)}
股票代码：{stock_code}
所属行业：{company_info.get('所属行业', '未知')}
主营业务：{company_info.get('主营业务', '未知')}
公司简介：{company_info.get('机构简介', '暂无公司详细信息')}

重要提醒：上述公司信息来源于提供的company_profile.csv文件，请务必在分析报告中使用这些信息，不要显示为"未知"。
"""
                    cache[cache_key] = company_context
                    return company_context

            # 如果没有文件，返回基本信息
            fallback_context = f"""
公司名称：{stock_code}
股票代码：{stock_code}
所属行业：未知
主营业务：未知
公司简介：暂无公司详细信息
"""
            cache[cache_key] = fallback_context
            return fallback_context

        except Exception as e:
            print(f"⚠️ 加载公司上下文失败 {stock_code}: {e}")
            return f"公司 {stock_code} 的基本信息（加载失败）"

    @staticmethod
    async def load_market_context(market_type: str, data_dir: str, cache: dict):
        """加载市场上下文（简化版）"""
        return f"市场 {market_type} 的基本信息"


# 创建缓存管理器实例
cache_manager = CacheManager()

# 常量导出（向后兼容）
MODEL_NAME = config.model_name
MAX_CONCURRENCY = config.max_workers


# 导出
__all__ = [
    'config', 'Config',
    'get_web_port', 'get_api_key', 'get_target_stocks',
    'get_project_root', 'get_data_dir',
    'strategy_configs', 'StrategyConfigs',
    'CacheManager', 'cache_manager',
    'AsyncAIAnalyzerBase', 'DataProcessor',
    'MODEL_NAME', 'MAX_CONCURRENCY'
]