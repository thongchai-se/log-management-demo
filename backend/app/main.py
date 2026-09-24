from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import CORS_ORIGINS
from app.database.opensearch import client
from app.routes.admin import router as admin_router
from app.routes.alerts import router as alerts_router
from app.routes.auth import router as auth_router
from app.routes.dashboard import router as dashboard_router
from app.routes.ingest import router as ingest_router
from app.routes.logs import router as logs_router
from app.services.index_setup import ensure_index
from app.services.retention_worker import start_retention_worker
from app.services.syslog_server import start_syslog_server


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        ensure_index()
    except Exception as exc:
        print(f"[startup] ensure_index failed (will retry on first write): {exc}")
    start_syslog_server()
    start_retention_worker()
    yield


app = FastAPI(
    title="Log Management API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    opensearch_status = False
    try:
        opensearch_status = bool(client.ping())
    except Exception:
        opensearch_status = False
    return {
        "api": "healthy",
        "opensearch": opensearch_status,
    }


app.include_router(auth_router, prefix="/api")
app.include_router(ingest_router, prefix="/api")
app.include_router(logs_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")
app.include_router(alerts_router, prefix="/api")
app.include_router(admin_router, prefix="/api")
