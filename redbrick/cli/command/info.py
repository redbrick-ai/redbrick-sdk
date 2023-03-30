"""CLI info command."""
from argparse import ArgumentParser, Namespace
from typing import List, Tuple

from rich.console import Console
from rich.table import Table
from rich.box import ROUNDED
import shtab

from redbrick.cli.input.text import CLIInputText
from redbrick.cli.input.uuid import CLIInputUUID
from redbrick.cli.project import CLIProject
from redbrick.cli.cli_base import CLIInfoInterface
from redbrick.utils.logging import logger


class CLIInfoController(CLIInfoInterface):
    """CLI info command controller."""

    def __init__(self, parser: ArgumentParser) -> None:
        """Intialize info sub commands."""
        parser.add_argument(
            "--get",
            "-g",
            choices=[self.SETTING_LABELSTORAGE],
            help="Get a project's setting information",
        )
        parser.add_argument(
            "--set",
            "-s",
            choices=[self.SETTING_LABELSTORAGE],
            help="Set a project setting",
        )
        parser.add_argument(
            "path",
            nargs="?",
            default=".",
            help="Path of project (Default: current directory)",
        ).complete = shtab.DIRECTORY  # type: ignore

    def handler(self, args: Namespace) -> None:
        """Handle info command."""
        self.args = args
        project = CLIProject.from_path(path=self.args.path)
        assert project, "Not a valid project"
        self.project = project

        if self.args.get:
            self.handle_get()
        elif self.args.set:
            self.handle_set()
        else:
            self.handle_info()

    @staticmethod
    def _show_info(title: str, attrs: List[Tuple[str, str]]) -> None:
        console = Console()
        table = Table(
            title="[bold green]" + title,
            show_header=False,
            header_style=None,
            box=ROUNDED,
        )
        for key, value in attrs:
            table.add_row(key, value)
        console.print(table)

    def handle_get(self) -> None:
        """Handle get sub command."""
        if self.args.get == self.SETTING_LABELSTORAGE:
            console = Console()
            with console.status("Get: Label Storage") as status:
                try:
                    storage_id, path = self.project.project.label_storage
                except Exception as error:
                    status.stop()
                    raise error

            CLIInfoController._show_info(
                "Label Storage", [("Storage ID", storage_id), ("Path prefix", path)]
            )

    def handle_set(self) -> None:
        """Handle set sub command."""
        if self.args.set == self.SETTING_LABELSTORAGE:
            storage_id = CLIInputUUID(None, "Storage ID").get()
            path = CLIInputText(None, "Path prefix", "", True).get()
            console = Console()
            with console.status("Set: Label Storage") as status:
                try:
                    new_storage_id, new_path = self.project.project.set_label_storage(
                        storage_id, path
                    )
                except Exception as error:
                    status.stop()
                    raise error

            CLIInfoController._show_info(
                "Label Storage",
                [("Storage ID", new_storage_id), ("Path prefix", new_path)],
            )

    def handle_info(self) -> None:
        """Handle empty sub command."""
        logger.debug("Fetching project info")
        org = self.project.org
        project = self.project.project

        org_data, project_data = [], []
        org_data.append(("ID", org.org_id))
        org_data.append(("Name", org.name))

        project_data.append(("ID", project.project_id))
        project_data.append(("Name", project.name))
        project_data.append(("Taxonomy", project.taxonomy_name))
        project_data.append(("URL", project.url))

        CLIInfoController._show_info("Organization", org_data)
        CLIInfoController._show_info("Project", project_data)
