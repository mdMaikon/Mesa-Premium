"""
Rate limiting middleware using slowapi
Implementation for preventing API abuse and DoS attacks
"""

import logging
import os
import time
from functools import wraps

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class InMemoryRateLimiter:
    """
    Simple in-memory rate limiter using Python dictionaries
    For production, consider using Redis for distributed rate limiting
    """

    def __init__(self):
        self.requests: dict[str, list] = {}
        self.cleanup_threshold = 1000  # Clean up when dict gets too large

    def is_allowed(self, key: str, limit: int, window: int) -> bool:
        """
        Check if request is allowed based on rate limit

        Args:
            key: Unique identifier (IP address or user ID)
            limit: Number of requests allowed
            window: Time window in seconds

        Returns:
            True if allowed, False if rate limited
        """
        current_time = time.time()

        # Clean up old entries periodically
        if len(self.requests) > self.cleanup_threshold:
            self._cleanup_old_entries(current_time, window)

        # Get request timestamps for this key
        if key not in self.requests:
            self.requests[key] = []

        request_times = self.requests[key]

        # Remove timestamps outside the current window
        cutoff_time = current_time - window
        request_times[:] = [t for t in request_times if t > cutoff_time]

        # Check if under the limit
        if len(request_times) < limit:
            request_times.append(current_time)
            return True

        return False

    def _cleanup_old_entries(self, current_time: float, max_window: int):
        """Clean up old entries from memory"""
        cutoff_time = current_time - max_window
        keys_to_remove = []

        for key, timestamps in self.requests.items():
            # Remove old timestamps
            timestamps[:] = [t for t in timestamps if t > cutoff_time]
            # If no recent requests, remove the key entirely
            if not timestamps:
                keys_to_remove.append(key)

        for key in keys_to_remove:
            del self.requests[key]

    def get_reset_time(self, key: str, window: int) -> float | None:
        """Get the time when rate limit will reset for a key"""
        if key not in self.requests or not self.requests[key]:
            return None

        oldest_request = min(self.requests[key])
        return oldest_request + window


class RateLimitConfig:
    """Configuration for different rate limits"""

    # Default rate limits
    DEFAULT_RATE_LIMIT = "60/minute"  # 60 requests per minute
    TOKEN_EXTRACTION_LIMIT = "5/minute"  # 5 token extractions per minute
    FIXED_INCOME_LIMIT = "10/minute"  # 10 data processing requests per minute
    HEALTH_CHECK_LIMIT = "120/minute"  # 120 health checks per minute

    @staticmethod
    def parse_rate_limit(rate_string: str) -> tuple[int, int]:
        """
        Parse rate limit string into (requests, seconds)

        Args:
            rate_string: String like "60/minute", "5/hour", "100/day"

        Returns:
            Tuple of (request_count, time_window_seconds)
        """
        try:
            requests, period = rate_string.split("/")
            requests = int(requests)

            if period == "second":
                seconds = 1
            elif period == "minute":
                seconds = 60
            elif period == "hour":
                seconds = 3600
            elif period == "day":
                seconds = 86400
            else:
                raise ValueError(f"Unknown period: {period}")

            return requests, seconds
        except Exception as e:
            logger.error(f"Error parsing rate limit '{rate_string}': {e}")
            # Default to 60 requests per minute
            return 60, 60


# Global rate limiter instance
rate_limiter = InMemoryRateLimiter()


def get_client_ip(request: Request) -> str:
    """Extract client IP address from request"""
    # Check for forwarded IP (behind proxy)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()

    # Check for real IP header
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    # Fallback to client host
    client_host = getattr(request.client, "host", "unknown")
    return client_host


async def rate_limit_middleware(request: Request, call_next):
    """
    Rate limiting middleware for FastAPI
    """
    # Skip rate limiting during tests
    if os.getenv("DISABLE_RATE_LIMITING") == "true":
        response = await call_next(request)
        return response

    # Skip rate limiting for health checks in development
    if (
        request.url.path == "/api/health"
        and os.getenv("ENVIRONMENT") == "development"
    ):
        response = await call_next(request)
        return response

    # Determine rate limit based on endpoint
    path = request.url.path
    method = request.method

    # Configure rate limits for different endpoints
    if path == "/api/token/extract":
        rate_limit_str = os.getenv(
            "TOKEN_RATE_LIMIT", RateLimitConfig.TOKEN_EXTRACTION_LIMIT
        )
    elif path == "/api/fixed-income/process":
        rate_limit_str = os.getenv(
            "FIXED_INCOME_RATE_LIMIT", RateLimitConfig.FIXED_INCOME_LIMIT
        )
    elif path.startswith("/api/health"):
        rate_limit_str = os.getenv(
            "HEALTH_RATE_LIMIT", RateLimitConfig.HEALTH_CHECK_LIMIT
        )
    else:
        rate_limit_str = os.getenv(
            "DEFAULT_RATE_LIMIT", RateLimitConfig.DEFAULT_RATE_LIMIT
        )

    # Parse rate limit
    requests_allowed, time_window = RateLimitConfig.parse_rate_limit(
        rate_limit_str
    )

    # Get client identifier
    client_ip = get_client_ip(request)
    rate_limit_key = f"{client_ip}:{path}:{method}"

    # Check rate limit
    if not rate_limiter.is_allowed(
        rate_limit_key, requests_allowed, time_window
    ):
        # Rate limit exceeded
        reset_time = rate_limiter.get_reset_time(rate_limit_key, time_window)
        retry_after = (
            int(reset_time - time.time()) if reset_time else time_window
        )

        logger.warning(f"Rate limit exceeded for {client_ip} on {path}")

        # Return rate limit error
        headers = {
            "X-RateLimit-Limit": str(requests_allowed),
            "X-RateLimit-Window": str(time_window),
            "X-RateLimit-Retry-After": str(max(retry_after, 1)),
        }

        return JSONResponse(
            status_code=429,
            content={
                "error": "Rate limit exceeded",
                "message": f"Too many requests. Limit: {requests_allowed} per {time_window} seconds",
                "retry_after": retry_after,
            },
            headers=headers,
        )

    # Add rate limit headers to response
    response = await call_next(request)

    # Add informational headers
    response.headers["X-RateLimit-Limit"] = str(requests_allowed)
    response.headers["X-RateLimit-Window"] = str(time_window)

    return response


def rate_limit(limit_string: str):
    """
    Decorator for applying rate limits to specific endpoints

    Usage:
        @rate_limit("10/minute")
        async def my_endpoint():
            pass
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            # Parse rate limit
            requests_allowed, time_window = RateLimitConfig.parse_rate_limit(
                limit_string
            )

            # Get client identifier
            client_ip = get_client_ip(request)
            rate_limit_key = f"{client_ip}:{func.__name__}"

            # Check rate limit
            if not rate_limiter.is_allowed(
                rate_limit_key, requests_allowed, time_window
            ):
                reset_time = rate_limiter.get_reset_time(
                    rate_limit_key, time_window
                )
                retry_after = (
                    int(reset_time - time.time())
                    if reset_time
                    else time_window
                )

                raise HTTPException(
                    status_code=429,
                    detail={
                        "error": "Rate limit exceeded",
                        "message": f"Too many requests. Limit: {requests_allowed} per {time_window} seconds",
                        "retry_after": retry_after,
                    },
                )

            return await func(request, *args, **kwargs)

        return wrapper

    return decorator
