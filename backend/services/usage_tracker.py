"""
usage_tracker.py — OpenRouter 일일·분당 사용량 추적

제한값:
  DAILY_LIMIT = 90   건/일  (UTC 자정 초기화)
  RATE_LIMIT  = 20   건/분  (슬라이딩 윈도우)

모델 폴백 순서 (MODELS):
  1순위: deepseek/deepseek-v4-flash:free
  2순위: openai/gpt-oss-120b:free  (HTTP 429 수신 시 자동 전환)
"""

import time
from datetime import datetime, timezone

DAILY_LIMIT: int = 90
RATE_LIMIT: int  = 20

MODELS: list[str] = [
    "deepseek/deepseek-v4-flash:free",
    "openai/gpt-oss-120b:free",
]

_daily_count: int            = 0
_daily_date: str             = ""
_minute_timestamps: list[float] = []


def _today_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _reset_if_new_day() -> None:
    global _daily_count, _daily_date
    today = _today_utc()
    if _daily_date != today:
        _daily_count = 0
        _daily_date  = today


def _prune_minute_window() -> None:
    cutoff = time.time() - 60.0
    _minute_timestamps[:] = [t for t in _minute_timestamps if t > cutoff]


def can_use_api() -> bool:
    _reset_if_new_day()
    _prune_minute_window()
    return _daily_count < DAILY_LIMIT and len(_minute_timestamps) < RATE_LIMIT


def increment_usage() -> None:
    global _daily_count
    _reset_if_new_day()
    _daily_count += 1
    _minute_timestamps.append(time.time())


def get_usage_status() -> dict:
    _reset_if_new_day()
    return {
        "used":      _daily_count,
        "limit":     DAILY_LIMIT,
        "remaining": max(0, DAILY_LIMIT - _daily_count),
    }
