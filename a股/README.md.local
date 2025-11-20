# 🚀 A股智能分析系统

基于专业投资理念的智能股票分析系统，集成AI分析、技术分析、回测系统等功能。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io/)

## 📋 项目概述

本项目是一个完整的A股市场智能分析平台，集成了实时数据获取、AI智能分析、技术指标分析、估值模型、回测系统等功能，为投资者提供全方位的股票分析支持。

### 🎯 核心特性

- **📊 Web可视化界面**: 基于Streamlit的现代化Web应用
- **🤖 AI智能分析**:
  - **Google Gemini分析**: 智能财务分析和投资建议
  - **AutoGen多智能体**: 8个专业AI智能体协作分析 (v3.0)
  - **智能体职责分离**: 彻底解决重复分析问题
- **📈 技术分析系统**: 完整的技术指标和图表分析
- **💰 财务分析**: 深度基本面分析和估值模型
- **🔄 实时数据**: 支持多数据源的实时股票数据
- **⚡ 回测系统**: 完整的策略回测和参数优化
- **🏭 行业分析**: 行业对比和趋势分析

## 🏗️ 项目结构

```
A股/
├── streamlit_app.py         # 🚀 主启动脚本 - Web应用入口
├── requirements.txt        # 📦 项目依赖
├── src/                     # 💻 核心源代码
│   ├── ai_analysis/        # 🤖 AI分析模块
│   ├── backtesting/        # 📊 回测系统
│   ├── web/               # 🌐 Web应用组件
│   ├── crawling/          # 📡 数据爬取
│   ├── cleaning/          # 🧹 数据清洗
│   └── launchers/         # 🚀 启动脚本
├── autogen_graphflow/      # 🤖 AutoGen多智能体分析系统 (v3.0)
│   ├── main.py            # 主程序 - 8智能体协作分析
│   ├── config.py          # 配置管理 - MCP工具集成
│   ├── agent_factory.py   # 智能体工厂 - 职责分离
│   ├── prompt.py          # 提示词管理 - 严格职责限制
│   ├── workflow.py        # GraphFlow工作流 - 顺序执行
│   ├── report_saver.py    # 报告保存 - 用户优先
│   └── README.md          # AutoGen系统文档
├── config/                 # ⚙️ 配置文件
├── data/                   # 📊 数据存储目录
├── reports/                # 📄 分析报告输出
└── .streamlit/            # 🎨 Streamlit配置
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

```bash
# 配置Gemini API (用于AI分析)
export GEMINI_API_KEY="your-gemini-api-key"

# 配置OpenAI/Kimi API (用于AutoGen多智能体)
export OPENAI_API_KEY="your-openai-api-key"
export KIMI_API_KEY="your-kimi-api-key"

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

### 6. 使用AutoGen多智能体分析

```bash
# 进入AutoGen目录
cd autogen_graphflow

# 分析平安银行
python main.py 000001
```

### 7. 完整工作流程示例

```bash
# 1. 数据获取
python src/launchers/run_data_pipeline_async.py 000001&
python src/launchers/run_market_data_pipeline_async.py &

# 2. 在另一个终端运行AI分析
python src/launchers/run_data_ai_pipeline_async.py 000001
python src/launchers/run_market_ai_data_pipeline_async.py

# 3. 启动Web应用
python streamlit_app.py
```

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

## 🤖 AutoGen多智能体分析

### 🎯 核心突破
- **8个专业智能体**: 严格职责分离，避免重复分析
- **MCP工具集成**: Tavily搜索 + 结构化思维工具
- **实时数据获取**: 基于最新市场信息的专业分析
- **用户优先报告**: 用户请求在前，精简结果输出

### 🤖 智能体团队
```
🎯 协调者 → 🏢 公司基本面 → 📊 财务数据 → 🏭 行业分析
       ↓
📰 市场分析 → 🗞️ 新闻舆情 → 📈 技术分析 → 💡 投资策略
```

### 📋 智能体详情
1. **🎯 Coordinator Agent**: 制定分析策略和任务分工
2. **🏢 Company Analyst**: 专注公司基本面和商业模式分析
3. **📊 Financial Analyst**: 专业财务数据和估值分析
4. **🏭 Industry Analyst**: 行业趋势和竞争格局分析
5. **📰 Market Analyst**: 市场情绪和资金流向分析
6. **🗞️ News Analyst**: 新闻舆情和重大事件分析
7. **📈 Technical Analyst**: 技术指标和价格走势分析
8. **💡 Strategy Advisor**: 整合所有分析，提供最终投资建议

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
- **Google Gemini**: 大语言模型API
- **AutoGen 0.4+**: 多智能体协作框架
- **MCP**: Model Context Protocol
- **OpenAI API**: 补充AI分析能力

### 数据源
- **AKShare**: 实时股票数据
- **Tavily Search**: 实时新闻和资讯

## 📋 数据流架构

```
实时数据源 → 数据爬取 → 数据清洗 → 数据存储
    ↓                                    ↓
Web应用界面 ← 数据分析 ← AI智能分析 ← 历史数据
                    ↓
               AutoGen多智能体协作
```

## 📚 详细文档

### 📖 用户文档
- **[🤖 AutoGen多智能体系统](autogen_graphflow/README.md)** - 详细使用指南
- **[📊 Web应用使用指南](src/web/README.md)** - 界面功能说明
- **[🔧 配置参考](config/README.md)** - 配置详细说明

### 👨‍💻 开发文档
- **[💻 API接口文档](docs/api.md)** - API接口文档
- **[🧪 策略开发指南](src/backtesting/README.md)** - 策略开发
- **[🎨 界面定制](docs/ui-customization.md)** - 界面定制指南

### 📋 参考文档
- **[AKShare文档](https://akshare.akfamily.xyz/)** - 数据获取API
- **[Streamlit文档](https://docs.streamlit.io/)** - Web应用框架
- **[AutoGen文档](https://microsoft.github.io/autogen/)** - 多智能体框架
- **[Pandas文档](https://pandas.pydata.org/docs/)** - 数据处理库
- **[Plotly文档](https://plotly.com/python/)** - 可视化库

## 🌟 核心优势

1. **🎯 专业级分析**: 结合传统量化分析和现代AI技术
2. **🤖 多智能体协作**: AutoGen 8智能体深度分析，避免认知偏差
3. **📊 可视化友好**: 现代化Web界面，数据可视化直观
4. **⚡ 实时性能**: 实时数据更新，快速响应用户需求
5. **🔧 易于扩展**: 模块化设计，支持功能定制和扩展
6. **💡 智能决策**: AI辅助投资决策，提高分析效率

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

### 已完成 ✅ (v3.0)
- [x] Web可视化界面 (v1.0)
- [x] AI智能分析 (v2.0)
- [x] AutoGen多智能体系统 (v3.0)
- [x] 实时数据集成
- [x] 完整回测系统
- [x] Launcher批处理框架

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

🔥 **核心特色**: 🤖 AutoGen多智能体协作 + 📊 实时数据分析 + 💰 AI智能投资建议

**用科技赋能投资，让AI协作更专业**