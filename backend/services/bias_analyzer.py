"""편향도 분석기

B_total = W1·S_media + W2·S_text + W3·S_quote + W4·S_struct

등록 언론사:   W1=0.15 / W2=0.45 / W3=0.25 / W4=0.15
미등록 언론사: W1=0.10 / W2=0.50 / W3=0.25 / W4=0.15

태그 3종 통일:
  균형 보도  (score < 0.30)
  관점 포함  (0.30 ≤ score < 0.60)
  편향 주의  (score ≥ 0.60)
"""

import re
from dataclasses import dataclass

from services.data_loader import load_debate_patterns, load_known_stance, load_media_bias

# ── 가중치 ─────────────────────────────────────────────────────────────────────
_W_REGISTERED   = (0.15, 0.45, 0.25, 0.15)
_W_UNREGISTERED = (0.10, 0.50, 0.25, 0.15)

# ── 이중부정 해소 상수 ──────────────────────────────────────────────────────────
_NEGATION_WORDS = [
    '않', '안', '못', '없', '아니', '거부', '철회', '반대',
    '반박', '중단', '폐지', '취소', '보류',
]
_NEGATION_COMPOUNDS = re.compile(
    r'(미실현|미이행|미완성|미준수|불가|불법|불공정|불필요|불합리|'
    r'비효율|비리|비합리|비공개|무효|무능|무책임|무관심|'
    r'반정부|반기업|반민주|반헌법|반환경|탈규제|탈원전|탈탄소)'
)

_STANCE_CATEGORY_MAP: dict[str, list[str]] = {
    "정치":    ["국방·안보", "default"],
    "경제":    ["금융규제", "default"],
    "사회":    ["노동", "부동산", "의료", "교육", "환경", "default"],
    "과학기술": ["기술규제", "default"],
    "스포츠":  [],
    "연예":    [],
    "미분류":  ["default"],
}


@dataclass
class BiasResult:
    bias_score: float
    bias_tag:   str
    viewpoint:  str
    components: dict


def _count_negations(sentence: str) -> int:
    count = sum(1 for w in _NEGATION_WORDS if w in sentence)
    count += len(_NEGATION_COMPOUNDS.findall(sentence))
    return count


def _resolve_double_negation(sentence: str, direction: str) -> str:
    if direction == "neutral":
        return direction
    if _count_negations(sentence) >= 2:
        return "con" if direction == "pro" else "pro"
    return direction


def _calc_s_media(source: str) -> tuple[float, bool]:
    m = load_media_bias()
    if source in m:
        return float(m[source]["score"]), True
    return 0.3, False


def _classify_sentence_direction(sentence: str, category: str) -> str:
    pats = load_debate_patterns()
    stance_all = load_known_stance()
    cat_keys = _STANCE_CATEGORY_MAP.get(category, ["default"])

    pro_hits = con_hits = 0
    for key in cat_keys + ["default"]:
        for org, stance in stance_all.get(key, {}).items():
            if org in sentence:
                if stance == "pro":
                    pro_hits += 1
                elif stance == "con":
                    con_hits += 1

    emotional = pats.get("emotional", {})
    has_neg = any(w in sentence for w in emotional.get("strong_negative", []))
    has_pos = any(w in sentence for w in emotional.get("strong_positive_propaganda", []))

    if has_neg and not has_pos:
        con_hits += 1
    if has_pos and not has_neg:
        pro_hits += 1

    if pro_hits > con_hits:
        return "pro"
    if con_hits > pro_hits:
        return "con"
    return "neutral"


def _split_sentences(text: str) -> list[str]:
    parts = re.split(r'(?<=[.!?。])\s+', text.strip())
    return [p.strip() for p in parts if p.strip()]


def _calc_s_text(text: str, category: str) -> float:
    sentences = _split_sentences(text)
    if not sentences:
        return 0.0

    directions: list[str] = []
    for sent in sentences:
        raw_dir = _classify_sentence_direction(sent, category)
        final_dir = _resolve_double_negation(sent, raw_dir)
        directions.append(final_dir)

    total = len(directions)
    pro_ratio     = directions.count("pro")     / total
    con_ratio     = directions.count("con")     / total
    neutral_ratio = directions.count("neutral") / total

    direction_imbalance = abs(pro_ratio - con_ratio)
    neutral_bonus = neutral_ratio * 0.3
    return round(min(direction_imbalance * (1.0 - neutral_bonus), 1.0), 4)


_DIRECT_QUOTE_RE = re.compile(r'[""「『](.*?)[""」』]', re.DOTALL)


def _calc_s_quote(text: str, category: str) -> float:
    pats = load_debate_patterns()

    direct_count = len(_DIRECT_QUOTE_RE.findall(text))
    factual_count = sum(1 for phrase in pats.get("factual", []) if phrase in text)

    if direct_count == 0 and factual_count == 0:
        return 0.3

    total_citations = direct_count + factual_count
    diversity_score = min(total_citations / 3.0, 1.0)

    stance_all = load_known_stance()
    cat_keys = _STANCE_CATEGORY_MAP.get(category, ["default"])
    pro_orgs = con_orgs = 0
    for key in cat_keys + ["default"]:
        for org, stance in stance_all.get(key, {}).items():
            if org in text:
                if stance == "pro":
                    pro_orgs += 1
                elif stance == "con":
                    con_orgs += 1

    total_orgs = pro_orgs + con_orgs
    stance_imbalance = (
        abs(pro_orgs - con_orgs) / total_orgs if total_orgs else 0.0
    )

    s_quote = stance_imbalance * (1.0 - diversity_score * 0.3)
    return round(min(s_quote, 1.0), 4)


def _calc_s_struct(title: str, text: str) -> float:
    pats = load_debate_patterns()
    emotional = pats.get("emotional", {})
    bias_pats = pats.get("bias", {})

    all_emotional = (
        emotional.get("strong_negative", []) +
        emotional.get("strong_positive_propaganda", [])
    )
    title_emotional = sum(1 for w in all_emotional if w in title)
    title_gap = min(title_emotional / 2.0, 1.0)

    def _match_templates(templates: list[str], target: str) -> int:
        return sum(
            1 for t in templates
            if (stripped := t.lstrip("~").strip()) and stripped in target
        )

    assertive_score = (
        _match_templates(bias_pats.get("strong", []), text) * 1.0 +
        _match_templates(bias_pats.get("medium", []), text) * 0.5 +
        _match_templates(bias_pats.get("weak",   []), text) * 0.2
    )
    assertive_ratio = min(assertive_score / 3.0, 1.0)

    q_count = title.count("?") + title.count("？")
    rhetorical_ratio = min(q_count / 2.0, 1.0)

    s_struct = title_gap * 0.40 + assertive_ratio * 0.35 + rhetorical_ratio * 0.25
    return round(min(s_struct, 1.0), 4)


def _get_bias_tag(score: float) -> str:
    if score < 0.30:
        return "균형 보도"
    if score < 0.60:
        return "관점 포함"
    return "편향 주의"


def _get_viewpoint(source: str, s_text: float, text: str, category: str) -> str:
    m = load_media_bias()
    media_bias = m.get(source, {}).get("bias", "neutral")

    stance_all = load_known_stance()
    cat_keys = _STANCE_CATEGORY_MAP.get(category, ["default"])
    pro_hits = con_hits = 0
    for key in cat_keys + ["default"]:
        for org, stance in stance_all.get(key, {}).items():
            if org in text:
                if stance == "pro":
                    pro_hits += 1
                elif stance == "con":
                    con_hits += 1

    text_leans_pro = pro_hits > con_hits
    text_leans_con = con_hits > pro_hits

    if media_bias == "conservative":
        return "pro" if text_leans_pro else "con"
    if media_bias == "progressive":
        return "con" if text_leans_con else "pro"
    if text_leans_pro:
        return "pro"
    if text_leans_con:
        return "con"
    return "neutral"


def analyze(
    title: str,
    source: str,
    summary: str,
    category: str = "사회",
) -> BiasResult:
    """기사 제목·출처·요약을 받아 BiasResult를 반환한다."""
    text = title + " " + summary

    s_media, is_registered = _calc_s_media(source)
    s_text   = _calc_s_text(text, category)
    s_quote  = _calc_s_quote(text, category)
    s_struct = _calc_s_struct(title, summary)

    w = _W_REGISTERED if is_registered else _W_UNREGISTERED
    b_total = round(
        w[0] * s_media + w[1] * s_text + w[2] * s_quote + w[3] * s_struct,
        4,
    )
    b_total = min(b_total, 1.0)

    bias_tag = _get_bias_tag(b_total)
    viewpoint = _get_viewpoint(source, s_text, text, category)

    return BiasResult(
        bias_score = b_total,
        bias_tag   = bias_tag,
        viewpoint  = viewpoint,
        components = {
            "s_media":  s_media,
            "s_text":   s_text,
            "s_quote":  s_quote,
            "s_struct": s_struct,
        },
    )
