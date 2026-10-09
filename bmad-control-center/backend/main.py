import sys
from pathlib import Path
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Ensure project root is in sys.path so 'backend' imports resolve automatically
ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core.config import settings
from api.routes import router as api_router
from api.websockets import router as ws_router
from services.file_watcher import FileWatcher
from services.connection_manager import manager



file_watcher = FileWatcher()


def _get_utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for starting and stopping background file watcher."""
    loop = asyncio.get_running_loop()
    if settings.HAS_PROJECT:
        file_watcher.start(loop)
    try:
        yield
    finally:
        if settings.HAS_PROJECT:
            file_watcher.stop()


app = FastAPI(
    title="BMAD Control Center - Monitoreo y Explorador de Artefactos",
    version=settings.VERSION,
    lifespan=lifespan
)

# CORS configuration for local loopback
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS + ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API and WebSocket routers
app.include_router(api_router, prefix="/api/v1")
app.include_router(ws_router)


@app.middleware('http')
async def require_selected_project(request: Request, call_next):
    if (not settings.HAS_PROJECT and request.url.path.startswith('/api/v1/')
            and request.url.path.rstrip('/') not in {'/api/v1/project', '/api/v1/projects'}):
        return JSONResponse(status_code=409, content={
            'error_code': 'PROJECT_NOT_SELECTED',
            'detail': 'Selecciona BMAD_WORKSPACE o BMAD_PROJECT al iniciar este backend.',
        })
    return await call_next(request)


# -------------------------------------------------------------
# Structured Error Handlers (RFC 7807 / ADR-05 Adaptation)
# -------------------------------------------------------------

STATUS_TO_ERROR_CODE = {
    400: "INVALID_PARAMETER",
    403: "PATH_TRAVERSAL_DETECTED",
    404: "ARTIFACT_NOT_FOUND",
    413: "PAYLOAD_TOO_LARGE",
    415: "UNSUPPORTED_MEDIA_TYPE",
    500: "INTERNAL_SERVER_ERROR"
}


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Standardized machine-readable error response according to ADR-05.
    Returns error_code, detail, timestamp, path and optional metadata.
    """
    error_code = getattr(exc, "error_code", None) or STATUS_TO_ERROR_CODE.get(exc.status_code, "HTTP_ERROR")
    metadata = getattr(exc, "metadata", None)

    content: Dict[str, Any] = {
        "error_code": error_code,
        "detail": exc.detail,
        "timestamp": _get_utc_now(),
        "path": request.url.path,
    }
    if metadata:
        content["metadata"] = metadata

    return JSONResponse(status_code=exc.status_code, content=content)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global catch-all exception handler returning structured JSON."""
    return JSONResponse(
        status_code=500,
        content={
            "error_code": "INTERNAL_SERVER_ERROR",
            "detail": f"Internal Server Error: {str(exc)}",
            "timestamp": _get_utc_now(),
            "path": request.url.path,
        },
    )
