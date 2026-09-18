"""固定池、門檻、觀察股設定。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

# 代碼 -> (名稱, 族群)
POOL: Dict[str, Tuple[str, str]] = {
    "2330": ("台積電", "半導體"),
    "2454": ("聯發科", "IC設計"),
    "3711": ("日月光投控", "封測"),
    "3034": ("聯詠", "IC設計"),
    "2317": ("鴻海", "電子代工"),
    "2382": ("廣達", "NB代工"),
    "2345": ("智邦", "網通"),
    "3661": ("世芯-KY", "AI"),
    "3037": ("欣興", "PCB"),
    "0050": ("元大台灣50", "ETF"),
    "2303": ("聯電", "晶圓代工"),
    "2324": ("仁寶", "電子代工"),
    "3231": ("緯創", "電子代工"),
}

POOL_IDS: List[str] = list(POOL.keys())
OBSERVE_IDS: List[str] = ["2330", "0050", "2303", "2324", "3231"]

# 池外中大型參考（可擴充）
EXTRA_MIDLARGE: Dict[str, Tuple[str, str]] = {
    "3443": ("創意", "IC設計"),
    "5347": ("世界", "晶圓代工"),
    "3533": ("嘉澤", "連接器"),
    "6505": ("台塑化", "塑化"),
    "1303": ("南亞", "塑化"),
    "1301": ("台塑", "塑化"),
    "1326": ("台化", "塑化"),
    "6770": ("力積電", "記憶體"),
}


@dataclass(frozen=True)
class VolumeThreshold:
    green: float
    yellow: float
    white: float


def volume_threshold_for_hour(hour: int) -> VolumeThreshold:
    """依台北時間小時回傳量能門檻（volume_ratio×100）。"""
    if hour < 10:
        return VolumeThreshold(50, 35, 25)
    if hour < 11:
        return VolumeThreshold(70, 55, 40)
    if hour < 12:
        return VolumeThreshold(90, 75, 55)
    return VolumeThreshold(105, 90, 70)
