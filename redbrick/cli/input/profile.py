"""Input params handlers."""
from datetime import datetime
import re
from typing import List, Optional

from InquirerPy import inquirer  # type: ignore

from redbrick.cli.cli_base import CLIInputParams


class CLIInputProfile(CLIInputParams):
    """Input profile handler."""

    def __init__(
        self,
        entity: Optional[str],
        profiles: List[str],
        add: bool = False,
        default: Optional[str] = None,
    ) -> None:
        """Init handlers."""
        self.entity = entity
        self.error_message = (
            f"Non-alphanumeric / {'duplicate' if add else 'missing'} profile name"
        )
        self.add = add
        self.profiles = profiles
        self.default = default

    def filtrator(self, entity: str) -> str:
        """Filter input entity."""
        return entity.strip()

    def validator(self, entity: str) -> bool:
        """Validate input entity."""
        profile = self.filtrator(entity)
        return (
            profile.lower() != "default"
            and re.match(r"^\w+$", profile) is not None
            and (profile not in self.profiles if self.add else profile in self.profiles)
        )

    def get(self) -> str:
        """Get filtered profile value post validation."""
        self.entity = self.from_args()
        if self.entity is None:
            if self.add:
                self.entity = inquirer.text(
                    qmark=">",
                    amark=">",
                    message="Profile name:",
                    default="rb_" + datetime.strftime(datetime.now(), "%Y%m%d%H%M%S%f"),
                    transformer=self.filtrator,
                    filter=self.filtrator,
                    validate=self.validator,
                    invalid_message=self.error_message,
                ).execute()
            elif self.profiles:
                self.entity = inquirer.fuzzy(
                    qmark=">",
                    amark=">",
                    message="Profile name:",
                    choices=self.profiles,
                    default=self.default,
                ).execute()
            else:
                raise ValueError("No profiles available")
        return self.entity
