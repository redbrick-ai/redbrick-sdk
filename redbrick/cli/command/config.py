"""CLI config command."""
from argparse import ArgumentError, ArgumentParser, Namespace
from typing import Optional

from InquirerPy import inquirer  # type: ignore
from InquirerPy.utils import color_print  # type: ignore
from InquirerPy.separator import Separator  # type: ignore
from halo import Halo  # type: ignore

from redbrick.cli.input import (
    CLIInputAPIKey,
    CLIInputUUID,
    CLIInputURL,
    CLIInputProfile,
)
from redbrick import get_org
from redbrick.cli import CLIProject
from redbrick.common.cli import CLIConfigInterface


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

        _list_sub_command = sub_command.add_parser(self.LIST, help="List all profiles")

        set_sub_command = sub_command.add_parser(self.SET, help="Set default profile")
        set_sub_command.add_argument("profile", nargs="?", help="Profile name")

        add_sub_command = sub_command.add_parser(self.ADD, help="Add a new profile")
        add_sub_command.add_argument("--org", "-o", help="Org ID")
        add_sub_command.add_argument("--key", "-k", help="API Key")
        add_sub_command.add_argument("--url", "-u", help="Endpoint URL")
        add_sub_command.add_argument("--profile", "-p", help="Profile name")

        unset_sub_command = sub_command.add_parser(self.REMOVE, help="Remove a profile")
        unset_sub_command.add_argument("profile", nargs="?", help="Profile name")

        _clear_sub_command = sub_command.add_parser(
            self.CLEAR, help="Clear all credentials"
        )

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
        if not self.args.force and self.project.creds.exists:
            confirmation = inquirer.confirm(
                message="Credentials file already exists. Overwrite?", default=False
            ).execute()
            if not confirmation:
                return

        self.handle_add(True)

    def handle_list(self) -> None:
        """Handle list sub command."""
        assert self.project.creds.exists, "Credentials file does not exist"
        default_profile = self.project.creds.selected_profile
        profiles = self.project.creds.profile_names
        if profiles:
            print(Separator())
        for profile in profiles:
            for key, value in self.project.creds.get_profile(profile).items():
                if profile == default_profile:
                    color_print([("green", f"{profile}.{key}={value}")])
                else:
                    print(f"{profile}.{key}={value}")
            print(Separator())

    def handle_set(self) -> None:
        """Handle set sub command."""
        assert self.project.creds.exists, "Credentials file does not exist"
        profile = CLIInputProfile(
            self.args.profile, self.project.creds.profile_names
        ).get()
        self.project.creds.set_default(profile)
        self.project.creds.save()

    def handle_add(self, set_default: bool = False) -> None:
        """Handle add sub command."""
        assert self.project.creds.exists, "Credentials file does not exist"
        org_id = CLIInputUUID(self.args.org, "Org ID").get()
        api_key = CLIInputAPIKey(self.args.key).get()
        url = CLIInputURL(self.args.url).get()
        profile = CLIInputProfile(
            self.args.profile, self.project.creds.profile_names, True
        ).get()

        self.project.creds.add_profile(profile, api_key, org_id, url)
        self.handle_verify(profile)

        if set_default:
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
        assert self.project.creds.exists, "Credentials file does not exist"
        if profile is None:
            profile = CLIInputProfile(
                self.args.profile, self.project.creds.profile_names
            ).get()

        with Halo(text="Fetching organization", spinner="dots") as spinner:
            try:
                org = get_org(
                    self.project.creds.api_key,
                    self.project.creds.url,
                    self.project.creds.org_id,
                )
                spinner.succeed(str(org))
            except Exception as error:
                spinner.fail()
                raise error