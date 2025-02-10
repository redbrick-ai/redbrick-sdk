"""CLI cache handler."""

import os
import shutil
import zlib
import json
from typing import Dict, List, Optional, Union

from redbrick.config import config
from redbrick.utils.common_utils import hash_sha256
from .conf import CLIConfiguration


class CLICache:
    """CLICache entity."""

    _cache_dir: str
    _conf: CLIConfiguration

    _cache_name: str
    _fixed_cache_name: str = "sdk-cache"

    CACHE_LIFETIME: int = 86400

    def __init__(self, cache_dir: str, conf: CLIConfiguration) -> None:
        """Initialize CLICache."""
        self._cache_dir = cache_dir
        self._conf = conf

        self._cache_name = "cache-" + ".".join(config.version.split(".", 2)[:2])

        if self._conf.exists and self._cache_name != self._conf.get_option(
            "cache", "name"
        ):
            self.clear_cache()
            self._conf.set_option("cache", "name", self._cache_name)
            self._conf.save()

    def cache_path(self, *path: str, fixed_cache: bool = False) -> str:
        """Get cache file path."""
        path_dir = os.path.join(
            self._cache_dir,
            self._fixed_cache_name if fixed_cache else self._cache_name,
            *path[:-1],
        )
        os.makedirs(path_dir, exist_ok=True)
        return os.path.join(path_dir, path[-1])

    def get_data(
        self,
        name: str,
        cache_hash: Optional[str],
        json_data: bool = True,
        fixed_cache: bool = False,
    ) -> Optional[Union[str, Dict, List]]:
        """Get cache data."""
        if cache_hash is None:
            return None
        cache_file = self.cache_path(name, fixed_cache=fixed_cache)
        if os.path.isfile(cache_file):
            with open(cache_file, "rb") as file_:
                data = file_.read()
            if cache_hash == hash_sha256(data):
                data = zlib.decompress(data)
                return json.loads(data) if json_data else data.decode()
        return None

    def set_data(
        self, name: str, entity: Union[str, Dict, List], fixed_cache: bool = False
    ) -> str:
        """Set cache data."""
        cache_file = self.cache_path(name, fixed_cache=fixed_cache)
        data = zlib.compress(
            (
                entity
                if isinstance(entity, str)
                else json.dumps(entity, separators=(",", ":"))
            ).encode()
        )
        cache_hash = hash_sha256(data)
        with open(cache_file, "wb") as file_:
            file_.write(data)
        return cache_hash

    def remove_data(self, name: str, fixed_cache: bool = False) -> None:
        """Remove cache data."""
        cache_file = self.cache_path(name, fixed_cache=fixed_cache)
        if os.path.isfile(cache_file):
            os.remove(cache_file)

    def get_entity(
        self, name: str, fixed_cache: bool = False
    ) -> Optional[Union[str, Dict, List]]:
        """Get cache entity."""
        cache_file = self.cache_path(*self._task_path(name), fixed_cache=fixed_cache)
        with open(cache_file, "r", encoding="utf-8") as file_:
            data = json.load(file_)
        return data

    def set_entity(
        self, name: str, entity: Union[str, Dict, List], fixed_cache: bool = False
    ) -> None:
        """Set cache entity."""
        cache_file = self.cache_path(*self._task_path(name), fixed_cache=fixed_cache)
        with open(cache_file, "w", encoding="utf-8") as file_:
            json.dump(entity, file_, separators=(",", ":"))

    def remove_entity(self, name: str, fixed_cache: bool = False) -> None:
        """Remove cache entity."""
        cache_file = self.cache_path(*self._task_path(name), fixed_cache=fixed_cache)
        if os.path.isfile(cache_file):
            os.remove(cache_file)

    def _task_path(self, task_id: str) -> List[str]:
        """Get task dir from id."""
        return [
            task_id[6:8],
            task_id[11:13],
            task_id[16:18],
            task_id[21:23],
            task_id[34:36],
            task_id,
        ]

    def clear_cache(self, all_caches: bool = False) -> None:
        """Clear project cache."""
        if not os.path.isdir(self._cache_dir):
            return

        caches = os.listdir(self._cache_dir)
        if not all_caches:
            caches = [
                cache
                for cache in caches
                if cache not in (self._cache_name, self._fixed_cache_name)
            ]

        for cache in caches:
            shutil.rmtree(os.path.join(self._cache_dir, cache), ignore_errors=True)
