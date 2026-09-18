"""部位載入與倉位建議文案。"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from .scoring import PriceLines, ScoreResult, StockRow


@dataclass
class Position:
    sid: str
    shares: float
    cost: Optional[float] = None
    name: str = ""


def load_positions(path: str | Path) -> List[Position]:
    p = Path(path)
    if not p.exists():
        return []
    data = json.loads(p.read_text(encoding="utf-8"))
    items = data.get("positions", data if isinstance(data, list) else [])
    out: List[Position] = []
    for it in items:
        out.append(
            Position(
                sid=str(it["sid"]),
                shares=float(it.get("shares") or it.get("qty") or 0),
                cost=float(it["cost"]) if it.get("cost") is not None else None,
                name=str(it.get("name") or ""),
            )
        )
    return [x for x in out if x.shares > 0]


def build_position_advice(
    result: ScoreResult,
    longs: List[StockRow],
    positions: Optional[List[Position]] = None,
) -> str:
    """產出【倉位建議】純文字區塊。"""
    lines = result.lines
    tier = result.tier
    positions = positions or []
    held = {p.sid: p for p in positions}

    openable = [r for r in longs if r.above_open][:3]
    chase = [r for r in longs if r.change_rate >= 5]  # 漲多提醒

    blocks: List[str] = []
    blocks.append("【倉位建議】")
    blocks.append("")
    blocks.append(f"本輪倉位檔位：{tier}")
    blocks.append("")

    # 積極
    blocks.append("積極加倉／可開倉：")
    if tier == "積極加倉" and openable:
        names = "、".join(f"{r.name}({r.sid})" for r in openable)
        blocks.append(f"可對 {names} 分批開／加；單檔先 3–5 成試單，破開停損。")
    elif tier in ("偏多持有", "保守觀望") and openable:
        prefer = [r for r in openable if abs(r.close - r.open) / r.open <= 0.01 or r.change_rate < 4]
        if prefer:
            names = "、".join(f"{r.name}({r.sid})@{r.close:g}" for r in prefer[:2])
            blocks.append(f"僅平開附近可小開：{names}；漲多近高者不追。")
        else:
            blocks.append("暫不積極加倉；等回測開盤或站回做多線。")
    else:
        blocks.append("條件未達（未站做多線／量能不足／檔位偏弱），不做積極加倉。")
    blocks.append("")

    # 保守
    blocks.append("保守持有／觀望：")
    if tier in ("偏多持有", "保守觀望", "減碼"):
        if held:
            strong_held = [p for p in positions if p.sid in {r.sid for r in longs}]
            weak_held = [p for p in positions if p.sid not in {r.sid for r in longs}]
            if strong_held:
                blocks.append(
                    "已持股強勢可留核心："
                    + "、".join(f"{p.name or p.sid}({p.sid})" for p in strong_held)
                    + "；不加碼。"
                )
            if weak_held:
                blocks.append(
                    "已持股偏弱先觀望／準備減："
                    + "、".join(f"{p.name or p.sid}({p.sid})" for p in weak_held)
                )
            if not strong_held and not weak_held:
                blocks.append("已持股維持、不加倉；空手慎開。")
        else:
            blocks.append("空手慎開；已持股（若有）維持核心、不加倉。")
    elif tier == "積極加倉":
        blocks.append("既有強勢倉可續抱；弱勢破開者不納入保守續抱。")
    else:
        blocks.append("防守為主，不做新多的保守試倉。")
    blocks.append("")

    # 減碼
    blocks.append("減碼／停損：")
    if tier == "清倉防守":
        blocks.append(f"大盤低於開盤防守 {lines.open_line:.0f} 或紅燈 → 大幅減／清倉，停止新開多。")
    elif tier == "減碼":
        blocks.append(
            f"現價低於減碼線 {lines.cut_line:.0f}：總部位先降到半倉或更低；破開個股優先減。"
        )
    else:
        blocks.append(
            f"若跌破減碼線 {lines.cut_line:.0f} 開始降倉；跌破開盤 {lines.open_line:.0f} 改清倉防守。"
        )
    if chase:
        blocks.append(
            "漲多近高可先減獲利："
            + "、".join(f"{r.name}({r.sid})" for r in chase[:3])
        )
    if held:
        broken = []
        # 沒有即時價時僅提示：破開標的請對照本輪弱勢
        blocks.append("請對照本輪破開觀察股，有倉則優先減碼。")

    blocks.append("")
    blocks.append(
        f"（門檻）做多 {lines.long_line:.0f}｜保守 {lines.cons_line:.0f}｜"
        f"減碼 {lines.cut_line:.0f}｜開盤 {lines.open_line:.0f}｜現況 {lines.position_label}"
    )
    return "\n".join(blocks)
