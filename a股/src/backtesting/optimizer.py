#!/usr/bin/env python3

"""
基于贝叶斯优化的参数优化器
专注于使用贝叶斯优化和夏普比率作为唯一优化目标
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Tuple, Optional, Callable
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
import time
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    from skopt import gp_minimize
    from skopt.space import Real, Integer, Categorical
    from skopt.utils import use_named_args
    BAYESIAN_AVAILABLE = True
except ImportError:
    BAYESIAN_AVAILABLE = False
    logger.warning("scikit-optimize未安装，贝叶斯优化功能不可用")


@dataclass
class OptimizationResult:
    """优化结果数据类"""
    best_params: Dict[str, Any]
    best_score: float
    best_performance: Dict[str, float]
    all_results: List[Dict[str, Any]]
    optimization_time: float
    total_evaluations: int
    success_rate: float
    method: str


class ParameterOptimizer:
    """
    参数优化器 - 专注于贝叶斯优化
    """

    def __init__(self, config=None):
        from .config import BacktestConfig
        from .evaluator import StrategyEvaluator

        self.config = config or BacktestConfig()
        self.evaluator = StrategyEvaluator(self.config)

    def get_strategy_param_grid(self, strategy_name: str) -> Dict[str, List]:
        """获取策略的参数网格"""
        from .config import STRATEGY_PARAM_GRIDS
        return STRATEGY_PARAM_GRIDS.get(strategy_name, {})

    def optimize(self, symbol: str, strategy_name: str, param_grid: Dict[str, List] = None,
                 method: str = None, max_evaluations: int = None,
                 objective: str = None, **kwargs) -> OptimizationResult:
        """
        参数优化主函数 - 专注于贝叶斯优化

        Args:
            symbol: 股票代码
            strategy_name: 策略名称
            param_grid: 参数网格（可选，如果不提供则使用默认配置）
            method: 优化方法（目前只支持贝叶斯优化）
            max_evaluations: 最大评估次数
            objective: 优化目标（目前只支持夏普比率）
            **kwargs: 其他参数

        Returns:
            优化结果
        """
        start_time = time.time()

        # 从config获取默认配置
        from .config import OPTIMIZATION_CONFIG

        method = method or OPTIMIZATION_CONFIG["default_method"]
        max_evaluations = max_evaluations or OPTIMIZATION_CONFIG["default_max_evaluations"]
        objective = objective or OPTIMIZATION_CONFIG["default_objective"]

        logger.info(f"开始贝叶斯参数优化: {strategy_name} on {symbol}")
        logger.info(f"优化方法: {method}, 目标: {objective}, 最大评估: {max_evaluations}")

        # 获取参数网格
        param_grid = param_grid or self.get_strategy_param_grid(strategy_name)
        if not param_grid:
            raise ValueError(f"策略 {strategy_name} 没有可优化的参数配置")

        # 执行贝叶斯优化
        if method == "bayesian":
            if not BAYESIAN_AVAILABLE:
                raise ImportError("贝叶斯优化需要安装 scikit-optimize: pip install scikit-optimize")
            result = self._bayesian_optimization(symbol, strategy_name, param_grid,
                                               max_evaluations, objective, **kwargs)
        else:
            raise ValueError(f"不支持的优化方法: {method}，只支持贝叶斯优化 (bayesian)")

        optimization_time = time.time() - start_time

        # 构建结果对象
        optimization_result = OptimizationResult(
            best_params=result["best_params"],
            best_score=result["best_score"],
            best_performance=result["best_performance"],
            all_results=result["all_results"],
            optimization_time=optimization_time,
            total_evaluations=result["total_evaluations"],
            success_rate=result["success_rate"],
            method=method
        )

        logger.info(f"优化完成: 最佳{objective}={optimization_result.best_score:.3f}, "
                   f"耗时{optimization_time:.1f}秒")

        return optimization_result

    def _bayesian_optimization(self, symbol: str, strategy_name: str, param_grid: Dict[str, List],
                              max_evaluations: int, objective: str, **kwargs) -> Dict[str, Any]:
        """贝叶斯优化实现"""
        logger.info("开始贝叶斯优化...")

        # 构建搜索空间
        dimensions = []
        param_names = []

        for param_name, param_values in param_grid.items():
            param_names.append(param_name)

            if isinstance(param_values[0], int):
                dimensions.append(Integer(min(param_values), max(param_values), name=param_name))
            elif isinstance(param_values[0], float):
                dimensions.append(Real(min(param_values), max(param_values), name=param_name))
            else:
                dimensions.append(Categorical(param_values, name=param_name))

        @use_named_args(dimensions)
        def objective_function(**params):
            """目标函数：返回负的夏普比率（因为贝叶斯优化是最小化）"""
            try:
                # 参数验证逻辑
                if not self._validate_params(strategy_name, params):
                    return 1000  # 返回大值表示无效参数组合

                score, performance = self._evaluate_params(symbol, strategy_name, params, objective)
                return -score if score is not None else 1000  # 返回大值表示无效结果
            except Exception as e:
                logger.warning(f"参数评估失败: {params}, 错误: {e}")
                return 1000

        # 执行贝叶斯优化
        result = gp_minimize(
            func=objective_function,
            dimensions=dimensions,
            n_calls=max_evaluations,
            n_initial_points=10,
            random_state=42,
            verbose=False
        )

        # 评估最佳参数
        best_params_dict = dict(zip(param_names, result.x))
        best_score, best_performance = self._evaluate_params(symbol, strategy_name, best_params_dict, objective)

        # 收集所有评估结果
        all_results = []
        successful_count = 0

        for i, params in enumerate(result.x_iters):
            if result.func_vals[i] < 1000:  # 有效结果
                params_dict = dict(zip(param_names, params))
                score, performance = self._evaluate_params(symbol, strategy_name, params_dict, objective)
                if score is not None:
                    all_results.append({
                        "params": params_dict,
                        "score": score,
                        "performance": performance
                    })
                    successful_count += 1

        if not all_results:
            return {
                "best_params": best_params_dict,
                "best_score": best_score or float('-inf'),
                "best_performance": best_performance or {},
                "all_results": [],
                "total_evaluations": max_evaluations,
                "success_rate": 0
            }

        return {
            "best_params": best_params_dict,
            "best_score": best_score or float('-inf'),
            "best_performance": best_performance or {},
            "all_results": all_results,
            "total_evaluations": max_evaluations,
            "success_rate": successful_count / max_evaluations * 100
        }

    def _evaluate_params(self, symbol: str, strategy_name: str, params: Dict[str, Any],
                        objective: str) -> Tuple[Optional[float], Dict[str, float]]:
        """评估单组参数"""
        try:
            # 运行回测
            result = self.evaluator.evaluate_strategy(symbol, strategy_name, params)

            if result and result.success and result.performance:
                performance = result.performance

                # 根据目标返回对应的分数
                if objective == "sharpe_ratio":
                    score = performance.get('sharpe_ratio', 0)
                elif objective == "total_return":
                    score = performance.get('total_return', 0) / 100
                elif objective == "max_drawdown":
                    score = -performance.get('max_drawdown', 0) / 100  # 最小化回撤
                else:
                    score = performance.get('sharpe_ratio', 0)

                return score, performance
            else:
                return None, {}

        except Exception as e:
            logger.warning(f"参数评估异常: {params}, 错误: {e}")
            return None, {}

    def _validate_params(self, strategy_name: str, params: Dict[str, Any]) -> bool:
        """验证参数组合是否合理"""
        try:
            if strategy_name == "双均线策略":
                # 短期均线必须小于长期均线
                if 'short_period' in params and 'long_period' in params:
                    if params['short_period'] >= params['long_period']:
                        return False

            elif strategy_name == "RSI反转策略":
                # 超卖线必须小于超买线
                if 'oversold' in params and 'overbought' in params:
                    if params['oversold'] >= params['overbought']:
                        return False
                # RSI超卖线通常不应该超过40，超买线通常不应该低于60
                if 'oversold' in params and params['oversold'] > 40:
                    return False
                if 'overbought' in params and params['overbought'] < 60:
                    return False

            elif strategy_name == "MACD趋势策略":
                # 快线必须小于慢线
                if 'fast' in params and 'slow' in params:
                    if params['fast'] >= params['slow']:
                        return False

            elif strategy_name == "布林带策略":
                # 周期必须合理（5-200）
                if 'period' in params:
                    if not (5 <= params['period'] <= 200):
                        return False
                # 标准差必须合理（1.0-3.0）
                if 'std_dev' in params:
                    if not (1.0 <= params['std_dev'] <= 3.0):
                        return False

            elif strategy_name == "成交量突破策略":
                # 成交量倍数必须合理（1.0-5.0）
                if 'volume_multiplier' in params:
                    if not (1.0 <= params['volume_multiplier'] <= 5.0):
                        return False

            return True
        except Exception as e:
            logger.warning(f"参数验证失败: {params}, 错误: {e}")
            return False

    