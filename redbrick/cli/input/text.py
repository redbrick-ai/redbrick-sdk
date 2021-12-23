"""Input text handler."""
from typing import Optional

from InquirerPy import inquirer  # type: ignore

from redbrick.cli.cli_base import CLIInputParams


class CLIInputText(CLIInputParams):
    """Input text handler."""

    def __init__(self, entity: Optional[str], name: str, default: str = "") -> None:
        """Init handlers."""
        self.entity = entity
        self.error_message = "Empty value"
        self.name = name
        self.default = default

    def filtrator(self, entity: str) -> str:
        """Filter input entity."""
        return entity.strip()

    def validator(self, entity: str) -> bool:
        """Validate input entity."""
        text = self.filtrator(entity)
        return bool(text)

    def get(self) -> str:
        """Get filtered text value post validation."""
        self.entity = self.from_args()
        if self.entity is None:
            self.entity = inquirer.text(
                qmark=">",
                amark=">",
                message=self.name + ":",
                default=self.default,
                transformer=self.filtrator,
                filter=self.filtrator,
                validate=self.validator,
                invalid_message=self.error_message,
            ).execute()
        return self.entity
