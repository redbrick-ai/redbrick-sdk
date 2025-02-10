"""CLI init command."""

import os
from argparse import ArgumentParser, Namespace
from typing import List

from rich.console import Console

from redbrick.config import config
from redbrick.cli.input import CLIInputNumber, CLIInputSelect, CLIInputText
from redbrick.cli.project import CLIProject
from redbrick.cli.cli_base import CLIInitInterface
from redbrick.organization import RBOrganizationImpl
from redbrick.utils.logging import assert_validation


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
            "--workspace",
            "-w",
            help="The workspace that you want to add this project to",
        )
        parser.add_argument(
            "--sibling-tasks",
            help="Number of tasks created for each uploaded datapoint",
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
        assert_validation(project is None, "Already inside a project")

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
        # pylint: disable=too-many-locals
        assert_validation(self.project.creds.exists, "Credentials missing")

        console = Console()
        with console.status("Fetching organization") as status:
            try:
                org = RBOrganizationImpl(
                    self.project.context, self.project.creds.org_id
                )
            except Exception as error:
                status.stop()
                raise error
        if config.log_info:
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

        with console.status("Fetching workspaces") as status:
            try:
                workspaces = org.workspaces_raw()
            except Exception as error:
                status.stop()
                raise error

        name = CLIInputText(
            self.args.name, "Name", os.path.basename(self.project.path)
        ).get()
        taxonomy = CLIInputSelect(self.args.taxonomy, "Taxonomy", taxonomies).get()
        reviews = int(CLIInputNumber(self.args.reviews, "Reviews", "1").get())

        workspace_ids, workspace_names, workspace_choices = [""], [""], ["--- NONE ---"]
        for workspace in workspaces:
            workspace_ids.append(workspace["workspaceId"])
            workspace_names.append(workspace["name"])
            workspace_choices.append(
                workspace["name"] + " (" + workspace["workspaceId"] + ")"
            )

        selected_workspace = self.args.workspace
        if selected_workspace:
            index = -1
            if selected_workspace in workspace_ids:
                index = workspace_ids.index(selected_workspace)
            elif selected_workspace in workspace_names:
                index = workspace_names.index(selected_workspace)

            if index >= 0:
                selected_workspace = (
                    workspace_names[index] + " (" + workspace_ids[index] + ")"
                )

        workspace_id = workspace_ids[
            workspace_choices.index(
                CLIInputSelect(
                    selected_workspace, "Workspaces", workspace_choices
                ).get()
            )
        ]

        sibling_tasks = CLIInputNumber(
            self.args.sibling_tasks, "Sibling Tasks", "", False
        ).get()

        with console.status("Creating project") as status:
            try:
                project = org.create_project(
                    name=name,
                    taxonomy_name=taxonomy,
                    reviews=reviews,
                    workspace_id=workspace_id or None,
                    sibling_tasks=(
                        None
                        if not sibling_tasks or int(sibling_tasks) <= 1
                        else int(sibling_tasks)
                    ),
                )
            except Exception as error:
                status.stop()
                raise error
        if config.log_info:
            console.print("[bold green]" + str(project))

        self.project.initialize_project(org, project)
