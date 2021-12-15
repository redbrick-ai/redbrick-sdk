"""Input uuid handler."""
import re
from typing import Optional

from InquirerPy import inquirer  # type: ignore

from redbrick.cli.cli_base import CLIInputParams


class CLIInputUUID(CLIInputParams):
    """Input uuid handler."""

    def __init__(self, entity: Optional[str], name: str) -> None:
        """Init handlers."""
        self.entity = entity
        self.error_message = "Invalid " + name
        self.name = name

    def filtrator(self, entity: str) -> str:
        """Filter input entity."""
        return entity.strip().lower()

    def validator(self, entity: str) -> bool:
        """Validate input entity."""
        uuid = self.filtrator(entity)
        return re.match(r"^[\da-f]{8}-([\da-f]{4}-){3}[\da-f]{12}$", uuid) is not None

    def get(self) -> str:
        """Get filtered uuid value post validation."""
        self.entity = self.from_args()
        if self.entity is None:
            self.entity = inquirer.text(
                qmark=">",
                amark=">",
                message=self.name + ":",
                transformer=self.filtrator,
                filter=self.filtrator,
                validate=self.validator,
                invalid_message=self.error_message,
            ).execute()
        return self.entity
