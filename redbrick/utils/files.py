"""Handler for file upload/download."""
from typing import List, Tuple

import asyncio
import aiohttp
import aiofiles
from yarl import URL

from redbrick.utils.async_utils import gather_with_concurrency


async def download_files(files: List[Tuple[str, str]]) -> None:
    """Download files from url to local path."""

    async def _download_file(
        session: aiohttp.ClientSession, url: URL, path: str
    ) -> None:
        async with session.get(url) as response:
            if response.status == 200:
                async with aiofiles.open(path, "wb") as file_:  # type: ignore
                    await file_.write(await response.read())

    # limit to 30, default is 100, cleanup is done by session
    conn = aiohttp.TCPConnector(limit=30)
    async with aiohttp.ClientSession(connector=conn) as session:
        coros = [
            _download_file(session, URL(url, encoded=True), path)
            for url, path in files
            if url and path
        ]
        await gather_with_concurrency(10, coros, "Downloading files")

    await asyncio.sleep(0.250)  # give time to close ssl connections
