"""Handler for file upload/download."""
import os
from typing import List, Optional, Tuple, Set

import asyncio
import aiohttp
import aiofiles
from yarl import URL
import tenacity
from natsort import natsorted, ns

from redbrick.common.constants import MAX_CONCURRENCY, MAX_RETRY_ATTEMPTS
from redbrick.utils.async_utils import gather_with_concurrency

IMAGE_FILE_TYPES = {
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "bmp": "image/bmp",
}

VIDEO_FILE_TYPES = {
    "mp4": "video/mp4",
}

DICOM_FILE_TYPES = {
    "dcm": "application/dicom",
}

FILE_TYPES = {**IMAGE_FILE_TYPES, **VIDEO_FILE_TYPES, **DICOM_FILE_TYPES}


def get_file_type(file_path: str) -> Tuple[str, str]:
    """
    Return file type.

    Return
    ------------
    [file_ext, file_type]
        file_ext: png, jpeg, jpg etc.
        file_type: this is the MIME file type e.g. image/png
    """
    file_ext = file_path.split("?", 1)[0].rstrip("/").rsplit(".", 1)[-1].lower()

    if file_ext not in FILE_TYPES:
        raise ValueError(
            f"Unsupported file type {file_ext}! Only {','.join(FILE_TYPES.keys())} are supported"
        )
    return file_ext, FILE_TYPES[file_ext]


def find_files_recursive(
    root: str, file_types: Set[str], multiple: bool = False
) -> List[List[str]]:
    """Find files recursively in a directory, that belong to a list of allowed file types."""
    if not os.path.isdir(root):
        return []

    items = []
    list_items = []
    discard_list_items = False

    for item in os.listdir(root):
        if item.startswith("."):
            continue
        path = os.path.join(root, item)
        if os.path.isdir(path):
            items.extend(find_files_recursive(path, file_types, multiple))
            discard_list_items = True
        elif os.path.isfile(path) and item.rsplit(".", 1)[-1].lower() in file_types:
            if multiple:
                if not discard_list_items:
                    list_items.append(path)
            else:
                items.append([path])
        else:
            discard_list_items = True

    if (
        not discard_list_items
        and len({item.rsplit(".", 1)[-1].lower() for item in list_items}) == 1
    ):
        items.append(list(natsorted(list_items, alg=ns.IGNORECASE)))  # type: ignore

    return items


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
        reraise=True,
        stop=tenacity.stop_after_attempt(MAX_RETRY_ATTEMPTS),
        wait=tenacity.wait_exponential(multiplier=1, min=1, max=10),
        retry=tenacity.retry_if_not_exception_type(
            (KeyboardInterrupt, PermissionError, ValueError)
        ),
    )
    async def _download_file(
        session: aiohttp.ClientSession, url: str, path: str
    ) -> Optional[str]:
        if not url or not path:
            return None
        async with session.get(URL(url, encoded=True)) as response:
            if response.status == 200:
                path = uniquify_path(path)
                async with aiofiles.open(path, "wb") as file_:  # type: ignore
                    await file_.write(await response.read())
                return path
            return None

    # limit to 30, default is 100, cleanup is done by session
    conn = aiohttp.TCPConnector(limit=MAX_CONCURRENCY)
    async with aiohttp.ClientSession(connector=conn) as session:
        coros = [_download_file(session, url, path) for url, path in files]
        paths = await gather_with_concurrency(10, coros, "Downloading files")

    await asyncio.sleep(0.250)  # give time to close ssl connections
    return paths
