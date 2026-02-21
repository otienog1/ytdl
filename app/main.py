from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from slowapi.errors import RateLimitExceeded
from contextlib import asynccontextmanager
import uvicorn
import traceback

from app.config.settings import settings
from app.config.database import connect_to_mongo, close_mongo_connection
from app.config.redis_client import redis_client
from app.middleware.rate_limit import limiter, _rate_limit_exceeded_handler
from app.middleware.metrics_middleware import MetricsMiddleware
from app.routes import download, status as status_routes, history, storage_routes, websocket_routes, admin_routes, cookie_routes, health
from app.utils.logger import logger
from app.exceptions import AppException
from prometheus_client import make_asgi_app


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    logger.info("Starting YouTube Shorts Downloader API...")
    await connect_to_mongo()
    await redis_client.connect()

    # Start cleanup scheduler (optional)
    # You can add APScheduler here if needed

    yield

    # Shutdown
    logger.info("Shutting down...")
    await close_mongo_connection()
    await redis_client.close()


app = FastAPI(
    title="YouTube Shorts Downloader API",
    description="API for downloading YouTube Shorts videos",
    version="1.0.0",
    lifespan=lifespan
)

# Add rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Metrics middleware
app.add_middleware(MetricsMiddleware)


# Include routers
app.include_router(health.router, prefix="/api/health", tags=["health"])
app.include_router(download.router, prefix="/api/download", tags=["download"])
app.include_router(status_routes.router, prefix="/api/status", tags=["status"])
app.include_router(history.router, prefix="/api/history", tags=["history"])
app.include_router(storage_routes.router)
app.include_router(websocket_routes.router)
app.include_router(admin_routes.router)
app.include_router(cookie_routes.router, prefix="/api/cookies", tags=["cookies"])

# Mount Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


# Error handlers
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    """Handle custom application exceptions"""
    logger.error(
        f"Application error: {exc.error_code}",
        extra={
            "error_code": exc.error_code,
            "path": request.url.path,
            "method": request.method,
            "details": exc.details
        }
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict()
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors"""
    logger.warning(
        "Validation error",
        extra={
            "path": request.url.path,
            "errors": exc.errors()
        }
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid request data",
                "details": exc.errors()
            }
        }
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    logger.error(
        "Unexpected error",
        extra={
            "path": request.url.path,
            "error": str(exc),
            "traceback": traceback.format_exc()
        }
    )

    # Don't expose internal errors in production
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred",
                "details": {} if settings.ENVIRONMENT == "production" else {"error": str(exc)}
            }
        }
    )


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.ENVIRONMENT == "development",
        log_level="info"
    )
