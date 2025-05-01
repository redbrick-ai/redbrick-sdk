"""Handler for file upload/download."""

import os
import gzip
from typing import Any, Callable, Dict, List, Optional, Tuple, Set
import urllib.parse

import aiohttp
from yarl import URL
from tenacity import Retrying, RetryError
from tenacity.retry import retry_if_not_exception_type
from tenacity.stop import stop_after_attempt
from tenacity.wait import wait_random_exponential
from natsort import natsorted, ns

from redbrick.common.constants import (
    MAX_FILE_BATCH_SIZE,
    MAX_RETRY_ATTEMPTS,
)
from redbrick.utils.async_utils import gather_with_concurrency, get_session
from redbrick.utils.logging import log_error, logger
from redbrick.config import config


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
    "dicom": "application/dicom",
}

JSON_FILE_TYPES = {"json": "application/json"}

NIFTI_FILE_TYPES = {"nii": "application/octet-stream"}

NRRD_FILE_TYPES = {"nrrd": "application/octet-stream"}

REPORT_FILE_TYPES = {"txt": "text/plain"}

FILE_TYPES = {
    **IMAGE_FILE_TYPES,
    **VIDEO_FILE_TYPES,
    **DICOM_FILE_TYPES,
    **JSON_FILE_TYPES,
    **NIFTI_FILE_TYPES,
    **NRRD_FILE_TYPES,
    **REPORT_FILE_TYPES,
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
    segmentations_upload: bool = False,
    zipped: bool = False,
    keep_progress_bar: bool = False,
    upload_callback: Optional[Callable] = None,
) -> List[bool]:
    """Upload files from local path to url (file path, presigned url, file type)."""
    timeout = aiohttp.ClientTimeout(connect=60)
    verify_ssl = config.verify_ssl

    async def _upload_file(
        session: aiohttp.ClientSession, path: str, url: str, file_type: str
    ) -> bool:
        if not path or not url or not file_type:
            return False

        status: int = 0
        request_params: aiohttp.client._RequestOptions = {
            "timeout": timeout,
            "headers": {"Content-Type": file_type},
        }

        tmp_path: Optional[str] = None

        if zipped:
            tmp_path = uniquify_path(path + ".gz")
            request_params["headers"]["Content-Encoding"] = "gzip"  # type: ignore
            with open(path, "rb") as f_:
                data = gzip.compress(f_.read())
            with open(tmp_path, "wb") as f_:
                f_.write(data)

        if segmentations_upload:
            request_params["headers"]["x-ms-blob-type"] = "BlockBlob"  # type: ignore

        if not verify_ssl:
            request_params["ssl"] = False

        try:
            for attempt in Retrying(
                reraise=True,
                stop=stop_after_attempt(MAX_RETRY_ATTEMPTS),
                wait=wait_random_exponential(min=5, max=30),
                retry=retry_if_not_exception_type(KeyboardInterrupt),
            ):
                with attempt:
                    with open(tmp_path or path, "rb") as f_:
                        request_params["data"] = f_
                        async with session.put(url, **request_params) as response:
                            status = response.status
        except RetryError as error:
            if tmp_path:
                os.remove(tmp_path)
            raise Exception("Unknown problem occurred") from error

        if tmp_path:
            os.remove(tmp_path)

        if status in (200, 201):
            if upload_callback:
                upload_callback()
            return True

        raise ConnectionError(f"Error in uploading {path} to RedBrick")

    async with get_session() as session:
        coros = [
            _upload_file(session, path, url, file_type)
            for path, url, file_type in files
        ]
        uploaded = await gather_with_concurrency(
            MAX_FILE_BATCH_SIZE,
            *coros,
            progress_bar_name=progress_bar_name,
            keep_progress_bar=keep_progress_bar,
        )

    return uploaded


async def download_files(
    files: List[Tuple[Optional[str], Optional[str]]],
    progress_bar_name: Optional[str] = "Downloading files",
    keep_progress_bar: bool = True,
    overwrite: bool = False,
    zipped: bool = False,
) -> List[Optional[str]]:
    """Download files from url to local path (presigned url, file path)."""
    # pylint: disable=too-many-statements

    async def _download_file(
        session: aiohttp.ClientSession, url: Optional[str], path: Optional[str]
    ) -> Optional[str]:
        # pylint: disable=no-member
        if not url or not path:
            logger.debug(f"Downloading empty '{url}' to '{path}'")
            return None

        path = urllib.parse.unquote(path)
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
                    request_params: Dict[str, Any] = {}
                    if not config.verify_ssl:
                        request_params["ssl"] = False
                    async with session.get(
                        URL(url, encoded=True), **request_params
                    ) as response:
                        if response.status == 200:
                            headers = dict(response.headers)
                            data = await response.read()
        except RetryError as error:
            log_error(error)
            raise Exception("Unknown problem occurred") from error

        if not data:
            logger.debug(f"Received empty data from '{url}'")
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

    dirs: Set[str] = set()
    for _, path in files:
        if not path:
            continue
        parent = os.path.dirname(path)
        if parent in dirs:
            continue
        if not os.path.isdir(parent):
            logger.debug(f"Creating parent dir for {path}")
            os.makedirs(parent, exist_ok=True)
        dirs.add(parent)

    async with get_session() as session:
        coros = [_download_file(session, url, path) for url, path in files]
        paths = await gather_with_concurrency(
            MAX_FILE_BATCH_SIZE,
            *coros,
            progress_bar_name=progress_bar_name,
            keep_progress_bar=keep_progress_bar,
            return_exceptions=True,
        )
        await session.close()

    output: List[Optional[str]] = []
    for path in paths:
        if path is None or isinstance(path, str):
            output.append(path)
        else:
            log_error(path)
            output.append(None)

    return output


async def download_files_altadb(
    files: List[Tuple[str, str]],
    progress_bar_name: Optional[str] = "Downloading files",
    keep_progress_bar: bool = True,
) -> List[Optional[List[str]]]:
    """Download files from altadb (presigned url, file path)."""
    # pylint: disable=import-outside-toplevel, cyclic-import
    from redbrick.utils.dicom import save_dicom_series

    paths = await gather_with_concurrency(
        MAX_FILE_BATCH_SIZE,
        *[save_dicom_series(url, path) for url, path in files],
        progress_bar_name=progress_bar_name,
        keep_progress_bar=keep_progress_bar,
        return_exceptions=True,
    )

    output: List[Optional[List[str]]] = []
    for path in paths:
        if path is None or isinstance(path, list):
            output.append(path or None)
        else:
            log_error(path)
            output.append(None)

    return output


def is_altadb_item(item: str) -> bool:
    """Check if current item is an altadb item."""
    return item.startswith("altadb:")


def contains_altadb_item(items_list: List[str]) -> bool:
    """Filter out altadb items."""
    return any(is_altadb_item(item) for item in items_list)


async def is_valid_file_url(url: str) -> bool:
    """Check if the file url is valid."""
    result = False
    url = url.replace("altadb://", "https://")
    async with get_session() as session:
        try:
            async with session.get(url) as response:
                result = response.status == 200
        except Exception as error:  # pylint: disable=broad-except
            log_error(error)

    return result
