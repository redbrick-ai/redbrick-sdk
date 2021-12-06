"""CLI cache handler."""
import os
import shutil
import pickle
from typing import Any
from datetime import datetime

import redbrick
from redbrick.cli.entity import CLIConfiguration


class CLICache:
    """CLICache entity."""

    _cache_dir: str
    _conf: CLIConfiguration

    CACHE_LIFETIME: int = 86400

    def __init__(self, cache_dir: str, conf: CLIConfiguration) -> None:
        """Initialize CLICache."""
        self._cache_dir = cache_dir
        self._conf = conf

        if self._conf.exists:
            conf_version = self._conf.get_option("module", "version")
            if conf_version and conf_version != redbrick.__version__:
                self.clear_cache()
                self._conf.set_option("module", "version", redbrick.__version__)
                self._conf.save()

    @property
    def exists(self) -> bool:
        """Boolean flag to indicate if cache directory exists."""
        if os.path.exists(self._cache_dir):
            if os.path.isdir(self._cache_dir):
                return True
            raise Exception(f"Not a directory {self._cache_dir}")
        return False

    def cache_path(self, *path: str) -> str:
        """Get cache file path."""
        path_dir = os.path.join(self._cache_dir, *path[:-1])
        os.makedirs(path_dir, exist_ok=True)
        return os.path.join(path_dir, path[-1])

    def get_object(self, entity: str) -> Any:
        """Get entity object from cache."""
        try:
            prev_timestamp = self._conf.get_option(entity, "refresh", "0")
            timestamp = int(datetime.utcnow().timestamp())
            if (
                prev_timestamp
                and timestamp - int(prev_timestamp) <= self.CACHE_LIFETIME
            ):
                cache_file = self.cache_path(f"{entity}.pickle")

                with open(cache_file, "rb") as cache:
                    return pickle.load(cache)
            return None
        except Exception:  # pylint: disable=broad-except
            return None

    def set_object(self, entity: str, obj: Any, save_conf: bool = True) -> None:
        """Set entity object into cache."""
        self._conf.set_option(
            entity, "refresh", str(int(datetime.utcnow().timestamp()))
        )

        cache_file = self.cache_path(f"{entity}.pickle")

        with open(cache_file, "wb") as cache:
            pickle.dump(obj, cache)

        if save_conf:
            self._conf.save()

    def clear_cache(self, all_caches: bool = False) -> None:
        """Clear project cache."""
        if not self.exists:
            return

        caches = os.listdir(self._cache_dir)
        if not all_caches:
            caches = [cache for cache in caches if cache != redbrick.__version__]

        for cache in caches:
            shutil.rmtree(os.path.join(self._cache_dir, cache), True)
