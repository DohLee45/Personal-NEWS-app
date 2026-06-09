"""
data_loader.py — JSON 데이터 파일 중앙 로더
"""

import json
from functools import lru_cache
from pathlib import Path

_DATA = Path(__file__).parent.parent / "data"


@lru_cache(maxsize=1)
def load_media_bias() -> dict:
    return json.loads((_DATA / "media_bias.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def load_debate_patterns() -> dict:
    return json.loads((_DATA / "debate_patterns.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def load_known_stance() -> dict:
    return json.loads((_DATA / "known_stance.json").read_text(encoding="utf-8"))
