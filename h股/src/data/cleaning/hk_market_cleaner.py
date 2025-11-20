#!/usr/bin/env python3
from __future__ import annotations

"""
港股 市场数据清洗器
- 读取: h股/data/market 下的 CSV（如 spot_sina_all, hot_rank_em, famous_spot_em_all, index_daily_em_HSI）
- 输出: 同目录 *_cleaned.csv
"""

import os
import re
from typing import Dict

import numpy as np
import pandas as pd


def _to_datetime(val):
    try:
        return pd.to_datetime(val, errors="coerce")
    except Exception:
        return pd.NaT


def _to_numeric_chinese(value):
    if pd.isna(value) or value == "":
        return np.nan
    s = str(value).strip()
    mult = 1
    if "万亿" in s:
        mult, s = 1e12, s.replace("万亿", "")
    elif "千亿" in s:
        mult, s = 1e11, s.replace("千亿", "")
    elif "百亿" in s:
        mult, s = 1e10, s.replace("百亿", "")
    elif "十亿" in s:
        mult, s = 1e9, s.replace("十亿", "")
    elif "亿" in s:
        mult, s = 1e8, s.replace("亿", "")
    elif "万" in s:
        mult, s = 1e4, s.replace("万", "")
    s = re.sub(r"[^\d.+-]", "", s)
    try:
        return float(s) * mult
    except Exception:
        return np.nan


def _clean_market_df(df: pd.DataFrame, name: str) -> pd.DataFrame:
    df = df.dropna(how="all").drop_duplicates()
    # 常见日期列尝试规范化
    for cand in ["日期", "时间", "date", "Date", "更新时间", "更新时间-北京时间"]:
        if cand in df.columns:
            df[cand] = df[cand].map(_to_datetime)
            df = df.dropna(subset=[cand]).sort_values(cand)
            df = df.rename(columns={cand: "日期"})
            break
    # 量额类统一数值
    for col in list(df.columns):
        if col == "日期":
            continue
        if df[col].dtype == object:
            conv = df[col].map(_to_numeric_chinese)
            if conv.notna().sum() >= max(3, int(0.2 * len(conv))):
                df[col] = conv
            else:
                df[col] = pd.to_numeric(df[col], errors="ignore")
    # 日期放首列
    if "日期" in df.columns:
        cols = ["日期"] + [c for c in df.columns if c != "日期"]
        df = df[cols]

    # 三大报表和财务指标只保留报告期数据
    if "financial_hk_report" in name or "financial_hk_analysis_indicator" in name:
        if "indicator" in df.columns:
            df = df[df["indicator"] == "报告期"]
        elif "INDICATOR" in df.columns: # 兼容大小写
            df = df[df["INDICATOR"] == "报告期"]

    # 盘中数据只保留 15 分钟级的数据
    if "hist_min_em" in name:
        if "period" in df.columns: # 假设period列存在于数据中
            df = df[df["period"] == "15"]
        # 如果没有period列，则无法在清洗阶段进行过滤，需要依赖数据收集阶段的正确参数

    # 盈利预测只保留「综合盈利预测」和「盈利预测概览」
    if "profit_forecast_et" in name:
        if "indicator" in df.columns:
            df = df[df["indicator"].isin(["综合盈利预测", "盈利预测概览"])]
        elif "INDICATOR" in df.columns: # 兼容大小写
            df = df[df["INDICATOR"].isin(["综合盈利预测", "盈利预测概览"])]

    return df


def clean_market_folder(market_root: str) -> Dict[str, str]:
    if not os.path.isdir(market_root):
        raise FileNotFoundError(market_root)
    # 目标输出目录：data/cleaned_market
    data_root = os.path.dirname(market_root)
    cleaned_market = os.path.join(data_root, "cleaned_market")
    os.makedirs(cleaned_market, exist_ok=True)

    outputs: Dict[str, str] = {}
    for name in sorted(os.listdir(market_root)):
        if not name.endswith(".csv"):
            continue
        # 移除热度榜相关数据
        if "hot_rank" in name:
            print(f"Skipping hot_rank data: {name}")
            continue
        in_path = os.path.join(market_root, name)
        out_path = os.path.join(cleaned_market, name)
        try:
            df = pd.read_csv(in_path)
            if df.empty:
                continue
            df = _clean_market_df(df, name)
            df.to_csv(out_path, index=False)
            outputs[name] = out_path
        except Exception:
            continue
    return outputs


if __name__ == "__main__":
    project_root = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    )
    market_dir = os.path.join(project_root, "data", "market")
    res = clean_market_folder(market_dir)
    print("Cleaned market files:")
    for k, v in res.items():
        print(f"  {k} -> {v}")


