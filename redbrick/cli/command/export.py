"""CLI export command."""
import os
import re
import json
from datetime import datetime, timezone
from argparse import ArgumentError, ArgumentParser, Namespace
from typing import Dict

import shtab

from redbrick.cli.project import CLIProject
from redbrick.cli.cli_base import CLIExportInterface
from redbrick.utils.logging import logger


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
            help="Export labels as PNG masks",
        )
        parser.add_argument(
            "--rt-struct",
            action="store_true",
            help="Export labels as DICOM RT-Struct. (Only for DICOM images)",
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
            not no_consensus,
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

        self.project.conf.save()

        export_dir = self.args.destination
        os.makedirs(export_dir, exist_ok=True)

        with_files = bool(self.args.with_files)
        png_mask = bool(self.args.png)
        rt_struct = bool(self.args.rt_struct)
        dicom_to_nifti = bool(self.args.dicom_to_nifti)

        segmentations_dir = os.path.join(export_dir, "segmentations")
        os.makedirs(segmentations_dir, exist_ok=True)
        task_file = os.path.join(export_dir, "tasks.json")
        class_file = os.path.join(export_dir, "class_map.json")
        tasks, class_map = self.project.project.export.export_nifti_label_data(
            data,
            self.args.concurrency,
            taxonomy,
            export_dir,
            segmentations_dir,
            bool(self.args.old_format),
            no_consensus,
            with_files,
            dicom_to_nifti,
            png_mask,
            rt_struct,
        )
        logger.info(f"Exported segmentations to: {segmentations_dir}")

        with open(task_file, "w", encoding="utf-8") as tasks_file:
            json.dump(tasks, tasks_file, indent=2)

        logger.info(f"Exported: {task_file}")

        if png_mask:
            with open(class_file, "w", encoding="utf-8") as classes_file:
                json.dump(class_map, classes_file, indent=2)

            logger.info(f"Exported: {class_file}")
