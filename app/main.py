from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.core.logging import logger, setup_logging
from app.core.middleware import RequestLoggingMiddleware, RateLimitMiddleware
from app.core.exceptions import (
    AppException,
    app_exception_handler,
    validation_exception_handler,
    sqlalchemy_exception_handler,
    generic_exception_handler
)
from app.api.endpoints import auth, signals, oracle, alerts, admin, admin_ui, legal, transparency, content, public, marketing, chart_analysis, whale
from app.services.scheduler import start_scheduler, stop_scheduler, get_scheduled_jobs

setup_logging(debug=settings.DEBUG)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="ELUXRAJ - AI-Powered Trading Signals API",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

app.add_middleware(RateLimitMiddleware, requests_per_minute=100)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Public Pages
app.include_router(public.router, prefix="/track", tags=["Public Tracker"])
app.include_router(legal.router, prefix="/legal", tags=["Legal"])

# API Routes
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(signals.router, prefix="/api/v1/signals", tags=["Signals"])
app.include_router(oracle.router, prefix="/api/v1/oracle", tags=["Oracle Engine"])
app.include_router(chart_analysis.router, prefix="/api/v1/chart", tags=["Chart Analysis"])
app.include_router(whale.router, prefix="/api/v1/whale", tags=["Whale Intelligence"])
app.include_router(alerts.router, prefix="/api/v1/alerts", tags=["Alerts"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])
app.include_router(transparency.router, prefix="/api/v1/transparency", tags=["Transparency"])
app.include_router(content.router, prefix="/api/v1/content", tags=["Content"])
app.include_router(marketing.router, prefix="/api/v1/marketing", tags=["Marketing"])

# Admin UI
app.include_router(admin_ui.router, prefix="/admin", tags=["Admin UI"])

@app.on_event("startup")
async def startup_event():
    logger.info(f"🚀 Starting {settings.APP_NAME} v{settings.VERSION}")
    from app.db.base import Base
    from app.db.session import engine
    from app.models.user import User
    from app.models.signal import Signal
    from app.models.chart import ChartUpload, ChartAnalysisResult
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Database tables ready")
    start_scheduler()

@app.on_event("shutdown")
async def shutdown_event():
    stop_scheduler()

@app.get("/", tags=["Health"])
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.VERSION,
        "status": "operational",
        "tagline": "An open experiment in AI trading signals",
        "disclaimer": "Not financial advice. Past performance ≠ future results.",
        "public_tracker": "/track",
        "links": {
            "public_dashboard": "/track",
            "homepage_copy": "/api/v1/marketing/homepage",
            "api_docs": "/docs",
            "admin": "/admin"
        }
    }

@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy", "version": settings.VERSION}
