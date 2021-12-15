"""Input number handler."""
from typing import Optional

from InquirerPy import inquirer  # type: ignore

from redbrick.cli.cli_base import CLIInputParams


class CLIInputNumber(CLIInputParams):
    """Input number handler."""

    def __init__(self, entity: Optional[str], name: str) -> None:
        """Init handlers."""
        self.entity = entity
        self.error_message = "Not a number"
        self.name = name

    def filtrator(self, entity: str) -> str:
        """Filter input entity."""
        return entity.strip()

    def validator(self, entity: str) -> bool:
        """Validate input entity."""
        number = self.filtrator(entity)
        return number.isnumeric()

    def get(self) -> str:
        """Get filtered number value post validation."""
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
