from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import Request


def key_func(request: Request) -> str:
    """
    Rate-limit by IP address only (safe, async-compatible).
    """
    return get_remote_address(request)


limiter = Limiter(key_func=key_func)
