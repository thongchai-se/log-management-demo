from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database.opensearch import client
from app.routes.ingest import router as ingest_router
from app.routes.logs import router as logs_router
from app.routes.dashboard import router as dashboard_router
from app.routes.alerts import router as alerts_router
from app.routes.auth import router as auth_router


app = FastAPI(
    title="Log Management API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():

    opensearch_status = client.ping()

    return {
        "api": "healthy",
        "opensearch": opensearch_status
    }

app.include_router(auth_router, prefix="/api")
app.include_router(ingest_router, prefix="/api")
app.include_router(logs_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")
app.include_router(alerts_router, prefix="/api")
