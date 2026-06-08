from __future__ import annotations

from datetime import datetime, time
from zoneinfo import ZoneInfo

LME_TZ = ZoneInfo("Europe/London")
LME_OPEN = time(1, 0)
LME_CLOSE = time(19, 0)


def is_lme_market_open(now: datetime | None = None) -> bool:
    now_lme = (now or datetime.now(LME_TZ)).astimezone(LME_TZ)
    if now_lme.weekday() >= 5:
        return False
    t = now_lme.time()
    return LME_OPEN <= t < LME_CLOSE
