# 🚀 A股智能分析系统

基于专业投资理念的智能股票分析系统，集成AI分析、技术分析、回测系统等功能。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io/)
[![AKShare](https://img.shields.io/badge/AKShare-1.10+-green.svg)](https://akshare.akfamily.xyz/)

## 📋 项目概述

本项目是一个完整的A股市场智能分析平台，集成了实时数据获取、AI智能分析、技术指标分析、估值模型、回测系统等功能，为投资者提供全方位的股票分析支持。

### 🎯 核心特性

- **📊 Web可视化界面**: 基于Streamlit的现代化Web应用，支持实时数据展示
- **🤖 AI智能分析**:
  - **Google Gemini分析**: 智能财务分析和投资建议
  - **API轮换机制**: 支持多API密钥自动轮换，提高稳定性
  - **多维度分析**: 财务报表、技术指标、市场情绪综合分析
- **📈 技术分析系统**: 完整的技术指标和图表分析（MACD、RSI、KDJ、BOLL等）
- **💰 财务分析**: 深度基本面分析和估值模型
- **🔄 实时数据**: 支持AKShare、BaoStock等多数据源的实时股票数据
- **⚡ 回测系统**: 完整的策略回测和参数优化框架
- **🏭 行业分析**: 行业对比和趋势分析
- **📡 数据管道**: 完整的数据爬取→清洗→分析→可视化流程

## 🏗️ 项目结构

```
A股/
├── streamlit_app.py         # 🚀 主启动脚本 - Web应用入口
├── requirements.txt         # 📦 项目依赖
├── config/                  # ⚙️ 配置文件
│   ├── config.py           # 统一配置管理（API密钥、系统参数等）
│   └── README.md           # 配置说明文档
├── src/                     # 💻 核心源代码
│   ├── ai_analysis/        # 🤖 AI分析模块
│   │   ├── comprehensive_stock_analyser.py    # 个股综合分析
│   │   ├── comprehensive_market_analyser.py   # 市场综合分析
│   │   └── prompts/                           # AI提示词管理
│   ├── backtesting/        # 📊 回测系统
│   │   ├── engine.py       # 回测引擎
│   │   ├── strategies.py   # 策略定义
│   │   └── evaluator.py   # 回测评估
│   ├── web/                # 🌐 Web应用组件
│   │   ├── components/     # UI组件（公司概况、财务分析、技术分析等）
│   │   ├── templates/      # UI模板
│   │   └── utils/         # 工具函数
│   ├── crawling/           # 📡 数据爬取
│   │   ├── stock_data_collector.py      # 股票数据收集
│   │   └── market_data_collector.py     # 市场数据收集
│   ├── cleaning/           # 🧹 数据清洗
│   │   ├── stock_data_cleaner.py        # 股票数据清洗
│   │   └── market_data_cleaner.py      # 市场数据清洗
│   └── launchers/          # 🚀 启动脚本
│       ├── run_data_pipeline_async.py           # 股票数据管道
│       ├── run_data_ai_pipeline_async.py        # 股票AI分析管道
│       ├── run_market_data_pipeline_async.py    # 市场数据管道
│       └── run_market_ai_pipeline_async.py      # 市场AI分析管道
├── data/                    # 📊 数据存储目录
│   ├── stocks/             # 原始股票数据
│   ├── cleaned_stocks/     # 清洗后股票数据
│   ├── market_data/        # 市场数据
│   ├── ai_reports/         # AI分析报告
│   └── cache/              # 缓存数据
└── logs/                    # 📝 日志文件
```

## 🚀 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone <repository-url>
cd a股

# 安装依赖
pip install -r requirements.txt

# 验证安装
python -c "import streamlit; import pandas; import akshare; print('✅ 核心依赖安装成功')"
```

### 2. 配置API密钥

#### 方式一：在配置文件中配置（推荐）

编辑 `config/config.py` 文件，在 `GEMINI_API_KEYS` 列表中添加你的API密钥：

```python
# Gemini API Keys - 用于轮换
GEMINI_API_KEYS = [
    "your-api-key-1",
    "your-api-key-2",
    # 可以添加多个密钥实现自动轮换
]
```

**优势**：
- 支持多密钥自动轮换，提高稳定性
- 避免单点故障
- 自动负载均衡

#### 方式二：使用环境变量

```bash
# 配置Gemini API (用于AI分析)
export GEMINI_API_KEY="your-gemini-api-key"

# 或使用 .env 文件
echo "GEMINI_API_KEY=your-gemini-api-key" > .env
```

#### 获取API密钥

1. 访问 [Google AI Studio](https://makersuite.google.com/app/apikey)
2. 创建新的API密钥
3. 将密钥添加到配置文件中

### 3. 启动Web应用

```bash
# 或使用Streamlit命令
streamlit run streamlit_app.py
```

### 4. 数据获取 (Launchers)

#### 📡 完整数据爬取流程
```bash
# 1. 爬取基础股票数据 (推荐先运行)
python src/launchers/run_data_pipeline_async.py 000001

# 2. 爬取市场数据
python src/launchers/run_market_data_pipeline_async.py

# 3. 爬取指数数据
python src/launchers/run_index_pipeline_async.py
```

#### 🤖 AI分析流程
```bash
# 1. 个股AI分析 (Gemini)
python src/launchers/run_data_ai_pipeline_async.py 000001

# 2. 市场AI分析
python src/launchers/run_market_ai_pipeline_async.py
```

### 5. 完整工作流程示例

```bash
# 1. 数据获取（后台运行）
python src/launchers/run_data_pipeline_async.py 000001 &
python src/launchers/run_market_data_pipeline_async.py &

# 2. 等待数据爬取完成后，运行AI分析
python src/launchers/run_data_ai_pipeline_async.py 000001
python src/launchers/run_market_ai_pipeline_async.py

# 3. 启动Web应用查看结果
streamlit run streamlit_app.py
# 或
python streamlit_app.py
```

**提示**：
- 首次运行需要先获取数据，建议先运行数据爬取脚本
- AI分析需要数据文件存在，确保数据爬取完成后再运行
- Web应用会自动扫描 `data/cleaned_stocks/` 目录下的股票数据

## 📊 Web应用功能

### 🏠 主页功能
- **📈 实时行情**: 股票实时价格和涨跌幅
- **🔍 智能搜索**: 股票代码搜索和选择
- **📊 市场概览**: 大盘指数和市场情绪
- **🤖 AI助手**: 智能投资建议和分析

### 💰 AI分析功能
- **个股AI分析**: 基于Gemini的智能分析
- **财务健康度**: AI评估公司财务状况
- **投资建议**: AI生成的投资评级和策略
- **风险评估**: AI识别投资风险

### 📈 技术分析功能
- **K线图表**: 专业级股票K线图
- **技术指标**: MACD、RSI、KDJ等常用指标
- **趋势分析**: 支撑位和阻力位识别
- **交易信号**: 买入和卖出信号提示

### 🏭 行业分析功能
- **行业对比**: 同行业股票对比分析
- **行业排名**: 行业内股票表现排名
- **板块热点**: 热门板块和市场主题
- **资金流向**: 板块资金流向分析

### 📊 回测功能
- **策略回测**: 多种投资策略历史表现
- **参数优化**: 策略参数自动优化
- **风险评估**: 最大回撤和夏普比率分析
- **业绩报告**: 详细的回测报告

## 🤖 AI智能分析系统

### 🎯 核心特性
- **多维度分析**: 财务报表、技术指标、市场情绪综合分析
- **API轮换机制**: 支持多API密钥自动轮换，提高稳定性
- **实时数据获取**: 基于AKShare等数据源的最新市场信息
- **智能报告生成**: 自动生成Markdown格式的分析报告

### 📊 分析模块

#### 个股分析 (`comprehensive_stock_analyser.py`)
- **公司概况分析**: 公司基本信息、业务模式、行业地位
- **财务报表分析**: 资产负债表、利润表、现金流量表深度分析
- **财务指标分析**: ROE、ROA、PE、PB等关键指标评估
- **技术分析**: K线形态、技术指标、趋势判断
- **综合分析**: 整合所有维度，生成投资建议

#### 市场分析 (`comprehensive_market_analyser.py`)
- **市场情绪分析**: 资金流向、市场热度、投资者情绪
- **板块分析**: 行业板块表现、资金流向、热点追踪
- **新闻舆情分析**: 重大新闻事件、市场反应、政策影响
- **综合市场报告**: 市场整体状况和投资机会

### 📁 报告输出

AI分析报告保存在 `data/ai_reports/` 目录下：

```
data/ai_reports/
├── {股票代码}/
│   ├── company_profile.md           # 公司概况
│   ├── income_statement_analysis.md # 利润表分析
│   ├── balance_sheet_analysis.md    # 资产负债表分析
│   ├── cash_flow_analysis.md        # 现金流量表分析
│   ├── financial_indicators_analysis.md # 财务指标分析
│   ├── technical_analysis.md        # 技术分析
│   ├── intraday_trading.md          # 日内交易分析
│   └── comprehensive.md             # 综合分析报告
└── market_analysis/
    ├── comprehensive.md             # 市场综合分析
    ├── fund_flow_industry.md        # 行业资金流向
    └── news_main_cx.md              # 新闻舆情分析
```

## 🛠️ 技术架构

### 前端技术
- **Streamlit**: 快速构建Web应用的Python框架
- **Plotly**: 交互式数据可视化
- **Pyecharts**: 中国风图表库

### 后端技术
- **Python**: 核心开发语言
- **Pandas**: 数据处理和分析
- **NumPy**: 数值计算
- **AKShare/BaoStock**: 股票数据获取

### AI技术
- **Google Gemini**: 大语言模型API（支持API轮换）
- **API轮换机制**: 多密钥自动轮换，提高稳定性
- **异步处理**: 支持并发AI分析请求

### 数据源
- **AKShare**: A股实时和历史数据（主要数据源）
- **BaoStock**: 备用数据源
- **Tushare**: 补充数据源

## 📋 数据流架构

```
┌─────────────────────────────────────────────────────────┐
│                   数据获取层                              │
│  AKShare/BaoStock → 数据爬取 → 数据清洗 → 数据存储      │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│                   数据分析层                              │
│  技术分析 → 财务分析 → 行业分析 → 市场分析              │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│                   AI智能分析层                            │
│  Gemini API → 多维度分析 → 报告生成                     │
│  (支持API轮换)                                          │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│                   可视化展示层                            │
│  Streamlit Web应用 → 交互式图表 → 分析报告展示         │
└─────────────────────────────────────────────────────────┘
```

## 📚 详细文档

### 📖 用户文档
- **[📊 Web应用使用指南](src/web/README.md)** - 界面功能说明
- **[🔧 配置参考](config/README.md)** - 配置详细说明
- **[🧪 回测系统指南](src/backtesting/README.md)** - 回测系统使用

### 👨‍💻 开发文档
- **[🧪 策略开发指南](src/backtesting/README.md)** - 策略开发
- **[📡 数据爬取模块](src/crawling/)** - 数据获取实现
- **[🧹 数据清洗模块](src/cleaning/)** - 数据清洗实现

### 📋 参考文档
- **[AKShare文档](https://akshare.akfamily.xyz/)** - 数据获取API
- **[Streamlit文档](https://docs.streamlit.io/)** - Web应用框架
- **[Pandas文档](https://pandas.pydata.org/docs/)** - 数据处理库
- **[Plotly文档](https://plotly.com/python/)** - 可视化库
- **[Google Gemini API](https://ai.google.dev/)** - Gemini API文档

## 🌟 核心优势

1. **🎯 专业级分析**: 结合传统量化分析和现代AI技术
2. **🔄 API轮换机制**: 多密钥自动轮换，提高系统稳定性和可用性
3. **📊 可视化友好**: 现代化Web界面，数据可视化直观
4. **⚡ 实时性能**: 实时数据更新，快速响应用户需求
5. **🔧 易于扩展**: 模块化设计，支持功能定制和扩展
6. **💡 智能决策**: AI辅助投资决策，提高分析效率
7. **📡 完整数据流**: 从数据获取到分析展示的完整流程
8. **🏭 A股专注**: 专门针对A股市场优化，支持中国股市特色功能

## 📊 项目统计

### 代码规模
- **总文件数**: 50+ 个Python文件
- **代码行数**: 20,000+ 行
- **模块数量**: 10+ 个核心模块
- **功能组件**: 30+ 个Web组件

### 技术栈覆盖
- **Web框架**: Streamlit (可视化界面)
- **数据处理**: Pandas, NumPy, AKShare
- **AI技术**: Gemini, AutoGen 0.4+, OpenAI
- **数据源**: 5+ 个金融数据API
- **回测引擎**: 完整的策略回测框架

### 功能覆盖
- **数据获取**: 股票、市场、指数、新闻
- **分析类型**: 技术、基本面、情绪、宏观
- **AI分析**: Gemini + AutoGen多智能体
- **可视化**: 图表、仪表板、交互式界面
- **回测**: 20+ 个内置策略

## 🔮 发展路线

### 已完成 ✅ (v2.0)
- [x] Web可视化界面 (v1.0)
- [x] AI智能分析系统 (v2.0)
- [x] API轮换机制
- [x] 实时数据集成
- [x] 完整回测系统
- [x] Launcher批处理框架
- [x] 多维度财务分析
- [x] 技术指标分析
- [x] 行业对比分析

### 计划中 🚧
- [ ] 实时预警系统
- [ ] 更多技术指标支持
- [ ] 移动端适配
- [ ] 数据导出功能增强

## 🤝 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## ⚠️ 免责声明

本项目仅供学习和研究使用，不构成投资建议。投资有风险，入市需谨慎。使用本系统进行实际投资决策的风险由用户自行承担。

---

## 📞 联系方式

- 🐛 **Bug报告**: [GitHub Issues](https://github.com/your-repo/issues)
- 💡 **功能建议**: [GitHub Discussions](https://github.com/your-repo/discussions)
- 📧 **技术交流**: 欢迎提交PR或Issue

---

*🚀 智能股票分析系统 - 让投资更科学，让决策更理性*

🔥 **核心特色**: 🤖 AI智能分析 + 📊 实时数据分析 + 💰 专业投资建议 + 🔄 API轮换机制

**用科技赋能投资，让分析更专业**

---

## 💡 常见问题

### Q: 如何配置多个API密钥？
A: 在 `config/config.py` 文件的 `GEMINI_API_KEYS` 列表中添加多个密钥，系统会自动轮换使用。

### Q: 数据爬取失败怎么办？
A: 检查网络连接，确保可以访问AKShare数据源。如果持续失败，可以尝试使用BaoStock作为备用数据源。

### Q: Web应用无法启动？
A: 确保已安装所有依赖：`pip install -r requirements.txt`，并检查端口8501是否被占用。

### Q: AI分析报告在哪里？
A: 报告保存在 `data/ai_reports/` 目录下，按股票代码分类存储。

### Q: 如何添加新的技术指标？
A: 在 `src/backtesting/indicators.py` 中添加指标计算函数，然后在策略中使用。

---

**⭐ 如果这个项目对你有帮助，欢迎Star支持！**