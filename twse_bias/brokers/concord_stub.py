"""
康和證券 API 接點（本機 stub）。

說明：
- 雲端 Linux 無法直接跑康和官方元件（需 Windows + .NET + 申請開通）。
- 請在本機用官方 API 或 conrich 查庫存後，寫成 positions.json。
- 或實作 fetch_positions_from_concord() 後匯出相同格式。

官方申請：https://stock.concords.com.tw/trade_071.html
社群封裝參考：https://concords6016.github.io/conrich_docs/
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


def positions_to_file(positions: List[Dict[str, Any]], path: str | Path) -> None:
    """寫入助手可讀格式。"""
    Path(path).write_text(
        json.dumps({"positions": positions}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def fetch_positions_from_concord() -> List[Dict[str, Any]]:
    """
    TODO：在本機接康和 API／conrich。

    預期回傳：
    [
      {"sid": "2303", "name": "聯電", "shares": 2000, "cost": 152.0},
      ...
    ]
    """
    raise NotImplementedError(
        "請在 Windows 本機實作康和庫存查詢，或手動維護 data/positions.json"
    )


if __name__ == "__main__":
    # 示範：把手動庫存寫成檔
    demo = [
        {"sid": "2303", "name": "聯電", "shares": 2000, "cost": 152.0},
        {"sid": "2454", "name": "聯發科", "shares": 100, "cost": 4550.0},
    ]
    out = Path(__file__).resolve().parents[2] / "data" / "positions.example.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    positions_to_file(demo, out)
    print(f"wrote {out}")
