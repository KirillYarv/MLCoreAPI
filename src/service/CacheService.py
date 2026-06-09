import json
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, List

import redis


class CacheServiceInterface(ABC):
    """Interface for file-based cache operations used by services."""

    @abstractmethod
    def load_many(self, cache_paths: List[str]) -> List[Any]:
        """Load and merge JSON payloads from many cache files."""
        pass

    @abstractmethod
    def save(self, data: Any, cache_name: str, time_to_expire_s: int = 0) -> None:
        pass

    @abstractmethod
    def load(self, cache_name: str) -> Any:
        pass


class JsonFileCacheService(CacheServiceInterface):
    """JSON file cache service implementation."""

    def load_many(self, cache_paths: List[str]) -> List[Any]:
        data: List[Any] = []
        for cache_path in cache_paths:
            path = Path(cache_path)
            if not path.exists():
                continue
            try:
                with open(path, "r", encoding="utf-8") as file:
                    payload = json.load(file)
                    if isinstance(payload, list):
                        data.extend(payload)
                    else:
                        data.append(payload)
            except json.JSONDecodeError:
                continue
        return data

    def save(self, data: List[Any], cache_name: str, time_to_expire_s: int = 0) -> None:
        path = Path(cache_name)
        with open(path, "w", encoding="utf-8") as file:
            json.dump(data, file, default=str)

    def load(self, cache_name: str) -> Any:
        pass


class RedisCacheService(CacheServiceInterface):
    """Redis cache service implementation."""

    def __init__(
        self,
        host: str = os.getenv("DEFAULT_URI") or "",
        port: int = int(os.getenv("REDIS_PORT") or 6379),
    ) -> None:
        self.redis_service: redis.Redis = redis.Redis(
            host=host,
            port=port,
            db=0,
        )

    def load_many(self, cache_paths: List[str]) -> List[Any]:
        data: List[Any] = []
        for cache_path in cache_paths:
            cached_part = self.redis_service.get(cache_path)

            if cached_part is None:
                continue

            data.append(json.loads(cached_part))

        return data

    def save(
        self, data: List[Any], cache_name: str, time_to_expire_s: int = 180
    ) -> None:
        self.redis_service.set(
            cache_name, json.dumps(data, default=str), ex=time_to_expire_s
        )

    def load(self, cache_name: str) -> Any:
        return self.redis_service.get(cache_name)
