# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> The parent-level `../CLAUDE.md` contains project overview, hard constraints, and coding conventions. **Read it first.** This file covers implementation-level details that require understanding multiple files together.

---

## Development Commands

### Running both servers (required for full functionality)

**Backend** (from `backend/`):
```bash
uvicorn main:app --reload --port 8000
```
Requires `OPENROUTER_API_KEY` in `backend/.env` (see `.env.example`).

**Frontend** (from `frontend/`):
```bash
npm run dev        # Vite dev server → http://localhost:5173
npm run build      # Production build → outputs to ../backend/static/
```

The Vite dev proxy forwards `/api/*` → `localhost:8000`. In production, `main.py` serves the React build directly from `backend/static/`.

**There is no test runner configured** in either the frontend or backend.

---

## Key Architectural Flows

### 1. Article bias analysis pipeline (backend-only, synchronous at fetch time)

Every article returned by any `/api/news`, `/api/breaking`, or `/api/ranking` endpoint already carries pre-computed bias fields. The analysis runs once during RSS fetch and is cached for 5 minutes per `keyword:when` key.

```
fetch_google_news(keyword, max_items, when="7d")   [news_fetcher.py]
  ├─ _feed_cache hit → return cached list immediately (5-min TTL)
  └─ cache miss → _fetch_feed()
       └─ analyze()                    [bias_analyzer.py]
            ├─ _calc_s_media()         media_bias.json lookup
            ├─ _calc_s_text()          sentence direction + double-negation resolver
            ├─ _calc_s_quote()         citation diversity + stance-org imbalance
            └─ _calc_s_struct()        emotional title + assertive templates + rhetorical ?
```

**Article dict shape** (returned to frontend):
```json
{ "id", "title", "link", "source", "published", "summary",
  "category", "biasTag", "biasScore", "viewpoint" }
```

**Bias weights** — registered media: `(S_media=0.15, S_text=0.45, S_quote=0.25, S_struct=0.15)`; unregistered: `(0.10, 0.50, 0.25, 0.15)`.

**Tag labels**:
| Score | Tag |
|-------|-----|
| < 0.30 | 균형 보도 🟢 |
| 0.30–0.60 | 관점 포함 🟡 |
| ≥ 0.60 | 편향 주의 🔴 |

---

### 2. Frontend article history — 2-stage save (`hooks/useHistory.js`)

```
Card click (MainPage)
  └─ addStage1(article)
       • Saves to pn_history with _stage:1

ArticlePage — POST /api/analysis completes
  └─ updateStage2(id, patch)
       • Overwrites biasTag, biasScore with full-body analysis result
       • Sets _stage:2
```

`pn_history` max 100 items — oldest deleted on overflow.

---

### 3. Interest scoring (`utils/interestScore.js`)

`sortByInterest(articles, userKeywords, history)` applies different weights based on history size:

| Condition | Formula |
|-----------|--------|
| `history.length < 10` (cold start) | `kw×0.7 + freshness×0.3` |
| Normal | `kw×0.5 + frequency×0.3 + freshness×0.2` |

---

### 4. Feed fetch + stale-while-revalidate (`hooks/useFeed.js`)

`useFeed(keywords, search, history)` — no `category` parameter. Tab switching is client-side `articles.filter(a => a.category === activeTab)` with no API re-call.

Uses a **module-level `Map`** (not React state) as a 5-minute cache keyed by `${keywords.join(',')}|${search}`.

---

### 5. ArticlePage — progressive loading

Immediately shows title, category, bias bar, and original link from router `state`. Then fires two parallel requests:

```
useEffect parallel:
  ├─ POST /api/analysis  (crawl + summary, 1–3 s)
  │    → skeleton UI while loading → summary on complete
  │    → updateStage2() called after completion
  └─ GET  /api/related   (RSS recommendation, 2–5 s)
       → shows related articles as soon as available
```

**AI 정밀 분석 버튼 클릭 시 (API 1회)**:
```
POST /api/deep-analysis → Agent A → 7 sections result
```

---

## Caching Architecture

| Layer | Location | Key | TTL |
|-------|----------|-----|-----|
| Backend feed | `news_fetcher._feed_cache` (dict) | `keyword:when` | 5 min |
| Backend breaking | `breaking._cache` (dict) | single entry | 2 min |
| Backend ranking | `ranking._cache` (dict) | single entry | 1 hr |
| Backend market | `market._cache` (dict) | single entry | 5 min |
| Backend article/AI | `article_cache.py` (dict) | `md5(url)` | 6 hr |
| Frontend feed | `useFeed._cache` (module Map) | `keywords\|search` | 5 min |
| Frontend weather | `localStorage pn_weather` | single entry | 30 min |

---

## Lazy Loading (App.jsx)

`ArticlePage`, `AnalysisPage`, `SettingsPage` are loaded as separate Vite chunks via `React.lazy()`. `NicknamePage`, `OnboardingPage`, `MainPage` remain eagerly loaded.

---

## Production Build Notes

`npm run build` writes to `backend/static/`. The `main.py` mounts `/assets` as static files and catches all non-`/api` paths with a catch-all SPA route. **API routers must be registered before the static mount** — this ordering is already correct and must not be changed.
