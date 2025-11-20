# 配置系统 - 极简版

极简的配置管理，使用单一Python文件，避免冗余。

## 📁 文件结构

```
config/
├── __init__.py    # 统一导入接口
├── config.py      # 所有配置（核心文件）
└── README.md      # 说明文档
```

## 🚀 使用方法

### 基础配置访问

```python
from config import config

# 直接访问配置
port = config.web_port
api_key = config.api_key
stocks = config.target_stocks
project_root = config.project_root

# 路径管理
data_dir = config.data_dir
stock_dir = config.get_stock_dir("000001")
```

### 便捷函数

```python
from config import get_web_port, get_api_key, get_target_stocks

port = get_web_port()
key = get_api_key()
stocks = get_target_stocks()
```

### 策略配置

```python
from config import strategy_configs

kdj_config = strategy_configs.get_strategy_config("Base_DailyKDJ")
rsi_config = strategy_configs.get_strategy_config("Base_RSI")
```

## 📋 配置项

### Web配置
- `web_host`: 主机地址
- `web_port`: 端口号
- `web_debug`: 调试模式
- `web_theme`: 主题
- `web_wide_mode`: 宽屏模式

### 系统配置
- `app_name`: 应用名称
- `target_stocks`: 目标股票列表
- `enable_parallel`: 并行处理
- `max_workers`: 最大线程数

### API配置
- `api_key`: API密钥
- `api_base_url`: API基础URL
- `api_timeout`: 超时时间

### AI模型配置
- `model_name`: 模型名称
- `model_temperature`: 温度参数

### 回测配置
- `initial_capital`: 初始资金
- `commission_rate`: 佣金费率
- `slippage_rate`: 滑点率
- `benchmark`: 基准指数

### 技术指标配置
- KDJ参数：快线、慢线周期
- MACD参数：快线、慢线、信号线周期
- BBI、BOLL、RSI参数等


## 🎯 极简优势

1. **单一文件**：所有配置集中在一个Python文件中
2. **类型安全**：使用dataclass确保类型安全
3. **无冗余**：删除所有重复和不必要的文件
4. **易于维护**：清晰的配置结构
5. **向后兼容**：现有代码无需修改

---

*极简配置 - 让配置管理更简单*