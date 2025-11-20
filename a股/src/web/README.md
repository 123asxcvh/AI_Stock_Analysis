# 🌐 Web应用模块

基于Streamlit的A股分析系统Web界面。

## 📋 功能概述

### 🏠 核心页面
- **首页**: 系统概览和快速导航
- **公司概况**: 公司基本信息和核心指标
- **技术分析**: 技术指标和K线图表
- **基本面分析**: 财务数据和估值分析
- **行业对比**: 同行业公司横向对比
- **估值分析**: 多维度估值模型
- **投资建议**: AI生成的投资建议

## 🏗️ 模块结构

```
src/web/
├── app.py                    # 主应用入口
├── components/              # 页面组件
│   ├── company_overview_page.py
│   ├── technical_analysis.py
│   ├── fundamental_analysis_page.py
│   ├── industry_comparison_page.py
│   ├── valuation_page.py
│   └── investment_recommendation_page.py
├── utils/                   # 工具函数
│   ├── unified_utils.py     # 统一工具
│   └── common.py           # 通用函数
└── templates/              # UI模板
    └── ui_templates.py     # 模板管理器
```

## 🚀 快速启动

```bash
# 使用启动脚本
python src/launchers/scripts/run_app.py

# 或直接运行
streamlit run src/web/app.py --server.port 8501
```

访问 http://localhost:8501 查看应用。

## 🎨 界面特性

### 📱 响应式设计
- 支持桌面和移动端
- 自适应布局
- 触摸友好交互

### 🌙 主题系统
- 深色主题 (默认)
- 金色强调配色
- 专业的金融界面风格

### 📊 图表系统
- 交互式K线图
- 技术指标图表
- 财务数据可视化
- 行业对比图表

## 🔧 技术实现

### 核心技术栈
- **Streamlit**: Web框架
- **Plotly**: 图表库
- **Pandas**: 数据处理
- **NumPy**: 数值计算

### 数据流
```
数据源 → 清洗处理 → 组件渲染 → 用户界面
    ↓
AI分析 → 智能建议 → 决策支持
```

### 缓存机制
- 数据加载缓存
- AI分析缓存
- 图表渲染缓存

## 📝 开发指南

### 添加新页面

1. 在 `src/web/components/` 创建新组件文件
2. 继承基础组件类
3. 实现 `render()` 方法
4. 在主应用中注册页面

### 自定义图表

```python
from src.web.templates import ui_template_manager
import plotly.graph_objects as go

def create_custom_chart(data):
    fig = go.Figure()
    # 添加图表内容
    return fig
```

### 样式定制

编辑 `src/web/templates/ui_templates.py` 中的主题配置。

## 🐛 常见问题

### Q: 页面加载慢？
A: 检查数据文件大小，考虑使用分页或懒加载。

### Q: 图表不显示？
A: 确认数据格式正确，检查浏览器控制台错误信息。

### Q: AI分析无结果？
A: 检查API配置，确认数据完整性。

## 📚 相关文档

- [用户使用指南](../../USER_GUIDE.md)
- [回测系统文档](../backtesting/README.md)
- [配置说明](../../config/README.md)

---

*Web应用模块 v3.0*
