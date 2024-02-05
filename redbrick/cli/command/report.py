"""CLI report command."""

import os
import json
from datetime import datetime
from argparse import ArgumentError, ArgumentParser, Namespace
from typing import cast

from redbrick.cli.project import CLIProject
from redbrick.cli.cli_base import CLIReportInterface
from redbrick.utils.logging import assert_validation, logger


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
        assert_validation(project, "Not a valid project")
        self.project = cast(CLIProject, project)

        self.handle_report()

    def handle_report(self) -> None:
        """Handle empty sub command."""
        if self.args.type not in (self.TYPE_ALL, self.TYPE_GROUNDTRUTH):
            raise ArgumentError(None, f"Invalid report type: {self.args.type}")

        reports = self.project.project.export.get_task_events(
            only_ground_truth=self.args.type == self.TYPE_GROUNDTRUTH,
            concurrency=self.args.concurrency,
        )

        report_file = os.path.abspath(f"report-{int(datetime.now().timestamp())}.json")
        if os.path.isfile(report_file):
            os.remove(report_file)

        for idx, report in enumerate(reports):
            if idx == 0:
                with open(report_file, "wb") as report_file_:
                    report_file_.write(
                        b"[" + json.dumps(report, indent=2).encode("utf-8") + b"]"
                    )
            else:
                with open(report_file, "rb+") as report_file_:
                    report_file_.seek(-1, 2)
                    report_file_.write(
                        b"," + json.dumps(report, indent=2).encode("utf-8") + b"]"
                    )

        if not os.path.isfile(report_file):
            with open(report_file, "w", encoding="utf-8") as report_file_:
                report_file_.write("[]")

        logger.info(f"Exported successfully to: {report_file}")
