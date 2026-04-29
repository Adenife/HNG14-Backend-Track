import time
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .logging import configure_logging, LogLevel
from .config import settings

logger = configure_logging(level=LogLevel.INFO)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that logs the request method, endpoint, status code, and response time on every request.

    This middleware measures the time it takes to process a request and logs the request method, endpoint, status code, and response time using the configured logging level.

    Args:
        request (Request): The incoming request.
        call_next (Callable): The next middleware in the chain.

    Returns:
        Response: The response from the next middleware.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Dispatches the request through the middleware.

        This function measures the time it takes to process a request and logs the request method, endpoint, status code, and response time using the configured logging level.

        Args:
            request (Request): The incoming request.
            call_next (Callable): The next middleware in the chain.

        Returns:
            Response: The response from the next middleware.
        """
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000
        logger.info(
            f"{request.method} {request.url.path} "
            f"status={response.status_code} "
            f"duration={duration_ms:.2f}ms"
        )
        return response


class APIVersionMiddleware(BaseHTTPMiddleware):
    """
    Require the X-API-Version: 1 header on all /api/* requests.
    Auth and health-check routes are exempt.
    """

    EXEMPT_PREFIXES = ("/auth", "/docs", "/redoc", "/openapi", "/api/check")

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Dispatches the request through the middleware.

        This function checks if the request path starts with "/api/" and is not exempted.
        If the request is for an exempted route, it proceeds to the next middleware.
        Otherwise, it checks if the X-API-Version header is present and matches the configured API version.
        If the header is missing or does not match, a JSON response with a 400 status code is returned.
        If the header is present and matches, the request is passed to the next middleware.

        Args:
            request (Request): The incoming request.
            call_next (Callable): The next middleware in the chain.

        Returns:
            Response: The response from the next middleware.
        """
        path = request.url.path

        # Skip non-API routes
        if not path.startswith("/api/"):
            return await call_next(request)

        # Skip exempt routes
        if any(path.startswith(p) for p in self.EXEMPT_PREFIXES):
            return await call_next(request)

        # Skip Swagger UI (important fix)
        if request.headers.get("user-agent", "").startswith("Swagger"):
            return await call_next(request)

        api_version = request.headers.get("X-API-Version")

        if api_version != settings.API_VERSION:
            return JSONResponse(
                status_code=400,
                content={
                    "status": "error",
                    "message": "API version header required",
                },
            )

        return await call_next(request)
