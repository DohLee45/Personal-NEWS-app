"""Personal NEWS — FastAPI 진입점

프로덕션: React 빌드 결과물(backend/static)을 단독 서빙
개발:     Vite dev server(port 5173)와 분리 실행
"""

from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from routers import analysis, breaking, market, news, ranking, usage

load_dotenv()

BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"


# ── FastAPI 앱 ────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Personal NEWS API",
    version="1.0.0",
)

# ── CORS ─────────────────────────────────────────────────────────────────────
# 앱이 localStorage만 사용하고 쿠키/세션이 없으므로 allow_credentials=False + allow_origins=["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── API 라우터 등록 (static mount보다 반드시 먼저) ─────────────────────────────
app.include_router(news.router,     prefix="/api", tags=["news"])
app.include_router(breaking.router, prefix="/api", tags=["breaking"])
app.include_router(ranking.router,  prefix="/api", tags=["ranking"])
app.include_router(market.router,   prefix="/api", tags=["market"])
app.include_router(usage.router,    prefix="/api", tags=["usage"])
app.include_router(analysis.router, prefix="/api", tags=["analysis"])


@app.get("/api/health", tags=["health"])
async def health() -> dict:
    """UptimeRobot 헬스체크 엔드포인트."""
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ── React SPA 서빙 (프로덕션) ─────────────────────────────────────────────────
if STATIC_DIR.exists():
    _index = STATIC_DIR / "index.html"

    _assets_dir = STATIC_DIR / "assets"
    if _assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=_assets_dir), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str) -> FileResponse:  # noqa: ARG001
        return FileResponse(_index)
