"""CLI clone command."""
import os
import re
from argparse import ArgumentParser, Namespace

from halo.halo import Halo  # type: ignore

from redbrick.cli.input.select import CLIInputSelect
from redbrick.cli.project import CLIProject
from redbrick.cli.cli_base import CLICloneInterface
from redbrick.organization import RBOrganization
from redbrick.project import RBProject


class CLICloneController(CLICloneInterface):
    """CLI clone command controller."""

    def __init__(self, parser: ArgumentParser) -> None:
        """Intialize clone sub commands."""
        parser.add_argument("project", nargs="?", help="Project ID or Name")
        parser.add_argument("path", nargs="?", help="Local path of project")

    def handler(self, args: Namespace) -> None:
        """Handle clone command."""
        self.args = args

        if self.args.path is not None:
            path = os.path.realpath(self.args.path)
            assert not os.path.exists(path), f"{path} already exists"

        project = CLIProject.from_path(
            path="." if self.args.path is None else self.args.path, required=False
        )
        assert project is None, f"Already in a project {project.path}"

        self.handle_clone()

    def handle_clone(self) -> None:
        """Handle empty sub command."""
        temp = CLIProject(required=False)
        assert temp.creds.exists, "Credentials missing"

        with Halo(text="Fetching organization", spinner="dots") as spinner:
            try:
                org = RBOrganization(temp.context, temp.creds.org_id)
                spinner.succeed(str(org))
            except Exception as error:
                spinner.fail()
                raise error

        with Halo(text="Fetching projects", spinner="dots") as spinner:
            try:
                projects = temp.context.project.get_projects(org.org_id)
                spinner.succeed()
            except Exception as error:
                spinner.fail()
                raise error

        projects = list(
            filter(lambda proj: proj["status"] == "CREATION_SUCCESS", projects)
        )

        project_ids, project_names, choices = [], [], []
        for proj in projects:
            project_ids.append(proj["projectId"])
            project_names.append(proj["name"])
            choices.append(proj["name"] + " (" + proj["projectId"] + ")")

        selected = self.args.project
        if selected:
            index = -1
            if selected in project_ids:
                index = project_ids.index(selected)
            elif selected in project_names:
                index = project_names.index(selected)

            if index >= 0:
                selected = project_names[index] + " (" + project_ids[index] + ")"

        selected_index = choices.index(
            CLIInputSelect(selected, "Project", choices).get()
        )

        if self.args.path is not None:
            path = os.path.realpath(self.args.path)
        else:
            path = os.path.join(
                os.path.realpath("."),
                re.sub(r"\W+", "-", project_names[selected_index]),
            )

        os.makedirs(path)

        project = CLIProject(path=path, required=False)
        project.initialize_project(
            org, RBProject(org.context, org.org_id, project_ids[selected_index])
        )
