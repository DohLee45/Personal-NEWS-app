"""
ai_writer.py — Agent A (분석관) & Agent C (관점 탐색기)

AI 3원칙 (모든 프롬프트 포함):
  ① 출처 명시  ② 사실 검증(신뢰도 ≥ 0.85)  ③ 사견 배제
"""

import asyncio
import json
import os
import re
from typing import Any

import httpx

from services.article_cache import (
    get_article,
    get_recommend,
    set_article,
    set_recommend,
)
from services.usage_tracker import MODELS, can_use_api, increment_usage

OPENROUTER_URL: str = "https://openrouter.ai/api/v1/chat/completions"

AI_UNAVAILABLE: dict[str, Any] = {
    "ai_unavailable": True,
    "message": "OpenRouter API 사용량이 다 하였습니다.",
}

_BODY_LIMIT: int = 4_000

_AGENT_A_SYSTEM: str = (
    "너는 뉴스 분析관. 기사를 분析하고 다양한 관점을 정리한다. "
    "[원칙] 1.원문 사실 인용만 2.AI 판단 금지 3.찬반=원문 인물 발언만 "
    "4.사실 여부 판단 금지, 보도 방식·구조·균형만 5.출처 명시 "
    "[금지] 당위표현/AI사견/정치성향지지비판/원문외사실 "
    "JSON으로만 응답."
)

_AGENT_A_USER_TMPL: str = """\
[출처: {source}] [제목: {title}]
[원문: {body}]
[편향도: B={bias_score:.2f}, 관점편중도={d_opinion:.2f}, 언론사편중도={d_source:.2f}, \
이봉성={d_bimodal:.2f}, 편향강도={d_intensity:.2f}]
[유형: {bias_type}]

다음 JSON 형식으로만 응답하세요:
{{
  "bias_explanation": "편향 판별 설명 — 원문 근거 포함 (2~3문장)",
  "pro_view": "찬성 측 입장 — 원문에서 찬성 발언을 한 인물·기관 입장 요약 (없으면 빈 문자열)",
  "con_view": "반대 측 입장 — 원문에서 반대 발언을 한 인물·기관 입장 요약 (없으면 빈 문자열)",
  "neutral_view": "중도·균형 시각 — 양측을 절충하거나 사실만 보도한 관점 (없으면 빈 문자열)",
  "context_note": "맥락 정보 — 이 기사를 이해하는 데 필요한 역사·정책·사회적 배경 (2~3문장)",
  "ai_bias_score": 0.0,
  "cross_check": "교차검증 포인트 — 독자가 추가로 확인해야 할 사항"
}}

ai_bias_score는 0.0~1.0 사이 숫자로만 응답 (0=편향 없음, 1=매우 편향)."""

_AGENT_C_SYSTEM: str = (
    "관점탐색기. 같은주제다른시각 선별. "
    "원칙: 1)출처 명시 2)사실 검증 신뢰도 0.85 이상만 포함 3)사견 배제. "
    "JSON만응답."
)

_AGENT_C_USER_TMPL: str = """\
[원본 제목: {title}] [출처: {source}] [요약: {summary}] [편향도: {bias_score:.2f}]

[후보 목록]
{candidates_text}

다음 JSON 형식으로만 응답하세요:
{{
  "recommendations": [
    {{"index": 0, "reason": "추천 이유"}}
  ],
  "no_result_reason": "추천 불가 사유 (해당 없으면 빈 문자열)"
}}"""


async def call_openrouter(
    system: str,
    user: str,
    models: list[str],
    max_tokens: int = 2000,
) -> str:
    """OpenRouter API를 호출하고 모델 응답 텍스트를 반환한다."""
    api_key = os.getenv("OPENROUTER_API_KEY", "")
    headers: dict[str, str] = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://personal-news.onrender.com",
        "X-Title": "Personal NEWS",
    }
    messages: list[dict] = [
        {"role": "system", "content": system},
        {"role": "user",   "content": user},
    ]

    last_exc: Exception = Exception("모델 목록이 비어 있습니다.")

    async with httpx.AsyncClient(timeout=30) as client:
        for model in models:
            payload: dict[str, Any] = {
                "model":      model,
                "messages":   messages,
                "max_tokens": max_tokens,
            }
            try:
                resp = await client.post(
                    OPENROUTER_URL, headers=headers, json=payload
                )
                if resp.status_code == 429:
                    await asyncio.sleep(3)
                    last_exc = Exception(f"429 Too Many Requests (model={model})")
                    continue
                resp.raise_for_status()
                content: str = resp.json()["choices"][0]["message"]["content"]
                increment_usage()
                return content
            except httpx.HTTPStatusError as e:
                last_exc = e
                continue
            except Exception as e:
                last_exc = e
                continue

    raise Exception(f"모든 모델 실패: {last_exc}") from last_exc


async def analyze_article(
    url: str,
    title: str,
    source: str,
    body: str,
    bias_meta: dict[str, Any],
) -> dict[str, Any]:
    """[Agent A] 기사 원문을 바탕으로 편향 설명·배경 정보·교차검증을 생성한다."""
    cached = get_article(url)
    if cached:
        return cached

    if not can_use_api():
        return dict(AI_UNAVAILABLE)

    user_prompt = _AGENT_A_USER_TMPL.format(
        source=source,
        title=title,
        body=body[:_BODY_LIMIT],
        bias_score=float(bias_meta.get("bias_score",  0.0)),
        d_opinion= float(bias_meta.get("d_opinion",   0.0)),
        d_source=  float(bias_meta.get("d_source",    0.0)),
        d_bimodal= float(bias_meta.get("d_bimodal",   0.0)),
        d_intensity=float(bias_meta.get("d_intensity",0.0)),
        bias_type= str(bias_meta.get("bias_type", "미분류")),
    )

    try:
        raw = await call_openrouter(
            system=_AGENT_A_SYSTEM,
            user=user_prompt,
            models=MODELS,
            max_tokens=1500,
        )
        result = _parse_json(raw)
    except Exception:
        return dict(AI_UNAVAILABLE)

    result.setdefault("bias_explanation", "")
    result.setdefault("pro_view",         "")
    result.setdefault("con_view",         "")
    result.setdefault("neutral_view",     "")
    result.setdefault("context_note",     "")
    result.setdefault("ai_bias_score",    -1)
    result.setdefault("cross_check",      "")

    set_article(url, result)
    return result


async def recommend_viewpoints(
    article: dict[str, Any],
    candidates: list[dict[str, Any]],
) -> dict[str, Any]:
    """[Agent C] 후보 기사 목록에서 원본 기사와 다른 시각을 가진 기사를 선별한다."""
    url = str(article.get("link", ""))

    cached = get_recommend(url)
    if cached is not None:
        return {"recommendations": cached, "no_result_reason": ""}

    if not can_use_api():
        return dict(AI_UNAVAILABLE)

    summary_text: str = str(article.get("summary", ""))

    if candidates:
        lines = [
            f"{i}. [{c.get('source', '')}] {c.get('title', '')}"
            for i, c in enumerate(candidates)
        ]
        candidates_text = "\n".join(lines)
    else:
        candidates_text = "(후보 없음)"

    bias_score = float(
        article.get("biasScore", article.get("bias_score", 0.0))
    )

    user_prompt = _AGENT_C_USER_TMPL.format(
        title=          str(article.get("title",  "")),
        source=         str(article.get("source", "")),
        summary=        summary_text[:500],
        bias_score=     bias_score,
        candidates_text=candidates_text,
    )

    try:
        raw = await call_openrouter(
            system=_AGENT_C_SYSTEM,
            user=user_prompt,
            models=MODELS,
            max_tokens=1000,
        )
        result = _parse_json(raw)
    except Exception:
        return dict(AI_UNAVAILABLE)

    result.setdefault("recommendations",  [])
    result.setdefault("no_result_reason", "")

    set_recommend(url, result["recommendations"])
    return result


def _parse_json(raw: str) -> dict[str, Any]:
    """LLM 응답에서 JSON을 추출·파싱한다."""
    text = raw.strip()

    fence = re.match(r"^```(?:json)?\s*\n?(.*?)```$", text, re.DOTALL)
    if fence:
        text = fence.group(1).strip()

    start = text.find("{")
    end   = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        text = text[start : end + 1]

    return json.loads(text)
