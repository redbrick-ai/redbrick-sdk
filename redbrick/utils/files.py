"""Handler for file upload/download."""
import os
import gzip
from typing import Dict, List, Optional, Tuple, Set

import asyncio
import aiohttp
from yarl import URL
from tenacity import Retrying, RetryError
from tenacity.retry import retry_if_not_exception_type
from tenacity.stop import stop_after_attempt
from tenacity.wait import wait_random_exponential
from natsort import natsorted, ns

from redbrick.common.constants import MAX_FILE_BATCH_SIZE, MAX_RETRY_ATTEMPTS
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

DICOM_FILE_TYPES = {
    "": "application/dicom",
    "dcm": "application/dicom",
    "ima": "application/dicom",
}

JSON_FILE_TYPES = {"json": "application/json"}

NIFTI_FILE_TYPES = {"nii": "application/octet-stream"}

FILE_TYPES = {
    **IMAGE_FILE_TYPES,
    **VIDEO_FILE_TYPES,
    **DICOM_FILE_TYPES,
    **JSON_FILE_TYPES,
    **NIFTI_FILE_TYPES,
}

ALL_FILE_TYPES = {"*": "*/*"}


def get_file_type(file_path: str) -> Tuple[str, str]:
    """
    Return file type.

    Return
    ------------
    [file_ext, file_type]
        file_ext: png, jpeg, jpg etc.
        file_type: this is the MIME file type e.g. image/png
    """
    file_path, file_ext = os.path.splitext(file_path.lower())
    if file_ext == ".gz":
        file_path, file_ext = os.path.splitext(file_path)
    file_ext = file_ext.lstrip(".")

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
        elif os.path.isfile(path) and (  # pylint: disable=too-many-boolean-expressions
            "*" in file_types
            or (
                item.rsplit(".", 1)[-1].lower() in file_types
                or (
                    "." in item
                    and item.rsplit(".", 1)[-1].lower() == "gz"
                    and item.rsplit(".", 2)[-2].lower() in file_types
                )
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
    if extension == ".gz":
        filename, extension = os.path.splitext(filename)
        extension += ".gz"

    counter = 1

    while os.path.exists(path):
        path = filename + " (" + str(counter) + ")" + extension
        counter += 1

    return path


def is_gzipped_data(data: bytes) -> bool:
    """Check if data is gzipped."""
    return data[:2] == b"\x1f\x8b"


def is_dicom_file(file_name: str) -> bool:
    """Check if data is dicom."""
    with open(file_name, "rb") as fp_:
        data = fp_.read()

    if is_gzipped_data(data):
        data = gzip.decompress(data)

    return data[128:132] == b"\x44\x49\x43\x4d"


async def upload_files(
    files: List[Tuple[str, str, str]],
    progress_bar_name: Optional[str] = "Uploading files",
    keep_progress_bar: bool = True,
) -> List[bool]:
    """Upload files from local path to url (file path, presigned url, file type)."""

    async def _upload_file(
        session: aiohttp.ClientSession, path: str, url: str, file_type: str
    ) -> bool:
        if not path or not url or not file_type:
            return False

        with open(path, mode="rb") as file_:
            data = file_.read()

        status: int = 0

        headers = {"Content-Type": file_type}
        if not is_gzipped_data(data):
            headers["Content-Encoding"] = "gzip"
            data = gzip.compress(data)

        try:
            for attempt in Retrying(
                reraise=True,
                stop=stop_after_attempt(MAX_RETRY_ATTEMPTS),
                wait=wait_random_exponential(min=5, max=30),
                retry=retry_if_not_exception_type(KeyboardInterrupt),
            ):
                with attempt:
                    async with session.put(url, headers=headers, data=data) as response:
                        status = response.status
        except RetryError as error:
            raise Exception("Unknown problem occurred") from error

        if status == 200:
            return True
        raise ConnectionError(f"Error in uploading {path} to RedBrick")

    conn = aiohttp.TCPConnector()
    async with aiohttp.ClientSession(connector=conn) as session:
        coros = [
            _upload_file(session, path, url, file_type)
            for path, url, file_type in files
        ]
        uploaded = await gather_with_concurrency(
            MAX_FILE_BATCH_SIZE, coros, progress_bar_name, keep_progress_bar
        )

    await asyncio.sleep(0.250)  # give time to close ssl connections
    return uploaded


async def download_files(
    files: List[Tuple[Optional[str], Optional[str]]],
    progress_bar_name: Optional[str] = "Downloading files",
    keep_progress_bar: bool = True,
    overwrite: bool = False,
    zipped: bool = False,
) -> List[Optional[str]]:
    """Download files from url to local path (presigned url, file path)."""

    async def _download_file(
        session: aiohttp.ClientSession, url: Optional[str], path: Optional[str]
    ) -> Optional[str]:
        # pylint: disable=no-member
        if not url or not path:
            return None

        if not overwrite and os.path.isfile(path):
            return path

        headers: Dict = {}
        data: Optional[bytes] = None

        try:
            for attempt in Retrying(
                reraise=True,
                stop=stop_after_attempt(MAX_RETRY_ATTEMPTS),
                wait=wait_random_exponential(min=5, max=30),
                retry=retry_if_not_exception_type(KeyboardInterrupt),
            ):
                with attempt:
                    async with session.get(URL(url, encoded=True)) as response:
                        if response.status == 200:
                            headers = dict(response.headers)
                            data = await response.read()
        except RetryError as error:
            raise Exception("Unknown problem occurred") from error

        if not data:
            return None

        if not zipped and headers.get("Content-Encoding") == "gzip":
            try:
                data = gzip.decompress(data)
            except Exception:  # pylint: disable=broad-except
                pass
        if zipped and not is_gzipped_data(data):
            data = gzip.compress(data)
        if zipped and not path.endswith(".gz"):
            path += ".gz"
        if not overwrite:
            path = uniquify_path(path)
        with open(path, "wb") as file_:
            file_.write(data)
        return path

    conn = aiohttp.TCPConnector()
    async with aiohttp.ClientSession(connector=conn) as session:
        coros = [_download_file(session, url, path) for url, path in files]
        paths = await gather_with_concurrency(
            MAX_FILE_BATCH_SIZE,
            coros,
            progress_bar_name,
            keep_progress_bar,
            True,
        )
        await session.close()

    await asyncio.sleep(0.250)  # give time to close ssl connections
    return [(path if isinstance(path, str) else None) for path in paths]
