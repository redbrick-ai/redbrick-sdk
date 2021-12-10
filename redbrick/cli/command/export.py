"""CLI export command."""
import asyncio
import os
import re
import json
from datetime import datetime, timezone
from argparse import ArgumentError, ArgumentParser, Namespace
from typing import Dict

from redbrick.cli import CLIProject
from redbrick.common.cli import CLIExportInterface
from redbrick.coco.coco_main import _get_image_dimension_map, coco_converter
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
            choices=[self.FORMAT_REDBRICK, self.FORMAT_COCO],
            default=self.FORMAT_REDBRICK,
            help="Export format",
        )
        parser.add_argument(
            "--clear-cache", action="store_true", help="Clear local cache"
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

    def handle_export(self) -> None:
        """Handle empty sub command."""
        # pylint: disable=too-many-locals, too-many-branches
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
            25, cache_time
        )

        print_info(f"Refreshed {len(datapoints)} tasks")

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

        if self.args.format == self.FORMAT_COCO:
            compute_dims = [dp for dp in data if cached_dimensions[dp["dpId"]] is None]
            if compute_dims:
                image_dimensions = asyncio.run(_get_image_dimension_map(compute_dims))
                for dp_id, dimension in image_dimensions.items():
                    cached_dimensions[dp_id] = dimension

        dim_hash = self.project.cache.set_data("dimensions", cached_dimensions)
        self.project.conf.set_section("dimensions", {"cache": dim_hash})
        self.project.conf.save()

        data = [
            {
                key: value
                for key, value in dp.items()
                if key not in ("itemsPresigned", "currentStageName")
            }
            for dp in data
        ]

        export_path = os.path.join(
            self.project.path
            if self.args.destination is None
            else self.args.destination,
            f"export_{self.args.format}_{self.args.type}_"
            + datetime.strftime(datetime.now(), "%Y-%m-%d_%H-%M-%S")
            + ".json",
        )
        os.makedirs(os.path.dirname(export_path), exist_ok=True)
        with open(export_path, "w", encoding="utf-8") as file_:
            json.dump(
                coco_converter(data, taxonomy, cached_dimensions)
                if self.args.format == "coco"
                else data,
                file_,
                indent=2,
            )

        print_info(f"Exported successfully to: {export_path}")
