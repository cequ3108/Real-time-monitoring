"""報告組裝（純文字繁中）。"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List, Optional

from .positions import Position, build_position_advice
from .scoring import MarketSnapshot, ScoreResult, StockRow, select_longs, select_relative

TZ = timezone(timedelta(hours=8))


def _fmt_stock(r: StockRow) -> str:
    sign_p = f"{r.change_price:+g}" if r.change_price else f"{r.change_price:g}"
    return (
        f"{r.name}({r.sid})｜{r.sector}｜{r.close:g}（{sign_p}／{r.change_rate:+.2f}%）"
        f"｜量比昨約 {r.volume_ratio_pct:.0f}%｜{r.strength_label}"
    )


def render_report(
    m: MarketSnapshot,
    result: ScoreResult,
    pool_rows: List[StockRow],
    extra_rows: Optional[List[StockRow]] = None,
    positions: Optional[List[Position]] = None,
    hhmm: Optional[str] = None,
) -> str:
    hhmm = hhmm or datetime.now(TZ).strftime("%H:%M")
    th = result.threshold
    lines = result.lines

    if result.light in ("綠燈", "黃燈"):
        picks = select_longs(pool_rows)
        pick_title = "【可做多標的（強勢優先）】"
    else:
        picks = select_relative(pool_rows)
        pick_title = "【相對強勢（僅供優先順序參考）】"

    parts: List[str] = []
    parts.append(f"【{hhmm}｜{result.light}｜分數 {result.score}】")
    parts.append("")
    parts.append(
        f"大盤：開 {m.open:g}　高 {m.high:g}　低 {m.low:g}　現 {m.close:g}"
        f"（{m.change_price:+g}／{m.change_rate:+.2f}%）"
    )
    parts.append("")
    parts.append(f"成交金額：約 {m.amount_yi:.0f} 億")
    parts.append("")
    parts.append(
        f"量能白話：約昨天全天的 {m.volume_ratio_pct:.0f}%"
        f"（門檻綠{th.green:.0f}／黃{th.yellow:.0f}／白{th.white:.0f}）"
    )
    parts.append("")
    parts.append(f"此時間門檻：{th.green:.0f}／{th.yellow:.0f}／{th.white:.0f}")
    parts.append("")
    parts.append(
        f"櫃買：{m.otc_close:g}（開 {m.otc_open:g}，{m.otc_change_rate:+.2f}%）"
    )
    parts.append("")
    parts.append(f"期貨：{m.fut_id} {m.fut_close:g}｜期現差約 {m.basis:+.0f}")
    parts.append("")
    parts.append(
        f"價位門檻：做多 {lines.long_line:.0f}｜保守 {lines.cons_line:.0f}｜"
        f"減碼 {lines.cut_line:.0f}｜開盤防守 {lines.open_line:.0f}"
    )
    parts.append("")
    parts.append(f"現價相對：{lines.position_label}")
    parts.append("")
    parts.append(build_position_advice(result, picks, positions))
    parts.append("")

    # 建議一句
    advice = {
        "積極加倉": "偏多且站上做多線，強勢股可積極加／開，仍設破開停損。",
        "偏多持有": "偏多持有，可小加不可追高。",
        "保守觀望": "落在保守～減碼區，空手慎開、已持股不加。",
        "減碼": "低於減碼線，先降倉；空手暫不開。",
        "清倉防守": "跌破開盤或紅燈，以防守／清倉為主。",
    }.get(result.tier, "依倉位檔位操作。")
    parts.append(f"建議：{advice}")
    parts.append("")
    parts.append(
        f"依據：{result.light}（{result.score}分）、量能 {m.volume_ratio_pct:.0f}%、"
        f"期現差 {m.basis:+.0f}、現況 {lines.position_label}。"
    )
    parts.append("")
    parts.append("---")
    parts.append("")
    parts.append(pick_title)
    parts.append("")
    if not picks:
        parts.append("（本輪無符合條件標的）")
        parts.append("")
    else:
        for i, r in enumerate(picks, 1):
            parts.append(f"{i}. {_fmt_stock(r)}")
            parts.append("")

    if extra_rows:
        tops = extra_rows[:5]
        ref = "、".join(f"{r.name}({r.sid}){r.change_rate:+.2f}%" for r in tops)
        parts.append(f"池外中大型參考：{ref}")
        parts.append("")

    parts.append("---")
    parts.append("")
    parts.append("【觀察股】")
    parts.append("")
    by_id = {r.sid: r for r in pool_rows}
    for i, sid in enumerate(["2330", "0050", "2303", "2324", "3231"], 1):
        r = by_id.get(sid)
        if not r:
            parts.append(f"{i}. {sid}｜資料缺失")
        else:
            flag = "站上開盤" if r.above_open else "跌破開盤"
            parts.append(
                f"{i}. {r.name}({sid})：{r.close:g}｜{flag}（{r.change_rate:+.2f}%）"
            )
        parts.append("")

    weak = [r for r in pool_rows if not r.above_open]
    if weak:
        parts.append(
            "另：破開暫不列做多 → "
            + "／".join(f"{r.name}" for r in weak[:8])
        )
        parts.append("")

    parts.append("僅分析建議，不構成投資建議。")
    return "\n".join(parts)
