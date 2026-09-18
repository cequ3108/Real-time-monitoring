"""評分、燈號、價位門檻、倉位檔位。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from .config import POOL, VolumeThreshold, volume_threshold_for_hour


@dataclass
class MarketSnapshot:
    open: float
    high: float
    low: float
    close: float
    change_price: float
    change_rate: float
    volume_ratio_pct: float  # 已 ×100
    amount_yi: float  # 億
    otc_open: float
    otc_close: float
    otc_change_rate: float
    fut_id: str
    fut_close: float
    basis: float
    hour: int


@dataclass
class PriceLines:
    long_line: float
    cons_line: float
    cut_line: float
    open_line: float
    position_label: str  # 做多線上／保守線上／減碼線上／減碼線下


@dataclass
class ScoreResult:
    score: int
    light: str
    threshold: VolumeThreshold
    lines: PriceLines
    tier: str  # 積極加倉｜偏多持有｜保守觀望｜減碼｜清倉防守


@dataclass
class StockRow:
    sid: str
    name: str
    sector: str
    close: float
    open: float
    change_price: float
    change_rate: float
    volume_ratio_pct: float
    above_open: bool
    strength: int
    strength_label: str


def price_lines(o: float, h: float, c: float) -> PriceLines:
    r = max(h - o, 0.0)
    long_l = h - 0.25 * r
    cons_l = h - 0.382 * r
    cut_l = h - 0.50 * r
    if c >= long_l:
        label = "做多線上"
    elif c >= cons_l:
        label = "保守線上"
    elif c >= cut_l:
        label = "減碼線上"
    else:
        label = "減碼線下"
    return PriceLines(long_l, cons_l, cut_l, o, label)


def score_market(m: MarketSnapshot) -> ScoreResult:
    th = volume_threshold_for_hour(m.hour)
    score = 0

    if m.close > m.open:
        score += 2
    elif m.close < m.open:
        score -= 2

    if m.change_rate >= 1:
        score += 2
    elif m.change_rate >= 0.3:
        score += 1
    elif m.change_rate <= -1:
        score -= 2
    elif m.change_rate <= -0.3:
        score -= 1

    if m.volume_ratio_pct >= th.green:
        score += 2
    elif m.volume_ratio_pct >= th.yellow:
        score += 1
    elif m.volume_ratio_pct < th.white:
        score -= 1

    if m.otc_close > m.otc_open:
        score += 1
    elif m.otc_close < m.otc_open:
        score -= 1

    if m.basis > 50:
        score += 1
    elif m.basis < -50:
        score -= 1

    if score >= 4:
        light = "綠燈"
    elif score >= 2:
        light = "黃燈"
    elif score >= 0:
        light = "白燈"
    else:
        light = "紅燈"

    lines = price_lines(m.open, m.high, m.close)
    tier = position_tier(m.close, lines, light, m.volume_ratio_pct, th)
    return ScoreResult(score, light, th, lines, tier)


def position_tier(
    close: float,
    lines: PriceLines,
    light: str,
    vol_pct: float,
    th: VolumeThreshold,
) -> str:
    if close < lines.open_line or light == "紅燈":
        return "清倉防守"
    if close < lines.cut_line:
        return "減碼"
    if close < lines.cons_line:
        return "保守觀望"
    if close < lines.long_line:
        return "偏多持有"
    if light == "綠燈" and vol_pct >= th.yellow:
        return "積極加倉"
    return "偏多持有"


def strength_label(st: int) -> str:
    if st >= 6:
        return "強"
    if st >= 4:
        return "中強"
    if st >= 2:
        return "中"
    if st >= 0:
        return "偏弱"
    return "弱"


def score_stock(
    sid: str,
    close: float,
    open_: float,
    change_price: float,
    change_rate: float,
    volume_ratio_pct: float,
    name_sector: Optional[tuple] = None,
) -> StockRow:
    name, sector = name_sector or POOL.get(sid, (sid, ""))
    above = close >= open_
    st = 2 if above else -2
    if change_rate >= 2:
        st += 3
    elif change_rate >= 1:
        st += 2
    elif change_rate >= 0.5:
        st += 1
    elif change_rate < 0:
        st -= 1
    if volume_ratio_pct >= 150:
        st += 2
    elif volume_ratio_pct >= 100:
        st += 1
    return StockRow(
        sid=sid,
        name=name,
        sector=sector,
        close=close,
        open=open_,
        change_price=change_price,
        change_rate=change_rate,
        volume_ratio_pct=volume_ratio_pct,
        above_open=above,
        strength=st,
        strength_label=strength_label(st),
    )


def select_longs(rows: List[StockRow], max_n: int = 6) -> List[StockRow]:
    cands = [r for r in rows if r.above_open and r.change_rate >= 0.3]
    cands.sort(key=lambda r: (-r.strength, -r.change_rate))
    return cands[:max_n]


def select_relative(rows: List[StockRow], max_n: int = 6) -> List[StockRow]:
    rows = sorted(rows, key=lambda r: (-r.strength, -r.change_rate))
    return rows[:max_n]
