"""
Simple TTL-based caching for market data to reduce API calls.
"""
import time
from typing import Any, Optional, Callable
from functools import wraps


class SimpleCache:
    """Simple in-memory cache with TTL support."""
    
    def __init__(self):
        self._cache = {}
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired."""
        if key not in self._cache:
            return None
        
        value, expiry = self._cache[key]
        if time.time() > expiry:
            del self._cache[key]
            return None
        
        return value
    
    def set(self, key: str, value: Any, ttl: int):
        """Set value in cache with TTL in seconds."""
        expiry = time.time() + ttl
        self._cache[key] = (value, expiry)
    
    def invalidate(self, key: str):
        """Remove key from cache."""
        if key in self._cache:
            del self._cache[key]
    
    def clear(self):
        """Clear entire cache."""
        self._cache.clear()
    
    def size(self) -> int:
        """Get number of cached items."""
        # Clean expired items first
        current_time = time.time()
        expired_keys = [k for k, (_, expiry) in self._cache.items() if current_time > expiry]
        for key in expired_keys:
            del self._cache[key]
        return len(self._cache)


# Global cache instance
_market_data_cache = SimpleCache()


def get_cache() -> SimpleCache:
    """Get global cache instance."""
    return _market_data_cache


def cache_key(prefix: str, *args, **kwargs) -> str:
    """Generate cache key from prefix and arguments."""
    key_parts = [prefix]
    key_parts.extend(str(arg) for arg in args)
    key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
    return ":".join(key_parts)


def cached(ttl: int, prefix: str = ""):
    """
    Decorator to cache function results.
    
    Args:
        ttl: Time to live in seconds
        prefix: Prefix for cache key
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            key = cache_key(prefix or func.__name__, *args, **kwargs)
            
            # Try to get from cache
            cached_value = _market_data_cache.get(key)
            if cached_value is not None:
                return cached_value
            
            # Call function and cache result
            result = func(*args, **kwargs)
            _market_data_cache.set(key, result, ttl)
            return result
        
        return wrapper
    return decorator
