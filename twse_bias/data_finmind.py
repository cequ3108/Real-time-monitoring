"""FinMind 行情抓取。"""

from __future__ import annotations

import os
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from .config import EXTRA_MIDLARGE, POOL_IDS
from .scoring import MarketSnapshot, StockRow, score_stock

TZ = timezone(timedelta(hours=8))


def _f(x: Any, d: float = 0.0) -> float:
    try:
        if x is None or x == "":
            return d
        return float(x)
    except (TypeError, ValueError):
        return d


def _today() -> str:
    return datetime.now(TZ).strftime("%Y-%m-%d")


def make_loader():
    from FinMind.data import DataLoader

    token = os.environ.get("FINMIND_TOKEN")
    if not token:
        raise RuntimeError("請設定環境變數 FINMIND_TOKEN")
    dl = DataLoader()
    dl.login_by_token(api_token=token)
    return dl


def snap_stock(dl, sid: str, retries: int = 1, sleep_s: float = 0.55) -> Optional[Dict[str, Any]]:
    today = _today()
    for attempt in range(retries + 1):
        try:
            time.sleep(sleep_s)
            df = dl.taiwan_stock_tick_snapshot(stock_id=sid)
            if df is None or len(df) == 0:
                continue
            row = df.iloc[0].to_dict()
            d = str(row.get("date", ""))[:10]
            if d and d != today:
                return None  # 隔夜殘值
            row["stock_id"] = sid
            return row
        except Exception:
            time.sleep(1.2)
    return None


def fetch_futures_best(dl) -> Dict[str, Any]:
    today = _today()
    time.sleep(0.5)
    df = dl.taiwan_futures_snapshot(futures_id="TXF")
    recs = df.to_dict(orient="records") if df is not None else []
    today_recs = [r for r in recs if str(r.get("date", ""))[:10] == today]
    pool = today_recs or recs
    if not pool:
        return {}
    return max(pool, key=lambda r: _f(r.get("total_volume")))


def fetch_market_and_pool(
    include_extra: bool = True,
) -> tuple[MarketSnapshot, List[StockRow], List[StockRow], Dict[str, Any]]:
    """回傳 (大盤快照, 池內列, 池外強勢列, 原始meta)。"""
    dl = make_loader()
    now = datetime.now(TZ)
    today = now.strftime("%Y-%m-%d")

    idx = snap_stock(dl, "001")
    otc = snap_stock(dl, "101")
    if not idx or not otc:
        raise RuntimeError("無法取得 001/101 快照")

    fut = fetch_futures_best(dl)
    fut_px = _f(fut.get("close"))
    spot = _f(idx["close"])
    basis = fut_px - spot

    m = MarketSnapshot(
        open=_f(idx["open"]),
        high=_f(idx["high"]),
        low=_f(idx["low"]),
        close=spot,
        change_price=_f(idx["change_price"]),
        change_rate=_f(idx["change_rate"]),
        volume_ratio_pct=_f(idx.get("volume_ratio")) * 100,
        amount_yi=_f(idx.get("total_amount")) / 1e8,
        otc_open=_f(otc["open"]),
        otc_close=_f(otc["close"]),
        otc_change_rate=_f(otc["change_rate"]),
        fut_id=str(fut.get("futures_id") or "TXF"),
        fut_close=fut_px,
        basis=basis,
        hour=now.hour,
    )

    pool_rows: List[StockRow] = []
    for sid in POOL_IDS:
        r = snap_stock(dl, sid)
        if not r:
            continue
        pool_rows.append(
            score_stock(
                sid,
                _f(r["close"]),
                _f(r["open"]),
                _f(r["change_price"]),
                _f(r["change_rate"]),
                _f(r.get("volume_ratio")) * 100,
            )
        )

    extra_rows: List[StockRow] = []
    if include_extra:
        for sid, (name, sector) in EXTRA_MIDLARGE.items():
            r = snap_stock(dl, sid)
            if not r:
                continue
            row = score_stock(
                sid,
                _f(r["close"]),
                _f(r["open"]),
                _f(r["change_price"]),
                _f(r["change_rate"]),
                _f(r.get("volume_ratio")) * 100,
                name_sector=(name, sector),
            )
            if row.above_open and row.change_rate >= 1.5:
                extra_rows.append(row)
        extra_rows.sort(key=lambda x: -x.change_rate)

    meta = {"today": today, "ts": now.isoformat(), "fut_raw": fut}
    return m, pool_rows, extra_rows, meta
