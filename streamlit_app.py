#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
🚀 智能股票分析系统 - Streamlit启动脚本
专业级A股投资分析平台

运行方式：
1. 直接运行: python streamlit_app.py
2. Streamlit运行: streamlit run streamlit_app.py
3. 指定端口: streamlit run streamlit_app.py --server.port 8501

功能特性：
- 📊 实时股票数据分析
- 💰 AI驱动的财务分析
- 📈 技术指标分析
- 💎 估值模型分析
- 🏭 行业对比分析
- 📰 新闻舆情分析
- 🌐 市场数据概览
- 🤖 综合AI分析
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 确保必要的目录存在
def ensure_directories():
    """确保项目所需的目录结构存在"""
    directories = [
        "data",
        "data/stocks",
        "data/cleaned_stocks",
        "data/ai_reports",
        "data/market_data",
        "data/index_data",
        "data/cache",
        "logs"
    ]

    for dir_path in directories:
        full_path = project_root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)

# 在导入其他模块前创建目录
ensure_directories()

# 启动检查
def check_startup_requirements():
    """检查启动所需的环境和依赖"""
    try:
        # 检查Python版本
        if sys.version_info < (3, 8):
            raise RuntimeError("需要Python 3.8或更高版本")

        # 检查必要的目录（data目录会在启动时自动创建）
        required_dirs = [
            project_root / "config",
            project_root / "src"
        ]

        for dir_path in required_dirs:
            if not dir_path.exists():
                raise RuntimeError(f"缺少必要目录: {dir_path}")

        # 检查配置文件
        config_files = [
            project_root / "config" / "config.py"
        ]

        for config_file in config_files:
            if not config_file.exists():
                print(f"⚠️  警告: 配置文件不存在 - {config_file}")

        return True

    except Exception as e:
        print(f"❌ 启动检查失败: {str(e)}")
        return False

# 执行启动检查
if not check_startup_requirements():
    print("💡 请确保项目环境配置正确后再启动应用")
    sys.exit(1)

import streamlit as st

# 应用启动信息
print("🚀 智能股票分析系统启动中...")
print(f"📂 项目路径: {project_root}")
print(f"🐍 Python版本: {sys.version.split()[0]}")

# --- 使用统一路径管理 ---

# --- 核心模块导入 ---
# 使用统一配置管理器
from config import config
from src.web.templates import ui_template_manager

# UI 组件实例
from src.web.components.company_overview_page import (
    company_overview_component,
)
from src.web.components.fundamental_analysis_page import (
    financial_analysis_component,
)
# 市场概览组件
from src.web.components.market_overview_page import (
    render_market_data,
)
# 技术分析组件
from src.web.components.technical_analysis import technical_analysis_component
# 估值分析组件
from src.web.components.valuation_page import StockValuationComponent
valuation_component = StockValuationComponent()
# 使用统一配置管理器获取应用配置
APP_INFO = {
    "name": config.app_name,
    "version": config.app_version,
    "author": "Stock Analysis Team",
    "contact": "contact@stockanalysis.com"
}

PAGE_CONFIG = {
    "page_title": "股票分析系统",
    "page_icon": "📈",
    "layout": "wide",
    "initial_sidebar_state": "expanded"
}

def get_custom_css():
    """获取自定义CSS样式"""
    return """
    <style>
    /* 全局样式 - 纯黑主题 */
    .stApp {
        background: #000000;
        color: #FFFFFF;
    }
    
    /* 确保所有容器都是黑色背景 */
    .main .block-container {
        background: #000000;
    }
    
    /* 侧边栏样式 */
    .css-1d391kg {
        background: #000000;
    }
    
    /* 标签页样式 */
    .stTabs [data-baseweb="tab-list"] {
        background: #000000;
    }
    
    /* 内容区域样式 */
    .stApp > div {
        background: #000000;
    }
    </style>
    """

# 新闻舆情组件
from src.web.components.news_page import NewsSentimentComponent
# 行业对比分析组件
from src.web.components.industry_comparison_page import IndustryComparisonComponent
# 工具/加载器 - 使用统一接口
from src.web.utils import data_loader, ai_report_manager


class StockAnalysisApp:
    """股票分析应用主类"""

    def __init__(self):
        self.app_info = APP_INFO
        self.data_loader = data_loader
        self.news_sentiment_component = NewsSentimentComponent()
        self.industry_comparison_component = IndustryComparisonComponent()
        self._setup_page()

    def _setup_page(self):
        """设置页面配置"""
        st.set_page_config(**PAGE_CONFIG)
        st.markdown(get_custom_css(), unsafe_allow_html=True)
        
        # 应用配置驱动的主题样式
        st.markdown(ui_template_manager.apply_theme_css(), unsafe_allow_html=True)
        if "selected_stock" not in st.session_state:
            # 获取可用股票列表，选择第一个作为默认股票
            available_stocks = self.data_loader.get_available_stocks()
            if available_stocks:
                st.session_state.selected_stock = available_stocks[0]
            # 如果没有可用股票，不设置默认值，让后续逻辑处理

    def run(self):
        """运行应用"""
        self._display_sidebar()
        self._display_main_content()

    def _display_sidebar(self):
        """显示现代化侧边栏"""
        # 应用标题
        app_name = self.app_info.get("app_name") or "股票分析系统"
        app_version = self.app_info.get("app_version") or "2.0.0"
        st.sidebar.markdown(
            f'''<div class="sidebar-header">{app_name}</div>
            <div style="text-align: center; color: #B0B0B0; margin-bottom: 2rem;">
                版本 {app_version}
            </div>''',
            unsafe_allow_html=True
        )

        # 股票选择器
        available_stocks = self.data_loader.get_available_stocks()
        if not available_stocks:
            st.sidebar.error("❌ 没有找到可用的股票数据")
            # 添加重试按钮
            if st.sidebar.button("🔄 重新扫描股票数据", key="reload_stocks"):
                st.rerun()
            return
        

        if st.session_state.selected_stock not in available_stocks:
            st.session_state.selected_stock = available_stocks[0]

        default_index = available_stocks.index(st.session_state.selected_stock)

        # 美化的股票选择器
        st.sidebar.markdown("""
        <div style="margin-bottom: 1rem;">
            <div style="color: #FFD700; font-weight: 700; font-size: 1.1rem; margin-bottom: 0.5rem;">
                🎯 选择股票
            </div>
        </div>
        """, unsafe_allow_html=True)

        selected_stock = st.sidebar.selectbox(
            "选择股票",
            available_stocks,
            index=default_index,
            format_func=lambda x: f"📈 {x} - {self.data_loader.get_stock_name(x) or '未知'}",
            label_visibility="collapsed",
            key="stock_selector",
        )

        if st.session_state.selected_stock != selected_stock:
            st.session_state.selected_stock = selected_stock
            # 清除缓存 - 统一加载器使用lru_cache
            ai_report_manager.clear_cache()
            st.rerun()

        # 系统信息和帮助
        st.sidebar.markdown("---")
        st.sidebar.markdown("### ℹ️ 系统信息")
        st.sidebar.info(f"版本: {self.app_info.get('app_version', '2.0.0')}")

        # 快速操作按钮
        st.sidebar.markdown("### 🚀 快速操作")
        col1, col2 = st.sidebar.columns(2)
        with col1:
            if st.button("🔄", help="刷新页面", key="refresh_page"):
                st.rerun()
        with col2:
            if st.button("📊", help="重新加载数据", key="reload_data"):
                ai_report_manager.clear_cache()
                st.rerun()

        # 使用说明
        st.sidebar.markdown("### 📖 使用说明")
        with st.sidebar.expander("启动方式", expanded=False):
            st.code("""
# 方式1: 直接运行
python streamlit_app.py

# 方式2: Streamlit运行
streamlit run streamlit_app.py

# 方式3: 指定端口
streamlit run streamlit_app.py --server.port 8501
            """, language="bash")

        with st.sidebar.expander("功能介绍", expanded=False):
            st.markdown("""
            **📊 实时股票数据分析**
            - 实时股价和涨跌幅显示
            - 交互式图表和技术指标

            **💰 AI驱动财务分析**
            - 4个专业财务分析Tab
            - 智能财务健康诊断

            **📈 技术指标分析**
            - 多种技术分析工具
            - K线图和成交量分析

            **💎 估值模型分析**
            - 多种估值方法
            - 投资建议和风险评估

            **🏭 行业对比分析**
            - 同行业公司对比
            - 行业地位分析

            **📰 新闻舆情分析**
            - 实时新闻监控
            - 情感分析

            **🌐 市场数据概览**
            - 板块资金流向
            - 市场热点追踪

            **🤖 综合AI分析**
            - 全面投资分析报告
            - 智能投资建议
            """)

        # 技术支持
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 🛠️ 技术支持")
        st.sidebar.caption("智能股票分析系统 v2.0")
        st.sidebar.caption("专业级A股投资分析平台")

    def _display_main_content(self):
        """显示现代化主要内容"""
        # 首先检查是否有可用股票
        available_stocks = self.data_loader.get_available_stocks()
        if not available_stocks:
            st.markdown("""
            <div style="background: rgba(255,68,68,0.1); border: 2px solid #ff4444; border-radius: 10px; padding: 1rem; text-align: center;">
                <div style="color: #ff4444; font-size: 1.1rem; font-weight: 700; margin-bottom: 0.5rem;">
                    ❌ 没有找到可用的股票数据
                </div>
                <div style="color: #E0E0E0;">
                    请在 data/cleaned_stocks/ 目录下放置股票数据文件。
                </div>
            </div>
            """, unsafe_allow_html=True)
            return
        
        # 确保选中的股票在可用列表中
        if st.session_state.selected_stock not in available_stocks:
            st.session_state.selected_stock = available_stocks[0]
        
        # 数据加载状态
        with st.spinner(f"🔄 正在加载 {st.session_state.selected_stock} 的数据..."):
            data = self.data_loader.load_stock_data(st.session_state.selected_stock)

        if not data:
            st.markdown(f"""
            <div style="background: rgba(255,68,68,0.1); border: 2px solid #ff4444; border-radius: 10px; padding: 1rem;">
                <div style="color: #ff4444; font-size: 1.1rem; font-weight: 700; margin-bottom: 0.5rem;">
                    ❌ 数据加载失败
                </div>
                <div style="color: #E0E0E0;">
                    无法加载股票 {st.session_state.selected_stock} 的数据，请确保数据文件存在。
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # 添加重试按钮
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                if st.button("🔄 重新加载数据", key="reload_main_data", use_container_width=True):
                    st.rerun()
            return
            
        # 成功加载提示已删除

        # 获取当前股票的关键数据
        price_change = 0
        if 'historical_quotes' in data and not data['historical_quotes'].empty:
            prices = data['historical_quotes']['收盘']
            if len(prices) > 1:
                price_change = (prices.iloc[-1] - prices.iloc[-2]) / prices.iloc[-2] * 100
        
        price_color = ui_template_manager.colors['chart_up'] if price_change >= 0 else ui_template_manager.colors['chart_down']
        price_arrow = '📈' if price_change >= 0 else '📉'
        
        # 桌面端标题样式
        st.markdown(f"""
            <div style="text-align: center; margin-bottom: 2rem;">
                <h1 style="background: linear-gradient(90deg, #FFD700 0%, #FFFFFF 50%, #FFD700 100%);
                           -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                           background-clip: text; font-size: 2.8rem; font-weight: 800;
                           text-shadow: 0 0 30px rgba(255, 215, 0, 0.3);
                           animation: titleGlow 3s ease-in-out infinite alternate;">
                    🚀 智能股票分析系统
                </h1>
                <div style="display: flex; justify-content: center; align-items: center; gap: 2rem; margin-top: 0.5rem;">
                    <div style="background: rgba(30,30,40,0.9); padding: 0.5rem 1.5rem; border-radius: 20px; border: 1px solid rgba(255, 215, 0, 0.3);">
                        <span style="color: #FFD700; font-size: 1.1rem; font-weight: 700;">{st.session_state.selected_stock or '未知'}</span>
                        <span style="color: {price_color}; font-size: 1.2rem; font-weight: 700; margin-left: 0.5rem;">{price_arrow} {price_change:+.2f}%</span>
                    </div>
                    <div style="background: rgba(30,30,40,0.9); padding: 0.5rem 1.5rem; border-radius: 20px; border: 1px solid rgba(255, 215, 0, 0.3);">
                        <span style="color: #B0B0B0; font-size: 1rem;">实时数据</span>
                        <span style="color: #00ff88; font-size: 1rem; margin-left: 0.5rem;">●</span>
                    </div>
                </div>
                <p style="color: #B0B0B0; font-size: 1rem; margin-top: 0.5rem;">
                    基于智能算法的专业投资分析平台
                </p>
            </div>
            
            <style>
            @keyframes titleGlow {{
                from {{ filter: brightness(1); }}
                to {{ filter: brightness(1.2); }}
            }}
            </style>
            """, unsafe_allow_html=True)
        
        # 标签页设计
        tab_names = [
            "🏢 公司概况",
            "💰 财务分析",
            "📈 技术分析",
            "💎 估值分析",
            "🏭 行业对比",
            "📰 新闻舆情",
            "🌐 市场数据",
            "🤖 综合分析"
        ]

        # 创建标签页
        tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs(tab_names)

        with tab1:
            company_overview_component.render(data)

        with tab2:
            financial_analysis_component.render(data)

        with tab3:
            technical_analysis_component.render(data)

        with tab4:
            valuation_component.render(data)

        with tab5:
            self.industry_comparison_component.render(data)

        with tab6:
            self.news_sentiment_component.render(data)

        with tab7:
            render_market_data()

        with tab8:
            # 新增：综合分析页面 - 直接显示分析报告
            st.markdown("## 🤖 综合分析")

            # 获取股票代码
            stock_code = data.get("stock_code", "未知") if data else "未知"

            # 显示综合分析报告 - comprehensive.md
            try:
                reports = ai_report_manager.load_reports(stock_code, "stock")

                if reports and "comprehensive.md" in reports:
                    content = reports["comprehensive.md"]
                    if content.startswith("❌"):
                        st.warning(f"🤖 综合分析报告暂未生成")
                    else:
                        st.markdown(content)
                else:
                    st.info("🤖 综合分析报告暂未加载")

            except Exception as e:
                st.warning(f"🤖 综合分析报告加载失败")
                st.caption(f"错误信息: {str(e)}")

def main():
    """主函数 - 带错误处理的应用启动"""
    try:
        print("✅ 环境检查通过，正在启动应用...")
        app = StockAnalysisApp()
        app.run()
    except KeyboardInterrupt:
        print("\n👋 用户中断应用")
    except ImportError as e:
        print(f"❌ 模块导入错误: {str(e)}")
        print("💡 请检查是否安装了所需依赖: pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 应用启动失败: {str(e)}")
        print("💡 请检查配置文件和数据目录")
        sys.exit(1)

if __name__ == "__main__":
    main()
