"""Public interface to upload module."""

import asyncio
import os
from typing import Callable, List, Dict, Optional

import tqdm  # type: ignore

from redbrick.common.entities import RBDataset
from redbrick.common.constants import MAX_FILE_BATCH_SIZE
from redbrick.common.upload import DatasetUpload
from redbrick.utils.async_utils import gather_with_concurrency
from redbrick.utils.logging import log_error, logger
from redbrick.utils.files import (
    DICOM_FILE_TYPES,
    find_files_recursive,
    get_file_type,
    upload_files,
)


SUPPORTED_UPLOAD_FILE_TYPES = [
    *list(DICOM_FILE_TYPES.keys()),
]


class DatasetUploadImpl(DatasetUpload):
    """
    Primary interface for uploading to a dataset.

    .. code:: python

        >>> dataset = redbrick.get_dataset(api_key="", org_id="", dataset_name="")
        >>> dataset.upload
    """

    def __init__(self, dataset: RBDataset) -> None:
        """Construct DatasetUpload object."""
        self.dataset = dataset
        self.context = self.dataset.context

    async def _upload_files_intermediate_function(
        self,
        import_id: str,
        import_name: Optional[str] = None,
        files_paths: Optional[List[Dict[str, str]]] = None,
        upload_callback: Optional[Callable] = None,
    ) -> bool:
        """Upload files to presigned URLs."""
        # Generate presigned URLs for concurrency number of files at a time
        files_paths = files_paths or []
        _, presigned_urls = self.context.upload.import_dataset_files(
            org_id=self.dataset.org_id,
            data_store=self.dataset.dataset_name,
            import_name=import_name,
            import_id=import_id,
            files=[
                {
                    "filePath": file["filePath"],
                    "fileType": file["fileType"],
                }
                for file in files_paths
            ],
        )

        if not presigned_urls:
            return False

        # Upload files to presigned URLs
        results = await upload_files(
            [
                (
                    file_path["abs_file_path"],
                    presigned_url,
                    get_file_type(file_path["abs_file_path"])[-1],
                )
                for file_path, presigned_url in zip(files_paths, presigned_urls)
            ],
            progress_bar_name="Batch Progress",
            keep_progress_bar=False,
            upload_callback=upload_callback,
        )
        return all(results)

    def upload_files(
        self,
        path: str,
        import_name: Optional[str] = None,
        concurrency: int = MAX_FILE_BATCH_SIZE,
    ) -> None:
        """Upload files."""
        files: List[str] = []
        if not path:
            logger.warning("No file path provided")
            return

        if not os.path.exists(path):
            logger.warning(f"Provided path {path} does not exist.")
            return

        if os.path.isdir(path):
            _files = find_files_recursive(
                path, set(DICOM_FILE_TYPES.keys()), multiple=False
            )
            files = [_file[0] for _file in _files if _file]

        else:
            file_type = get_file_type(path)[0]
            if file_type in SUPPORTED_UPLOAD_FILE_TYPES:
                files = [path]
            else:
                logger.warning(f"File {path} is not supported")

        if not files:
            logger.warning(f"No files found in path {path}")
            return

        # Now that we have the files list, let us generate the presigned URLs
        files_list: List[Dict[str, str]] = []
        for file_ in files:
            files_list.append(
                {
                    "filePath": os.path.basename(file_),
                    "abs_file_path": file_,
                    "fileType": "application/dicom",
                }
            )

        import_id, _ = self.context.upload.import_dataset_files(
            org_id=self.dataset.org_id,
            data_store=self.dataset.dataset_name,
            import_name=import_name,
        )
        if not import_id:
            log_error("Unable to import", True)

        progress_bar = tqdm.tqdm(desc="Uploading all files", total=len(files_list))

        def _upload_callback(*_):
            progress_bar.update(1)

        # Upload files to presigned URLs
        upload_status = asyncio.run(
            gather_with_concurrency(
                min(5, concurrency),
                *[
                    self._upload_files_intermediate_function(
                        import_name=import_name,
                        import_id=import_id,
                        files_paths=files_list[i : i + MAX_FILE_BATCH_SIZE],
                        upload_callback=_upload_callback,
                    )
                    for i in range(0, len(files_list), MAX_FILE_BATCH_SIZE)
                ],
            )
        )

        if not upload_status:
            log_error("Error uploading files", True)

        mutation_status = self.context.upload.process_dataset_import(
            org_id=self.dataset.org_id,
            data_store=self.dataset.dataset_name,
            import_id=import_id,
            total_files=len(files),
        )
        if not mutation_status:
            log_error("Error finalizing the import", True)
