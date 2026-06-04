from __future__ import annotations

from utils.data_fetch import _find_lme_price, _fmt_price, _get_usd_mid
from utils.secrets_config import load_pricing_config


def _num(section: dict, key: str) -> float:
    return float(section[key])


def _rate(items: dict, key: str) -> float:
    return _num(items, key) / 1000


def _b(cu: float, sn: float, zn: float, fx: float, alloy: dict) -> tuple[float, float, float, float]:
    r = cu / 1000 * fx
    p = (cu * _num(alloy, "cu_sn_cu") / 100 + sn * _num(alloy, "cu_sn_sn") / 100) / 1000 * fx
    q = (cu * _num(alloy, "cu_zn_cu") / 100 + zn * _num(alloy, "cu_zn_zn") / 100) / 1000 * fx
    d = (cu * _num(alloy, "cu_dq_cu") / 100 + zn * _num(alloy, "cu_dq_zn") / 100) / 1000 * fx
    return r, p, q, d


def build_quote_rows(df_lme, df_fx) -> tuple[list[dict], str | None]:
    if df_lme.empty or df_fx.empty:
        return [], "無法取得 LME 或匯率資料"

    try:
        alloy, items = load_pricing_config()
    except KeyError:
        return [], "暫時無法顯示報價，請稍後再試"

    fx = _get_usd_mid(df_fx)
    cu = _find_lme_price(df_lme, ["LME铜", "LME銅"])
    sn = _find_lme_price(df_lme, ["LME锡", "LME錫"])
    zn = _find_lme_price(df_lme, ["LME锌", "LME鋅"])

    if None in (fx, cu, sn, zn):
        return [], "缺少 LME 銅/錫/鋅或美金匯率"

    r, p, q, d = _b(cu, sn, zn, fx, alloy)

    def row(
        name: str,
        val: float,
        col: int,
        lines: list[str] | None = None,
    ) -> dict:
        out = {"品名": name, "單價": _fmt_price(val), "col": col}
        if lines:
            out["品名_lines"] = lines
        return out

    return [
        row("仁碎", p * _rate(items, "ren_sui"), 1),
        row("紅碎", r * _rate(items, "hong_sui"), 1),
        row("青碎", q * _rate(items, "qing_sui"), 1),
        row(
            "青電",
            q * _rate(items, "qing_dian") - _num(items, "qing_dian_sub"),
            1,
        ),
        row("光亮線", r * _rate(items, "guang_liang_xian"), 2),
        row("光亮米", r * _rate(items, "guang_liang_mi"), 2),
        row(
            "乾淨紅銅管/破碎銅(註一)",
            r * _rate(items, "gan_jing"),
            2,
            ["乾淨紅銅管 / 乾淨粗鍍錫", "線、板 / 破碎銅(註一)"],
        ),
        row("次級紅清", r * _rate(items, "ci_ji"), 2),
        row("馬達銅", r * _rate(items, "ma_da"), 2),
        row("紅雜銅", r * _rate(items, "hong_za"), 2),
        row("大青", d * _rate(items, "da_qing"), 3),
        row("中銅", d * _rate(items, "zhong_tong"), 3),
    ], None
