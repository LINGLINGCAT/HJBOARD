from __future__ import annotations

import io
import math
from datetime import datetime

import pandas as pd
import requests

LME_URL = "https://quote.fx678.com/exchange/LME"
BOT_URL = "https://rate.bot.com.tw/xrt?Lang=zh-TW"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}


def fetch_lme_data() -> tuple[pd.DataFrame, str | None]:
    try:
        response = requests.get(LME_URL, headers=HEADERS, timeout=15)
        response.raise_for_status()
        tables = pd.read_html(io.StringIO(response.text))
        df = tables[0]
        df = df.rename(
            columns={
                df.columns[0]: "名稱",
                df.columns[1]: "最新價",
                df.columns[2]: "漲跌",
                df.columns[3]: "漲跌幅",
            }
        )
        df = df[["名稱", "最新價", "漲跌", "漲跌幅"]]
        df["抓取時間"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return df, None
    except Exception as e:
        return pd.DataFrame(), f"LME 載入失敗: {e}"


def fetch_bot_fx_data() -> tuple[pd.DataFrame, str | None]:
    try:
        response = requests.get(BOT_URL, headers=HEADERS, timeout=15)
        response.raise_for_status()
        tables = pd.read_html(io.StringIO(response.text), header=[0, 1])
        df = tables[0]
        currency_col = [col for col in df.columns if "幣別" in col[0]][0]
        buy_cols = [col for col in df.columns if col[1] == "本行買入"]
        sell_cols = [col for col in df.columns if col[1] == "本行賣出"]

        def pick_spot_col(cols_to_check, df_to_check):
            for col in cols_to_check:
                vals = pd.to_numeric(df_to_check[col], errors="coerce")
                if vals.notna().sum() > 0 and vals.max() < 100 and vals.min() > 0.1:
                    return col
            return None

        spot_buy_col = pick_spot_col(buy_cols, df)
        spot_sell_col = pick_spot_col(sell_cols, df)
        if not (currency_col and spot_buy_col and spot_sell_col):
            return pd.DataFrame(), "找不到正確的即期買入/賣出欄位"

        df_fx = df[[currency_col, spot_sell_col, spot_buy_col]].copy()
        df_fx.columns = ["幣別", "即期買入", "即期賣出"]
        df_fx["即期中間價"] = (
            pd.to_numeric(df_fx["即期買入"], errors="coerce")
            + pd.to_numeric(df_fx["即期賣出"], errors="coerce")
        ) / 2
        df_fx["幣別代碼"] = df_fx["幣別"].str.extract(r"([A-Z]{3})")
        return df_fx, None
    except Exception as e:
        return pd.DataFrame(), f"台銀匯率載入失敗: {e}"


def _find_lme_price(df_lme: pd.DataFrame, names: list[str]) -> float | None:
    for _, row in df_lme.iterrows():
        label = str(row["名稱"]).replace(" ", "")
        for name in names:
            if name in label:
                return float(
                    pd.to_numeric(
                        str(row["最新價"]).replace(",", ""),
                        errors="coerce",
                    )
                )
    return None


def _get_usd_mid(df_fx: pd.DataFrame) -> float | None:
    usd = df_fx[df_fx["幣別代碼"] == "USD"]
    if usd.empty:
        return None
    buy = pd.to_numeric(usd["即期買入"].iloc[0], errors="coerce")
    sell = pd.to_numeric(usd["即期賣出"].iloc[0], errors="coerce")
    return float((buy + sell) / 2)


def round_to_half(value: float) -> float:
    integer = math.floor(value)
    frac = value - integer
    if frac < 0.5:
        return float(integer)
    return integer + 0.5


def _fmt_price(value: float) -> str:
    v = round_to_half(value)
    if v == int(v):
        return str(int(v))
    return f"{v:.1f}"


def calculate_board_prices(
    df_lme: pd.DataFrame, df_fx: pd.DataFrame
) -> tuple[list[dict], str | None]:
    from utils.pricing_core import build_quote_rows

    return build_quote_rows(df_lme, df_fx)
