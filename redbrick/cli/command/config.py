"""CLI config command."""

from argparse import ArgumentError, ArgumentParser, Namespace
from typing import List, Optional

from InquirerPy.prompts.confirm import ConfirmPrompt
from rich.console import Console
from rich.table import Table
from rich.box import ROUNDED

from redbrick.config import config
from redbrick.cli.input import (
    CLIInputAPIKey,
    CLIInputUUID,
    CLIInputURL,
    CLIInputProfile,
)
from redbrick.cli.project import CLIProject
from redbrick.cli.cli_base import CLIConfigInterface
from redbrick.common.constants import DEFAULT_URL
from redbrick.common.context import RBContextImpl
from redbrick.organization import RBOrganizationImpl
from redbrick.utils.logging import assert_validation


class CLIConfigController(CLIConfigInterface):
    """CLI config command controller."""

    def __init__(self, parser: ArgumentParser) -> None:
        """Intialize config sub commands."""
        sub_command = parser.add_subparsers(dest="sub_command")

        parser.add_argument("--org", "-o", help="Org ID")
        parser.add_argument("--key", "-k", help="API Key")
        parser.add_argument(
            "--url",
            "-u",
            help=f"Endpoint URL, should default to {DEFAULT_URL}.",
        )
        parser.add_argument("--profile", "-p", help="Profile name")
        parser.add_argument(
            "--force",
            "-f",
            action="store_true",
            help="Force create new credentials",
        )

        # list_sub_command
        _ = sub_command.add_parser(
            self.LIST,
            help="List all credential profiles",
            description="List all credential profiles",
        )

        set_sub_command = sub_command.add_parser(
            self.SET,
            help="Set your default credentials profile",
            description="Set your default credentials profile",
        )
        set_sub_command.add_argument("profile", nargs="?", help="Profile name")

        add_sub_command = sub_command.add_parser(
            self.ADD, help="Add a new profile", description="Add a new profile"
        )
        add_sub_command.add_argument("--org", "-o", help="Org ID")
        add_sub_command.add_argument("--key", "-k", help="Add your API Key.")
        add_sub_command.add_argument(
            "--url",
            "-u",
            help=f"Endpoint URL, should default to {DEFAULT_URL}.",
        )
        add_sub_command.add_argument(
            "--profile",
            "-p",
            help="Define a name for your authentication profile.",
        )

        unset_sub_command = sub_command.add_parser(
            self.REMOVE, help="Remove a profile", description="Remove a profile"
        )
        unset_sub_command.add_argument("profile", nargs="?", help="Profile name")

        # clear_sub_command
        _ = sub_command.add_parser(
            self.CLEAR,
            help="Clear all credentials",
            description="Clear all credentials",
        )

        verify_sub_command = sub_command.add_parser(
            self.VERIFY, help="Verify a profile", description="Verify a profile"
        )
        verify_sub_command.add_argument("profile", nargs="?", help="Profile name")

    def handler(self, args: Namespace) -> None:
        """Handle config command."""
        self.args = args
        self.project = CLIProject(required=False)

        if not args.sub_command:
            self.handle_config()
        elif args.sub_command == self.LIST:
            self.handle_list()
        elif args.sub_command == self.SET:
            self.handle_set()
        elif args.sub_command == self.ADD:
            self.handle_add()
        elif args.sub_command == self.REMOVE:
            self.handle_remove()
        elif args.sub_command == self.CLEAR:
            self.handle_clear()
        elif args.sub_command == self.VERIFY:
            self.handle_verify()
        else:
            raise ArgumentError(None, f"Invalid config sub command: {args.sub_command}")

    def handle_config(self) -> None:
        """Handle empty sub command."""
        if self.project.creds.exists:
            if not self.args.force:
                confirmation = ConfirmPrompt(
                    message="Credentials file already exists. Overwrite?", default=False
                ).execute()
                if not confirmation:
                    return
            self.project.creds.remove()

        self.handle_add()

    def handle_list(self) -> None:
        """Handle list sub command."""
        assert_validation(self.project.creds.exists, "Credentials file does not exist")
        default_profile: str = self.project.creds.selected_profile
        profiles: List[str] = self.project.creds.profile_names
        rows: List[List[str]] = []
        table = Table(
            title="[bold green]RedBrick AI Profiles", expand=True, box=ROUNDED
        )
        columns_set = False
        for profile in profiles:
            if not columns_set:
                table.add_column("Name")
            row: List[str] = [profile]
            for key, value in self.project.creds.get_profile(profile).items():
                if not columns_set:
                    table.add_column(
                        key.capitalize(),
                        width=(
                            (43 if config.debug else 6)
                            if key == "key"
                            else 36 if key == "org" else None
                        ),
                    )
                row.append(
                    ("***" + value[-3:]) if key == "key" and not config.debug else value
                )
            columns_set = True
            rows.append(row)

        rows.sort(key=lambda profile: [profile[0] == default_profile, profile[0]])

        for name, *row in rows:
            table.add_row(
                ("* " if name == default_profile else "") + name,
                *row,
                style="green" if name == default_profile else None,
            )

        console = Console()
        if config.log_info:
            console.print(table)

    def handle_set(self) -> None:
        """Handle set sub command."""
        assert_validation(self.project.creds.exists, "Credentials file does not exist")
        profile = CLIInputProfile(
            self.args.profile, self.project.creds.profile_names
        ).get()
        self.project.creds.set_default(profile)
        self.project.creds.save()

    def handle_add(self) -> None:
        """Handle add sub command."""
        org_id = CLIInputUUID(self.args.org, "Org ID").get()
        api_key = CLIInputAPIKey(self.args.key).get()
        url = CLIInputURL(self.args.url).get()
        profile = CLIInputProfile(
            self.args.profile, self.project.creds.profile_names, True
        ).get()

        self.project.creds.add_profile(profile, api_key, org_id, url)
        self.handle_verify(profile)

        self.project.creds.set_default(profile)
        self.project.creds.save()

    def handle_remove(self) -> None:
        """Handle remove sub command."""
        assert_validation(self.project.creds.exists, "Credentials file does not exist")
        profile = CLIInputProfile(
            self.args.profile, self.project.creds.profile_names
        ).get()

        self.project.creds.remove_profile(profile)
        self.project.creds.save()

    def handle_clear(self) -> None:
        """Handle clear sub command."""
        self.project.creds.remove()

    def handle_verify(self, profile: Optional[str] = None) -> None:
        """Handle verify sub command."""
        if profile is None:
            selected_profile = None
            try:
                selected_profile = self.project.creds.selected_profile
            except AssertionError:
                pass
            profile = CLIInputProfile(
                self.args.profile,
                self.project.creds.profile_names,
                default=selected_profile,
            ).get()

        profile_details = self.project.creds.get_profile(profile)
        context = RBContextImpl(
            api_key=profile_details["key"].strip(),
            url=profile_details["url"].strip().rstrip("/"),
        )

        console = Console()
        with console.status("Fetching organization") as status:
            try:
                org = RBOrganizationImpl(context, profile_details["org"])
            except Exception as error:
                status.stop()
                raise error
        if config.log_info:
            console.print("[bold green]" + str(org))
