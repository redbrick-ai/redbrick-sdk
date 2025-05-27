"""AltaDB utils."""

import os
from typing import Any, Dict, List, Optional

import aiohttp
import pydicom
import pydicom.dataset
import pydicom.encaps
import pydicom.tag
import pydicom.uid
from pydicom.uid import (
    UID_dictionary,  # type: ignore
    AllTransferSyntaxes,
    JPEG2000TransferSyntaxes,
)

from redbrick.common.constants import DEFAULT_URL, MAX_CONCURRENCY, MAX_FILE_BATCH_SIZE
from redbrick.utils.async_utils import gather_with_concurrency
from redbrick.utils.logging import logger


def move_group2_to_file_meta(dataset: Any) -> Any:
    """Move all group 2 elements to file meta.

    Args
    ----
    metadata_dcm_dataset: pydicom.Dataset
        The metadata of the DICOM file.
    """
    if not hasattr(dataset, "file_meta"):
        dataset.file_meta = pydicom.dataset.FileMetaDataset()

    for elem in dataset:
        if elem.tag.group == 2:
            dataset.file_meta.add(elem)
            del dataset[elem.tag]

    return dataset


async def save_dicom_dataset(
    instance_metadata: Dict,
    instance_frames_metadata: List[Dict],
    presigned_image_urls: List[str],
    destination_file: str,
    aiosession: aiohttp.ClientSession,
) -> None:
    """Create and save a DICOM dataset using metadata and image frame URLs.

    Args
    ------------
    instance_metadata: Dict
        Metadata of the instance.
    instance_frames_metadata: List[Dict]
        Metadata of the instance frames.
    presigned_image_urls: List[str]
        Presigned URLs of the image frames.
    destination_file: str
        Destination file to save the DICOM dataset.
    aiosession: aiohttp.ClientSession
        aiohttp ClientSession to be used for the HTTP requests.
    """
    HTJ2KLosslessRPCL = pydicom.uid.UID(  # pylint: disable=invalid-name
        "1.2.840.10008.1.2.4.202"
    )
    AllTransferSyntaxes.append(HTJ2KLosslessRPCL)
    JPEG2000TransferSyntaxes.append(HTJ2KLosslessRPCL)
    UID_dictionary[HTJ2KLosslessRPCL] = (
        "High-Throughput JPEG 2000 with RPCL Options Image Compression (Lossless Only)",
        "Transfer Syntax",
        "",
        "",
        "HTJ2KLosslessRPCL",
    )

    async def get_image_content(
        aiosession: aiohttp.ClientSession, image_url: str
    ) -> bytes:
        """Get image content."""
        async with aiosession.get(image_url) as response:
            return await response.content.read()

    frame_contents = await gather_with_concurrency(
        MAX_FILE_BATCH_SIZE,
        *[
            get_image_content(aiosession, image_url=image_frame_url)
            for image_frame_url in presigned_image_urls
        ],
    )

    ds_file = pydicom.Dataset.from_json(instance_metadata)
    ds_file.TransferSyntaxUID = pydicom.uid.UID(
        instance_frames_metadata[0]["metaData"]["00020010"]["Value"][0]
    )

    move_group2_to_file_meta(ds_file)

    ds_file.PixelData = pydicom.encaps.encapsulate(frame_contents)

    if ds_file.file_meta.TransferSyntaxUID == HTJ2KLosslessRPCL:
        ds_file.is_little_endian = True
        ds_file.is_implicit_VR = False
    ds_file.save_as(destination_file, write_like_original=False)
    logger.debug(f"Saved DICOM dataset to {destination_file}")


async def save_dicom_series(
    altadb_meta_content_url: str,
    series_dir: str,
    base_url: str = DEFAULT_URL,
    headers: Optional[Dict[str, str]] = None,
) -> List[str]:
    """Save DICOM files using AltaDB URLs.
    Given an AltaDB URL containing the metadata and image frames.

    Save the DICOM files to the destination directory.
    One DICOM file can contain multiple image frames.

    Args
    ------------
    altadb_meta_content_url: str
        AltaDB URL containing the metadata and image frames.
        This URL can be signed or unsigned.
    base_dir: str
        Destination directory to save the DICOM files.
    base_url: str
        Base URL for the AltaDB API.
    headers: Optional[Dict[str, str]]
        Headers to be used for the HTTP requests.
        If the altaDB_meta_content_url is unsigned, the headers should contain the authorization token.

    Returns
    ------------
    List[str]
        List of the saved DICOM files relative to the dataset root.
    """
    # pylint: disable=too-many-locals
    os.makedirs(series_dir, exist_ok=True)

    res: List[str] = []
    if altadb_meta_content_url.startswith("altadb:///"):
        altadb_meta_content_url = "".join([base_url, "/", altadb_meta_content_url[10:]])
    elif altadb_meta_content_url.startswith("altadb://"):
        altadb_meta_content_url = altadb_meta_content_url.replace(
            "altadb://", "https://"
        )

    async with aiohttp.ClientSession() as aiosession:
        async with aiosession.get(altadb_meta_content_url, headers=headers) as response:
            res_json = await response.json()
            frameid_url_map: Dict[str, str] = {
                frame["id"]: frame["path"] for frame in res_json.get("imageFrames", [])
            }

            tasks = []
            metadata_url = res_json["metaData"]
            instances: List[Dict[str, Any]] = []
            async with aiosession.get(metadata_url) as response:
                response.raise_for_status()
                instances = (await response.json())["instances"]
            for instance in instances:
                frame_ids = [frame["id"] for frame in instance["frames"]]
                image_frames_urls = [
                    frameid_url_map[frame_id] for frame_id in frame_ids
                ]
                file_from_dataset_root = os.path.join(
                    series_dir, f"{instance['frames'][0]['id']}.dcm"
                )
                tasks.append(
                    save_dicom_dataset(
                        instance["metaData"],
                        instance["frames"],
                        image_frames_urls,
                        file_from_dataset_root,
                        aiosession,
                    )
                )
                res.append(file_from_dataset_root)

            await gather_with_concurrency(
                MAX_CONCURRENCY,
                *tasks,
                progress_bar_name=f"Saving series {series_dir.split('/')[-1]}",
                keep_progress_bar=False,
            )

    return res
