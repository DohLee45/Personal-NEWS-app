"""GET /api/news — 카테고리 RSS 피드 + 키워드 검색"""

import asyncio

from fastapi import APIRouter, Query

from services.news_fetcher import fetch_category_news, fetch_google_news

router = APIRouter()


@router.get("/news")
async def get_news(
    keywords: str = Query(default=""),
    max: int = Query(default=20, ge=1, le=50),
    when: str = Query(default="7d"),
) -> list[dict]:
    if keywords.strip():
        kw_list = [kw.strip() for kw in keywords.split(",") if kw.strip()]
        if not kw_list:
            kw_list = ["뉴스"]

        results = await asyncio.gather(
            *[fetch_google_news(kw, max, when=when) for kw in kw_list],
            return_exceptions=False,
        )

        seen: set[str] = set()
        articles: list[dict] = []
        for batch in results:
            for article in batch:
                if article["id"] not in seen:
                    seen.add(article["id"])
                    articles.append(article)

        articles.sort(key=lambda x: x.get("published", ""), reverse=True)
        return articles[:max]

    return await fetch_category_news(max_items=max)
