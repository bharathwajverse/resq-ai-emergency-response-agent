"""
ResQ-AI FastAPI Application Entrypoint.
Initializes FastAPI, configures CORS, lifespan startup table creation & seeding,
health checks, educational disclaimer headers, and API routers.
"""

import time
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import engine, Base, SessionLocal, get_db
from app.schemas.common import HealthCheckResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("resq_ai.main")

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager.
    Runs database schema initialization and idempotent seeding on startup.
    Disposes of database engine pool on shutdown.
    """
    logger.info("Initializing ResQ-AI Backend (%s v%s)...", settings.PROJECT_NAME, settings.PROJECT_VERSION)
    logger.info("Environment: %s | Demo Mode: %s", settings.ENVIRONMENT, settings.is_demo_mode_active)

    # 1. Create database tables if they do not exist
    try:
        logger.info("Verifying and creating database tables...")
        import app.models  # noqa: F401
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized successfully.")
    except Exception as exc:
        logger.error("Failed to initialize database tables: %s", exc, exc_info=True)
        raise

    # 2. Idempotent seeding if enabled
    if settings.AUTO_SEED_ON_STARTUP:
        try:
            logger.info("Checking seed data status...")
            from app.services.seed_service import seed_database_if_empty
            with SessionLocal() as db:
                seed_database_if_empty(db)
            logger.info("Database seeding check complete.")
        except Exception as exc:
            logger.warning("Seeding deferred or skipped: %s", exc)

    yield  # Application serves requests

    # Shutdown logic
    logger.info("Shutting down ResQ-AI Backend. Disposing database engine...")
    engine.dispose()
    logger.info("Shutdown complete.")


# Initialize FastAPI Application
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description="ResQ-AI: Intelligent Emergency Response & Resource Planning Agent (Fundamentals of Artificial Intelligence)",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# 1. Configure CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-ResQ-AI-Disclaimer", "X-Response-Time-Ms"],
)


# 2. Custom Disclaimer & Telemetry Middleware
@app.middleware("http")
async def add_educational_disclaimer_and_timing(request: Request, call_next):
    """Adds educational disclaimer header and execution duration to all responses."""
    start_time = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start_time) * 1000.0
    disclaimer_clean = (
        settings.DISCLAIMER_TEXT.replace("\u2014", "-")
        .replace("\u2013", "-")
        .encode("latin-1", errors="replace")
        .decode("latin-1")
    )
    response.headers["X-ResQ-AI-Disclaimer"] = disclaimer_clean
    response.headers["X-Response-Time-Ms"] = f"{duration_ms:.2f}"
    return response


# 3. Exception Handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Standardized 422 Validation Error response."""
    errors = []
    for err in exc.errors():
        loc = " -> ".join(str(l) for l in err.get("loc", []))
        errors.append(f"{loc}: {err.get('msg', 'Invalid input')}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Request validation failed.",
            "status_code": 422,
            "error_type": "ValidationError",
            "validation_errors": errors,
            "disclaimer": settings.DISCLAIMER_TEXT,
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Standardized HTTP Exception response."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "status_code": exc.status_code,
            "error_type": "HTTPException",
            "disclaimer": settings.DISCLAIMER_TEXT,
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Catches unhandled server exceptions (500)."""
    logger.error("Unhandled exception at %s: %s", request.url.path, exc, exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An internal server error occurred while processing the emergency request.",
            "status_code": 500,
            "error_type": type(exc).__name__,
            "disclaimer": settings.DISCLAIMER_TEXT,
        },
    )


# 4. Core Root and Health Endpoints
@app.get(
    "/",
    tags=["System"],
    summary="Root metadata endpoint",
)
def read_root():
    """Returns application status, version, demo mode flag, and academic disclaimer."""
    return {
        "status": "online",
        "app": settings.PROJECT_NAME,
        "version": settings.PROJECT_VERSION,
        "environment": settings.ENVIRONMENT,
        "demo_mode": settings.is_demo_mode_active,
        "disclaimer": settings.DISCLAIMER_TEXT,
        "documentation": "/docs",
    }


@app.get(
    "/health",
    response_model=HealthCheckResponse,
    tags=["System"],
    summary="System and database health check",
)
def health_check(db: Session = Depends(get_db)):
    """
    Verifies API and database connectivity with a live SELECT 1 probe.
    Returns 200 OK if healthy, or 503 Service Unavailable if database is down.
    """
    db_status = "connected"
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:
        logger.error("Health check database probe failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database probe failed: {exc}",
        )

    return HealthCheckResponse(
        status="healthy",
        version=settings.PROJECT_VERSION,
        database=db_status,
        demo_mode=settings.is_demo_mode_active,
        disclaimer=settings.DISCLAIMER_TEXT,
    )


# 5. Modular API Router Mounting (if available)
try:
    from app.api.router import api_router
    app.include_router(api_router, prefix=settings.API_V1_STR)
except ImportError:
    logger.info("API router module not yet implemented; root & health routes active.")
