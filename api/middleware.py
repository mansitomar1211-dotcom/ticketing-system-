# api/middleware.py
"""
Middleware for simulating network conditions.
"""
import asyncio
import random
from typing import Callable, Awaitable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from config.settings import api_settings
from .exception import SimulatedServerError


class NetworkSimulationMiddleware(BaseHTTPMiddleware):
    """Middleware to simulate network latency and failures."""
    
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        # Skip simulation for health checks and docs
        if request.url.path in ["/health", "/docs", "/openapi.json", "/redoc"]:
            return await call_next(request)
        
        # Simulate network latency
        delay = random.uniform(api_settings.min_latency, api_settings.max_latency)
        await asyncio.sleep(delay)
        
        # Simulate intermittent failures
        if random.random() < api_settings.failure_rate:
            error_type = random.choice([500, 503])
            raise SimulatedServerError(error_type)
        
        # Process the request normally
        return await call_next(request)
