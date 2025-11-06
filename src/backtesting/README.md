# Backtesting Module 回测模块 v3.0

一个极简但功能完整的股票策略回测框架，专注于策略有效性测试。

## 📁 极简架构

```
src/backtesting/
├── __init__.py              # 统一入口
├── core/                    # 核心功能模块
│   ├── __init__.py
│   ├── engine.py           # 回测引擎
│   ├── indicators.py       # 技术指标计算
│   ├── strategies.py       # 策略定义和管理
│   └── tester.py           # 统一测试工具
└── README.md               # 使用指南
```

## 🚀 极简使用

### 1. 单策略测试

```python
from src.backtesting import BacktestEngine, BacktestConfig, strategy_registry, indicator_calculator
from config import config
import pandas as pd

# 加载数据
data_file = config.get_stock_file_path("000001", "historical_quotes", cleaned=True)
data = pd.read_csv(data_file)
data = indicator_calculator.calculate_all(data)

# 获取策略
strategy = strategy_registry.get("MACD策略")

# 运行回测
engine = BacktestEngine(BacktestConfig(initial_capital=100000))
result = engine.run(data, strategy, output_dir="./results")

# 可视化结果
from src.backtesting import BacktestPlotter
plotter = BacktestPlotter()
plotter.plot_equity_curve(result, show=True)
```

### 2. 命令行测试

```bash
# 列出所有策略
python -m src.backtesting.core.tester --list-strategies

# 测试单个策略
python -m src.backtesting.core.tester 000001 --strategy "MACD策略"

# 测试所有策略
python -m src.backtesting.core.tester 000001 --all-strategies

# 在多只股票上测试策略
python -m src.backtesting.core.tester --strategy "MACD策略" --stocks "000001,000002,600519"
```

### 3. 统一测试器

```python
from src.backtesting import BacktestTester

tester = BacktestTester()

# 测试单个策略
result = tester.test_single_strategy("000001", "MACD策略")

# 测试多个策略
results = tester.test_multiple_strategies("000001")

# 在多只股票上测试策略
results = tester.test_multiple_stocks(["000001", "000002"], "MACD策略")
```

## 📊 内置策略

| 策略名称 | 类型 | 所需指标 | 说明 |
|---------|------|----------|------|
| MACD策略 | 单指标 | MACD_DIF | DIF上穿下穿0轴 |
| MACD金叉死叉策略 | 交叉 | MACD_DIF, MACD_DEA | 金叉买入，死叉卖出 |
| KDJ策略 | 单指标 | DAILY_KDJ_J | J值超买卖 |
| 周KDJ策略 | 单指标 | WEEKLY_KDJ_J | 周线J值超买卖 |
| RSI策略 | 单指标 | RSI | RSI超买卖 |
| BBI策略 | 价格 | BBI | 价格突破BBI |
| 布林带策略 | 价格 | BOLL_UPPER, BOLL_LOWER | 价格突破布林带 |
| 周KDJ+BBI策略 | 组合 | WEEKLY_KDJ_J, BBI | 周KDJ超卖+价格站上BBI |
| 日KDJ+MACD策略 | 组合 | DAILY_KDJ_J, MACD_DIF, MACD_DEA | 日KDJ超卖+MACD金叉 |
| 成交量突破策略 | 成交量 | VOLUME_MA5 | 成交量突破+价格上涨 |

## 🎯 自定义策略

### 单指标策略
```python
from src.backtesting.core.strategies import IndicatorStrategy

class MyStrategy(IndicatorStrategy):
    def __init__(self):
        super().__init__(
            name="我的策略",
            indicator="RSI",
            buy_condition=lambda x: x < 30,
            sell_condition=lambda x: x > 70
        )
```

### 交叉策略
```python
from src.backtesting.core.strategies import CrossOverStrategy

class MyCrossStrategy(CrossOverStrategy):
    def __init__(self):
        super().__init__(
            name="我的交叉策略",
            fast_line="MACD_DIF",
            slow_line="MACD_DEA"
        )
```

### 组合策略
```python
from src.backtesting.core.strategies import CombinedStrategy

class MyCombinedStrategy(CombinedStrategy):
    def __init__(self):
        conditions = [
            {"type": "buy", "indicator": "RSI", "operator": "<", "value": 30},
            {"type": "sell", "indicator": "RSI", "operator": ">", "value": 70}
        ]
        super().__init__("我的组合策略", conditions)
```

## ⚙️ 配置参数

```python
from src.backtesting import BacktestConfig

config = BacktestConfig(
    initial_capital=100000.0,    # 初始资金
    position_size=1.0            # 仓位比例 (0-1)
)
```

## 📈 输出结果

每次回测都会生成以下文件：
- `trades.csv`: 交易记录
- `equity_curve.csv`: 权益曲线
- `performance.csv`: 性能指标
- `config.json`: 配置信息

## 📊 可视化功能

### 自动生成图表
```bash
# 测试策略时自动生成图表
python -m src.backtesting.core.tester 000001 --strategy "MACD策略"
# 自动生成4个图表文件到输出目录
```

### 手动绘制图表
```python
from src.backtesting import BacktestPlotter

plotter = BacktestPlotter()

# 绘制权益曲线
plotter.plot_equity_curve(result, "equity_curve.png")

# 绘制交易点
plotter.plot_trades(result, "trades.png")

# 绘制回撤分析
plotter.plot_drawdown(result, "drawdown.png")

# 绘制月度收益热力图
plotter.plot_monthly_returns(result, "monthly_returns.png")

# 生成综合报告（包含所有图表）
plotter.plot_comprehensive_report(result, "./charts", show=False)
```

### 策略比较可视化
```python
# 比较多个策略的表现
results = {}
results["MACD"] = engine.run(data, strategy1)
results["KDJ"] = engine.run(data, strategy2)

# 生成比较图表
plotter.plot_strategy_comparison(results, "strategy_comparison.png")
```

## 🔧 高级功能

### 技术指标计算
```python
from src.backtesting import indicator_calculator

# 计算所有指标
data_with_indicators = indicator_calculator.calculate_all(data)

# 计算单个指标
macd_data = indicator_calculator.calculate_macd(data["收盘"])
kdj_data = indicator_calculator.calculate_kdj(data["最高"], data["最低"], data["收盘"])
```

### 策略管理
```python
from src.backtesting import strategy_registry

# 列出所有策略
strategy_names = strategy_registry.list_all()

# 获取策略实例
strategy = strategy_registry.get("MACD策略")

# 查看策略汇总
print(strategy_registry.create_summary())
```

## 📚 最佳实践

1. **数据验证**: 始终检查数据完整性
2. **指标计算**: 使用统一的指标计算器
3. **策略开发**: 使用策略模板快速开发
4. **批量测试**: 使用统一测试器提高效率
5. **结果分析**: 关注夏普比率和最大回撤

## 🎉 特点总结

- ✅ **极简架构**: 只有一个core模块，包含所有功能
- ✅ **零重复**: 消除所有代码重复
- ✅ **统一接口**: 一致的API设计
- ✅ **内置策略**: 10个常用策略开箱即用
- ✅ **灵活扩展**: 易于添加新策略和指标
- ✅ **命令行支持**: 完整的CLI工具
- ✅ **批量测试**: 高效的批量测试功能

---

**🎉 一个模块，所有功能！极简但不简单！**