"""CLI prune command."""
import os
import re
from datetime import datetime
from argparse import ArgumentParser, Namespace

from redbrick.cli.project import CLIProject
from redbrick.cli.cli_base import CLIExportInterface, CLIPruneInterface
from redbrick.utils.logging import print_info, print_warning


class CLIPruneController(CLIPruneInterface):
    """CLI prune command controller."""

    def __init__(self, parser: ArgumentParser) -> None:
        """Intialize prune sub commands."""
        parser.add_argument(
            "--time",
            "-t",
            type=int,
            default=1,
            help="Time (Default: 1)",
        )
        parser.add_argument(
            "--unit",
            "-u",
            choices=["s", "m", "h", "d"],
            default="d",
            help="Unit [s(seconds), m(minutes), h(hours), d(days)] (Default: d)",
        )
        parser.add_argument(
            "path",
            nargs="?",
            default=".",
            help="Directory containing exported files (Default: current directory)",
        )

    def handler(self, args: Namespace) -> None:
        """Handle prune command."""
        self.args = args
        project = CLIProject.from_path()
        assert project, "Not a valid project"
        self.project = project

        self.handle_prune()

    def handle_prune(self) -> None:
        """Handle empty sub command."""
        directory = self.args.path
        if not os.path.isdir(directory):
            print_warning(f"Directory {directory} does not exist")
            return

        pattern = re.compile(
            r"export_("
            + (
                "|".join(
                    (CLIExportInterface.FORMAT_REDBRICK, CLIExportInterface.FORMAT_COCO)
                )
            )
            + r")_[^.]+\.json$"
        )
        threshold = datetime.now().timestamp() - (
            self.args.time * {"s": 1, "m": 60, "h": 3600, "d": 86400}[self.args.unit]
        )
        print_info(
            f"Deleting files that were last modified before {datetime.fromtimestamp(threshold)}"
        )
        for item in os.listdir(directory):
            path = os.path.join(directory, item)
            if (
                re.match(pattern, item)
                and os.path.isfile(path)
                and os.stat(path).st_mtime < threshold
            ):
                os.remove(path)
                print_info(f"Deleted: {path}")
