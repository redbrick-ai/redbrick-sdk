"""CLI export command."""
import os
import json
from datetime import datetime
from argparse import ArgumentError, ArgumentParser, Namespace

from redbrick.cli import CLIProject
from redbrick.cli.input.uuid import CLIInputUUID
from redbrick.common.cli import CLIExportInterface


class CLIExportController(CLIExportInterface):
    """CLI export command controller."""

    def __init__(self, parser: ArgumentParser) -> None:
        """Intialize export sub commands."""
        parser.add_argument("type", nargs="?", default="latest")
        parser.add_argument(
            "--format", "-f", choices=["coco", "redbrick"], default="redbrick"
        )
        parser.add_argument("--clear-cache", action="store_true")
        parser.add_argument("--destination", "-d", default=".")

    def handler(self, args: Namespace) -> None:
        """Handle export command."""
        self.args = args
        project = CLIProject.from_path()
        assert project, "Not a valid project"
        self.project = project

        self.handle_export()

    def handle_export(self) -> None:
        """Handle empty sub command."""
        if self.args.clear_cache:
            self.project.cache.clear_cache(True)

        export_func = (
            self.project.project.export.coco_format
            if self.args.format == "coco"
            else self.project.project.export.redbrick_format
        )

        task_id = CLIInputUUID("", "")

        if self.args.type == "latest":
            data = export_func(only_ground_truth=False)
        elif self.args.type == "groundtruth":
            data = export_func(only_ground_truth=True)
        elif task_id.validator(self.args.type):
            data = export_func(task_id=task_id.filtrator(self.args.type))
        else:
            raise ArgumentError(None, "")

        export_path = os.path.join(
            self.project.path
            if self.args.destination is None
            else self.args.destination,
            "export_" + datetime.strftime(datetime.now(), "%Y%m%d%H%M%S%f") + ".json",
        )
        os.makedirs(os.path.dirname(export_path), exist_ok=True)
        with open(export_path, "w", encoding="utf-8") as file_:
            json.dump(data, file_)

        print(f"Exported successfully to: {export_path}")
