"""Logging functions."""
from termcolor import colored
from typing import Union


def print_info(text: str) -> None:
    """Logging general information."""
    print(colored("[INFO]: ", "blue"), text)


def print_warning(text: str) -> None:
    """Logging warnings."""
    print(colored("[WARNING]: ", "yellow"), text)


def print_error(text: Union[str, Exception]) -> None:
    """Logging errors."""
    print(colored("[ERROR]: ", "red"), text)
