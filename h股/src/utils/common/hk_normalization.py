from __future__ import annotations

from typing import List
import pandas as pd


HK_COL_MAP = {
    "date": "日期",
    "时间": "日期",
    "日期": "日期",
    "open": "开盘",
    "开盘": "开盘",
    "close": "收盘",
    "收盘": "收盘",
    "high": "最高",
    "最高": "最高",
    "low": "最低",
    "最低": "最低",
    "volume": "成交量",
    "成交量": "成交量",
    "amount": "成交额",
    "成交额": "成交额",
}


def normalize_hk_ohlcv(source_df: pd.DataFrame) -> pd.DataFrame:
    """Normalize HK OHLCV dataframe to internal standard columns.

    Target columns (ordered): 日期, 开盘, 收盘, 最高, 最低, 成交量, [成交额]
    - Ensures 日期 is datetime and sorted ascending
    - Fills missing required columns with NA
    """
    if source_df is None or len(source_df) == 0:
        return source_df

    df = source_df.copy()
    df = df.rename(columns={col: HK_COL_MAP.get(col, col) for col in df.columns})

    if "日期" in df.columns:
        df["日期"] = pd.to_datetime(df["日期"], errors="coerce")
        df = df.dropna(subset=["日期"]).sort_values("日期")

    required_cols: List[str] = ["日期", "开盘", "收盘", "最高", "最低", "成交量"]
    optional_cols: List[str] = ["成交额"]

    for col in required_cols:
        if col not in df.columns:
            df[col] = pd.NA

    final_cols: List[str] = required_cols + [c for c in optional_cols if c in df.columns]
    return df[final_cols]


