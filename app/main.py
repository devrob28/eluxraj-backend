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
from app.api.endpoints import auth, signals, oracle
from app.services.scheduler import start_scheduler, stop_scheduler, get_scheduled_jobs

# Setup logging
setup_logging(debug=settings.DEBUG)

# Create app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="ELUXRAJ - AI-Powered Trading Signals API",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Exception handlers
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Middleware
app.add_middleware(RateLimitMiddleware, requests_per_minute=100)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://eluxraj.ai",
        "https://www.eluxraj.ai",
        "http://localhost:3000",
        "http://localhost:5173",
        "*"  # Allow all for mobile apps
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(signals.router, prefix="/api/v1/signals", tags=["Signals"])
app.include_router(oracle.router, prefix="/api/v1/oracle", tags=["Oracle Engine"])

@app.on_event("startup")
async def startup_event():
    logger.info(f"🚀 Starting {settings.APP_NAME} v{settings.VERSION}")
    
    # Create tables on startup
    from app.db.base import Base
    from app.db.session import engine
    from app.models.user import User
    from app.models.signal import Signal
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Database tables ready")
    
    # Start scheduler
    start_scheduler()

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down...")
    stop_scheduler()

@app.get("/", tags=["Health"])
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.VERSION,
        "status": "operational",
        "docs": "/docs",
    }

@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy", "version": settings.VERSION}

@app.get("/scheduler/jobs", tags=["Scheduler"])
async def get_jobs():
    return {"jobs": get_scheduled_jobs()}

@app.post("/scheduler/scan-now", tags=["Scheduler"])
async def trigger_scan_now():
    from app.services.scheduler import scheduled_market_scan
    result = await scheduled_market_scan()
    return {"triggered": True, "result": result}
