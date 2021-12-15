"""Input api_key handler."""
from typing import Optional

from InquirerPy import inquirer  # type: ignore

from redbrick.cli.cli_base import CLIInputParams


class CLIInputAPIKey(CLIInputParams):
    """Input api_key handler."""

    def __init__(self, entity: Optional[str]) -> None:
        """Init handlers."""
        self.entity = entity
        self.error_message = "Invalid API Key"

    def filtrator(self, entity: str) -> str:
        """Filter input entity."""
        return entity.strip()

    def validator(self, entity: str) -> bool:
        """Validate input entity."""
        api_key = self.filtrator(entity)
        return len(api_key) == 43

    def get(self) -> str:
        """Get filtered api_key value post validation."""
        self.entity = self.from_args()
        if self.entity is None:
            self.entity = inquirer.text(
                qmark=">",
                amark=">",
                message="API Key:",
                transformer=self.filtrator,
                filter=self.filtrator,
                validate=self.validator,
                invalid_message=self.error_message,
            ).execute()
        return self.entity
