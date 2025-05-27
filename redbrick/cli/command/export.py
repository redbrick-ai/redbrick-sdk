"""CLI export command."""

import os
import re
import json
import asyncio
from datetime import datetime, timezone
from argparse import ArgumentError, ArgumentParser, Namespace
from typing import Dict, Set, Optional, cast

import shtab
import tqdm  # type: ignore

from redbrick.config import config
from redbrick.cli.project import CLIProject
from redbrick.cli.cli_base import CLIExportInterface
from redbrick.common.constants import MAX_FILE_BATCH_SIZE
from redbrick.types.taxonomy import Taxonomy
from redbrick.utils.async_utils import gather_with_concurrency
from redbrick.utils.logging import assert_validation, logger


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
            "--without-masks",
            action="store_true",
            help="""Exports only tasks JSON without downloading any segmentation masks.
            Note: This is not recommended for tasks with overlapping labels.""",
        )

        parser.add_argument(
            "--semantic",
            action="store_true",
            help="""Whether to export all segmentations as semantic_mask.
            This will create one segmentation file per class.
            If this is set to True and a task has multiple instances per class,
            then attributes belonging to each instance will not be exported.""",
        )

        parser.add_argument(
            "--binary-mask",
            action="store_true",
            help="""Whether to export all segmentations as binary masks.
            This will create one segmentation file per instance.""",
        )

        parser.add_argument(
            "--single-mask",
            action="store_true",
            help="""Whether to export all segmentations in a single file.
            Binary mask will be considered if both binary_mask and single_mask are set.""",
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
            help="Export labels as PNG masks",
        )
        parser.add_argument(
            "--rt-struct",
            action="store_true",
            help="Export labels as DICOM RT-Struct. (Only for DICOM images)",
        )
        parser.add_argument(
            "--dicom-seg",
            action="store_true",
            help="Export labels as DICOM SEG. (Only for DICOM images)",
        )
        parser.add_argument(
            "--mhd",
            action="store_true",
            help="Export segmentation masks in MHD format.",
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
        assert_validation(project, "Not a valid project")
        self.project = cast(CLIProject, project)

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
            else not self.project.project.is_consensus_enabled
        )

        cached_tasks: Set[str] = set()
        cache_timestamp = None
        dp_conf = self.project.conf.get_section("datapoints")
        if dp_conf and "timestamp" in dp_conf:
            cached_tasks = set(
                self.project.cache.get_data("tasks", dp_conf["cache"]) or []
            )
            if cached_tasks:
                cache_timestamp = int(dp_conf["timestamp"]) or None
            else:  # Migration
                cached_dps = self.project.cache.get_data("datapoints", dp_conf["cache"])
                if cached_dps:
                    for task_id, cached_dp in (
                        cached_dps if isinstance(cached_dps, dict) else {}
                    ).items():
                        cached_tasks.add(task_id)
                        self.project.cache.set_entity(task_id, cached_dp)
                    self.project.cache.remove_data("datapoints")

        current_timestamp = int(datetime.now(timezone.utc).timestamp())
        datapoint_count = self.project.project.context.export.datapoints_in_project(
            self.project.project.org_id, self.project.project.project_id, None
        )
        datapoints = self.project.project.export.get_raw_data_latest(
            self.args.concurrency,
            None,
            cache_timestamp,
            False,
            not no_consensus,
        )
        fetched = 0
        with tqdm.tqdm(
            datapoints,
            unit=" datapoints",
            total=datapoint_count,
            leave=config.log_info,
        ) as progress:
            for task in progress:
                cached_tasks.add(task["taskId"])
                self.project.cache.set_entity(task["taskId"], task)
                fetched += 1
            try:
                disable = progress.disable
                progress.disable = False
                progress.update(datapoint_count - progress.n)
                progress.disable = disable
            except Exception:  # pylint: disable=broad-except
                pass

        logger.info(f"Refreshed {fetched} newly updated tasks")

        cache_hash = self.project.cache.set_data("tasks", list(cached_tasks))
        self.project.conf.set_section(
            "datapoints",
            {
                "timestamp": str(
                    current_timestamp if fetched else (cache_timestamp or 0)
                ),
                "cache": cache_hash,
            },
        )
        self.project.conf.save()

        export_dir = self.args.destination
        os.makedirs(export_dir, exist_ok=True)

        semantic_mask = bool(self.args.semantic)
        binary_mask = (
            True
            if bool(self.args.binary_mask)
            else False if bool(self.args.single_mask) else None
        )
        old_format = bool(self.args.old_format)
        with_files = bool(self.args.with_files)
        without_masks = bool(self.args.without_masks)
        png_mask = bool(self.args.png)
        rt_struct = bool(self.args.rt_struct)
        dicom_seg = bool(self.args.dicom_seg)
        mhd_mask = bool(self.args.mhd)
        dicom_to_nifti = bool(self.args.dicom_to_nifti)

        task_file = os.path.join(export_dir, "tasks.json")

        image_dir: Optional[str] = None
        if with_files or rt_struct or dicom_seg:
            image_dir = os.path.join(export_dir, "images")
            os.makedirs(image_dir, exist_ok=True)

        segmentation_dir: Optional[str] = None
        if not without_masks:
            segmentation_dir = os.path.join(export_dir, "segmentations")
            os.makedirs(segmentation_dir, exist_ok=True)

        class_file = os.path.join(export_dir, "class_map.json")
        coloured_png = png_mask and not binary_mask
        class_map, color_map = self.project.project.export.preprocess_export(
            self.project.project.taxonomy, coloured_png
        )

        if os.path.isfile(task_file):
            os.remove(task_file)

        asyncio.run(
            gather_with_concurrency(
                min(self.args.concurrency, MAX_FILE_BATCH_SIZE),
                *[
                    self._process_task(
                        cached_task,
                        self.project.project.taxonomy,
                        task_file,
                        image_dir,
                        segmentation_dir,
                        semantic_mask,
                        binary_mask,
                        old_format,
                        no_consensus,
                        color_map,
                        dicom_to_nifti,
                        png_mask,
                        rt_struct,
                        dicom_seg,
                        mhd_mask,
                    )
                    for cached_task in cached_tasks
                ],
                progress_bar_name="Processing labels",
                keep_progress_bar=True,
            )
        )

        if not os.path.isfile(task_file):
            with open(task_file, "w", encoding="utf-8") as task_file_:
                task_file_.write("[]")

        if segmentation_dir:
            logger.info(f"Exported segmentations to: {segmentation_dir}")
        if image_dir:
            logger.info(f"Exported images to: {image_dir}")
        logger.info(f"Exported: {task_file}")

        if coloured_png:
            with open(class_file, "w", encoding="utf-8") as classes_file:
                json.dump(class_map, classes_file, indent=2)

            logger.info(f"Exported: {class_file}")

    async def _process_task(
        self,
        cached_task: str,
        taxonomy: Taxonomy,
        task_file: Optional[str],
        image_dir: Optional[str],
        segmentation_dir: Optional[str],
        semantic_mask: bool,
        binary_mask: Optional[bool],
        old_format: bool,
        no_consensus: bool,
        color_map: Dict,
        dicom_to_nifti: bool,
        png_mask: bool,
        rt_struct: bool,
        dicom_seg: bool,
        mhd_mask: bool,
    ) -> None:
        # pylint: disable=too-many-locals, too-many-boolean-expressions
        task: Dict = self.project.cache.get_entity(cached_task)  # type: ignore

        if (
            (
                self.args.type == self.TYPE_LATEST
                and self.args.stage
                and task["currentStageName"].lower() != self.args.stage.lower()
            )
            or (
                self.args.type == self.TYPE_GROUNDTRUTH
                and task["currentStageName"].lower() != "end"
            )
            or (
                self.args.type != self.TYPE_LATEST
                and self.args.type != self.TYPE_GROUNDTRUTH
                and task["taskId"] != self.args.type.strip().lower()
            )
        ):
            return

        await self.project.project.export.export_nifti_label_data(
            task,
            taxonomy,
            task_file,
            image_dir,
            segmentation_dir,
            semantic_mask,
            binary_mask,
            old_format,
            no_consensus,
            color_map,
            dicom_to_nifti,
            png_mask,
            rt_struct,
            dicom_seg,
            mhd_mask,
            False,
        )
