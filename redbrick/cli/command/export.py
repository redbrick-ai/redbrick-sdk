"""CLI export command."""
import asyncio
import os
import re
import json
from datetime import datetime, timezone
from argparse import ArgumentError, ArgumentParser, Namespace
from typing import List, Dict
import shutil

from redbrick.cli.project import CLIProject
from redbrick.cli.cli_base import CLIExportInterface
from redbrick.coco.coco_main import _get_image_dimension_map, coco_converter
from redbrick.common.enums import LabelType
from redbrick.utils.files import uniquify_path, download_files
from redbrick.utils.logging import print_info, print_warning, print_error


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
            "--format",
            "-f",
            choices=[
                self.FORMAT_REDBRICK,
                self.FORMAT_COCO,
                self.FORMAT_MASK,
                self.FORMAT_NIFTI,
            ],
            help="Export format (Default: "
            + f"{self.FORMAT_MASK} if project type is {LabelType.IMAGE_SEGMENTATION}, "
            + f"{self.FORMAT_NIFTI} if project type is {LabelType.DICOM_SEGMENTATION}, "
            + f"else {self.FORMAT_REDBRICK})",
        )
        parser.add_argument(
            "--with-files",
            action="store_true",
            help="Export with files (e.g. images/video frames)",
        )
        parser.add_argument(
            "--clear-cache", action="store_true", help="Clear local cache"
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
            + f"Applicable for only type = {self.TYPE_LATEST}",
        )
        parser.add_argument(
            "--fill-holes",
            action="store_true",
            help=f"Fill holes (for {self.FORMAT_MASK} export format)",
        )
        parser.add_argument(
            "--max-hole-size",
            type=int,
            default=30,
            help=f"Max hole size (for {self.FORMAT_MASK} export format. Default: 30)",
        )
        parser.add_argument(
            "--destination",
            "-d",
            default=".",
            help="Destination directory (Default: current directory)",
        )

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

        from redbrick.export.public import (  # pylint: disable=import-outside-toplevel
            Export,
        )

        format_type = (
            self.args.format
            if self.args.format
            else (
                self.FORMAT_MASK
                if self.project.project.project_type == LabelType.IMAGE_SEGMENTATION
                else self.FORMAT_NIFTI
                if self.project.project.project_type == LabelType.DICOM_SEGMENTATION
                else self.FORMAT_REDBRICK
            )
        )
        if (
            format_type == self.FORMAT_MASK
            and self.project.project.project_type != LabelType.IMAGE_SEGMENTATION
        ):
            raise Exception(
                f"{self.FORMAT_MASK} is available for {LabelType.IMAGE_SEGMENTATION} projects."
            )
        if (
            format_type == self.FORMAT_NIFTI
            and self.project.project.project_type != LabelType.DICOM_SEGMENTATION
        ):
            raise Exception(
                f"{self.FORMAT_NIFTI} is available for {LabelType.DICOM_SEGMENTATION} projects."
            )
        if (
            self.args.type not in (self.TYPE_LATEST, self.TYPE_GROUNDTRUTH)
            and re.match(
                r"^[\da-f]{8}-([\da-f]{4}-){3}[\da-f]{12}$",
                self.args.type.strip().lower(),
            )
            is None
        ):
            raise ArgumentError(None, "")

        if self.args.clear_cache or self.args.with_files:
            self.project.cache.clear_cache(True)

        cached_datapoints: Dict = {}
        cache_timestamp = None
        dp_conf = self.project.conf.get_section("datapoints")
        if dp_conf and "timestamp" in dp_conf:
            cached_dp = self.project.cache.get_data("datapoints", dp_conf["cache"])
            if isinstance(cached_dp, dict):
                cached_datapoints = cached_dp
                cache_timestamp = int(dp_conf["timestamp"])

        cached_dimensions: Dict = {}
        dim_cache = self.project.conf.get_option("dimensions", "cache")
        cached_dim = self.project.cache.get_data("dimensions", dim_cache)
        if isinstance(cached_dim, dict):
            cached_dimensions = cached_dim

        current_timestamp = int(datetime.now(timezone.utc).timestamp())
        datapoints, taxonomy = self.project.project.export._get_raw_data_latest(
            self.args.concurrency, False, cache_timestamp
        )

        print_info(f"Refreshed {len(datapoints)} newly updated tasks")

        for datapoint in datapoints:
            task_id = datapoint["taskId"]
            if task_id not in cached_dimensions:
                cached_dimensions[task_id] = None

            cached_datapoints[task_id] = datapoint

        dp_hash = self.project.cache.set_data("datapoints", cached_datapoints)
        self.project.conf.set_section(
            "datapoints", {"timestamp": str(current_timestamp), "cache": dp_hash}
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
        if format_type == self.FORMAT_COCO:
            compute_dims = [
                task
                for task in data
                if task["taskId"] not in cached_dimensions
                or cached_dimensions[task["taskId"]] is None
            ]
            if compute_dims:
                image_dimensions = loop.run_until_complete(
                    _get_image_dimension_map(compute_dims)
                )
                for task_id, dimension in image_dimensions.items():
                    cached_dimensions[task_id] = dimension

        dim_hash = self.project.cache.set_data("dimensions", cached_dimensions)
        self.project.conf.set_section("dimensions", {"cache": dim_hash})
        self.project.conf.save()

        export_dir = self.args.destination

        os.makedirs(export_dir, exist_ok=True)

        cli_data = [
            {key: value for key, value in task.items() if key != "itemsPresigned"}
            for task in data
        ]
        if format_type == self.FORMAT_MASK:
            mask_dir = os.path.join(export_dir, "masks")
            class_map = os.path.join(export_dir, "class_map.json")
            datapoint_map = os.path.join(export_dir, "datapoint_map.json")
            shutil.rmtree(mask_dir, ignore_errors=True)
            os.makedirs(mask_dir, exist_ok=True)
            Export._export_png_mask_data(
                cli_data,
                taxonomy,
                mask_dir,
                class_map,
                datapoint_map,
                self.args.fill_holes,
                self.args.max_hole_size,
            )
            print_info(f"Exported: {class_map}")
            print_info(f"Exported: {datapoint_map}")
            print_info(f"Exported masks to: {mask_dir}")
        elif format_type == self.FORMAT_NIFTI:
            nifti_dir = os.path.join(export_dir, "nifti")
            shutil.rmtree(nifti_dir, ignore_errors=True)
            os.makedirs(nifti_dir, exist_ok=True)
            task_map = os.path.join(export_dir, "tasks.json")
            Export._export_nifti_label_data(cli_data, nifti_dir, task_map)
            print_info(f"Exported: {task_map}")
            print_info(f"Exported nifti to: {nifti_dir}")
        else:
            export_path = os.path.join(
                export_dir,
                f"export_{format_type}_{self.args.type}_"
                + datetime.strftime(
                    datetime.fromtimestamp(current_timestamp), "%Y-%m-%d_%H-%M-%S"
                )
                + ".json",
            )

            cleaned_data = [
                {key: value for key, value in task.items() if key not in ("labelsMap",)}
                for task in cli_data
            ]
            output = (
                coco_converter(cleaned_data, taxonomy, cached_dimensions)
                if format_type == self.FORMAT_COCO
                else cleaned_data
            )
            with open(export_path, "w", encoding="utf-8") as file_:
                json.dump(output, file_, indent=2)

            print_info(f"Exported successfully to: {export_path}")

        if self.args.with_files:
            try:
                loop.run_until_complete(self._download_files(data, export_dir))
            except Exception:  # pylint: disable=broad-except
                print_error("Failed to download files")

    async def _download_files(self, data: List[Dict], export_dir: str) -> None:
        project_type = str(self.project.project.project_type.value)
        if project_type.startswith("IMAGE_"):
            files_dir = os.path.join(export_dir, "images")
        elif project_type.startswith("VIDEO_"):
            files_dir = os.path.join(export_dir, "videos")
        elif project_type.startswith("DICOM_"):
            files_dir = os.path.join(export_dir, "dicom")
        else:
            print_warning(
                "Project data type needs to be IMAGE, VIDEO or DICOM to export files"
            )
            return

        shutil.rmtree(files_dir, ignore_errors=True)
        os.makedirs(files_dir, exist_ok=True)

        files = []
        for task in data:
            if project_type.startswith("IMAGE_"):
                task_dir = files_dir
                items = [
                    re.sub(r"[^\w.]+", "-", os.path.basename(task.get("name", "")))
                    or task["taskId"]
                ]
                fill_index = 0
            else:
                task_dir = uniquify_path(
                    os.path.join(
                        files_dir,
                        re.sub(r"\W+", "-", task.get("name", "")) or task["taskId"],
                    )
                )
                os.makedirs(task_dir, exist_ok=True)
                items = [
                    re.sub(r"[^\w.]+", "-", os.path.basename(item))
                    for item in task["items"]
                ]
                fill_index = (
                    0
                    if all(items) and len(items) == len(set(items))
                    else len(str(len(items)))
                )

            for index, (item, url) in enumerate(zip(items, task["itemsPresigned"])):
                file_name, file_ext = os.path.splitext(item)
                files.append(
                    (
                        url,
                        os.path.join(
                            task_dir,
                            file_name
                            + (
                                ("-" + str(index).zfill(fill_index))
                                if fill_index
                                else ""
                            )
                            + file_ext,
                        ),
                    )
                )

        await download_files(files)
