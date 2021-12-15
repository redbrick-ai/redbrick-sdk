"""CLI info command."""
from argparse import ArgumentParser, Namespace

from redbrick.cli.project import CLIProject
from redbrick.common.cli import CLIInfoInterface
from redbrick.utils.logging import print_info


class CLIInfoController(CLIInfoInterface):
    """CLI info command controller."""

    def __init__(self, parser: ArgumentParser) -> None:
        """Intialize info sub commands."""
        parser.add_argument("path", nargs="?", default=".", help="Path of project")

    def handler(self, args: Namespace) -> None:
        """Handle info command."""
        self.args = args
        project = CLIProject.from_path(path=self.args.path)
        assert project, "Not a valid project"
        self.project = project

        self.handle_info()

    def handle_info(self) -> None:
        """Handle empty sub command."""
        org = self.project.org
        project = self.project.project

        print_info(f"Organization: {org}")
        print_info(f"Project: {project}")
