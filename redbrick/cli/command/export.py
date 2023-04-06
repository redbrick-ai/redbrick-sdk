"""CLI export command."""
import asyncio
import os
import re
import json
from datetime import datetime, timezone
from argparse import ArgumentError, ArgumentParser, Namespace
from typing import List, Dict, Tuple
import shutil

import shtab

from redbrick.cli.project import CLIProject
from redbrick.cli.cli_base import CLIExportInterface
from redbrick.common.constants import MAX_FILE_BATCH_SIZE
from redbrick.utils.async_utils import gather_with_concurrency
from redbrick.utils.files import (
    uniquify_path,
    download_files,
    IMAGE_FILE_TYPES,
    VIDEO_FILE_TYPES,
    NIFTI_FILE_TYPES,
    DICOM_FILE_TYPES,
)
from redbrick.utils.logging import log_error, logger


class CLIExportController(CLIExportInterface):
    """CLI export command controller."""

    def __init__(self, parser: ArgumentParser) -> None:
        """Intialize export sub commands."""
        parser.add_argument(
            "type",
            nargs="?",
            default=self.TYPE_LATEST,
            help=f"Export type: ({self.TYPE_LATEST} [default], {self.TYPE_GROUNDTRUTH}, <task id>)",
        )
        parser.add_argument(
            "--with-files",
            action="store_true",
            help="Export with files (e.g. images/video frames)",
        )
        parser.add_argument(
            "--dicom-to-nifti",
            action="store_true",
            help="Convert DICOM images to NIfTI. Applicable when `--with-files` is set.",
        )
        parser.add_argument(
            "--old-format",
            action="store_true",
            help="""Whether to export tasks in old format. (Default: False)""",
        )
        parser.add_argument(
            "--no-consensus",
            action="store_true",
            help="""Whether to export tasks without consensus info.
            If None, will default to export with consensus info,
            if it is enabled for the given project.""",
        )
        parser.add_argument(
            "--png",
            action="store_true",
            help="Export labels as png masks",
        )
        parser.add_argument(
            "--clear-cache",
            action="store_true",
            help="Clear local cache",
        )
        parser.add_argument(
            "--concurrency",
            "-c",
            type=int,
            default=10,
            help="Concurrency value (Default: 10)",
        )
        parser.add_argument(
            "--stage",
            "-s",
            help="Export tasks that are currently in the given stage. "
            + "Applicable only with `redbrick export` and `redbrick export latest`",
        )
        parser.add_argument(
            "--destination",
            "-d",
            default=".",
            help="Destination directory (Default: current directory)",
        ).complete = shtab.DIRECTORY  # type: ignore

    def handler(self, args: Namespace) -> None:
        """Handle export command."""
        self.args = args
        project = CLIProject.from_path()
        assert project, "Not a valid project"
        self.project = project

        self.handle_export()

    def handle_export(self) -> None:
        """Handle empty sub command."""
        # pylint: disable=too-many-statements, too-many-locals, too-many-branches, protected-access
        if (
            self.args.type not in (self.TYPE_LATEST, self.TYPE_GROUNDTRUTH)
            and re.match(
                r"^[\da-f]{8}-([\da-f]{4}-){3}[\da-f]{12}$",
                self.args.type.strip().lower(),
            )
            is None
        ):
            raise ArgumentError(None, f"Invalid export type: {self.args.type}")

        if self.args.clear_cache:
            self.project.cache.clear_cache(True)

        no_consensus = (
            self.args.no_consensus
            if self.args.no_consensus
            else not self.project.project.consensus_enabled
        )

        cached_datapoints: Dict = {}
        cache_timestamp = None
        dp_conf = self.project.conf.get_section("datapoints")
        if dp_conf and "timestamp" in dp_conf:
            cached_dp = self.project.cache.get_data("datapoints", dp_conf["cache"])
            if isinstance(cached_dp, dict):
                cached_datapoints = cached_dp
                cache_timestamp = int(dp_conf["timestamp"]) or None

        current_timestamp = int(datetime.now(timezone.utc).timestamp())
        datapoints, taxonomy = self.project.project.export._get_raw_data_latest(
            self.args.concurrency,
            False,
            cache_timestamp,
            False,
            bool(self.project.project.label_stages)
            and not bool(self.project.project.review_stages)
            and not no_consensus,
        )

        logger.info(f"Refreshed {len(datapoints)} newly updated tasks")

        for datapoint in datapoints:
            cached_datapoints[datapoint["taskId"]] = datapoint

        dp_hash = self.project.cache.set_data("datapoints", cached_datapoints)
        self.project.conf.set_section(
            "datapoints",
            {
                "timestamp": str(
                    current_timestamp if datapoints else (cache_timestamp or 0)
                ),
                "cache": dp_hash,
            },
        )
        self.project.conf.save()

        data = list(cached_datapoints.values())

        if self.args.type == self.TYPE_LATEST:
            if self.args.stage:
                data = [
                    task
                    for task in data
                    if task["currentStageName"].lower() == self.args.stage.lower()
                ]
        elif self.args.type == self.TYPE_GROUNDTRUTH:
            data = [task for task in data if task["currentStageName"] == "END"]
        else:
            task_id = self.args.type.strip().lower()
            task = None
            for dpoint in data:
                if dpoint["taskId"] == task_id:
                    task = dpoint
                    break
            data = [task] if task else []

        loop = asyncio.get_event_loop()

        self.project.conf.save()

        export_dir = self.args.destination

        os.makedirs(export_dir, exist_ok=True)

        png_mask = bool(self.args.png)
        segmentations_dir = os.path.join(export_dir, "segmentations")
        os.makedirs(segmentations_dir, exist_ok=True)
        task_file = os.path.join(export_dir, "tasks.json")
        class_file = os.path.join(export_dir, "class_map.json")
        storage_ids = [task["storageId"] for task in data]
        tasks, class_map = self.project.project.export.export_nifti_label_data(
            data,
            self.args.concurrency,
            taxonomy,
            segmentations_dir,
            bool(self.args.old_format),
            no_consensus,
            png_mask,
        )
        logger.info(f"Exported segmentations to: {segmentations_dir}")

        if self.args.with_files:
            try:
                loop.run_until_complete(
                    self._download_tasks(
                        tasks,
                        storage_ids,
                        export_dir,
                        bool(self.args.dicom_to_nifti),
                        self.args.concurrency,
                    )
                )
            except Exception as err:  # pylint: disable=broad-except
                log_error(f"Failed to download files: {err}")

        with open(task_file, "w", encoding="utf-8") as tasks_file:
            json.dump(tasks, tasks_file, indent=2)

        logger.info(f"Exported: {task_file}")

        if png_mask:
            with open(class_file, "w", encoding="utf-8") as classes_file:
                json.dump(class_map, classes_file, indent=2)

            logger.info(f"Exported: {class_file}")

    async def _download_tasks(
        self,
        tasks: List[Dict],
        storage_ids: List[str],
        export_dir: str,
        dcm_to_nii: bool,
        concurrency: int = 5,
    ) -> List[Dict]:
        # pylint: disable=too-many-locals, import-outside-toplevel, too-many-nested-blocks

        images_dir = os.path.join(export_dir, "images")
        os.makedirs(images_dir, exist_ok=True)

        downloaded_tasks = await gather_with_concurrency(
            min(concurrency, MAX_FILE_BATCH_SIZE),
            [
                self._download_task(task, storage_id, images_dir)
                for task, storage_id in zip(tasks, storage_ids)
            ],
            progress_bar_name="Downloading images",
            keep_progress_bar=False,
        )
        tasks = [task for task, _ in downloaded_tasks]

        logger.info(f"Exported images to: {images_dir}")

        if not dcm_to_nii:
            return tasks

        import numpy as np  # type: ignore
        import nibabel as nb  # type: ignore
        from dicom2nifti import settings, dicom_series_to_nifti  # type: ignore

        settings.disable_validate_slice_increment()

        logger.info("Converting DICOM image volumes to NIfTI")

        dcm_ext = re.compile(
            r"\.("
            + "|".join(
                (
                    IMAGE_FILE_TYPES.keys()
                    | VIDEO_FILE_TYPES.keys()
                    | NIFTI_FILE_TYPES.keys()
                )
                - DICOM_FILE_TYPES.keys()
            )
            + r")(\.gz)?$"
        )
        for task, series_dirs in downloaded_tasks:
            if not task.get("series") or len(task["series"]) != len(series_dirs):
                continue
            for series, series_dir in zip(task["series"], series_dirs):
                items = (
                    [series["items"]]
                    if isinstance(series["items"], str)
                    else series["items"]
                )
                if (
                    dcm_to_nii
                    and len(items) > 1
                    and not any(
                        re.search(dcm_ext, item.split("?", 1)[0].rstrip("/"))
                        for item in items
                    )
                ):
                    logger.info(f"Converting {task['taskId']} image to nifti")
                    try:
                        nii_img = dicom_series_to_nifti(
                            series_dir, uniquify_path(series_dir + ".nii.gz")
                        )
                    except Exception as err:  # pylint: disable=broad-except
                        logger.warning(
                            f"Task {task['taskId']} : Failed to convert {series_dir} - {err}"
                        )
                        continue
                    series["items"] = nii_img["NII_FILE"]
                    if series.get("segmentations"):
                        logger.debug(f"{task['taskId']} matching headers")
                        try:
                            nii_seg = nb.load(  # type: ignore
                                os.path.abspath(
                                    series["segmentations"]
                                    if isinstance(series["segmentations"], str)
                                    else series["segmentations"][0]
                                )
                            )
                            imgh = nii_img["NII"].header
                            segh = nii_seg.header
                            if not (
                                imgh.get_data_shape() == segh.get_data_shape()
                                and imgh.get_data_offset() == segh.get_data_offset()
                                and np.array_equal(
                                    imgh.get_best_affine(), segh.get_best_affine()
                                )
                                and np.array_equal(imgh.get_qform(), segh.get_qform())
                                and np.array_equal(imgh.get_sform(), segh.get_sform())
                            ):
                                logger.warning(
                                    f"Task: {task['taskId']} : Headers of converted "
                                    + "nifti image and segmentation do not match."
                                )
                        except Exception as err:  # pylint: disable=broad-except
                            logger.warning(
                                f"Task {task['taskId']} : Failed to match headers - {err}"
                            )

        return tasks

    async def _download_task(
        self,
        task: Dict,
        storage_id: str,
        parent_dir: str,
    ) -> Tuple[Dict, List[str]]:
        # pylint: disable=too-many-locals, too-many-branches
        path_pattern = re.compile(r"[^\w.]+")
        task_name = re.sub(path_pattern, "-", task.get("name", "")) or task["taskId"]
        task_dir = os.path.join(parent_dir, task_name)

        if os.path.isfile(task_dir):
            os.remove(task_dir)
        else:
            shutil.rmtree(task_dir, ignore_errors=True)
        os.makedirs(task_dir, exist_ok=True)

        series_dirs: List[str] = []
        items_lists: List[List[str]] = []

        try:
            if task.get("series"):
                for series_idx, series in enumerate(task["series"]):
                    series_dir = uniquify_path(
                        os.path.join(
                            task_dir,
                            re.sub(path_pattern, "-", series.get("name", "") or "")
                            or (
                                task_name
                                if len(task["series"]) == 1
                                else chr(series_idx + ord("A"))
                            ),
                        )
                    )
                    os.makedirs(series_dir)
                    series_dirs.append(series_dir)
                    items_lists.append(
                        [series["items"]]
                        if isinstance(series["items"], str)
                        else series["items"]
                    )
            else:
                series_dir = os.path.join(task_dir, task_name)
                os.makedirs(series_dir)
                series_dirs.append(series_dir)
                items_lists.append(task["items"])

            to_presign = []
            local_files = []
            for series_dir, paths in zip(series_dirs, items_lists):
                file_names = [
                    re.sub(
                        path_pattern,
                        "-",
                        os.path.basename(path.split("?", 1)[0].rstrip("/")),
                    )
                    for path in paths
                ]
                fill_index = (
                    0
                    if all(file_names) and len(file_names) == len(set(file_names))
                    else len(str(len(file_names)))
                )
                to_presign.extend(paths)
                for index, item in enumerate(file_names):
                    file_name, file_ext = os.path.splitext(item)
                    local_files.append(
                        os.path.join(
                            series_dir,
                            file_name
                            + (
                                ("-" + str(index).zfill(fill_index))
                                if fill_index
                                else ""
                            )
                            + file_ext,
                        )
                    )

            presigned = self.project.context.export.presign_items(
                self.project.org_id, storage_id, to_presign
            )

            if any(not presigned_path for presigned_path in presigned):
                raise Exception("Failed to presign some files")

            downloaded = await download_files(
                list(zip(presigned, local_files)), "Downloading files", False
            )

            if any(not downloaded_file for downloaded_file in downloaded):
                raise Exception("Failed to download some files")

            if task.get("series"):
                prev_count = 0
                for series_dir, series in zip(series_dirs, task["series"]):
                    count = (
                        1 if isinstance(series["items"], str) else len(series["items"])
                    )
                    series["items"] = downloaded[prev_count : prev_count + count]
                    prev_count += count
            else:
                task["items"] = downloaded

        except Exception as err:  # pylint: disable=broad-except
            log_error(f"Failed to download files for task {task['taskId']}: {err}")
            shutil.rmtree(task_dir, ignore_errors=True)

        return task, series_dirs
