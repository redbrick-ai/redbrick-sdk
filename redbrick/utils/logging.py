"""Logging functions."""
from typing import Union, Optional
from termcolor import colored


def print_info(text: str, end: Optional[str] = None) -> None:
    """Log general information."""
    print(colored("[INFO]: ", "blue"), text, end=end)


def print_warning(text: str) -> None:
    """Log warnings."""
    print(colored("[WARNING]: ", "yellow"), text)


def print_error(text: Union[str, Exception]) -> None:
    """Log errors."""
    print(colored("[ERROR]: ", "red"), text)
