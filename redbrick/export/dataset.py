"""Public API to exporting."""

import asyncio
from typing import Iterator, List, Dict, Optional
from functools import partial
import os
import json

from rich.console import Console

from redbrick.common.constants import MAX_CONCURRENCY
from redbrick.common.entities import RBDataset
from redbrick.common.export import DatasetExport
from redbrick.utils.async_utils import gather_with_concurrency
from redbrick.utils.pagination import PaginationIterator


# pylint: disable=too-many-lines


class DatasetExportImpl(DatasetExport):
    """
    Primary interface for various export methods.

    The export module has many functions for exporting annotations and meta-data from projects. The export module is available from the :attr:`redbrick.RBProject` module.

    .. code:: python

        >>> project = redbrick.get_project(api_key="", org_id="", project_id="")
        >>> project.export # Export
    """

    def __init__(self, dataset: RBDataset) -> None:
        """Construct Export object."""
        self.dataset = dataset
        self.context = self.dataset.context

    def get_data_store_series(
        self, *, search: Optional[str] = None, page_size: int = MAX_CONCURRENCY
    ) -> Iterator[Dict[str, str]]:
        """Get data store series."""
        my_iter = PaginationIterator(
            partial(
                self.context.export.get_dataset_import_series,
                self.dataset.org_id,
                self.dataset.dataset_name,
                search,
            ),
            limit=page_size,
        )

        yield from my_iter

    def export_to_files(
        self,
        path: str,
        page_size: int = MAX_CONCURRENCY,
        number: Optional[int] = None,
        search: Optional[str] = None,  # pylint: disable=unused-argument
    ) -> None:
        """Export dataset to folder.

        Args
        ----
        path: str
            Path to the folder where the dataset will be saved.
        page_size: int
            Number of series to export in parallel.
        number: int
            Number of series to export in total.
        search: str
            Search string to filter the series to export.
        """
        try:
            console = Console()
            console.print(
                f"[bold green][\u2713] Saving dataset {self.dataset.dataset_name} to {path}"
            )
            dataset_root = f"{path}/{self.dataset.dataset_name}"
            json_path = f"{dataset_root}/series.json"
            if os.path.exists(json_path):
                console.print(
                    f"[bold yellow][\u26a0] Warning: {json_path} already exists. It will be overwritten."
                )
                os.remove(json_path)

            ds_import_series_list: List[Dict[str, str]] = []
            # Save the files in chunks of page_size
            for ds_import_series in self.get_data_store_series(
                search=search,
                page_size=number or MAX_CONCURRENCY,
            ):
                ds_import_series_list.append(ds_import_series)
                if len(ds_import_series_list) >= page_size:
                    asyncio.run(
                        self.save_series_data_chunk(
                            page_size,
                            dataset_root,
                            json_path,
                            ds_import_series_list,
                        )
                    )
                    ds_import_series_list = []

            if ds_import_series_list:
                asyncio.run(
                    self.save_series_data_chunk(
                        page_size,
                        dataset_root,
                        json_path,
                        ds_import_series_list,
                    )
                )
        except Exception as error:  # pylint: disable=broad-except
            console.print(f"[bold red][\u2717] Error: {error}")

    async def save_series_data_chunk(
        self,
        max_concurrency: int,
        dataset_root: str,
        json_path: str,
        ds_import_series_list: List[Dict[str, str]],
    ) -> None:
        """Store data for the given series imports.

        Args
        ----
        max_concurrency: int
            Number of series to export in parallel.
        dataset_root: str
            Path to the dataset root folder.
        json_path: str
            Path to the series.json file.
        ds_import_series_list: List[Dict]
            List of series to export.

        """
        # pylint: disable=import-outside-toplevel
        from redbrick.utils.altadb import save_dicom_series

        base_url = self.context.client.url.strip()
        if base_url.endswith("/graphql/"):
            base_url = base_url[:-8]
        if base_url.endswith("api/"):
            base_url = base_url.rstrip("api/")
        coros = [
            save_dicom_series(
                ds_import_series["url"],
                os.path.join(dataset_root, ds_import_series["seriesId"]),
                base_url,
                self.context.client.headers,
            )
            for ds_import_series in ds_import_series_list
        ]
        file_paths_list = await gather_with_concurrency(
            max_concurrency,
            *coros,
            progress_bar_name=f"Exporting {len(ds_import_series_list)} series",
            keep_progress_bar=True,
        )
        new_series = []
        # Save the series data to the series.json file
        for ds_import, file_paths in zip(ds_import_series_list, file_paths_list):
            new_series.append(
                {
                    "dataset": self.dataset.dataset_name,
                    "seriesId": ds_import["seriesId"],
                    "importId": ds_import["importId"],
                    "createdAt": ds_import["createdAt"],
                    "createdBy": ds_import["createdBy"],
                    "items": file_paths,
                }
            )
        if new_series:
            series = []
            if os.path.exists(json_path):
                with open(json_path, "r", encoding="utf-8") as series_file:
                    series = json.load(series_file)

            with open(json_path, "w+", encoding="utf-8") as series_file:
                json.dump(
                    [
                        *series,
                        *new_series,
                    ],
                    series_file,
                    indent=2,
                )
