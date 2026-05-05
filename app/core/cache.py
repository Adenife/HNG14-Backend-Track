import time
from typing import Any, Dict, Optional


class InMemoryCache:
    def __init__(self, default_ttl: int = 300, max_size: int = 1000):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl
        self.max_size = max_size

    def get(self, key: str) -> Optional[Any]:
        if key not in self.cache:
            return None

        item = self.cache[key]
        if time.time() > item["expiry"]:
            del self.cache[key]
            return None

        return item["value"]

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        if len(self.cache) >= self.max_size:
            # Simple eviction: remove the first key (FIFO)
            # In a production system, LRU would be better
            first_key = next(iter(self.cache))
            del self.cache[first_key]

        expiry = time.time() + (ttl if ttl is not None else self.default_ttl)
        self.cache[key] = {"value": value, "expiry": expiry}

    def invalidate_all(self):
        self.cache.clear()

    def invalidate(self, key: str):
        if key in self.cache:
            del self.cache[key]


# Global cache instance
query_cache = InMemoryCache()
