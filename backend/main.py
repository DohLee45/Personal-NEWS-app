"""Personal NEWS — FastAPI 진입점"""

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

app = FastAPI(title="Personal NEWS API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(news.router,     prefix="/api", tags=["news"])
app.include_router(breaking.router, prefix="/api", tags=["breaking"])
app.include_router(ranking.router,  prefix="/api", tags=["ranking"])
app.include_router(market.router,   prefix="/api", tags=["market"])
app.include_router(usage.router,    prefix="/api", tags=["usage"])
app.include_router(analysis.router, prefix="/api", tags=["analysis"])


@app.get("/api/health", tags=["health"])
async def health() -> dict:
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "cors_active": True,
    }


if STATIC_DIR.exists():
    _index = STATIC_DIR / "index.html"
    _assets_dir = STATIC_DIR / "assets"
    if _assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=_assets_dir), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str) -> FileResponse:  # noqa: ARG001
        return FileResponse(_index)
