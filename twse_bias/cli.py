"""CLI：本地產出盤中多空＋倉位報告。"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .data_finmind import fetch_market_and_pool
from .positions import load_positions
from .report import render_report
from .scoring import score_market

TZ = timezone(timedelta(hours=8))


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="台股盤中多空助手（偏做多）")
    p.add_argument("cmd", choices=["report"], help="report=輸出純文字報告")
    p.add_argument("--positions", default="", help="positions.json 路徑（康和庫存匯出）")
    p.add_argument("--no-extra", action="store_true", help="不抓池外中大型")
    p.add_argument("--save-json", default="", help="可選：存原始評分 JSON")
    args = p.parse_args(argv)

    if args.cmd == "report":
        m, pool_rows, extra_rows, meta = fetch_market_and_pool(
            include_extra=not args.no_extra
        )
        result = score_market(m)
        positions = load_positions(args.positions) if args.positions else []
        text = render_report(
            m,
            result,
            pool_rows,
            extra_rows=extra_rows,
            positions=positions or None,
        )
        print(text)
        if args.save_json:
            Path(args.save_json).write_text(
                json.dumps(
                    {
                        "meta": meta,
                        "tier": result.tier,
                        "light": result.light,
                        "score": result.score,
                        "close": m.close,
                    },
                    ensure_ascii=False,
                    indent=2,
                    default=str,
                ),
                encoding="utf-8",
            )
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
