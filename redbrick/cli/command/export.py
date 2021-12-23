"""CLI export command."""
import asyncio
import os
import re
import json
from datetime import datetime, timezone
from argparse import ArgumentError, ArgumentParser, Namespace
from typing import Dict

from redbrick.cli.project import CLIProject
from redbrick.cli.cli_base import CLIExportInterface
from redbrick.coco.coco_main import _get_image_dimension_map, coco_converter
from redbrick.common.enums import LabelType
from redbrick.export.public import Export
from redbrick.utils.logging import print_info


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
            choices=[self.FORMAT_REDBRICK, self.FORMAT_COCO, self.FORMAT_MASK],
            help="Export format (Default: "
            + f"{self.FORMAT_MASK} if project type is {LabelType.IMAGE_SEGMENTATION} "
            + f"else {self.FORMAT_REDBRICK}",
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
            "--destination", "-d", default=".", help="Destination directory"
        )

    def handler(self, args: Namespace) -> None:
        """Handle export command."""
        self.args = args
        project = CLIProject.from_path()
        assert project, "Not a valid project"
        self.project = project

        self.handle_export()

    # pylint: disable=too-many-statements
    def handle_export(self) -> None:
        """Handle empty sub command."""
        # pylint: disable=too-many-locals, too-many-branches
        format_type = (
            self.args.format
            if self.args.format
            else (
                self.FORMAT_MASK
                if self.project.project.project_type == LabelType.IMAGE_SEGMENTATION
                else self.FORMAT_REDBRICK
            )
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

        if self.args.clear_cache:
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

        cache_time = None
        if cache_timestamp is not None:
            cache_time = datetime.fromtimestamp(cache_timestamp, tz=timezone.utc)
            print_info(
                "Refreshing cache with tasks updated after: "
                + str(datetime.fromtimestamp(cache_timestamp))
            )
        else:
            print_info("Refreshing cache with all tasks")

        current_timestamp = int(datetime.now(timezone.utc).timestamp())
        # pylint: disable=protected-access
        datapoints, taxonomy = self.project.project.export._get_raw_data_latest(
            self.args.concurrency, cache_time
        )

        print_info(f"Refreshed {len(datapoints)} newly updated tasks")

        for datapoint in datapoints:
            dp_id = datapoint["dpId"]
            if dp_id not in cached_dimensions:
                cached_dimensions[dp_id] = None

            cached_datapoints[dp_id] = datapoint

        dp_hash = self.project.cache.set_data("datapoints", cached_datapoints)
        self.project.conf.set_section(
            "datapoints", {"timestamp": str(current_timestamp), "cache": dp_hash}
        )
        self.project.conf.save()

        data = list(cached_datapoints.values())

        if self.args.type == self.TYPE_LATEST:
            pass
        elif self.args.type == self.TYPE_GROUNDTRUTH:
            data = [dp for dp in data if dp["currentStageName"] == "END"]
        else:
            task_id = self.args.type.strip().lower()
            task = None
            for dpoint in data:
                if dpoint["taskId"] == task_id:
                    task = dpoint
                    break
            data = [task] if task else []

        if format_type == self.FORMAT_COCO:
            compute_dims = [
                dp
                for dp in data
                if dp["dpId"] not in cached_dimensions
                or cached_dimensions[dp["dpId"]] is None
            ]
            if compute_dims:
                image_dimensions = asyncio.run(_get_image_dimension_map(compute_dims))
                for dp_id, dimension in image_dimensions.items():
                    cached_dimensions[dp_id] = dimension

        dim_hash = self.project.cache.set_data("dimensions", cached_dimensions)
        self.project.conf.set_section("dimensions", {"cache": dim_hash})
        self.project.conf.save()

        export_dir = (
            self.project.path
            if self.args.destination is None
            else self.args.destination
        )

        os.makedirs(export_dir, exist_ok=True)

        if format_type == self.FORMAT_MASK:
            mask_dir = os.path.join(export_dir, "masks")
            class_map = os.path.join(export_dir, "class_map.json")
            datapoint_map = os.path.join(export_dir, "datapoint_map.json")
            os.makedirs(mask_dir, exist_ok=True)
            Export._export_png_mask_data(
                data,
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
        else:
            export_path = os.path.join(
                export_dir,
                f"export_{format_type}_{self.args.type}_"
                + datetime.strftime(
                    datetime.fromtimestamp(current_timestamp), "%Y-%m-%d_%H-%M-%S"
                )
                + ".json",
            )

            data = [
                {key: value for key, value in dp.items() if key != "itemsPresigned"}
                for dp in data
            ]

            if format_type == self.FORMAT_COCO:
                with open(export_path, "w", encoding="utf-8") as file_:
                    json.dump(
                        coco_converter(data, taxonomy, cached_dimensions),
                        file_,
                        indent=2,
                    )
            else:
                data = [
                    {
                        key: value
                        for key, value in dp.items()
                        if key not in ("dpId", "currentStageName")
                    }
                    for dp in data
                ]
                with open(export_path, "w", encoding="utf-8") as file_:
                    json.dump(data, file_, indent=2)

            print_info(f"Exported successfully to: {export_path}")
