"""
article_cache.py — 인메모리 기사·추천 캐시

TTL: CACHE_TTL = 21600초 (6시간)
"""

import hashlib
import time
from typing import Any

CACHE_TTL: int = 21_600
_store: dict[str, tuple[Any, float]] = {}


def _key(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()


def _recommend_key(url: str) -> str:
    return f"recommend_{_key(url)}"


def _get(cache_key: str) -> Any | None:
    entry = _store.get(cache_key)
    if entry is None:
        return None
    value, expires_at = entry
    if time.time() < expires_at:
        return value
    _store.pop(cache_key, None)
    return None


def _set(cache_key: str, value: Any) -> None:
    _store[cache_key] = (value, time.time() + CACHE_TTL)


def get_article(url: str) -> dict | None:
    return _get(_key(url))


def set_article(url: str, data: dict) -> None:
    _set(_key(url), data)


def get_recommend(url: str) -> list | None:
    return _get(_recommend_key(url))


def set_recommend(url: str, data: list) -> None:
    _set(_recommend_key(url), data)
