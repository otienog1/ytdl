from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from contextlib import asynccontextmanager
import uvicorn

from app.config.settings import settings
from app.config.database import connect_to_mongo, close_mongo_connection
from app.config.redis_client import redis_client
from app.middleware.rate_limit import limiter, _rate_limit_exceeded_handler
from app.routes import download, status, history, storage_routes
from app.utils.logger import logger


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


# Health check
@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "timestamp": __import__('datetime').datetime.utcnow().isoformat()
    }


# Include routers
app.include_router(download.router, prefix="/api/download", tags=["download"])
app.include_router(status.router, prefix="/api/status", tags=["status"])
app.include_router(history.router, prefix="/api/history", tags=["history"])
app.include_router(storage_routes.router)


# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.ENVIRONMENT == "development",
        log_level="info"
    )
