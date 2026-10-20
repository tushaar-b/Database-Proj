"""IntelliVest Application Gateway (FastAPI Entrypoint)."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.config import settings
from backend.database import close_pools
from backend.routers import alerts, cashflow, portfolios, recommendations, rebalance, users
from contextlib import asynccontextmanager
import psycopg2
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    yield
    close_pools()

app = FastAPI(
    title="IntelliVest API Gateway",
    description="Database-centric closed-loop financial platform API connecting personal cashflow and PostgreSQL risk analytics.",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(users.router)
app.include_router(cashflow.router)
app.include_router(recommendations.router)
app.include_router(portfolios.router)
app.include_router(alerts.router)
app.include_router(rebalance.router)


@app.exception_handler(psycopg2.Error)
async def database_error_handler(_request, exc: psycopg2.Error):
    logger.exception("PostgreSQL request failed", exc_info=exc)
    return JSONResponse(status_code=503, content={"detail": "Database operation failed; retry after checking database connectivity"})

# Configure CORS
origins = [origin.strip() for origin in settings.ALLOWED_ORIGINS.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Health"])
def root():
    return {
        "app": "IntelliVest API Gateway",
        "status": "online",
        "version": "0.1.0",
        "env": settings.APP_ENV,
    }


@app.get("/health", tags=["Health"])
def health_check():
    checks = {}
    for name, url in (("advisory_db", settings.ADVISORY_DB_URL), ("risk_db", settings.RISK_DB_URL)):
        try:
            conn = psycopg2.connect(url, connect_timeout=3)
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
            conn.close()
            checks[name] = "connected"
        except Exception as exc:
            checks[name] = f"unavailable: {exc.__class__.__name__}"
    healthy = all(value == "connected" for value in checks.values())
    from fastapi import HTTPException
    if not healthy:
        raise HTTPException(status_code=503, detail={"status": "unhealthy", **checks})
    return {"status": "healthy", **checks}
