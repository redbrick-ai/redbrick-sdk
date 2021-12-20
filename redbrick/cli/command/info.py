"""CLI info command."""
from argparse import ArgumentParser, Namespace

from InquirerPy.utils import color_print  # type: ignore
from InquirerPy.separator import Separator  # type: ignore

from redbrick.cli.project import CLIProject
from redbrick.cli.cli_base import CLIInfoInterface


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

        org_data, project_data = [], []
        org_data.append(f"ID: {org.org_id}")
        org_data.append(f"Name: {org.name}")

        project_data.append(f"ID: {project.project_id}")
        project_data.append(f"Name: {project.name}")
        project_data.append(f"Type: {project.project_type.value}")
        project_data.append(f"Taxonomy: {project.taxonomy_name}")

        max_length = max(map(len, org_data + project_data))

        color_print(
            [
                ("", "Organization"),
                ("", f"\n{Separator('-'*max_length)}\n"),
                ("", "\n".join(org_data)),
                ("", f"\n{Separator('*'*max_length)}\n"),
                ("", "Project"),
                ("", f"\n{Separator('-'*max_length)}\n"),
                ("", "\n".join(project_data)),
            ]
        )
