"""
recommendation.py — 1차 다른 논조/시각 추천 (Agent C 전 단계, 무료)
"""

from __future__ import annotations

import re

from services.data_loader import load_debate_patterns, load_media_bias
from services.news_fetcher import fetch_google_news

_KOREAN_WORD = re.compile(r"[가-힣]{2,}")


def _general_nouns() -> set[str]:
    return set(load_debate_patterns().get("general_nouns", []))

_OPPOSITE: dict[str, list[str]] = {
    "conservative": ["progressive", "neutral"],
    "progressive":  ["conservative", "neutral"],
    "neutral":      ["conservative", "progressive"],
}


def _get_source_lean(source: str) -> str:
    m = load_media_bias()
    if source in m:
        return m[source].get("bias", "neutral")
    for key, val in m.items():
        if key in source or source in key:
            return val.get("bias", "neutral")
    return "neutral"


def extract_search_keywords(title: str) -> str:
    """기사 제목에서 검색 키워드를 추출한다."""
    words = _KOREAN_WORD.findall(title)
    nouns = _general_nouns()
    filtered = [w for w in words if w not in nouns]

    long_words = [w for w in filtered if len(w) >= 3]
    if long_words:
        return " ".join(long_words[:2])

    if filtered:
        return " ".join(filtered[:2])

    return title[:20].strip()


async def get_related_articles(
    title: str,
    source: str,
    exclude_url: str,
) -> dict:
    """기사 제목 키워드로 Google News RSS를 재수집하고 반대 성향 언론사 기사를 필터링한다."""
    keyword = extract_search_keywords(title)
    if not keyword:
        return {"articles": [], "non_debate_message": ""}

    try:
        candidates = await fetch_google_news(keyword, max_items=30, when="7d")
        if len(candidates) < 3:
            candidates = await fetch_google_news(keyword, max_items=30, when="14d")
    except Exception:
        return {"articles": [], "non_debate_message": ""}

    origin_lean = _get_source_lean(source)
    opposite_leans = _OPPOSITE.get(origin_lean, ["conservative", "progressive"])

    results: list[dict] = []
    source_count: dict[str, int] = {}

    for article in candidates:
        if article.get("link", "") == exclude_url:
            continue

        article_source = article.get("source", "")
        if article_source == source:
            continue

        article_lean = _get_source_lean(article_source)
        if article_lean not in opposite_leans:
            continue

        cnt = source_count.get(article_source, 0)
        if cnt >= 2:
            continue

        results.append(article)
        source_count[article_source] = cnt + 1

        if len(results) >= 5:
            break

    return {"articles": results, "non_debate_message": ""}
