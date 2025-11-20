#!/usr/bin/env python
"""
行业对比分析页面组件
基于同行比较数据提供多维度分析
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from typing import Dict, Any, Optional
import numpy as np

from src.web.templates import ui_template_manager
from src.web.utils import display_comparison_table
from config import config


class IndustryComparisonComponent:
    """行业对比分析页面组件"""
    
    def __init__(self):
        self.ui_manager = ui_template_manager
        
    def render(self, data: Dict[str, Any]):
        """渲染行业对比分析页面"""
        stock_code = data.get("stock_code", "未知") if data else "未知"
        
        # 页面标题
        st.markdown("## 🏭 行业对比分析")
        
        # 加载同行比较数据
        peer_data = self._load_peer_comparison_data(stock_code)
        
        if not peer_data:
            st.warning("暂无同行比较数据，请先运行数据收集流程")
            return
        
        # 创建4个tab对应4份数据文件
        tab_scale, tab_growth, tab_valuation, tab_dupont = st.tabs([
            "📏 规模分析",
            "📈 成长性分析", 
            "💰 估值分析", 
            "🔍 杜邦分析"
        ])
        
        with tab_scale:
            self._display_scale_analysis(peer_data, stock_code)
        
        with tab_growth:
            self._display_growth_analysis(peer_data, stock_code)
        
        with tab_valuation:
            self._display_valuation_analysis(peer_data, stock_code)
        
        with tab_dupont:
            self._display_dupont_analysis(peer_data, stock_code)
    
    def _load_peer_comparison_data(self, stock_code: str) -> Optional[Dict[str, pd.DataFrame]]:
        """加载同行比较数据"""
        cleaned_dir = config.cleaned_stocks_dir / stock_code
        
        peer_data = {}
        file_mapping = {
            "growth": "peer_growth_comparison.csv",
            "valuation": "peer_valuation_comparison.csv", 
            "dupont": "peer_dupont_comparison.csv",
            "scale": "peer_scale_comparison.csv"
        }
        
        for key, filename in file_mapping.items():
            file_path = cleaned_dir / filename
            if file_path.exists():
                try:
                    df = pd.read_csv(file_path)
                    peer_data[key] = df
                except Exception as e:
                    peer_data[key] = pd.DataFrame()
            else:
                peer_data[key] = pd.DataFrame()
        
        return peer_data
    
    
    def _display_growth_analysis(self, peer_data: Dict[str, pd.DataFrame], stock_code: str):
        """显示成长性分析"""
        st.markdown("### 📈 成长性分析")
        
        growth_df = peer_data.get('growth')
        if growth_df is None or growth_df.empty:
            st.warning("暂无成长性数据")
            return
        
        # 过滤出实际公司数据（排除行业平均和中值）
        company_df = growth_df[~growth_df['代码'].isin(['行业平均', '行业中值'])]
        
        if company_df.empty:
            st.warning("暂无公司成长性数据")
            return
        
        # 创建成长性分析的子tab
        growth_tab1, growth_tab2, growth_tab3 = st.tabs([
            "📊 基本每股收益增长率",
            "📈 营业收入增长率", 
            "💰 净利润增长率"
        ])
        
        with growth_tab1:
            self._display_single_growth_metric(growth_df, stock_code, "基本每股收益增长率")
        
        with growth_tab2:
            self._display_single_growth_metric(growth_df, stock_code, "营业收入增长率")
        
        with growth_tab3:
            self._display_single_growth_metric(growth_df, stock_code, "净利润增长率")
    
    def _display_single_growth_metric(self, growth_df: pd.DataFrame, stock_code: str, metric_name: str):
        """显示单个成长性指标"""
        if growth_df.empty:
            st.warning(f"暂无{metric_name}数据")
            return

        # 使用原有的图表创建方法
        fig = self._create_single_metric_line_chart(growth_df, stock_code, metric_name, "growth")
        if fig is not None and len(fig.data) > 0:
            st.plotly_chart(fig, width="stretch")
        else:
            st.warning(f"暂无{metric_name}图表数据")

        # 显示单个指标的对比表格
        display_comparison_table(growth_df, stock_code, "growth", metric_name)

    def _prepare_growth_data_for_chart(self, growth_df: pd.DataFrame, stock_code: str, metric_name: str) -> pd.DataFrame:
        """将行业对比数据转换为财务趋势图模板所需的格式，处理缺失数据"""
        import pandas as pd
        from datetime import datetime

        # 时间点映射
        time_mapping = {
            '24A': '2024-01-01',
            '25E': '2025-01-01',
            '26E': '2026-01-01',
            '27E': '2027-01-01'
        }

        # 创建完整的时间序列
        all_dates = [pd.to_datetime(date_str) for date_str in time_mapping.values()]

        # 收集所有有效公司
        valid_companies = []
        for _, row in growth_df.iterrows():
            company_code = row['代码']
            # 检查是否有任何有效数据
            has_valid_data = False
            for time_suffix in time_mapping.keys():
                col_name = f'{metric_name}-{time_suffix}'
                if col_name in row.index:
                    value = row.get(col_name)
                    if pd.notna(value) and value != '' and float(value) != 0:
                        has_valid_data = True
                        break
            if has_valid_data:
                valid_companies.append((company_code, row['简称']))

        if not valid_companies:
            return pd.DataFrame()

        # 创建数据框架，确保所有时间点都有
        chart_dict = {'日期': all_dates}

        # 为每个公司填充数据
        for company_code, company_name in valid_companies:
            company_values = []
            company_row = growth_df[growth_df['代码'] == company_code].iloc[0]

            for date_str in time_mapping.values():
                time_suffix = None
                for ts, ds in time_mapping.items():
                    if ds == date_str:
                        time_suffix = ts
                        break

                col_name = f'{metric_name}-{time_suffix}'
                if col_name in company_row.index:
                    value = company_row.get(col_name)
                    if pd.notna(value) and value != '':
                        try:
                            float_value = float(value)
                            # 过滤异常值
                            if abs(float_value) < 10000:  # 防止异常大值
                                company_values.append(float_value)
                            else:
                                company_values.append(None)
                        except (ValueError, TypeError):
                            company_values.append(None)
                    else:
                        company_values.append(None)
                else:
                    company_values.append(None)

            chart_dict[company_code] = company_values

        # 转换为DataFrame
        chart_df = pd.DataFrame(chart_dict)
        chart_df = chart_df.set_index('日期')

        return chart_df

    def _display_valuation_analysis(self, peer_data: Dict[str, pd.DataFrame], stock_code: str):
        """显示估值分析"""
        st.markdown("### 💰 估值分析")
        
        valuation_df = peer_data.get('valuation')
        if valuation_df is None or valuation_df.empty:
            st.warning("暂无估值数据")
            return
        
        # 过滤出实际公司数据
        company_df = valuation_df[~valuation_df['代码'].isin(['行业平均', '行业中值'])]
        
        if company_df.empty:
            st.warning("暂无公司估值数据")
            return
        
        # 创建估值分析的子tab
        valuation_tab1, valuation_tab2, valuation_tab3, valuation_tab4 = st.tabs([
            "📊 市盈率",
            "📈 市销率", 
            "💰 市净率",
            "🔍 市现率"
        ])
        
        with valuation_tab1:
            self._display_single_valuation_metric(valuation_df, stock_code, "市盈率")
        
        with valuation_tab2:
            self._display_single_valuation_metric(valuation_df, stock_code, "市销率")
        
        with valuation_tab3:
            self._display_single_valuation_metric(valuation_df, stock_code, "市净率")
        
        with valuation_tab4:
            self._display_single_valuation_metric(valuation_df, stock_code, "市现率")
    
    def _display_single_valuation_metric(self, valuation_df: pd.DataFrame, stock_code: str, metric_name: str):
        """显示单个估值指标"""
        # 市净率和市现率使用柱状图，其他使用折线图
        if metric_name in ["市净率", "市现率"]:
            # 创建柱状图（只显示24A数据）
            fig = self._create_single_metric_bar_chart(valuation_df, stock_code, metric_name, "valuation")
            st.plotly_chart(fig)
            
            # 显示单个指标的对比表格（只显示24A）
            display_comparison_table(valuation_df, stock_code, "valuation", metric_name)
        else:
            # 创建折线图
            fig = self._create_single_metric_line_chart(valuation_df, stock_code, metric_name, "valuation")
            st.plotly_chart(fig)
            
            # 显示单个指标的对比表格
            display_comparison_table(valuation_df, stock_code, "valuation", metric_name)
    
    def _display_dupont_analysis(self, peer_data: Dict[str, pd.DataFrame], stock_code: str):
        """显示杜邦分析"""
        st.markdown("### 🔍 杜邦分析")
        
        dupont_df = peer_data.get('dupont')
        if dupont_df is None or dupont_df.empty:
            st.warning("暂无杜邦分析数据")
            return
        
        # 过滤出实际公司数据
        company_df = dupont_df[~dupont_df['代码'].isin(['行业平均', '行业中值'])]
        
        if company_df.empty:
            st.warning("暂无公司杜邦分析数据")
            return
        
        # 显示带数值的ROE公式
        self._display_dupont_formula_with_values(dupont_df, stock_code)
        
        # 创建杜邦分析的子tab
        dupont_tab1, dupont_tab2, dupont_tab3, dupont_tab4 = st.tabs([
            "📊 ROE",
            "📈 净利率", 
            "💰 总资产周转率",
            "🔍 权益乘数"
        ])
        
        with dupont_tab1:
            self._display_single_dupont_metric(dupont_df, stock_code, "ROE")
        
        with dupont_tab2:
            self._display_single_dupont_metric(dupont_df, stock_code, "净利率")
        
        with dupont_tab3:
            self._display_single_dupont_metric(dupont_df, stock_code, "总资产周转率")
        
        with dupont_tab4:
            self._display_single_dupont_metric(dupont_df, stock_code, "权益乘数")
    
    def _display_dupont_formula_with_values(self, df: pd.DataFrame, stock_code: str):
        """显示带数值的ROE公式"""
        try:
            # 尝试多种匹配方式找到目标公司
            target_row = None
            if target_row is None or target_row.empty:
                target_row = df[df['代码'] == stock_code]
            if target_row is None or target_row.empty:
                target_row = df[df['代码'].astype(str) == str(stock_code)]
            if target_row is None or target_row.empty:
                stock_code_no_zero = str(int(stock_code))
                target_row = df[df['代码'].astype(str) == stock_code_no_zero]
            if target_row is None or target_row.empty:
                stock_code_with_zero = str(stock_code).zfill(6)
                target_row = df[df['代码'].astype(str) == stock_code_with_zero]
            
            if not target_row.empty:
                target_company = target_row.iloc[0]
                company_name = target_company['简称']
                
                # 获取各个指标的2024A数值
                net_margin_col = '净利率-24A'
                asset_turnover_col = '总资产周转率-24A'
                equity_multiplier_col = '权益乘数-24A'
                roe_col = 'ROE-24A'
                
                # 获取数值
                net_margin = target_company.get(net_margin_col, 0) if pd.notna(target_company.get(net_margin_col)) else 0
                asset_turnover = target_company.get(asset_turnover_col, 0) if pd.notna(target_company.get(asset_turnover_col)) else 0
                equity_multiplier = target_company.get(equity_multiplier_col, 0) if pd.notna(target_company.get(equity_multiplier_col)) else 0
                roe_value = target_company.get(roe_col, 0) if pd.notna(target_company.get(roe_col)) else 0
                
                # 显示带数值的公式 - 使用5个column
                st.markdown("**ROE = 净利率 × 总资产周转率 × 权益乘数**")
                
                # 创建5个列
                col1, col2, col3, col4, col5 = st.columns(5)
                
                with col1:
                    st.markdown(f"<div style='text-align: center; padding: 10px; background-color: #e3f2fd; border-radius: 8px;'><small style='color: #666;'>ROE</small><br><strong style='color: #1976d2; font-size: 20px;'>{roe_value:.2f}%</strong></div>", unsafe_allow_html=True)
                
                with col2:
                    st.markdown("<div style='text-align: center; padding: 10px;'><strong style='color: #ffffff; font-size: 20px;'>=</strong></div>", unsafe_allow_html=True)
                
                with col3:
                    st.markdown(f"<div style='text-align: center; padding: 10px; background-color: #f3e5f5; border-radius: 8px;'><small style='color: #666;'>净利率</small><br><strong style='color: #7b1fa2; font-size: 20px;'>{net_margin:.2f}%</strong></div>", unsafe_allow_html=True)
                
                with col4:
                    st.markdown(f"<div style='text-align: center; padding: 10px; background-color: #e8f5e8; border-radius: 8px;'><small style='color: #666;'>总资产周转率</small><br><strong style='color: #388e3c; font-size: 20px;'>{asset_turnover:.2f}%</strong></div>", unsafe_allow_html=True)
                
                with col5:
                    st.markdown(f"<div style='text-align: center; padding: 10px; background-color: #fff3e0; border-radius: 8px;'><small style='color: #666;'>权益乘数</small><br><strong style='color: #f57c00; font-size: 20px;'>{equity_multiplier:.2f}</strong></div>", unsafe_allow_html=True)
                
                # 显示数据来源
                st.markdown(f"<div style='text-align: center; margin-top: 10px; color: #666; font-size: 14px;'>📊 {company_name} 2024年数据</div>", unsafe_allow_html=True)
                    
            else:
                st.markdown(f"<small>📊 未找到股票 {stock_code} 的数据</small>", unsafe_allow_html=True)
                
        except Exception as e:
            st.markdown(f"<small>📊 获取数据失败: {e}</small>", unsafe_allow_html=True)
    
    def _display_single_dupont_metric(self, dupont_df: pd.DataFrame, stock_code: str, metric_name: str):
        """显示单个杜邦指标"""
        # 创建单个指标的折线图
        fig = self._create_single_metric_line_chart(dupont_df, stock_code, metric_name, "dupont")
        st.plotly_chart(fig)
        
        # 显示单个指标的对比表格
        display_comparison_table(dupont_df, stock_code, "dupont", metric_name)
    
    def _create_single_metric_bar_chart(self, df: pd.DataFrame, stock_code: str, metric_name: str, analysis_type: str):
        """创建单个指标的柱状图（只显示24A数据）"""
        import plotly.graph_objects as go
        
        # 根据分析类型确定要显示的列
        if analysis_type == "valuation":
            if metric_name == "市净率":
                metric_column = f'{metric_name}-24A'
            elif metric_name == "市现率":
                metric_column = f'{metric_name}PCE-24A'  # 使用PCE版本
            else:
                metric_column = f'{metric_name}-24A'
        else:
            return go.Figure()
        
        # 创建图表
        fig = go.Figure()
        
        # 准备数据
        plot_data = []
        colors = []
        
        for _, company_row in df.iterrows():
            company_code = company_row['代码']
            company_name = company_row['简称']
            
            # 获取该公司的指标值
            if metric_column in company_row.index:
                value = company_row.get(metric_column)
                if pd.notna(value) and value != '':
                    plot_data.append({
                        'name': company_name,
                        'value': value,
                        'code': company_code
                    })
                    
                    # 设置颜色
                    if company_code == stock_code:
                        colors.append('#FF4444')  # 红色突出目标股票
                    elif company_code == '行业平均':
                        colors.append('#4CAF50')  # 绿色行业平均
                    elif company_code == '行业中值':
                        colors.append('#2196F3')  # 蓝色行业中值
                    else:
                        colors.append('#9E9E9E')  # 灰色其他公司
        
        if not plot_data:
            return go.Figure()
        
        # 按值排序（降序）
        plot_data.sort(key=lambda x: x['value'], reverse=True)
        
        # 提取数据
        names = [item['name'] for item in plot_data]
        values = [item['value'] for item in plot_data]
        
        # 重新分配颜色（按排序后的顺序）
        sorted_colors = []
        for item in plot_data:
            if item['code'] == stock_code:
                sorted_colors.append('#FF4444')
            elif item['code'] == '行业平均':
                sorted_colors.append('#4CAF50')
            elif item['code'] == '行业中值':
                sorted_colors.append('#2196F3')
            else:
                sorted_colors.append('#9E9E9E')
        
        # 添加柱状图
        fig.add_trace(
            go.Bar(
                x=names,
                y=values,
                marker_color=sorted_colors,
                text=[f"{v:.2f}" for v in values],
                textposition='auto',
                hovertemplate=f'<b>%{{x}}</b><br>{metric_name}: %{{y:.2f}}<extra></extra>'
            )
        )
        
        # 更新布局
        fig.update_layout(
            title=f"{metric_name}对比（2024A）",
            xaxis_title="公司",
            yaxis_title=metric_name,
            height=500,
            showlegend=False,
            xaxis={'categoryorder': 'total descending'}
        )
        
        return fig
    
    def _display_scale_analysis(self, peer_data: Dict[str, pd.DataFrame], stock_code: str):
        """显示规模分析"""
        st.markdown("### 📏 规模分析")
        
        scale_df = peer_data.get('scale')
        if scale_df is None or scale_df.empty:
            st.warning("暂无规模数据")
            return
        
        # 检查是否有目标股票数据（处理代码格式差异）
        # 尝试多种匹配方式
        target_row = None
        
        # 方式1：直接匹配
        if target_row is None or target_row.empty:
            target_row = scale_df[scale_df['代码'] == stock_code]
        
        # 方式2：转换为字符串匹配
        if target_row is None or target_row.empty:
            target_row = scale_df[scale_df['代码'].astype(str) == str(stock_code)]
        
        # 方式3：去除前导零匹配
        if target_row is None or target_row.empty:
            stock_code_no_zero = str(int(stock_code))
            target_row = scale_df[scale_df['代码'].astype(str) == stock_code_no_zero]
        
        # 方式4：添加前导零匹配
        if target_row is None or target_row.empty:
            stock_code_with_zero = str(stock_code).zfill(6)
            target_row = scale_df[scale_df['代码'].astype(str) == stock_code_with_zero]
        
        if target_row is None or target_row.empty:
            st.warning(f"未找到股票 {stock_code} 的规模数据")
            # 显示可用数据的基本信息
            if not scale_df.empty:
                available_codes = scale_df['代码'].astype(str).tolist()
                available_names = scale_df['简称'].tolist()
                st.info(f"可用的规模数据：{', '.join([f'{code}({name})' for code, name in zip(available_codes, available_names)])}")
            return
        
        target_data = target_row.iloc[0]
        
        # 关键指标卡片展示
        st.markdown("#### 📊 关键指标概览")
        
        # 创建指标卡片
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            market_cap = target_data['总市值']
            market_cap_rank = target_data['总市值排名']
            st.metric(
                label="总市值",
                value=f"{market_cap/1e8:.2f}亿元",
                delta=f"排名第{int(market_cap_rank)}名",
                help="公司总市值，反映公司整体价值"
            )
        
        with col2:
            float_cap = target_data['流通市值']
            float_rank = target_data['流通市值排名']
            st.metric(
                label="流通市值",
                value=f"{float_cap:.2f}亿元",
                delta=f"排名第{int(float_rank)}名",
                help="流通股总市值，反映可交易股票价值"
            )
        
        with col3:
            revenue = target_data['营业收入']
            revenue_rank = target_data['营业收入排名']
            st.metric(
                label="营业收入",
                value=f"{revenue/1e8:.2f}亿元", 
                delta=f"排名第{int(revenue_rank)}名",
                help="公司主营业务收入，反映经营规模"
            )
        
        with col4:
            net_profit = target_data['净利润']
            profit_rank = target_data['净利润排名']
            st.metric(
                label="净利润",
                value=f"{net_profit/1e8:.2f}亿元",
                delta=f"排名第{int(profit_rank)}名",
                help="公司净利润，反映盈利能力"
            )
        
    
    def _create_single_metric_line_chart(self, df: pd.DataFrame, stock_code: str, metric_name: str, analysis_type: str):
        """创建单个指标的折线图"""
        import plotly.graph_objects as go
        
        # 根据分析类型确定时间点和指标列
        if analysis_type == "growth":
            time_points = ['2024A', '2025E', '2026E', '2027E']
            metric_columns = [f'{metric_name}-24A', f'{metric_name}-25E', f'{metric_name}-26E', f'{metric_name}-27E']
        elif analysis_type == "valuation":
            if metric_name == "市净率":
                time_points = ['2024A', 'MRQ']
                metric_columns = [f'{metric_name}-24A', f'{metric_name}-MRQ']
            elif metric_name == "市现率":
                time_points = ['2024A', 'TTM']
                metric_columns = [f'{metric_name}PCE-24A', f'{metric_name}PCE-TTM']
            else:
                time_points = ['2024A', '2025E', '2026E', '2027E']
                metric_columns = [f'{metric_name}-24A', f'{metric_name}-25E', f'{metric_name}-26E', f'{metric_name}-27E']
        elif analysis_type == "dupont":
            time_points = ['2022A', '2023A', '2024A']
            metric_columns = [f'{metric_name}-22A', f'{metric_name}-23A', f'{metric_name}-24A']
        else:
            return go.Figure()
        
        # 创建图表
        fig = go.Figure()
        
        # 颜色映射
        colors = {
            '行业平均': 'blue',
            '行业中值': 'green', 
            stock_code: 'red'
        }
        
        # 为每个公司/行业创建折线
        for _, company_row in df.iterrows():
            company_code = company_row['代码']
            company_name = company_row['简称']
            
            # 获取该公司的指标值
            values = []
            valid_time_points = []
            
            for metric_col in metric_columns:
                if metric_col in company_row.index:
                    value = company_row.get(metric_col)
                    if pd.notna(value) and value != '':
                        values.append(value)
                        valid_time_points.append(time_points[metric_columns.index(metric_col)])
            
            if values:  # 只有当有有效数据时才绘制
                color = colors.get(company_code, 'lightgray')
                line_width = 3 if company_code == stock_code else 2
                line_dash = 'solid'
                
                fig.add_trace(
                    go.Scatter(
                        x=valid_time_points,
                        y=values,
                        mode='lines+markers',
                        name=company_name,
                        line=dict(color=color, width=line_width, dash=line_dash),
                        marker=dict(size=6),
                        hovertemplate=f'<b>{company_name}</b><br>%{{x}}<br>{metric_name}: %{{y:.2f}}<extra></extra>'
                    )
                )
        
        # 更新布局
        fig.update_layout(
            title=f"{metric_name}趋势对比",
            xaxis_title="时间",
            yaxis_title=metric_name,
            height=500,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        return fig

    def _create_scale_comparison_chart(self, df: pd.DataFrame, stock_code: str):
        """创建规模对比图表"""
        if df.empty:
            return
        
        # 创建子图
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=['总市值对比', '流通市值对比', '营业收入对比', '净利润对比'],
            specs=[[{"type": "bar"}, {"type": "bar"}],
                   [{"type": "bar"}, {"type": "bar"}]]
        )
        
        # 定义指标和位置
        metrics = [
            ('总市值', '总市值', (1, 1)),
            ('流通市值', '流通市值', (1, 2)),
            ('营业收入', '营业收入', (2, 1)),
            ('净利润', '净利润', (2, 2))
        ]
        
        for metric_name, col_name, (row, col) in metrics:
            if col_name in df.columns:
                # 准备数据
                plot_data = df[['代码', '简称', col_name]].copy()
                plot_data = plot_data.dropna(subset=[col_name])
                
                if not plot_data.empty:
                    # 转换单位用于显示
                    if col_name in ['总市值', '营业收入', '净利润']:
                        # 转换为亿元显示
                        plot_data[f'{col_name}_display'] = plot_data[col_name] / 1e8
                        y_title = f"{metric_name}(亿元)"
                    else:
                        # 流通市值已经是亿元
                        plot_data[f'{col_name}_display'] = plot_data[col_name]
                        y_title = f"{metric_name}(亿元)"
                    
                    # 设置颜色
                    colors = []
                    for _, row_data in plot_data.iterrows():
                        if row_data['代码'] == stock_code:
                            colors.append('#FF4444')  # 红色突出目标股票
                        else:
                            colors.append('#4CAF50')  # 绿色其他公司
                    
                    # 添加柱状图
                    fig.add_trace(
                        go.Bar(
                            x=plot_data['简称'],
                            y=plot_data[f'{col_name}_display'],
                            name=metric_name,
                            marker_color=colors,
                            showlegend=False,
                            text=plot_data[f'{col_name}_display'].round(2),
                            textposition='auto',
                        ),
                        row=row, col=col
                    )
        
        # 更新布局
        fig.update_layout(
            title="规模指标对比分析",
            height=600,
            showlegend=False
        )
        
        # 更新轴标签
        fig.update_xaxes(title_text="公司", row=1, col=1)
        fig.update_xaxes(title_text="公司", row=1, col=2)
        fig.update_xaxes(title_text="公司", row=2, col=1)
        fig.update_xaxes(title_text="公司", row=2, col=2)
        
        fig.update_yaxes(title_text="总市值(亿元)", row=1, col=1)
        fig.update_yaxes(title_text="流通市值(亿元)", row=1, col=2)
        fig.update_yaxes(title_text="营业收入(亿元)", row=2, col=1)
        fig.update_yaxes(title_text="净利润(亿元)", row=2, col=2)
        
        st.plotly_chart(fig)
    
    def _get_target_stock_data(self, peer_data: Dict[str, pd.DataFrame], stock_code: str) -> Dict[str, Any]:
        """获取目标股票的关键数据"""
        target_data = {}
        
        # 成长性排名
        growth_df = peer_data.get('growth')
        if growth_df is not None:
            target_row = growth_df[growth_df['代码'] == stock_code]
            if not target_row.empty:
                target_data['growth_rank'] = target_row.iloc[0].get('基本每股收益增长率-3年复合排名', 'N/A')
        
        # 估值排名
        valuation_df = peer_data.get('valuation')
        if valuation_df is not None:
            target_row = valuation_df[valuation_df['代码'] == stock_code]
            if not target_row.empty:
                target_data['valuation_rank'] = target_row.iloc[0].get('PEG排名', 'N/A')
        
        # ROE排名
        dupont_df = peer_data.get('dupont')
        if dupont_df is not None:
            target_row = dupont_df[dupont_df['代码'] == stock_code]
            if not target_row.empty:
                target_data['roe_rank'] = target_row.iloc[0].get('ROE-3年平均排名', 'N/A')
        
        # 规模排名
        scale_df = peer_data.get('scale')
        if scale_df is not None:
            target_row = scale_df[scale_df['代码'] == stock_code]
            if not target_row.empty:
                target_data['scale_rank'] = target_row.iloc[0].get('总市值排名', 'N/A')
        
        return target_data
    
    def _create_radar_chart(self, peer_data: Dict[str, pd.DataFrame], stock_code: str):
        """创建雷达图显示综合表现"""
        st.markdown("#### 🎯 综合表现雷达图")
        
        # 获取目标股票数据
        target_data = self._get_target_stock_data(peer_data, stock_code)
        
        # 计算相对表现（相对于行业平均）
        categories = ['成长性', '估值', '盈利能力', '规模']
        values = []
        
        # 成长性：排名越靠前越好
        growth_rank = target_data.get('growth_rank', 50)
        if growth_rank != 'N/A':
            growth_score = max(0, 100 - (growth_rank - 1) * 2)  # 排名1得100分，排名50得0分
        else:
            growth_score = 50
        values.append(growth_score)
        
        # 估值：排名越靠前越好（PEG越小越好）
        valuation_rank = target_data.get('valuation_rank', 50)
        if valuation_rank != 'N/A':
            valuation_score = max(0, 100 - (valuation_rank - 1) * 2)
        else:
            valuation_score = 50
        values.append(valuation_score)
        
        # 盈利能力：ROE排名
        roe_rank = target_data.get('roe_rank', 50)
        if roe_rank != 'N/A':
            roe_score = max(0, 100 - (roe_rank - 1) * 2)
        else:
            roe_score = 50
        values.append(roe_score)
        
        # 规模：排名越靠前越好
        scale_rank = target_data.get('scale_rank', 50)
        if scale_rank != 'N/A':
            scale_score = max(0, 100 - (scale_rank - 1) * 2)
        else:
            scale_score = 50
        values.append(scale_score)
        
        # 创建雷达图
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            name=stock_code,
            line_color='rgb(32, 201, 151)'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )),
            showlegend=True,
            title=f"{stock_code} 综合表现雷达图",
            height=500
        )
        
        st.plotly_chart(fig)
    
    def _create_growth_bar_chart(self, df: pd.DataFrame, metric: str, stock_code: str):
        """创建成长性柱状图"""
        # 按指标值排序
        df_sorted = df.sort_values(metric, ascending=False)
        
        # 创建颜色列表，目标股票用红色，其他用蓝色
        colors = ['red' if code == stock_code else 'lightblue' for code in df_sorted['代码']]
        
        fig = go.Figure(data=[
            go.Bar(
                x=df_sorted['简称'],
                y=df_sorted[metric],
                marker_color=colors,
                text=df_sorted[metric].round(2),
                textposition='auto',
            )
        ])
        
        fig.update_layout(
            title=f"{metric} 对比",
            xaxis_title="公司",
            yaxis_title=metric,
            height=500
        )
        
        st.plotly_chart(fig)
    
    def _create_valuation_bar_chart(self, df: pd.DataFrame, metric: str, stock_code: str):
        """创建估值柱状图"""
        # 按指标值排序（估值指标通常越小越好）
        ascending = metric in ['PEG', '市盈率-24A', '市盈率-TTM', '市销率-24A', '市净率-24A']
        df_sorted = df.sort_values(metric, ascending=ascending)
        
        # 创建颜色列表
        colors = ['red' if code == stock_code else 'lightgreen' for code in df_sorted['代码']]
        
        fig = go.Figure(data=[
            go.Bar(
                x=df_sorted['简称'],
                y=df_sorted[metric],
                marker_color=colors,
                text=df_sorted[metric].round(2),
                textposition='auto',
            )
        ])
        
        fig.update_layout(
            title=f"{metric} 对比",
            xaxis_title="公司",
            yaxis_title=metric,
            height=500
        )
        
        st.plotly_chart(fig)
    
    def _create_dupont_chart(self, df: pd.DataFrame, stock_code: str):
        """创建杜邦分析图表"""
        # 创建子图
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=['ROE对比', '净利率对比', '总资产周转率对比', '权益乘数对比'],
            specs=[[{"type": "bar"}, {"type": "bar"}],
                   [{"type": "bar"}, {"type": "bar"}]]
        )
        
        metrics = ['ROE-3年平均', '净利率-3年平均', '总资产周转率-3年平均', '权益乘数-3年平均']
        positions = [(1, 1), (1, 2), (2, 1), (2, 2)]
        
        for i, (metric, pos) in enumerate(zip(metrics, positions)):
            df_sorted = df.sort_values(metric, ascending=False)
            colors = ['red' if code == stock_code else 'lightcoral' for code in df_sorted['代码']]
            
            fig.add_trace(
                go.Bar(
                    x=df_sorted['简称'],
                    y=df_sorted[metric],
                    marker_color=colors,
                    name=metric,
                    showlegend=False
                ),
                row=pos[0], col=pos[1]
            )
        
        fig.update_layout(
            title="杜邦分析对比",
            height=800
        )
        
        st.plotly_chart(fig)
    
    def _create_growth_scatter_chart(self, df: pd.DataFrame, metric: str, stock_code: str):
        """创建成长性散点图"""
        # 这里可以添加散点图逻辑
        st.info("散点图功能待实现")
    
    def _create_valuation_line_chart(self, df: pd.DataFrame, stock_code: str):
        """创建估值折线图 - 显示不同估值指标的时间趋势"""
        st.markdown("#### 📈 估值指标时间趋势对比")
        
        # 定义时间序列的估值指标
        time_series_metrics = {
            '市盈率': ['市盈率-24A', '市盈率-TTM', '市盈率-25E', '市盈率-26E', '市盈率-27E'],
            '市销率': ['市销率-24A', '市销率-TTM', '市销率-25E', '市销率-26E', '市销率-27E'],
            '市净率': ['市净率-24A', '市净率-MRQ'],
            '市现率': ['市现率PCE-24A', '市现率PCE-TTM', '市现率PCF-24A', '市现率PCF-TTM']
        }
        
        # 创建子图
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=['市盈率趋势', '市销率趋势', '市净率趋势', '市现率趋势'],
            specs=[[{"type": "scatter"}, {"type": "scatter"}],
                   [{"type": "scatter"}, {"type": "scatter"}]]
        )
        
        # 定义时间点
        time_points = ['2024A', 'TTM', '2025E', '2026E', '2027E']
        time_points_pb = ['2024A', 'MRQ']
        time_points_pc = ['2024A', 'TTM', '2024A', 'TTM']
        
        # 颜色映射
        colors = {
            '行业平均': 'blue',
            '行业中值': 'green', 
            stock_code: 'red'
        }
        
        positions = [(1, 1), (1, 2), (2, 1), (2, 2)]
        metric_names = ['市盈率', '市销率', '市净率', '市现率']
        
        for i, (metric_name, metrics) in enumerate(time_series_metrics.items()):
            row, col = positions[i]
            
            # 为每个公司/行业创建折线
            for _, company_row in df.iterrows():
                company_code = company_row['代码']
                company_name = company_row['简称']
                
                # 获取该公司的指标值
                values = []
                valid_time_points = []
                
                if metric_name == '市净率':
                    time_points_to_use = time_points_pb
                elif metric_name == '市现率':
                    time_points_to_use = time_points_pc
                else:
                    time_points_to_use = time_points
                
                for j, metric in enumerate(metrics):
                    if j < len(time_points_to_use):
                        value = company_row.get(metric)
                        if pd.notna(value) and value != '':
                            values.append(value)
                            valid_time_points.append(time_points_to_use[j])
                
                if values:  # 只有当有有效数据时才绘制
                    color = colors.get(company_code, 'lightgray')
                    line_width = 3 if company_code == stock_code else 2
                    line_dash = 'solid' if company_code in ['行业平均', '行业中值'] else 'dash'
                    
                    fig.add_trace(
                        go.Scatter(
                            x=valid_time_points,
                            y=values,
                            mode='lines+markers',
                            name=company_name,
                            line=dict(color=color, width=line_width, dash=line_dash),
                            marker=dict(size=6),
                            showlegend=True if i == 0 else False  # 只在第一个子图显示图例
                        ),
                        row=row, col=col
                    )
        
        # 更新布局
        fig.update_layout(
            title="估值指标时间趋势对比",
            height=800,
            showlegend=True
        )
        
        # 更新x轴标签
        fig.update_xaxes(title_text="时间", row=1, col=1)
        fig.update_xaxes(title_text="时间", row=1, col=2)
        fig.update_xaxes(title_text="时间", row=2, col=1)
        fig.update_xaxes(title_text="时间", row=2, col=2)
        
        # 更新y轴标签
        fig.update_yaxes(title_text="市盈率", row=1, col=1)
        fig.update_yaxes(title_text="市销率", row=1, col=2)
        fig.update_yaxes(title_text="市净率", row=2, col=1)
        fig.update_yaxes(title_text="市现率", row=2, col=2)
        
        st.plotly_chart(fig)

    def _create_valuation_scatter_chart(self, df: pd.DataFrame, metric: str, stock_code: str):
        """创建估值散点图"""
        # 这里可以添加散点图逻辑
        st.info("散点图功能待实现")
    
    def _create_ranking_chart(self, df: pd.DataFrame, metric: str, stock_code: str):
        """创建排名图"""
        # 这里可以添加排名图逻辑
        st.info("排名图功能待实现")



