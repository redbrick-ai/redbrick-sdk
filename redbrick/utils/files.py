"""Handler for file upload/download."""
import os
import gzip
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
    "dcm": "application/dicom",
}

VIDEO_FILE_TYPES = {
    "mp4": "video/mp4",
    "avi": "video/x-msvideo",
    "dcm": "application/dicom",
}

DICOM_FILE_TYPES = {"dcm": "application/dicom", "ima": "application/dicom"}

JSON_FILE_TYPES = {"json": "application/json"}

NIFTI_FILE_TYPES = {"nii": "application/octet-stream"}

FILE_TYPES = {
    **IMAGE_FILE_TYPES,
    **VIDEO_FILE_TYPES,
    **DICOM_FILE_TYPES,
    **JSON_FILE_TYPES,
    **NIFTI_FILE_TYPES,
}


def get_file_type(file_path: str) -> Tuple[str, str]:
    """
    Return file type.

    Return
    ------------
    [file_ext, file_type]
        file_ext: png, jpeg, jpg etc.
        file_type: this is the MIME file type e.g. image/png
    """
    file_ext = file_path.split("?", 1)[0].rstrip("/").lower()
    if file_ext.endswith(".gz"):
        file_ext = file_ext[:-3]
    file_ext = file_ext.rsplit(".", 1)[-1].lower()

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
        elif os.path.isfile(path) and (
            item.rsplit(".", 1)[-1].lower() in file_types
            or (
                "." in item
                and item.rsplit(".", 1)[-1].lower() == "gz"
                and item.rsplit(".", 2)[-2].lower() in file_types
            )
        ):
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


async def upload_files(
    files: List[Tuple[str, str, str]],
    progress_bar_name: Optional[str] = "Uploading files",
    keep_progress_bar: bool = True,
) -> List[bool]:
    """Upload files from local path to url (file path, presigned url, file type)."""

    @tenacity.retry(
        reraise=True,
        stop=tenacity.stop_after_attempt(MAX_RETRY_ATTEMPTS),
        wait=tenacity.wait_exponential(multiplier=1, min=1, max=10),
        retry=tenacity.retry_if_not_exception_type((KeyboardInterrupt,)),
        retry_error_callback=lambda _: False,
    )
    async def _upload_file(
        session: aiohttp.ClientSession, path: str, url: str, file_type: str
    ) -> bool:
        if not path or not url or not file_type:
            return False
        async with aiofiles.open(path, mode="rb") as file_:  # type: ignore
            data = await file_.read()

        async with session.put(
            url,
            headers={"Content-Type": file_type, "Content-Encoding": "gzip"},
            data=data if path.endswith(".gz") else gzip.compress(data),
        ) as response:
            if response.status == 200:
                return True
            raise ConnectionError(f"Error in uploading {path} to RedBrick")

    # limit to 30, default is 100, cleanup is done by session
    conn = aiohttp.TCPConnector(limit=MAX_CONCURRENCY)
    async with aiohttp.ClientSession(connector=conn) as session:
        coros = [
            _upload_file(session, path, url, file_type)
            for path, url, file_type in files
        ]
        uploaded = await gather_with_concurrency(
            10, coros, progress_bar_name, keep_progress_bar
        )

    await asyncio.sleep(0.250)  # give time to close ssl connections
    return uploaded


async def download_files(
    files: List[Tuple[str, str]],
    progress_bar_name: Optional[str] = "Downloading files",
    keep_progress_bar: bool = True,
) -> List[Optional[str]]:
    """Download files from url to local path (presigned url, file path)."""

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
        # pylint: disable=no-member
        if not url or not path:
            return None
        async with session.get(URL(url, encoded=True)) as response:
            if response.status == 200:
                data = await response.read()
                if response.headers.get("Content-Encoding") == "gzip":
                    try:
                        data = gzip.decompress(data)
                    except Exception:  # pylint: disable=broad-except
                        pass
                path = uniquify_path(path)
                async with aiofiles.open(path, "wb") as file_:  # type: ignore
                    await file_.write(data)
                return path
            return None

    # limit to 30, default is 100, cleanup is done by session
    conn = aiohttp.TCPConnector(limit=MAX_CONCURRENCY)
    async with aiohttp.ClientSession(connector=conn) as session:
        coros = [_download_file(session, url, path) for url, path in files]
        paths = await gather_with_concurrency(
            10, coros, progress_bar_name, keep_progress_bar
        )

    await asyncio.sleep(0.250)  # give time to close ssl connections
    return paths
