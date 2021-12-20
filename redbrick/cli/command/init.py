"""CLI init command."""
import os
from argparse import ArgumentParser, Namespace

from halo.halo import Halo  # type: ignore

from redbrick.cli.input import CLIInputNumber, CLIInputSelect, CLIInputText
from redbrick.cli.project import CLIProject
from redbrick.cli.cli_base import CLIInitInterface
from redbrick.common.enums import LabelType
from redbrick.organization import RBOrganization


class CLIInitController(CLIInitInterface):
    """CLI init command controller."""

    def __init__(self, parser: ArgumentParser) -> None:
        """Intialize init sub commands."""
        parser.add_argument("--name", "-n", help="Project name")
        parser.add_argument("--label", "-l", help="Label type")
        parser.add_argument("--taxonomy", "-t", help="Taxonomy name")
        parser.add_argument("--reviews", "-r", help="Number of review stages")
        parser.add_argument(
            "path", nargs="?", default=".", help="Local path of project"
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

        with Halo(text="Fetching organization", spinner="dots") as spinner:
            try:
                org = RBOrganization(self.project.context, self.project.creds.org_id)
                spinner.succeed(str(org))
            except Exception as error:
                spinner.fail()
                raise error

        with Halo(text="Fetching taxonomies", spinner="dots") as spinner:
            try:
                taxonomies = org.taxonomies()
                spinner.succeed()
            except Exception as error:
                spinner.fail()
                raise error

        name = CLIInputText(
            self.args.name, "Name", os.path.basename(self.project.path)
        ).get()
        label_type = LabelType(
            CLIInputSelect(
                self.args.label, "Label", [label.value for label in LabelType]
            ).get()
        )
        taxonomy = CLIInputSelect(self.args.taxonomy, "Taxonomy", taxonomies).get()
        reviews = int(CLIInputNumber(self.args.reviews, "Reviews").get())

        with Halo(text="Creating project", spinner="dots") as spinner:
            try:
                project = org.create_project(name, label_type, taxonomy, reviews)
                spinner.succeed(str(project))
            except Exception as error:
                spinner.fail()
                raise error

        self.project.initialize_project(org, project)
