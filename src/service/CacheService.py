import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, List


class CacheServiceInterface(ABC):
    """Interface for file-based cache operations used by services."""

    @abstractmethod
    def load_many(self, cache_paths: List[str]) -> List[Any]:
        """Load and merge JSON payloads from many cache files."""

    @abstractmethod
    def save(self, data: Any, file_path: str) -> None:
        """Persist JSON-serializable payload into one cache file."""


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

    def save(self, data: Any, file_path: str) -> None:
        path = Path(file_path)
        with open(path, "w", encoding="utf-8") as file:
            json.dump(data, file, default=str)
