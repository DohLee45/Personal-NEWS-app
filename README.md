# Personal NEWS

AI 기반 뉴스 편향도 분석 서비스 — 관심 키워드로 큐레이션된 뉴스를 읽고, AI가 기사의 편향 성향을 실시간으로 분석합니다.

🔗 **배포 URL**: https://personal-news-be43.onrender.com

---

## 실행 방법

### 사전 준비

```
Python 3.11+
Node.js 20+
OpenRouter API 키 (https://openrouter.ai/)
```

### 1. 백엔드

```bash
cd backend
pip install -r requirements.txt

# .env 파일 생성 (아래 환경 변수 설정)
cp .env.example .env

uvicorn main:app --reload --port 8000
```

### 2. 프론트엔드

```bash
cd frontend
npm install
npm run dev          # 개발 서버: http://localhost:5173
npm run build        # 프로덕션 빌드 → backend/static/
```

개발 서버에서는 Vite 프록시(`/api → localhost:8000`)가 자동으로 활성화됩니다.

---

## 환경 변수 (`.env`)

| 변수 | 설명 | 예시 |
|------|------|------|
| `OPENROUTER_API_KEY` | OpenRouter API 인증 키 | `sk-or-v1-...` |

```env
OPENROUTER_API_KEY=sk-or-v1-여기에키입력
```

---

## 주요 기능

| 기능 | 설명 |
|------|------|
| **닉네임 / 온보딩** | 최초 접속 시 닉네임(2–10자) 설정 → 관심 키워드 선택(최대 20개) |
| **개인화 피드** | 관심사 기반 정렬 + 6개 카테고리 탭 + 스테일-화이트-리밸리데이트 캐시 |
| **사이드바 위젯** | 속보 20건 · 시세 20개 · 인기 기사 20건 · 날씨(Open-Meteo) |
| **검색** | 앱내 즉시 필터 + Google News RSS 검색 · 최근 검색 기록 저장 |
| **기사 상세** | 점진적 로딩 — 편향 바(즉시) → 원문 요약 → 다른 시각 기사(RSS 자동) |
| **AI 정밀 분석** | "AI 정밀 분석" 버튼 → Agent A가 7필드 분석 + 논거 기반 추천 (API 1회) |
| **설정** | 관심 키워드 관리 · 검색 기록 · 닉네임 변경 (3탭) |
| **편향 분석** | UP Score + Shannon 다양성 + 7개 섹션 + 변화 추이 그래프 |

---

## UP (Unbalanced Perspective) Score

```
UP(u) = 0.35 × D_opinion + 0.25 × D_source + 0.25 × D_bimodal + 0.15 × D_intensity
다양성 점수 = (1 − UP) × 100
```

---

## 기술 스택

| 영역 | 기술 |
|------|------|
| 프론트엔드 | React 19, Vite, CSS Modules, React Router |
| 백엔드 | FastAPI, httpx, feedparser, BeautifulSoup4, googlenewsdecoder, yfinance |
| AI | OpenRouter (deepseek-v4-flash / gpt-oss-120b) |
| 날씨 | Open-Meteo API (무료, 인증 불필요) |
| 배포 | Render free tier |

---

## 배포 (Render)

`render.yaml`이 이미 포함되어 있어 Git 연동만으로 자동 배포됩니다.

```
1. https://render.com → New Web Service
2. GitHub 저장소 연결
3. render.yaml 자동 감지 → 설정 확인
4. Environment → Add Secret → OPENROUTER_API_KEY 입력
5. Create Web Service
```
