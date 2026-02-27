"""
Proxy Headers Middleware
Handles X-Forwarded-* headers from reverse proxy (Nginx)
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.datastructures import Headers, MutableHeaders
from fastapi import Request


class ProxyHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to trust proxy headers (X-Forwarded-Proto, X-Forwarded-For, etc.)
    This ensures FastAPI generates correct URLs when behind a reverse proxy
    """

    async def dispatch(self, request: Request, call_next):
        # Trust X-Forwarded-Proto header from Nginx
        forwarded_proto = request.headers.get("X-Forwarded-Proto")
        if forwarded_proto:
            # Update the request scope to use the forwarded protocol
            request.scope["scheme"] = forwarded_proto

        # Trust X-Forwarded-For for real client IP
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP (the original client)
            client_ip = forwarded_for.split(",")[0].strip()
            request.scope["client"] = (client_ip, request.scope.get("client", ("", 0))[1])

        response = await call_next(request)
        return response
