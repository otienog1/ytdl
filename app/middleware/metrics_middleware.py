"""
Middleware for tracking HTTP metrics
"""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import time
from app.monitoring.metrics import (
    http_requests_total,
    http_request_duration_seconds
)


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to track HTTP request metrics"""

    async def dispatch(self, request: Request, call_next):
        # Start timer
        start_time = time.time()

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration = time.time() - start_time

        # Extract path pattern (remove IDs)
        path = request.url.path
        method = request.method
        status_code = response.status_code

        # Record metrics
        http_requests_total.labels(
            method=method,
            endpoint=path,
            status=status_code
        ).inc()

        http_request_duration_seconds.labels(
            method=method,
            endpoint=path
        ).observe(duration)

        # Add custom header
        response.headers["X-Process-Time"] = str(duration)

        return response
