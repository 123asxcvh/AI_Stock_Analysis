# 🚀 A股智能分析系统

基于z哥少妇战法的智能股票分析系统，集成AI分析、技术分析、回测系统等功能。

## 📋 项目概述

本项目是一个完整的A股市场分析系统，基于知名投资博主z哥的"少妇战法"投资理念构建。系统集成了数据爬取、技术分析、AI智能分析、回测系统等功能，为投资者提供全方位的股票分析支持。

### 🎯 核心特性

- **Z哥少妇战法**: 基于z哥投资理念的完整技术分析系统
- **AI驱动分析**: 集成Google Gemini API进行智能分析
- **极简回测系统**: 简化但功能完整的策略回测框架
- **异步处理**: 支持大规模并发分析
- **智能缓存**: 6个核心财务文件缓存机制
- **模块化设计**: 清晰的代码结构，易于维护扩展

## 🏗️ 项目结构

```
a股/
├── src/                    # 核心源代码
│   ├── backtesting/        # 回测系统 (v3.0)
│   ├── web/               # Web应用界面
│   ├── ai_analysis/       # AI分析模块
│   ├── crawling/          # 数据爬取
│   ├── cleaning/          # 数据清洗
│   └── launchers/         # 启动脚本
├── data/                   # 数据存储目录
├── config/                 # 配置文件
├── autogen_graphflow/      # AutoGen工作流
└── zzz/                   # 策略文件
```

## 🚀 快速开始

### 1. 环境准备

```bash
# 安装依赖
pip install -r requirements.txt

# 配置API密钥
cp config/unified_config.json.example config/unified_config.json
# 编辑配置文件，添加你的Gemini API密钥
```

### 2. 数据爬取

```bash
# 爬取股票数据
python src/launchers/scripts/run_data_pipeline_async.py

# 爬取市场数据
python src/launchers/scripts/run_market_data_pipeline_async.py

# 爬取指数数据
python src/launchers/scripts/run_index_pipeline_async.py
```

### 3. AI分析

```bash
# 个股AI分析
python src/launchers/scripts/run_data_ai_pipeline_async.py

# 市场AI分析
python src/launchers/scripts/run_market_ai_pipeline_async.py
```

### 4. 回测系统

```bash
# 运行批量回测
python src/backtesting/launchers/run_batch_backtest.py

# 运行参数优化
python src/backtesting/launchers/run_param_search.py

# 命令行回测
python -m src.backtesting.core.tester 000001 --strategy "MACD策略"
```

### 5. 启动Web应用

```bash
# 🚀 推荐方式：使用新的启动脚本
python streamlit_app.py

# 或使用Streamlit命令
streamlit run streamlit_app.py --server.port 8501

# 传统方式（仍然支持）
python src/launchers/scripts/run_app.py
streamlit run src/web/app.py --server.port 8501
```

#### 🎯 新启动脚本特性
- ✅ **自动环境检查** - Python版本、目录结构、配置文件
- ✅ **智能错误处理** - 友好的错误提示和解决建议
- ✅ **启动信息显示** - 项目路径、Python版本等系统信息
- ✅ **内置帮助文档** - 侧边栏包含完整使用说明
- ✅ **快捷操作按钮** - 一键刷新、数据重载等功能
- ✅ **响应式界面** - 现代化深色主题设计

## 📊 核心功能

### 技术分析系统
- **B1买点**: 基于周J和月J的多周期共振左侧策略
- **B2买点**: 基于日J、MACD、20日均线的右侧策略
- **3/4阴量法**: 识别假突破的重要工具
- **价格过滤机制**: 智能B1过滤，避免追高

### AI智能分析 (v3.0)
- **个股分析**: 基本面、技术面、新闻舆情分析
- **市场分析**: 宏观市场、行业分析、市场情绪
- **综合分析**: 多维度深度分析报告
- **智能缓存**: 6个核心财务文件缓存机制

### 极简回测系统 (v3.0)
- **内置策略**: 10个常用策略开箱即用
- **自动可视化**: 权益曲线、交易点、回撤分析
- **批量测试**: 支持多策略、多股票批量分析
- **命令行工具**: 完整的CLI支持

## 🎯 投资理念

### 六字箴言
- **不追**: 遵守交易纪律
- **不动**: 涨了卖一半会有问题，最简单就是不动
- **不慌**: 心态控制

### 核心策略
- **捡钱策略**: 在J值大负值时从容进场
- **右侧买入法**: 强势股盘中回调建仓
- **只亏一根K线**: 严格止损，最多亏1.5根K线

## 📚 详细文档

### 📖 文档中心
- **[📚 文档索引](DOCUMENTATION_INDEX.md)** - 完整文档导航中心
- **[📖 用户指南](USER_GUIDE.md)** - 详细使用教程
- **[📊 项目状态](PROJECT_STATUS.md)** - 当前项目状态报告

### 🔧 模块文档
- [回测系统](src/backtesting/README.md) - 极简回测框架 v3.0
- [Web应用](src/web/README.md) - Streamlit界面
- [AI分析](src/ai_analysis/README.md) - 智能分析模块
- [组件库](src/web/components/README.md) - Web组件
- [配置说明](config/README.md) - 配置文件

### 👨‍💻 开发文档
- [Claude开发指南](CLAUDE.md) - 面向AI助手的开发指南
- [AutoGen工作流](autogen_graphflow/README.md) - 代理工作流系统
- [投资理念](z哥投资理念深度解析.md) - z哥投资理念详解

## ⚙️ 配置说明

主要配置文件：
- `config/unified_config.json` - 统一配置文件
- `config/strategy_configs.py` - 策略配置
- `config/backtesting_default_config.json` - 回测配置

## 🤝 贡献指南

1. Fork 项目
2. 创建特性分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## ⚠️ 免责声明

本项目仅供学习和研究使用，不构成投资建议。投资有风险，入市需谨慎。使用本系统进行实际投资决策的风险由用户自行承担。

---

*基于z哥少妇战法的智能股票分析系统 - 让投资更科学，让决策更理性*