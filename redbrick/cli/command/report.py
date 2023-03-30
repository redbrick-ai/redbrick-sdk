"""CLI report command."""
import os
import json
from datetime import datetime
from argparse import ArgumentError, ArgumentParser, Namespace

from redbrick.cli.project import CLIProject
from redbrick.cli.cli_base import CLIReportInterface
from redbrick.utils.logging import logger


class CLIIReportController(CLIReportInterface):
    """CLI report command controller."""

    def __init__(self, parser: ArgumentParser) -> None:
        """Intialize report sub commands."""
        parser.add_argument(
            "type",
            nargs="?",
            default=self.TYPE_ALL,
            help=f"Export type: ({self.TYPE_ALL} [default], {self.TYPE_GROUNDTRUTH})",
        )
        parser.add_argument(
            "--concurrency",
            "-c",
            type=int,
            default=10,
            help="Concurrency value (Default: 10)",
        )

    def handler(self, args: Namespace) -> None:
        """Handle report command."""
        self.args = args
        project = CLIProject.from_path()
        assert project, "Not a valid project"
        self.project = project

        self.handle_report()

    def handle_report(self) -> None:
        """Handle empty sub command."""
        if self.args.type not in (self.TYPE_ALL, self.TYPE_GROUNDTRUTH):
            raise ArgumentError(None, f"Invalid report type: {self.args.type}")

        report = self.project.project.export.get_task_events(
            self.args.type == self.TYPE_GROUNDTRUTH, self.args.concurrency
        )
        report_path = os.path.abspath(f"report-{int(datetime.now().timestamp())}.json")
        with open(report_path, "w", encoding="utf-8") as file_:
            json.dump(report, file_, indent=2)

        logger.info(f"Exported successfully to: {report_path}")
