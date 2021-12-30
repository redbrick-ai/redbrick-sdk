"""Handler for file upload/download."""
import os
from typing import List, Optional, Tuple

import asyncio
import aiohttp
import aiofiles
from yarl import URL
import tenacity

from redbrick.common.client import MAX_CONCURRENCY, MAX_RETRY_ATTEMPTS
from redbrick.utils.async_utils import gather_with_concurrency


def uniquify_path(path: str) -> str:
    """Provide unique path with number index."""
    filename, extension = os.path.splitext(path)
    counter = 1

    while os.path.exists(path):
        path = filename + " (" + str(counter) + ")" + extension
        counter += 1

    return path


async def download_files(files: List[Tuple[str, str]]) -> List[Optional[str]]:
    """Download files from url to local path."""

    @tenacity.retry(
        stop=tenacity.stop_after_attempt(MAX_RETRY_ATTEMPTS),
        wait=tenacity.wait_exponential(multiplier=1, min=1, max=10),
        retry=tenacity.retry_if_not_exception_type((KeyboardInterrupt,)),
    )
    async def _download_file(
        session: aiohttp.ClientSession, url: URL, path: str
    ) -> Optional[str]:
        if not url or not path:
            return None
        async with session.get(url) as response:
            if response.status == 200:
                path = uniquify_path(path)
                async with aiofiles.open(path, "wb") as file_:  # type: ignore
                    await file_.write(await response.read())
                return path
            return None

    # limit to 30, default is 100, cleanup is done by session
    conn = aiohttp.TCPConnector(limit=MAX_CONCURRENCY)
    async with aiohttp.ClientSession(connector=conn) as session:
        coros = [
            _download_file(session, URL(url, encoded=True), path) for url, path in files
        ]
        paths = await gather_with_concurrency(10, coros, "Downloading files")

    await asyncio.sleep(0.250)  # give time to close ssl connections
    return paths
