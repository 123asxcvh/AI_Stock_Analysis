# A股智能分析系统

🤖 **基于AutoGen 0.4+的专业股票分析系统**

采用8个AI智能体顺序协作，职责分离，提供全面、专业、深入的投资分析报告。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![AutoGen 0.4+](https://img.shields.io/badge/AutoGen-0.4+-green.svg)](https://microsoft.github.io/autogen/)

---

## 🚀 核心特性

- ✅ **智能体职责分离**：每个智能体专注专业领域，避免重复分析
- ✅ **严格顺序执行**：8个智能体按严格顺序工作，确保分析深度
- ✅ **精简报告输出**：只保存每个智能体的最终结果，用户请求优先显示
- ✅ **最新API支持**：基于AutoGen 0.4+ GraphFlow架构
- ✅ **MCP工具集成**：支持Tavily搜索和结构化思维

---

## 🏁 快速开始

### 安装依赖
```bash
pip install -r requirements.txt
```

### 配置API密钥
```bash
# 方法1：编辑配置文件
vim config/unified_config.json

# 方法2：使用环境变量
export OPENAI_API_KEY="your-openai-api-key"
export KIMI_API_KEY="your-kimi-api-key"
```

### 运行分析
```bash
# 分析贵州茅台
python main.py 600519

# 分析平安银行
python main.py 000001

# 测试系统配置
python main.py --test
```

---

## 🤖 智能体架构

### 严格职责分离系统

```
🎯 协调者 → 🏢 公司基本面 → 📊 财务数据 → 🏭 行业分析
       ↓
📰 市场分析 → 🗞️ 新闻舆情 → 📈 技术分析 → 💡 投资策略
```

### 智能体详情

| 智能体 | 职责 | 绝不越界 | 输出 |
|--------|------|----------|------|
| 🎯 **协调者** | 制定分析策略框架 | 不进行具体分析 | 任务分工清单 |
| 🏢 **公司分析师** | 商业模式、竞争优势 | 不分析财务、技术面 | 纯基本面分析 |
| 📊 **财务分析师** | 财务报表、估值分析 | 不分析基本面、市场 | 专业财务数据 |
| 🏭 **行业分析师** | 行业趋势、竞争格局 | 不分析具体公司 | 宏观行业分析 |
| 📰 **市场分析师** | 市场情绪、资金流向 | 不进行技术分析 | 市场层面数据 |
| 🗞️ **新闻分析师** | 新闻事件、舆情环境 | 不分析股价走势 | 新闻舆情分析 |
| 📈 **技术分析师** | 技术指标、价格走势 | 不分析基本面 | 专业技术分析 |
| 💡 **策略顾问** | 整合分析、投资建议 | 不重复具体分析 | 最终投资策略 |

---

## 📋 分析流程

### 1. 用户请求 → 协调者
用户输入分析需求，协调者制定分析策略和任务分工

### 2. 专业分析顺序执行
```
公司基本面 → 财务数据 → 行业分析 → 市场分析 → 新闻舆情 → 技术分析
```

### 3. 策略顾问整合
整合前面7个专业分析师的结果，提供最终投资建议

### 4. 报告生成
用户请求优先显示，只保存各智能体的最终输出

---

## 📄 报告输出格式

```markdown
# 股票分析报告

**生成时间**: 2025-11-17 20:13:07
**股票代码**: 600519

## 用户请求
```
请对股票代码 600519 进行全面的投资分析...
```

---

## 智能体分析结果

### 🎯 协调者 (coordinator_agent)
[分析策略框架和任务分工]

### 🏢 公司基本面分析 (company_analyst)
[纯粹的公司基本面专业分析]

### 📊 财务数据分析 (financial_analyst)
[专业财务指标和估值分析]

### 💡 投资策略顾问 (strategy_advisor)
[最终投资建议：评级、目标价、操作策略]
TERMINATE
```

---

## 🛠️ MCP工具集成

### 搜索工具
- **Tavily搜索**：获取最新的公司、行业、市场信息
- **智能体工具映射**：不同智能体配置不同搜索策略

### 思维工具
- **Sequential Thinking**：结构化思维分析
- **协调者专用**：制定更专业化的分析策略

### 工具配置
```json
{
  "agent_tool_mapping": {
    "coordinator_agent": ["tavily", "sequentialthinking"],
    "company_analyst": ["tavily"],
    "financial_analyst": ["tavily"],
    "industry_analyst": ["tavily"],
    "market_analyst": ["tavily"],
    "news_analyst": ["tavily"],
    "technical_analyst": ["tavily"],
    "strategy_advisor": ["tavily"]
  }
}
```

---

## ⚡ 性能特点

- **分析时间**：3-10分钟 (根据股票复杂度)
- **智能体数量**：8个专业智能体
- **并发模式**：严格顺序执行 (避免混乱)
- **报告格式**：Markdown，便于阅读分享
- **结果保存**：`reports/`目录自动生成

---

## 💡 使用示例

```bash
# 分析贵州茅台
python main.py 600519

# 分析平安银行
python main.py 000001

# 批量分析
python main.py 600519 000001 000002

# 测试系统配置
python main.py --test
```

---

## 📊 输出示例

```bash
📋 AutoGen 0.4+ 股票分析系统 (8智能体顺序执行)
🚀 开始分析: 600519
✅ 创建智能体: coordinator_agent - 协调者
✅ 创建智能体: company_analyst - 公司基本面分析师
...
✅ 完整顺序GraphFlow工作流创建 (8个智能体)
🔄 开始8智能体顺序分析...

---------- coordinator_agent ----------
分析贵州茅台(600519)的投资策略框架和任务分工...

---------- company_analyst ----------
专注公司基本面分析：商业模式、护城河...

---------- strategy_advisor ----------
基于前面7个分析师的专业分析，提供最终投资建议：
**投资评级：持有**
**目标价区间：1700-1900元**
**投资逻辑：品牌护城河稳固，估值合理**
TERMINATE

✅ 分析完成！智能体数量: 8
📁 报告已保存到: reports/股票分析报告_600519_20251117_201307.md
```

---

## 🔧 系统要求

### 前置要求
- Python 3.8+
- OpenAI API密钥 或 Kimi API密钥
- 网络连接
- MCP服务器支持

### 推荐配置
- **模型**：kimi-k2-thinking-turbo (推荐) 或 gpt-4o-mini
- **内存**：8GB+ (MCP工具需要)
- **存储**：500MB+ (MCP日志和报告文件)

### 依赖包
- `autogen-agentchat` - 多智能体框架
- `autogen-ext` - 扩展工具支持
- `mcp` - Model Context Protocol
- 其他依赖见 `requirements.txt`

---

## 🎯 核心优势

1. **彻底解决职责重叠**：智能体严格分工，消除重复分析
2. **专业化深度**：每个智能体专注特定领域，提供专业分析
3. **流程清晰可控**：严格顺序执行，信息单向传递
4. **输出精简高效**：只保留最有价值的最终结果
5. **实时数据支持**：MCP工具集成，获取最新市场信息
6. **用户体验友好**：用户需求优先显示，结果一目了然

---

## 📈 技术架构

### 核心技术栈
- **AutoGen 0.4+**：多智能体协作框架
- **GraphFlow**：工作流编排
- **MCP**：Model Context Protocol，工具集成框架
- **Tavily搜索**：实时数据获取
- **Sequential Thinking**：结构化思维分析

### 系统架构图
```
用户请求 → 协调者 → [专业智能体顺序执行] → 策略顾问 → 报告生成
                ↓
            MCP工具集成
         (搜索 + 思维工具)
```

### 设计原则
- **单一职责**：每个智能体只做一件事
- **松耦合**：智能体之间通过消息传递
- **可扩展**：易于添加新的智能体和工具
- **可观测**：完整的执行过程记录

---

## 🔮 发展路线

### 已完成 ✅
- [x] 8个智能体职责分离
- [x] 严格顺序执行流程
- [x] 精简报告输出
- [x] MCP工具集成
- [x] 用户请求优先显示

### 计划中 📋
- [ ] Web界面支持
- [ ] 批量股票分析
- [ ] 历史分析对比
- [ ] 自定义智能体
- [ ] 更多数据源集成
- [ ] 报告可视化

---

## 📝 更新日志

### v3.0 (当前版本)
- ✨ **智能体职责分离**：彻底解决重复分析问题
- ✨ **报告格式优化**：用户请求优先，结果精简
- ✨ **MCP工具集成**：实时搜索和结构化思维
- ✨ **最新API**：基于AutoGen 0.4+架构

### v2.0
- 🔧 8智能体顺序执行架构
- 🔧 GraphFlow工作流编排
- 🔧 基础MCP集成

### v1.0
- 🔧 基础智能体框架
- 🔧 简单报告生成

---

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

### 开发环境设置
```bash
# 克隆项目
git clone <repository-url>
cd autogen_graphflow

# 安装依赖
pip install -r requirements.txt

# 运行测试
python main.py --test
```

---

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

---

## 📞 联系方式

- 🐛 **Bug报告**：请提交Issue
- 💡 **功能建议**：欢迎讨论
- 📧 **技术交流**：欢迎PR

---

**⭐ 如果这个项目对您有帮助，请给个星标支持！**