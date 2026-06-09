"""
routers/analysis.py — 기사 분석 엔드포인트 (STEP 8)

엔드포인트:
  POST /api/analysis        — 크롤링 + bias 재계산 + 요약 추출 (API 0회)
  POST /api/deep-analysis   — Agent A AI 정밀 분석 (API 1회, 수동)
  GET  /api/related         — 1차 다른 논조 추천 (RSS 재수집, 무료)
  POST /api/recommend       — Agent C 정밀 추천 (수동, 유지)
"""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, Query

from services.ai_writer import analyze_article, recommend_viewpoints
from services.bias_analyzer import analyze as analyze_bias
from services.crawler import crawl_article, extract_summary
from services.recommendation import get_related_articles

router = APIRouter()


@router.post("/analysis")
async def post_analysis(body: dict) -> dict:
    url      = str(body.get("url",      ""))
    title    = str(body.get("title",    ""))
    source   = str(body.get("source",   ""))
    category = str(body.get("category", "사회"))
    summary  = str(body.get("summary",  ""))

    article_body = await crawl_article(url)
    text_for_analysis = article_body or summary
    bias = analyze_bias(title, source, text_for_analysis, category)
    summary_text = extract_summary(article_body) if article_body else summary

    return {
        "summary": summary_text,
        "body":    article_body[:3000] if article_body else "",
        "updated_bias": {
            "biasScore": bias.bias_score,
            "biasTag":   bias.bias_tag,
            "viewpoint": bias.viewpoint,
        },
    }


@router.post("/deep-analysis")
async def post_deep_analysis(body: dict) -> dict:
    url      = str(body.get("url",      ""))
    title    = str(body.get("title",    ""))
    source   = str(body.get("source",   ""))
    category = str(body.get("category", "사회"))
    summary  = str(body.get("summary",  ""))

    article_body = await crawl_article(url)
    text_for_analysis = article_body or summary

    bias = analyze_bias(title, source, text_for_analysis, category)
    bias_meta: dict = {
        "bias_score":  bias.bias_score,
        "d_opinion":   bias.components.get("s_text",   0.0),
        "d_source":    bias.components.get("s_media",  0.0),
        "d_bimodal":   bias.components.get("s_quote",  0.0),
        "d_intensity": bias.components.get("s_struct", 0.0),
        "bias_type":   bias.bias_tag,
    }

    result, related = await asyncio.gather(
        analyze_article(
            url=url,
            title=title,
            source=source,
            body=text_for_analysis,
            bias_meta=bias_meta,
        ),
        get_related_articles(title=title, source=source, exclude_url=url),
    )

    if result.get("ai_unavailable"):
        return result

    try:
        result["ai_bias_score"] = float(result.get("ai_bias_score", -1))
    except (TypeError, ValueError):
        result["ai_bias_score"] = -1.0

    result["recommendations"] = related.get("articles", [])
    return result


@router.get("/related")
async def get_related(
    title:       str = Query(""),
    source:      str = Query(""),
    exclude_url: str = Query(""),
) -> dict:
    if not title:
        return {"articles": [], "non_debate_message": ""}
    return await get_related_articles(
        title=title,
        source=source,
        exclude_url=exclude_url,
    )


@router.post("/recommend")
async def post_recommend(body: dict) -> dict:
    article    = body.get("article",    {})
    candidates = body.get("candidates", [])
    if not isinstance(article, dict):   article = {}
    if not isinstance(candidates, list): candidates = []
    return await recommend_viewpoints(article, candidates)
