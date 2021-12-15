"""Input url handler."""
from typing import Optional

from InquirerPy import inquirer  # type: ignore

from redbrick.cli.cli_base import CLIInputParams


class CLIInputURL(CLIInputParams):
    """Input url handler."""

    def __init__(self, entity: Optional[str]) -> None:
        """Init handlers."""
        self.entity = entity
        self.error_message = "Invalid URL"

    def filtrator(self, entity: str) -> str:
        """Filter input entity."""
        return entity.strip().rstrip("/")

    def validator(self, entity: str) -> bool:
        """Validate input entity."""
        url = self.filtrator(entity)
        return url.startswith("http") and " " not in url and url.count("://") == 1

    def get(self) -> str:
        """Get filtered url value post validation."""
        self.entity = self.from_args()
        if self.entity is None:
            self.entity = inquirer.text(
                qmark=">",
                amark=">",
                message="URL:",
                default="https://api.redbrickai.com",
                transformer=self.filtrator,
                filter=self.filtrator,
                validate=self.validator,
                invalid_message=self.error_message,
            ).execute()
        return self.entity
