# A股分析系统 - 项目结构

基于"z哥"投资哲学的综合性A股市场分析系统，集成数据采集、技术分析、AI分析和回测功能。

## 📁 项目结构

```
A股分析系统/
├── 📁 src/                              # 核心源代码目录
│   ├── 📁 web/                          # Web应用模块
│   │   ├── 📄 app.py                    # Streamlit主应用
│   │   └── 📁 components/               # 页面组件
│   ├── 📁 backtesting/                  # 回测模块 (简化版)
│   │   ├── 📁 core/                     # 核心回测功能
│   │   │   ├── 📄 engine.py             # 回测引擎 (206行)
│   │   │   ├── 📄 strategies.py         # 策略管理 (377行)
│   │   │   ├── 📄 plotter.py            # 可视化 (285行)
│   │   │   ├── 📄 tester.py             # 测试工具 (337行)
│   │   │   └── 📄 indicators.py         # 技术指标 (310行)
│   │   └── 📄 README.md                 # 回测模块文档
│   ├── 📁 crawling/                     # 数据采集模块
│   ├── 📁 cleaning/                      # 数据清洗模块
│   ├── 📁 ai_analysis/                  # AI分析模块
│   ├── 📁 talib_analysis/               # 技术指标模块
│   ├── 📁 launchers/                    # 启动器模块
│   └── 📁 __init__.py                   # 包初始化
├── 📁 config/                           # 配置文件目录
│   ├── 📄 unified_config.json           # 主配置文件
│   ├── 📄 strategy_configs.py           # 策略配置
│   ├── 📄 ai_config.py                  # AI配置
│   └── 📄 system_config.py              # 系统配置
├── 📁 data/                             # 数据存储目录
│   ├── 📁 historical_quotes/            # 历史行情数据
│   ├── 📁 market_data/                  # 市场数据
│   ├── 📁 index_data/                   # 指数数据
│   └── 📁 analysis_results/             # 分析结果
├── 📁 requirements/                     # 依赖管理
│   └── 📄 requirements.txt              # Python依赖
├── 📄 CLAUDE.md                         # Claude Code指导文档
├── 📄 README.md                         # 项目说明文档
└── 📄 PROJECT_STRUCTURE.md              # 项目结构文档
```

## 🏗️ 核心模块说明

### 📁 src/ - 源代码目录
**功能**：系统核心功能实现

#### 📁 backtesting/ - 回测模块 (v3.1简化版)
**功能**：策略回测和验证
- **代码量**：1,205行 (减少37%)
- **核心功能**：完整保留所有回测功能
- **简化特点**：去除冗余验证，专注核心逻辑
- **文件结构**：
  - `engine.py` (206行) - 核心回测引擎
  - `strategies.py` (377行) - 10个内置策略
  - `plotter.py` (285行) - 结果可视化
  - `tester.py` (337行) - 测试工具
  - `indicators.py` (310行) - 技术指标计算

#### 📁 web/ - Web应用模块
**功能**：Streamlit Web界面
- `app.py` - 主应用入口
- `components/` - 页面组件

#### 📁 crawling/ - 数据采集模块
**功能**：股票数据采集
- 多数据源支持
- 自动化数据更新
- 数据质量验证

#### 📁 ai_analysis/ - AI分析模块
**功能**：基于Gemini的智能分析
- 个股分析
- 市场分析
- 情绪分析

#### 📁 talib_analysis/ - 技术指标模块
**功能**：TA-Lib技术指标计算
- 50+技术指标
- 多时间周期支持

### 📁 config/ - 配置文件目录
**功能**：系统配置管理
- `unified_config.json` - 主配置文件
- `strategy_configs.py` - 策略配置
- `ai_config.py` - AI分析配置

### 📁 data/ - 数据存储目录
**功能**：数据文件存储
- `historical_quotes/` - 历史行情数据
- `market_data/` - 市场数据
- `analysis_results/` - 分析结果

## 🎯 "少妇战法" 实现

### 核心策略
- **B1买点**：多周期KDJ共振策略
- **B2买点**：右侧交易策略
- **3/4负量法**：识别假突破工具
- **价格过滤**：智能B1过滤机制

### 技术实现
- **多时间周期**：周线、月线、日线
- **技术指标**：KDJ、MACD、布林带、BBI
- **成交量分析**：量价关系验证
- **风险管理**：止损和仓位控制

## 🔧 技术架构

### 数据流架构
1. **数据采集** → 原始市场数据
2. **数据清洗** → 标准化数据
3. **技术分析** → 技术指标计算
4. **AI分析** → 智能投资建议
5. **回测验证** → 策略效果验证
6. **Web展示** → 用户界面展示

### 核心技术栈
- **Python 3.8+** - 主要开发语言
- **Streamlit** - Web界面框架
- **Pandas/NumPy** - 数据处理
- **TA-Lib** - 技术指标计算
- **Gemini API** - AI分析引擎
- **Matplotlib** - 数据可视化

## 📊 系统特色

### 投资哲学融合
- **"z哥"理念**：价值投资与技术分析结合
- **"少妇战法"**：系统化策略实现
- **A股适配**：专门针对中国股市

### 系统优势
- **一体化**：数据采集到分析展示全流程
- **智能化**：AI驱动的投资建议
- **可视化**：丰富的图表和分析工具
- **可扩展**：模块化设计，易于扩展

## 📄 许可证

MIT License
