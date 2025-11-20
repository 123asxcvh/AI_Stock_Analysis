#!/usr/bin/env python3
from __future__ import annotations

"""
港股 个股数据清洗器
- 读取: h股/data/stocks/{symbol} 下各 CSV
- 输出: 同目录生成 *_cleaned.csv（非破坏性写入）
"""

import os
import re
from typing import Dict

import numpy as np
import pandas as pd


DATE_ALIASES = {
    "日期时间": "日期",
    "时间": "日期",
    "date": "日期",
    "Date": "日期",
}


def _to_datetime(df: pd.DataFrame, col: str = "日期") -> pd.DataFrame:
    if col in df.columns:
        df[col] = pd.to_datetime(df[col], errors="coerce")
        df = df.dropna(subset=[col]).sort_values(col)
    return df


def _rename_date_columns(df: pd.DataFrame) -> pd.DataFrame:
    for src, dst in DATE_ALIASES.items():
        if src in df.columns and src != dst:
            df = df.rename(columns={src: dst})
    return df


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


def _clean_generic(df: pd.DataFrame, file_name: str) -> pd.DataFrame:
    df = _rename_date_columns(df)
    df = df.dropna(how="all").drop_duplicates()
    df = _to_datetime(df, "日期")
    # 将明显的数值列转为数值
    for col in df.columns:
        if col == "日期":
            continue
        if df[col].dtype == object:
            # 尝试中文单位转换
            converted = df[col].map(_to_numeric_chinese)
            # 如果转换后有较多非空，则采用
            if converted.notna().sum() >= max(3, int(0.2 * len(converted))):
                df[col] = converted
            else:
                df[col] = pd.to_numeric(df[col], errors="ignore")
    # 日期放首列
    if "日期" in df.columns:
        cols = ["日期"] + [c for c in df.columns if c != "日期"]
        df = df[cols]
    return df


def clean_stock_folder(stocks_root: str, symbol: str) -> Dict[str, str]:
    stock_dir = os.path.join(stocks_root, symbol)
    if not os.path.isdir(stock_dir):
        raise FileNotFoundError(f"未找到目录: {stock_dir}")
    # 目标输出目录：data/clean_stocks/{symbol}
    data_root = os.path.dirname(stocks_root)  # h股/data
    cleaned_dir = os.path.join(data_root, "clean_stocks", symbol)
    os.makedirs(cleaned_dir, exist_ok=True)

    outputs: Dict[str, str] = {}
    for name in sorted(os.listdir(stock_dir)):
        if not name.endswith(".csv"):
            continue
        in_path = os.path.join(stock_dir, name)
        out_path = os.path.join(cleaned_dir, name)
        try:
            df = pd.read_csv(in_path)
            if df.empty:
                continue
            df = _clean_generic(df, name)
            df.to_csv(out_path, index=False)
            outputs[name] = out_path
        except Exception:
            continue
    return outputs


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(description="清洗 港股 个股数据")
    p.add_argument("--symbol", required=True, help="如 01810")
    args = p.parse_args()

    # h股/src/data/cleaning -> h股
    project_root = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    )
    data_root = os.path.join(project_root, "data", "stocks")
    result = clean_stock_folder(data_root, args.symbol)
    print("Cleaned files:")
    for k, v in result.items():
        print(f"  {k} -> {v}")


