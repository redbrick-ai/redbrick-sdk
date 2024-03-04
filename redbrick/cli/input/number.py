"""Input number handler."""

from typing import Optional

from InquirerPy.prompts.input import InputPrompt

from redbrick.cli.cli_base import CLIInputParams


class CLIInputNumber(CLIInputParams):
    """Input number handler."""

    def __init__(
        self,
        entity: Optional[str],
        name: str,
        default: str = "",
        mandatory: bool = True,
    ) -> None:
        """Init handlers."""
        self.entity = entity
        self.error_message = "Not a number"
        self.name = name
        self.default = default
        self.mandatory = mandatory

    def filtrator(self, entity: str) -> str:
        """Filter input entity."""
        return entity.strip()

    def validator(self, entity: str) -> bool:
        """Validate input entity."""
        number = self.filtrator(entity)
        return number.isnumeric() if number or self.mandatory else True

    def get(self) -> str:
        """Get filtered number value post validation."""
        self.entity = self.from_args()
        if self.entity is None:
            self.entity = InputPrompt(
                qmark=">",
                amark=">",
                message=self.name + ":",
                default=self.default,
                mandatory=self.mandatory,
                transformer=self.filtrator,
                filter=self.filtrator,
                validate=self.validator,
                invalid_message=self.error_message,
            ).execute()
        return self.entity
