from __future__ import annotations

import base64
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import streamlit as st
import streamlit.components.v1 as components
from streamlit_autorefresh import st_autorefresh

from utils.data_fetch import calculate_board_prices, fetch_bot_fx_data, fetch_lme_data

COMPANY_NAME = "聖展金屬有限公司"
LINE_PHONE = "0903226073"
WEBSITE_URL = "https://www.hungjan.com"
WEBSITE_LABEL = "www.hungjan.com"
QR_PATH = Path(__file__).resolve().parent / "assets" / "line_qr.png"

FOOTER_LINES = [
    ("銅價波動大，實際成交價格依據數量、品質、訂單及LME浮動調整", True),
    ("全品項訂單皆有限額，如當日收貨量足夠則會停止接單，請先來電確認", True),
    ("貨品需整理，實際來貨品質有落差則以現場報價為主", False),
    ("出貨請直接加Line提供數量跟照片，確認價格後才安排送貨時間", False),
    ("無回覆可能是訊息眾多被覆蓋，請再傳一次。", False),
    (
        "本公司為政府立案甲級廢棄物清除機構，具備國內外多元金屬循環通路，"
        "另與甲級處理廠合作，流程皆 100% 合法合規值得信賴。",
        False,
    ),
]

NOTE_ONE = "註一:需乾淨無油無雜質，銅管、粗鍍錫線、鍍錫板需分開裝"
TZ_TAIPEI = ZoneInfo("Asia/Taipei")

MARKET_NOTICE_TITLE = "請注意"
MARKET_NOTICE_LINES = [
    "本看板價格依國際銅價更新",
    "國際市場休市期間（週末及部分假日）不會產生新報價，因此價格將維持最後收盤價",
]

DISCLAIMER = (
    "【免責聲明】本看板所示價格僅供參考，非成交承諾；"
    "實際收購價格須經本公司電話或 LINE 確認後方為有效報價，未確認前不構成交易要約。"
)


def _qr_img_tag() -> str:
    if not QR_PATH.exists():
        return ""
    b64 = base64.b64encode(QR_PATH.read_bytes()).decode("ascii")
    return f'<img class="line-qr" src="data:image/png;base64,{b64}" alt="LINE" />'


def _render_price_table(rows: list[dict], col: int, wide: bool = False) -> str:
    items = [r for r in rows if r["col"] == col]
    cls = "price-table wide-table" if wide else "price-table"
    body = ""
    for r in items:
        if r.get("品名_lines"):
            lines = r["品名_lines"]
            label = "".join(f'<div class="name-line">{ln}</div>' for ln in lines)
            name_cls = "cell-name cell-name-split"
        else:
            label = r["品名"]
            name_cls = "cell-name"
        body += (
            f"<tr><td class='{name_cls}'>{label}</td>"
            f"<td class='cell-price'>{r['單價']}</td></tr>"
        )
    return f"""
    <table class="{cls}">
        <thead><tr><th>品名</th><th>價格</th></tr></thead>
        <tbody>{body}</tbody>
    </table>
    """


def _build_board_html(
    rows: list[dict],
    today: str,
    updated_at: str,
    side_html: str,
    qr_block: str,
) -> str:
    col1 = _render_price_table(rows, 1)
    col2 = _render_price_table(rows, 2, wide=True)
    col3 = _render_price_table(rows, 3)
    notice_body = "".join(f"<p>{line}</p>" for line in MARKET_NOTICE_LINES)

    return f"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, minimum-scale=1, maximum-scale=5, user-scalable=yes">
<style>
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
    font-family: "Microsoft JhengHei", "Noto Sans TC", "PingFang TC", sans-serif;
    color: #1a1a1a;
    background: #fff;
    padding: 8px;
}}
.board-wrap {{
    border: 1px solid #c8d0d8;
    border-radius: 8px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.07);
    padding: 18px 20px 20px;
    max-width: 100%;
    overflow: hidden;
}}
.board-header {{
    display: flex;
    align-items: baseline;
    flex-wrap: wrap;
    gap: 10px 16px;
    border-bottom: 2px solid #1e4f8a;
    padding-bottom: 12px;
    margin-bottom: 16px;
}}
.board-header-main {{
    display: flex;
    align-items: baseline;
    flex-wrap: wrap;
    gap: 8px 18px;
}}
.board-title {{
    font-size: clamp(1.35rem, 4vw, 2rem);
    font-weight: 700;
    letter-spacing: 0.1em;
    white-space: nowrap;
}}
.board-updated {{
    font-size: clamp(0.88rem, 2.2vw, 1.05rem);
    font-weight: 600;
    color: #555;
    white-space: nowrap;
}}
.market-notice {{
    margin-bottom: 14px;
    padding: 10px 12px;
    background: #f0f4f8;
    border: 1px solid #c8d0d8;
    border-radius: 6px;
}}
.market-notice-title {{
    font-size: clamp(0.95rem, 2.2vw, 1.1rem);
    font-weight: 700;
    color: #1e4f8a;
    margin-bottom: 6px;
}}
.market-notice p {{
    margin: 0 0 4px 0;
    font-size: clamp(0.82rem, 1.9vw, 0.95rem);
    line-height: 1.55;
    color: #333;
}}
.market-notice p:last-child {{ margin-bottom: 0; }}
.board-body {{
    display: flex;
    gap: 18px;
    align-items: flex-start;
}}
.board-left {{
    flex: 1;
    min-width: 0;
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
}}
.board-grid {{
    display: flex;
    gap: 10px;
    min-width: min(100%, 720px);
}}
.board-grid > .tbl-box {{
    flex: 1 1 0;
    min-width: 0;
}}
.board-grid > .tbl-box.wide {{
    flex: 1.55 1 0;
    min-width: 200px;
}}
.note-under-table {{
    margin-top: 8px;
    padding: 6px 4px 0;
    font-size: clamp(0.82rem, 1.8vw, 0.95rem);
    line-height: 1.5;
    text-align: center;
    color: #333;
}}
.price-table {{
    width: 100%;
    border-collapse: collapse;
    table-layout: fixed;
}}
.price-table th,
.price-table td {{
    border: 1px solid #4a5568;
    padding: 10px 6px;
    text-align: center;
    vertical-align: middle;
    word-wrap: break-word;
    overflow-wrap: break-word;
}}
.price-table th {{
    background: #e8eef4;
    font-weight: 700;
    font-size: clamp(0.95rem, 2.2vw, 1.15rem);
    color: #1e4f8a;
}}
.price-table td.cell-name {{
    width: 68%;
    font-size: clamp(1rem, 2.4vw, 1.22rem);
    line-height: 1.4;
}}
.price-table td.cell-name-split {{
    width: 72%;
    font-size: clamp(1rem, 2.4vw, 1.22rem);
    line-height: 1.4;
    padding: 10px 5px;
}}
.price-table td.cell-name-split .name-line {{
    display: block;
    text-align: center;
    margin: 2px 0;
}}
.price-table td.cell-price {{
    width: 32%;
    font-weight: 700;
    font-size: clamp(1.1rem, 2.8vw, 1.45rem);
    color: #0d3d6e;
    white-space: nowrap;
}}
.board-side {{
    flex: 0 0 280px;
    max-width: 300px;
    border-left: 2px solid #e2e8f0;
    padding-left: 14px;
}}
.board-side p {{
    margin: 0 0 6px 0;
    font-size: 0.84rem;
    line-height: 1.55;
}}
.board-side .emph {{ color: #b91c1c; font-weight: 700; }}
.board-contact {{
    font-size: 0.92rem;
    font-weight: 700;
    margin-top: 6px !important;
}}
.disclaimer-box {{
    margin-top: 10px;
    padding: 8px 10px;
    background: #f8f4e8;
    border-left: 4px solid #c9a227;
    font-size: 0.8rem;
    line-height: 1.5;
    color: #444;
}}
.website-row {{
    margin-top: 8px;
    font-size: 0.84rem;
}}
.website-row a {{ color: #1e4f8a; font-weight: 600; text-decoration: none; }}
.board-side-qr {{ text-align: center; margin-top: 10px; }}
.line-qr {{
    width: 130px;
    height: 130px;
    max-width: 100%;
    border: 1px solid #ddd;
    border-radius: 4px;
}}
.qr-caption {{ font-size: 0.78rem; color: #555; margin-top: 5px; }}

@media (max-width: 900px) {{
    body {{
        padding: 10px 6px;
        -webkit-text-size-adjust: 100%;
        text-size-adjust: 100%;
    }}
    .board-wrap {{ padding: 16px 12px 18px; }}
    .board-title {{ font-size: 1.65rem; }}
    .board-updated {{ font-size: 1rem; }}
    .board-header-main {{
        flex-direction: column;
        align-items: flex-start;
        gap: 4px;
    }}
    .board-updated {{ white-space: normal; }}
    .board-body {{ flex-direction: column; }}
    .board-side {{
        flex: none;
        max-width: 100%;
        width: 100%;
        border-left: none;
        border-top: 2px solid #e2e8f0;
        padding-left: 0;
        padding-top: 14px;
    }}
    .board-side p {{ font-size: 1rem; }}
    .board-contact {{ font-size: 1.05rem; }}
    .disclaimer-box {{ font-size: 0.95rem; }}
    .website-row {{ font-size: 1rem; }}
    .qr-caption {{ font-size: 0.9rem; }}
    .line-qr {{ width: 150px; height: 150px; }}
    .board-grid {{
        flex-direction: column;
        min-width: 0;
    }}
    .board-grid > .tbl-box,
    .board-grid > .tbl-box.wide {{
        flex: none;
        width: 100%;
        min-width: 0;
    }}
    .price-table th,
    .price-table td {{
        padding: 12px 8px;
    }}
    .price-table th {{ font-size: 1.15rem; }}
    .price-table td.cell-name {{ font-size: 1.2rem; }}
    .price-table td.cell-name-split {{ font-size: 1.2rem; }}
    .price-table td.cell-name-split .name-line {{ margin: 4px 0; }}
    .price-table td.cell-price {{ font-size: 1.45rem; }}
    .note-under-table {{ font-size: 0.95rem; text-align: left; padding: 8px 2px 0; }}
    .market-notice {{ margin-bottom: 12px; }}
    .market-notice-title {{ font-size: 1.05rem; }}
    .market-notice p {{ font-size: 0.95rem; }}
}}
@media (max-width: 480px) {{
    .board-title {{ font-size: 1.5rem; }}
    .price-table th {{ font-size: 1.1rem; }}
    .price-table td.cell-name {{ font-size: 1.15rem; }}
    .price-table td.cell-name-split {{ font-size: 1.15rem; }}
    .price-table td.cell-price {{ font-size: 1.35rem; }}
}}
</style>
</head>
<body>
<div class="board-wrap">
    <div class="board-header">
        <div class="board-header-main">
            <div class="board-title">{COMPANY_NAME}</div>
            <div class="board-updated">報價更新時間：{updated_at}</div>
        </div>
    </div>
    <div class="market-notice">
        <div class="market-notice-title">{MARKET_NOTICE_TITLE}</div>
        {notice_body}
    </div>
    <div class="board-body">
        <div class="board-left">
            <div class="board-grid">
                <div class="tbl-box">{col1}</div>
                <div class="tbl-box wide">
                    {col2}
                    <p class="note-under-table">{NOTE_ONE}</p>
                </div>
                <div class="tbl-box">{col3}</div>
            </div>
        </div>
        <div class="board-side">
            {side_html}
            <p class="board-contact">手機號碼/Line:{LINE_PHONE}</p>
            <div class="disclaimer-box">{DISCLAIMER}</div>
            <p class="website-row">
                宏展金屬企業網站：
                <a href="{WEBSITE_URL}" target="_blank" rel="noopener">{WEBSITE_LABEL}</a>
            </p>
            {qr_block}
        </div>
    </div>
</div>
</body>
</html>"""


def _price_signature(rows: list[dict]) -> tuple[str, ...]:
    return tuple(r["單價"] for r in rows)


def _load_board_cache() -> tuple[list[dict], str, str | None]:
    cache = st.session_state.get("board_cache")

    df_lme, lme_err = fetch_lme_data()
    df_fx, fx_err = fetch_bot_fx_data()
    if lme_err or fx_err:
        if cache is not None:
            return cache["rows"], cache["updated_at"], None
        return [], "", lme_err or fx_err

    rows, calc_err = calculate_board_prices(df_lme, df_fx)
    if calc_err:
        if cache is not None:
            return cache["rows"], cache["updated_at"], None
        return [], "", calc_err

    signature = _price_signature(rows)
    if cache is None or cache.get("signature") != signature:
        updated_at = datetime.now(TZ_TAIPEI).strftime("%Y/%m/%d %H:%M")
    else:
        updated_at = cache["updated_at"]

    st.session_state.board_cache = {
        "rows": rows,
        "updated_at": updated_at,
        "signature": signature,
    }
    return rows, updated_at, None


def main() -> None:
    st.set_page_config(
        page_title="聖展金屬 收購報價",
        page_icon="📋",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    st_autorefresh(interval=20000, key="hj_autorefresh")

    st.markdown(
        """
        <meta name="viewport" content="width=device-width, initial-scale=1,
        minimum-scale=1, maximum-scale=5, user-scalable=yes">
        <style>
        #MainMenu, footer, header {visibility: hidden;}
        .block-container {padding-top: 0.5rem; max-width: 100% !important;}
        .stApp { -webkit-text-size-adjust: 100%; }
        iframe { width: 100% !important; max-width: 100% !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    today = datetime.now(TZ_TAIPEI).strftime("%Y/%m/%d")
    rows, updated_at, load_err = _load_board_cache()

    if load_err:
        st.error(load_err)
        return

    if not rows:
        st.error("暫時無法顯示報價，請稍後再試")
        return

    side_html = ""
    for text, is_emph in FOOTER_LINES:
        side_html += f"<p class='{'emph' if is_emph else ''}'>{text}</p>"

    qr = _qr_img_tag()
    qr_block = (
        f'<div class="board-side-qr">{qr}<div class="qr-caption">掃碼加 LINE</div></div>'
        if qr
        else ""
    )

    html_doc = _build_board_html(rows, today, updated_at, side_html, qr_block)
    components.html(html_doc, height=1140, scrolling=True)


if __name__ == "__main__":
    main()
