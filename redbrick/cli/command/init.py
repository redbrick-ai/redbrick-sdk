"""CLI init command."""
import os
from argparse import ArgumentParser, Namespace
from typing import List

from rich.console import Console

from redbrick.cli.input import CLIInputNumber, CLIInputSelect, CLIInputText
from redbrick.cli.project import CLIProject
from redbrick.cli.cli_base import CLIInitInterface
from redbrick.organization import RBOrganization


class CLIInitController(CLIInitInterface):
    """CLI init command controller."""

    def __init__(self, parser: ArgumentParser) -> None:
        """Intialize init sub commands."""
        parser.add_argument("--name", "-n", help="Project name")
        parser.add_argument("--taxonomy", "-t", help="Taxonomy name")
        parser.add_argument(
            "--reviews",
            "-r",
            help="Number of review stages",
        )
        parser.add_argument(
            "path",
            nargs="?",
            default=".",
            help="Local path of the empty project directory",
        )

    def handler(self, args: Namespace) -> None:
        """Handle init command."""
        self.args = args
        project = CLIProject.from_path(path=self.args.path, required=False)
        assert project is None, f"Already a RedBrick project {project.path}"

        path = os.path.realpath(self.args.path)
        if os.path.exists(path):
            if not os.path.isdir(path):
                raise Exception(f"Not a directory {path}")
            if os.listdir(path):
                raise Exception(f"{path} is not empty")
        else:
            os.makedirs(path)

        self.project = CLIProject(path=self.args.path, required=False)

        self.handle_init()

    def handle_init(self) -> None:
        """Handle empty sub command."""
        assert self.project.creds.exists, "Credentials missing"

        console = Console()
        with console.status("Fetching organization") as status:
            try:
                org = RBOrganization(self.project.context, self.project.creds.org_id)
            except Exception as error:
                status.stop()
                raise error
        console.print("[bold green]" + str(org))

        with console.status("Fetching taxonomies") as status:
            try:
                taxonomies: List[str] = [
                    taxonomy["name"]  # type: ignore
                    for taxonomy in org.taxonomies(False)
                    if taxonomy.get("isNew") and not taxonomy.get("archived")  # type: ignore
                ]
            except Exception as error:
                status.stop()
                raise error

        name = CLIInputText(
            self.args.name, "Name", os.path.basename(self.project.path)
        ).get()
        taxonomy = CLIInputSelect(self.args.taxonomy, "Taxonomy", taxonomies).get()
        reviews = int(CLIInputNumber(self.args.reviews, "Reviews").get())

        with console.status("Creating project") as status:
            try:
                project = org.create_project(name, taxonomy, reviews)
            except Exception as error:
                status.stop()
                raise error
        console.print("[bold green]" + str(project))

        self.project.initialize_project(org, project)
