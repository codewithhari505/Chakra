"""
AML Investigation System — FastAPI Application Entry Point.

This is the top-level ASGI application.
All routers are registered here. Lifespan events handle startup/shutdown tasks.

Run with:
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
"""

import logging
import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import transactions, accounts, alerts, analytics, investigations
from app.config import get_settings
from app.database.database import check_db_connection
from app.database.init_db import init_db

settings = get_settings()

# ---------------------------------------------------------------------------
# Logging Configuration
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lifespan: Startup & Shutdown Events
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    FastAPI lifespan context manager.
    
    On startup:
      - Initialize database tables
      - Load ML models (populated in later phases)
      - Log application configuration
    
    On shutdown:
      - Release resources gracefully
    """
    logger.info("=" * 60)
    logger.info("Starting %s v%s", settings.app_name, settings.app_version)
    logger.info("Database: %s", settings.database_url.split("@")[-1] if "@" in settings.database_url else settings.database_url)
    logger.info("Debug mode: %s", settings.debug)
    logger.info("=" * 60)

    # Initialize database tables
    try:
        await init_db()
        logger.info("Database initialization complete.")
    except Exception as e:
        logger.error("Database initialization failed: %s", e)
        # Don't crash on startup — the health check will report DB as disconnected

    # ML model loading will be added in Phase 6+
    logger.info("ML models: not yet trained (Phase 6+)")

    yield  # Application is now running

    logger.info("Shutting down %s...", settings.app_name)


# ---------------------------------------------------------------------------
# FastAPI Application
# ---------------------------------------------------------------------------
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
## AI-Powered Anti-Money-Laundering (AML) Investigation System

An academic/prototype system for detecting suspicious financial transaction patterns
using ML, anomaly detection, graph analytics, and an investigator dashboard.

> **Disclaimer:** This system uses entirely synthetic data. Model outputs flag patterns
> for investigator review — they do not constitute legal determinations.

### Key Features
- **Supervised ML**: Random Forest + XGBoost for transaction classification
- **Anomaly Detection**: Isolation Forest for novel suspicious patterns
- **Graph Analysis**: NetworkX for circular transfers, layering, and network centrality
- **Risk Engine**: Weighted composite risk score (ML + Anomaly + Rules + Network)
- **Explainability**: SHAP values + rule explanations for every alert
- **Investigation Workflow**: Alert lifecycle management (NEW → CLOSED)
    """,
    contact={"name": "AML System", "email": "admin@aml-system.local"},
    license_info={"name": "MIT"},
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ---------------------------------------------------------------------------
# CORS Middleware
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Request Timing Middleware
# ---------------------------------------------------------------------------
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add X-Process-Time header to every response for performance monitoring."""
    start = time.perf_counter()
    response = await call_next(request)
    elapsed = time.perf_counter() - start
    response.headers["X-Process-Time"] = f"{elapsed:.4f}s"
    return response


# ---------------------------------------------------------------------------
# Global Exception Handler
# ---------------------------------------------------------------------------
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Catch any unhandled exception and return a structured 500 response.
    Never expose internal stack traces or sensitive data to the client.
    """
    logger.error("Unhandled exception on %s %s: %s", request.method, request.url, exc, exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "internal_server_error",
            "message": "An unexpected error occurred. Please contact support.",
        },
    )


# ---------------------------------------------------------------------------
# Health Check Endpoint
# ---------------------------------------------------------------------------
@app.get(
    "/health",
    summary="Health check",
    tags=["System"],
    response_description="System health status",
)
async def health_check():
    """
    Verify that the application and its dependencies are operational.
    
    Checks:
    - API server status
    - Database connectivity
    - ML model availability
    
    Returns 200 even if some non-critical components (e.g. models) are not yet loaded.
    """
    db_ok = await check_db_connection()

    return {
        "status": "healthy" if db_ok else "degraded",
        "version": settings.app_version,
        "database": "connected" if db_ok else "disconnected",
        "models_loaded": {
            "fraud_classifier": settings.fraud_classifier_exists,
            "anomaly_detector": settings.anomaly_detector_exists,
        },
        "debug_mode": settings.debug,
    }


@app.get("/", tags=["System"], summary="API root", include_in_schema=False)
async def root():
    """Redirect hint for the API root."""
    return {
        "message": f"Welcome to {settings.app_name} v{settings.app_version}",
        "docs": "/docs",
        "health": "/health",
    }


# ---------------------------------------------------------------------------
# Register API Routers
# ---------------------------------------------------------------------------
app.include_router(transactions.router, prefix="/api/v1")
app.include_router(accounts.router, prefix="/api/v1")
app.include_router(alerts.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")
app.include_router(investigations.router, prefix="/api/v1")
