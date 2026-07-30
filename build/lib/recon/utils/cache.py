"""
Simple caching layer for recon results.

Supports two backends:
- FileCache: stores pickled Python objects on disk.
- RedisCache: uses Redis (requires `redis` package).

The module provides a unified CacheBackend interface and a factory
function `get_cache` that reads configuration to choose the backend.
"""

import hashlib
import pickle
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Optional

import structlog

logger = structlog.get_logger(__name__)


class CacheBackend(ABC):
    """Abstract base for cache implementations."""

    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Retrieve a cached value, or None if missing/expired."""
        ...

    @abstractmethod
    def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        """Store a value with a TTL (in seconds)."""
        ...

    @abstractmethod
    def delete(self, key: str) -> None:
        """Remove a key from the cache."""
        ...

    @abstractmethod
    def clear(self) -> None:
        """Clear all cached entries."""
        ...

    def _make_key(self, *parts: str) -> str:
        """Create a deterministic cache key from parts."""
        raw = ":".join(parts)
        return hashlib.sha256(raw.encode()).hexdigest()


class FileCache(CacheBackend):
    """
    File‑based cache using pickle.

    Each key maps to a file named with the hashed key.
    """

    def __init__(self, cache_dir: Path, default_ttl: int = 3600):
        self.cache_dir = cache_dir
        self.default_ttl = default_ttl
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _file_path(self, key: str) -> Path:
        return self.cache_dir / f"{key}.cache"

    def get(self, key: str) -> Optional[Any]:
        path = self._file_path(key)
        if not path.exists():
            return None
        try:
            with open(path, "rb") as f:
                entry = pickle.load(f)
            if time.time() > entry.get("expires", 0):
                self.delete(key)
                return None
            return entry["value"]
        except Exception:
            logger.warning("Failed to read cache", key=key)
            return None

    def set(self, key: str, value: Any, ttl: int = None) -> None:
        ttl = ttl if ttl is not None else self.default_ttl
        entry = {
            "value": value,
            "expires": time.time() + ttl,
        }
        try:
            with open(self._file_path(key), "wb") as f:
                pickle.dump(entry, f)
        except Exception:
            logger.exception("Failed to write cache", key=key)

    def delete(self, key: str) -> None:
        path = self._file_path(key)
        try:
            path.unlink(missing_ok=True)
        except Exception:
            pass

    def clear(self) -> None:
        for cache_file in self.cache_dir.glob("*.cache"):
            try:
                cache_file.unlink()
            except Exception:
                pass


class RedisCache(CacheBackend):
    """
    Redis‑backed cache.

    Requires the `redis` Python package and a running Redis server.
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        default_ttl: int = 3600,
    ):
        self.default_ttl = default_ttl
        try:
            import redis
            self.client = redis.Redis(
                host=host, port=port, db=db, password=password, decode_responses=False
            )
            self.client.ping()
        except ImportError:
            raise RuntimeError(
                "Redis support requires the 'redis' package. Install it with: pip install redis"
            )
        except redis.ConnectionError as e:
            raise RuntimeError(f"Cannot connect to Redis at {host}:{port}") from e

    def get(self, key: str) -> Optional[Any]:
        try:
            data = self.client.get(key)
            if data is None:
                return None
            return pickle.loads(data)
        except Exception:
            logger.warning("Redis cache read failed", key=key)
            return None

    def set(self, key: str, value: Any, ttl: int = None) -> None:
        ttl = ttl if ttl is not None else self.default_ttl
        try:
            self.client.setex(key, ttl, pickle.dumps(value))
        except Exception:
            logger.exception("Redis cache write failed", key=key)

    def delete(self, key: str) -> None:
        try:
            self.client.delete(key)
        except Exception:
            pass

    def clear(self) -> None:
        try:
            self.client.flushdb()
        except Exception:
            logger.warning("Redis flush failed")


def get_cache(config: dict = None) -> CacheBackend:
    """
    Factory to instantiate the appropriate cache backend from configuration.

    Expects a configuration dict with a `cache` section:
        cache:
            backend: "file" or "redis"
            file_dir: "/path/to/cache"   # for file backend
            redis:
                host: "localhost"
                port: 6379
                db: 0
                password: null
            ttl: 3600

    Args:
        config: Configuration dictionary. If None, defaults to file cache.

    Returns:
        A CacheBackend instance.
    """
    if config is None:
        config = {}

    cache_cfg = config.get("cache", {})
    backend = cache_cfg.get("backend", "file").lower()
    ttl = cache_cfg.get("ttl", 3600)

    if backend == "redis":
        redis_cfg = cache_cfg.get("redis", {})
        return RedisCache(
            host=redis_cfg.get("host", "localhost"),
            port=redis_cfg.get("port", 6379),
            db=redis_cfg.get("db", 0),
            password=redis_cfg.get("password"),
            default_ttl=ttl,
        )
    else:
        file_dir = Path(cache_cfg.get("file_dir", "~/.recon/cache")).expanduser()
        return FileCache(cache_dir=file_dir, default_ttl=ttl)