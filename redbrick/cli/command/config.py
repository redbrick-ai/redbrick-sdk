"""CLI config command."""
import os
from argparse import ArgumentError, ArgumentParser, Namespace
from typing import Optional
import functools

from InquirerPy import inquirer  # type: ignore
from InquirerPy.utils import color_print  # type: ignore
from InquirerPy.separator import Separator  # type: ignore
from halo import Halo  # type: ignore

from redbrick import _populate_context
from redbrick.cli.input import (
    CLIInputAPIKey,
    CLIInputUUID,
    CLIInputURL,
    CLIInputProfile,
)
from redbrick.cli.project import CLIProject
from redbrick.cli.cli_base import CLIConfigInterface
from redbrick.common.context import RBContext
from redbrick.organization import RBOrganization


class CLIConfigController(CLIConfigInterface):
    """CLI config command controller."""

    def __init__(self, parser: ArgumentParser) -> None:
        """Intialize config sub commands."""
        sub_command = parser.add_subparsers(
            title="Config sub-commands", dest="sub_command"
        )

        parser.add_argument("--org", "-o", help="Org ID")
        parser.add_argument("--key", "-k", help="API Key")
        parser.add_argument("--url", "-u", help="Endpoint URL")
        parser.add_argument("--profile", "-p", help="Profile name")
        parser.add_argument(
            "--force", "-f", action="store_true", help="Force create new credentials"
        )

        # list_sub_command
        _ = sub_command.add_parser(self.LIST, help="List all profiles")

        set_sub_command = sub_command.add_parser(self.SET, help="Set default profile")
        set_sub_command.add_argument("profile", nargs="?", help="Profile name")

        add_sub_command = sub_command.add_parser(self.ADD, help="Add a new profile")
        add_sub_command.add_argument("--org", "-o", help="Org ID")
        add_sub_command.add_argument("--key", "-k", help="API Key")
        add_sub_command.add_argument("--url", "-u", help="Endpoint URL")
        add_sub_command.add_argument("--profile", "-p", help="Profile name")

        unset_sub_command = sub_command.add_parser(self.REMOVE, help="Remove a profile")
        unset_sub_command.add_argument("profile", nargs="?", help="Profile name")

        # clear_sub_command
        _ = sub_command.add_parser(self.CLEAR, help="Clear all credentials")

        verify_sub_command = sub_command.add_parser(
            self.VERIFY, help="Verify a profile"
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
            raise ArgumentError(None, "")

    def handle_config(self) -> None:
        """Handle empty sub command."""
        if self.project.creds.exists:
            if not self.args.force:
                confirmation = inquirer.confirm(
                    message="Credentials file already exists. Overwrite?", default=False
                ).execute()
                if not confirmation:
                    return
            self.project.creds.remove()

        self.handle_add()

    def handle_list(self) -> None:
        """Handle list sub command."""
        assert self.project.creds.exists, "Credentials file does not exist"
        default_profile = self.project.creds.selected_profile
        profiles = self.project.creds.profile_names
        data = []
        max_length = 0
        for profile in profiles:
            color = "green" if profile == default_profile else ""
            cur_data = [
                (color, f"{'*' if profile == default_profile else ''}{profile}\n"),
                (color, f"{Separator('-'*len(profile)*2)}\n"),
            ]
            for key, value in self.project.creds.get_profile(profile).items():
                value = (
                    ("***" + value[-3:])
                    if key == "key" and not os.environ.get("REDBRICK_SDK_DEBUG")
                    else value
                )
                info = f"{key}={value}"
                max_length = max(max_length, len(info))
                cur_data.append((color, f"{info}\n"))
            data.append(cur_data)
        if data:
            color_print(
                functools.reduce(
                    lambda x, y: x + [("", f"{Separator('*'*max_length)}\n")] + y, data
                )
            )

    def handle_set(self) -> None:
        """Handle set sub command."""
        assert self.project.creds.exists, "Credentials file does not exist"
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
        assert self.project.creds.exists, "Credentials file does not exist"
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
        context = _populate_context(
            RBContext(
                api_key=profile_details["key"].strip(),
                url=profile_details["url"].strip().rstrip("/"),
            )
        )

        with Halo(text="Fetching organization", spinner="dots") as spinner:
            try:
                org = RBOrganization(context, profile_details["org"])
                spinner.succeed(str(org))
            except Exception as error:
                spinner.fail()
                raise error
