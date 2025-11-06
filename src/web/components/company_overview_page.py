#!/usr/bin/env python

"""
公司概况组件 - 股票App风格 - 简化版
显示公司基本信息、主营业务构成等，采用现代化UI设计
"""

from typing import Any, Dict
import pandas as pd
import streamlit as st

# 使用新的可视化配置管理器
from src.web.templates import ui_template_manager

def safe_float(val, default=0.0):
    """安全转换为浮点数"""
    try:
        return float(val) if val is not None else default
    except (ValueError, TypeError):
        return default


class CompanyOverviewComponent:
    """公司概况组件类 - 股票App风格"""

    def __init__(self):
        self.ui_manager = ui_template_manager
        self.colors = self.ui_manager.colors
        self._fallback_info_shown = False  # 重置回退信息显示标记

    def extract_company_info(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """提取公司信息"""
        company_info = {}

        # 处理键值对格式的公司概况数据
        if "company_profile" in data and data["company_profile"] is not None:
            profile = data["company_profile"]
            if isinstance(profile, pd.DataFrame) and not profile.empty:
                # 检查是否是键值对格式（字段名/字段值）
                if '字段名' in profile.columns and '字段值' in profile.columns:
                    company_info = dict(zip(profile['字段名'], profile['字段值']))
                # 检查是否是标准格式（字段名作为列名）
                elif len(profile) > 0:
                    # 如果只有一行，将列名作为键，第一行数据作为值
                    if len(profile) == 1:
                        company_info = profile.iloc[0].to_dict()
                    else:
                        # 如果有多行，取第一行
                        company_info = profile.iloc[0].to_dict()
            elif isinstance(profile, dict):
                company_info = profile
            elif hasattr(profile, 'to_dict'):
                company_info = profile.to_dict()

        # 如果没有找到公司信息，使用默认值
        if not company_info:
            stock_code = data.get("stock_code", "")
            company_info = {
                "公司名称": f"股票{stock_code}",
                "A股简称": f"{stock_code}",
                "A股代码": stock_code,
                "成立日期": "未知",
                "所属行业": "未知",
                "主营业务": "未知",
                "经营范围": "未知"
            }

        return company_info

    def display_empty_message(self, message: str):
        """显示空消息"""
        st.info(message)

    def display_bid_ask_analysis(self, data: Dict[str, Any] = None):
        """显示盘口数据分析"""
        self.ui_manager.section_header("盘口数据分析", "📊")
        if data is None or "bid_ask" not in data:
            st.info("盘口数据暂未加载")
            return
        # 调用实际的分析方法
        self._display_bid_ask_analysis_impl(data)

    def create_ai_report_section(self, stock_code: str, analysis_type: str = None):
        """创建AI报告部分 - 只显示company_profile报告"""
        self.ui_manager.section_header("AI分析报告", "🤖")

        try:
            # 导入AI报告管理器
            from src.web.utils.unified_utils import ai_report_manager

            # 加载AI报告
            reports = ai_report_manager.load_reports(stock_code, "stock")

            if reports and "company_profile.md" in reports:
                # 只显示company_profile报告
                content = reports["company_profile.md"]
                if content.startswith("❌"):
                    st.error(f"🤖 公司概况AI分析失败: {content}")
                else:
                    st.markdown("##### 🤖 公司概况AI分析")
                    st.markdown(content)
            else:
                st.info("🤖 公司概况AI分析报告暂未加载")

        except Exception as e:
            st.error(f"加载公司概况AI报告时出错: {str(e)}")
            st.info("🤖 公司概况AI分析报告暂未加载")

    def render(self, data: Dict[str, Any]):
        """渲染公司概况页面 - 使用基类简化"""
        # 1. 公司基本信息
        self.display_company_basic_info(data)
        
        # 2. 盘口数据分析
        self.display_bid_ask_analysis(data)
        
        # 3. 主营业务构成
        self.display_business_composition_section(data)
        
        # 4. AI分析报告
        stock_code = data.get("stock_code", "未知")
        self.create_ai_report_section(stock_code, "company_overview")

    def display_company_basic_info(self, data: Dict[str, Any]):
        """显示公司基本信息 - 使用基类简化"""
        company_data = self.extract_company_info(data)
        if not company_data:
            return
        
        self.ui_manager.section_header("公司概况", "🏢")
        
        # 公司名称、A股简称和股票代码
        company_name = company_data.get("公司名称", "未知公司")
        stock_name = company_data.get("A股简称", "")
        stock_code = company_data.get("A股代码", "").zfill(6) if company_data.get("A股代码") else ""
        
        st.markdown(f"""
        <div style="display: flex; align-items: baseline; gap: 15px; margin-bottom: 0;">
            <h2 style="margin: 0; color: #ffffff; font-size: 2.2em;">{company_name}</h2>
            <h2 style="margin: 0; color: #ffffff; font-size: 2.2em;">{stock_name}</h2>
            <span style="font-size: 1.8em; color: #ffffff;">{stock_code}</span>
        </div>
        """, unsafe_allow_html=True)
        
        # 基本信息
        st.markdown(f"""
        <div style="color: #ffffff; font-size: 1.1em; line-height: 1.6; margin: 0;">
            <div style="margin-bottom: 8px;"><strong>成立日期:</strong> {company_data.get('成立日期', '')}</div>
            <div style="margin-bottom: 8px;"><strong>所属行业:</strong> {company_data.get('所属行业', '')}</div>
            <div><strong>主营业务:</strong> {company_data.get('主营业务', '')}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # 经营范围
        business_scope = company_data.get("经营范围", "")
        if business_scope:
            st.markdown(f"""
            <div style="color: #888888; font-size: 0.75em; margin-top: 8px; line-height: 1.3;">
                <strong>经营范围:</strong> {business_scope}
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")

    def display_business_composition_section(self, data: Dict[str, Any]):
        """显示主营业务构成部分 - 简化版"""
        self.ui_manager.section_header("主营业务构成", "💼")
        
        if "main_business_composition" not in data or data["main_business_composition"] is None:
            st.info("未找到主营业务构成数据")
            return

        df = data["main_business_composition"]
        
        # 动态获取可用的分类类型
        available_categories = df["分类类型"].unique()
        if len(available_categories) == 0:
            self.display_empty_message("暂无分类数据")
            return
        
        # 分类图标映射
        category_icons = {
            "按行业分类": "🏭",
            "按产品分类": "📈", 
            "按地区分类": "🌍"
        }
        
        # 固定排序：产品、行业、地区
        preferred_order = ["按产品分类", "按行业分类", "按地区分类"]
        ordered_categories = [cat for cat in preferred_order if cat in available_categories]
        ordered_categories.extend([cat for cat in available_categories if cat not in ordered_categories])
        
        # 创建tab
        tab_labels = [f"{category_icons.get(cat, '📊')} {cat}" for cat in ordered_categories]
        business_tabs = st.tabs(tab_labels)
        
        # 为每个分类显示内容
        for i, category in enumerate(ordered_categories):
            with business_tabs[i]:
                if category == "按行业分类":
                    self.display_industry_composition({"main_business_composition": df}, "industry")
                elif category == "按产品分类":
                    self.display_product_composition({"main_business_composition": df}, "product")
                elif category == "按地区分类":
                    self.display_region_composition({"main_business_composition": df}, "region")
                else:
                    self.display_generic_composition({"main_business_composition": df}, category)

    def get_latest_business_data(self, business_data, category_type, show_fallback_info=True):
        """获取最新的业务构成数据 - 简化版"""
        if "main_business_composition" not in business_data:
            return pd.DataFrame()

        df = business_data["main_business_composition"]

        # 数据已通过数据加载器设置日期索引
        latest_date = df.index.max()
        latest_df = df[df.index == latest_date]
        category_data = latest_df[latest_df["分类类型"] == category_type]

        # 如果最新数据中没有指定分类类型的数据，尝试回退到2024年12月31日
        if category_data.empty:
            fallback_date = pd.to_datetime("2024-12-31")
            fallback_df = df[df.index == fallback_date]
            if not fallback_df.empty and show_fallback_info:
                # 只在第一次调用时显示这个信息
                if not hasattr(self, '_fallback_info_shown'):
                    st.info("📅 使用2024年12月31日的数据（最新数据不可用）")
                    self._fallback_info_shown = True
                return fallback_df[fallback_df["分类类型"] == category_type]

        return category_data

    def _convert_to_composition_dict(self, data: pd.DataFrame) -> Dict[str, float]:
        """将DataFrame转换为构成字典的通用方法"""
        composition_dict = {}
        try:
            for _, row in data.iterrows():
                composition_name = row.get('主营构成', '未知')
                revenue = row.get('主营收入', 0)
                if pd.notna(revenue) and revenue > 0:
                    composition_dict[composition_name] = float(revenue)
        except Exception:
            pass
        return composition_dict

    def _display_composition_with_chart(self, business_data: Dict[str, Any], category_type: str, title: str, show_trend: bool = True):
        """通用的构成显示方法"""
        data = self.get_latest_business_data(business_data, category_type, show_fallback_info=False)

        if data.empty:
            st.info(f"暂无{category_type}数据")
            return

        composition_dict = self._convert_to_composition_dict(data)

        if composition_dict:
            fig = self.ui_manager.financial_pie(composition_dict, title)
            if fig:
                chart_key = f"{category_type.replace('按', '').replace('分类', '')}_pie_chart"
                st.plotly_chart(fig, use_container_width=True, key=chart_key)

            if show_trend:
                st.markdown(f"#### 📊 {category_type}收入趋势")
                self._display_business_composition_bar_chart(business_data, category_type)
        else:
            st.info(f"暂无有效的{category_type}数据")

    def display_product_composition(self, business_data: Dict[str, Any], mode: str = None):
        """显示产品构成"""
        self._display_composition_with_chart(business_data, "按产品分类", "产品收入构成")

    def display_region_composition(self, business_data: Dict[str, Any], mode: str = None):
        """显示地区构成"""
        self._display_composition_with_chart(business_data, "按地区分类", "地区收入构成")

    def display_industry_composition(self, business_data: Dict[str, Any], mode: str = None):
        """显示行业构成"""
        industry_data = self.get_latest_business_data(business_data, "按行业分类")

        # 如果没有行业分类数据，使用产品分类数据作为替代
        if industry_data.empty:
            product_data = self.get_latest_business_data(business_data, "按产品分类", show_fallback_info=False)
            if not product_data.empty:
                st.info("📊 注：当前数据源未提供行业分类信息，以下显示产品分类数据作为参考")
                self._display_composition_with_chart(business_data, "按产品分类", "按产品分类的收入构成", show_trend=False)
            else:
                st.info("暂无行业分类和产品分类数据")
            return

        # 正常显示行业分类数据
        self._display_composition_with_chart(business_data, "按行业分类", "行业收入构成")

    def display_generic_composition(self, business_data: Dict[str, Any], category_type: str):
        """显示通用分类构成"""
        data = self.get_latest_business_data(business_data, category_type, show_fallback_info=False)

        if not data.empty:
            composition_dict = self._convert_to_composition_dict(data)
            if composition_dict:
                fig = self.ui_manager.financial_pie(composition_dict, f"{category_type}的收入构成")
                chart_key = f"generic_{category_type}_pie_chart"
                st.plotly_chart(fig, use_container_width=True, key=chart_key)

            # 显示详细数据表格
            self._display_detailed_table(data, category_type)
        else:
            st.info(f"暂无{category_type}数据")

    def _display_detailed_table(self, data: pd.DataFrame, category_type: str):
        """显示详细数据表格"""
        st.markdown(f"##### 📋 {category_type}详细数据")

        try:
            display_df = data[["主营构成", "主营收入", "收入比例", "主营利润", "利润比例", "毛利率"]].copy()

            # 格式化数值显示
            formatter = lambda x, unit, divisor: f"{(x/divisor):.2f}{unit}"

            if "主营收入" in display_df.columns:
                display_df["主营收入(亿元)"] = display_df["主营收入"].apply(lambda x: formatter(x, "亿", 100000000))
            if "主营利润" in display_df.columns:
                display_df["主营利润(亿元)"] = display_df["主营利润"].apply(lambda x: formatter(x, "亿", 100000000))
            if "收入比例" in display_df.columns:
                display_df["收入比例(%)"] = (display_df["收入比例"] * 100).round(2)
            if "利润比例" in display_df.columns:
                display_df["利润比例(%)"] = (display_df["利润比例"] * 100).round(2)
            if "毛利率" in display_df.columns:
                display_df["毛利率(%)"] = (display_df["毛利率"] * 100).round(2)

            # 选择要显示的列
            hide_columns = ["主营收入", "主营利润", "收入比例", "利润比例", "毛利率"]
            display_columns = [col for col in display_df.columns if col not in hide_columns]

            st.dataframe(display_df[display_columns], use_container_width=True, hide_index=True)
        except Exception:
            st.info("无法显示详细数据表格")

    def _extract_bid_ask_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """提取盘口数据为字典格式"""
        bid_ask_dict = {}
        try:
            if not df.empty and '字段名' in df.columns and '字段值' in df.columns:
                bid_ask_dict = dict(zip(df['字段名'], df['字段值']))
        except Exception:
            pass
        return bid_ask_dict

    def _get_market_data(self, bid_ask_dict: Dict[str, Any]) -> Dict[str, float]:
        """获取市场基本数据"""
        return {
            'latest_price': safe_float(bid_ask_dict.get("最新", 0)),
            'change_pct': safe_float(bid_ask_dict.get("涨幅", 0)),
            'change_amount': safe_float(bid_ask_dict.get("涨跌", 0)),
            'volume': safe_float(bid_ask_dict.get("总手", 0)),
            'turnover': safe_float(bid_ask_dict.get("金额", 0)),
            'turnover_rate': safe_float(bid_ask_dict.get("换手", 0))
        }

    def _get_order_book_data(self, bid_ask_dict: Dict[str, Any]) -> Dict[str, list]:
        """获取买卖盘数据"""
        buy_prices, buy_vols = [], []
        sell_prices, sell_vols = [], []

        # 买盘数据
        for i in range(1, 6):
            buy_price = safe_float(bid_ask_dict.get(f"buy_{i}", 0))
            buy_vol = safe_float(bid_ask_dict.get(f"buy_{i}_vol", 0))
            if buy_price > 0 and buy_vol > 0:
                buy_prices.append(buy_price)
                buy_vols.append(buy_vol)

        # 卖盘数据
        for i in range(1, 6):
            sell_price = safe_float(bid_ask_dict.get(f"sell_{i}", 0))
            sell_vol = safe_float(bid_ask_dict.get(f"sell_{i}_vol", 0))
            if sell_price > 0 and sell_vol > 0:
                sell_prices.append(sell_price)
                sell_vols.append(sell_vol)

        return {
            'buy_prices': buy_prices,
            'buy_vols': buy_vols,
            'sell_prices': sell_prices,
            'sell_vols': sell_vols
        }

    def _display_bid_ask_analysis_impl(self, data: Dict[str, Any]):
        """显示盘口数据分析 - 简化版"""
        if "bid_ask" not in data or data["bid_ask"] is None:
            st.info("📊 暂无盘口深度数据")
            return

        df = data["bid_ask"]
        if df.empty:
            st.info("📊 盘口数据为空")
            return

        self.ui_manager.section_header("盘口数据分析", "💰")

        # 提取数据
        bid_ask_dict = self._extract_bid_ask_data(df)
        if not bid_ask_dict:
            st.info("📊 盘口数据格式不正确")
            return

        market_data = self._get_market_data(bid_ask_dict)
        order_book = self._get_order_book_data(bid_ask_dict)

        # 显示基本行情信息
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "最新价",
                f"{market_data['latest_price']:.2f}",
                f"{market_data['change_amount']:+.2f} ({market_data['change_pct']:+.2f}%)",
                delta_color="inverse",
            )
        with col2:
            st.metric("成交量", f"{market_data['volume'] / 100:,.0f}手")
        with col3:
            st.metric("成交额", f"{market_data['turnover'] / 1e8:.2f}亿")
        with col4:
            st.metric("换手率", f"{market_data['turnover_rate']:.2f}%")

        # 盘口深度图
        st.markdown("#### 📊 盘口深度图")
        try:
            fig = self.ui_manager.bid_ask_depth(bid_ask_dict, "盘口深度图")
            if fig:
                st.plotly_chart(fig, use_container_width=True, key="bid_ask_chart")
            else:
                st.info("暂无盘口深度数据")
        except Exception:
            st.info("无法生成盘口深度图")

        # 盘口分析指标
        total_buy_vol = sum(order_book['buy_vols'])
        total_sell_vol = sum(order_book['sell_vols'])
        buy_sell_ratio = (total_buy_vol / (total_buy_vol + total_sell_vol) * 100) if (total_buy_vol + total_sell_vol) > 0 else 0

        buy_1_price = safe_float(bid_ask_dict.get("buy_1", 0))
        sell_1_price = safe_float(bid_ask_dict.get("sell_1", 0))
        spread = (sell_1_price - buy_1_price) if sell_1_price > 0 and buy_1_price > 0 else 0
        spread_pct = (spread / buy_1_price * 100) if buy_1_price > 0 else 0

        analysis_col1, analysis_col2, analysis_col3 = st.columns(3)

        with analysis_col1:
            st.metric("买卖价差", f"{spread:.3f}", f"{spread_pct:.3f}%")
        with analysis_col2:
            st.metric("买盘占比", f"{buy_sell_ratio:.1f}%")
        with analysis_col3:
            st.metric("市场深度", f"{(total_buy_vol + total_sell_vol):,.0f}手")

        st.markdown("---")







    def _display_business_composition_bar_chart(self, business_data: Dict[str, Any], category_type: str):
        """显示主营业务构成柱状图 - 简化版"""
        try:
            if "main_business_composition" not in business_data:
                st.info("暂无主营业务构成数据")
                return

            df = business_data["main_business_composition"]
            if df.empty:
                st.info("主营业务构成数据为空")
                return

            # 获取指定分类类型的数据
            category_data = df[df["分类类型"] == category_type]
            if category_data.empty:
                st.info(f"暂无{category_type}数据")
                return

            # 按年份和分类构成分组
            category_data = category_data.copy()
            category_data['年份'] = category_data.index.year
            yearly_composition = category_data.groupby(['年份', '主营构成'])['主营收入'].sum().reset_index()

            if yearly_composition.empty:
                st.info(f"暂无{category_type}数据")
                return

            # 创建透视表
            pivot_data = yearly_composition.pivot(index='年份', columns='主营构成', values='主营收入').fillna(0)

            # 为图表准备数据格式
            pivot_data_reset = pivot_data.reset_index()
            pivot_data_reset['日期'] = pd.to_datetime(pivot_data_reset['年份'].astype(str) + '-12-31')

            # 创建数据字典格式
            all_compositions = pivot_data.columns.tolist()
            data_dict = {comp: comp for comp in all_compositions if comp != '年份'}

            # 创建柱状图
            fig = self.ui_manager.grouped_bar_years(
                pivot_data_reset,
                data_dict,
                f"{category_type}收入趋势分析"
            )

            if fig:
                chart_key = f"{category_type}_bar_chart"
                st.plotly_chart(fig, use_container_width=True, key=chart_key)
            else:
                st.info("无法生成柱状图")

        except Exception:
            st.info(f"生成{category_type}趋势图表时出错")


# 创建组件实例
company_overview_component = CompanyOverviewComponent()