"""Input select handler."""
from typing import Any, List, Optional

from InquirerPy import inquirer  # type: ignore

from redbrick.cli.cli_base import CLIInputParams


class CLIInputSelect(CLIInputParams):
    """Input select handler."""

    def __init__(self, entity: Optional[str], name: str, options: List[Any]) -> None:
        """Init handlers."""
        self.entity = entity
        self.error_message = "Invalid " + name
        self.name = name
        self.options = options

    def filtrator(self, entity: str) -> str:
        """Filter input entity."""
        return entity.strip()

    def validator(self, entity: str) -> bool:
        """Validate input entity."""
        select = self.filtrator(entity)
        if not self.options:
            return False

        if isinstance(self.options[0], dict):
            return select in [val["name"] for val in self.options]

        return select in self.options

    def get(self) -> str:
        """Get filtered select value post validation."""
        self.entity = self.from_args()
        if self.entity is None:
            if self.options:
                self.entity = inquirer.fuzzy(
                    qmark=">", amark=">", message=self.name + ":", choices=self.options
                ).execute()
            else:
                raise ValueError(f"No {self.name} available")
        return self.entity
