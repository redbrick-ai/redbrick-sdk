"""Logging functions."""
from typing import Union
from termcolor import colored


def print_info(text: str) -> None:
    """Logging general information."""
    print(colored("[INFO]: ", "blue"), text)


def print_warning(text: str) -> None:
    """Logging warnings."""
    print(colored("[WARNING]: ", "yellow"), text)


def print_error(text: Union[str, Exception]) -> None:
    """Logging errors."""
    print(colored("[ERROR]: ", "red"), text)
