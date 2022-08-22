"""Logging functions."""
import os
from typing import Union
import logging

from rich.logging import RichHandler
from rich import pretty, traceback


debug_mode = bool(os.environ.get("REDBRICK_SDK_DEBUG"))
pretty.install(overflow="fold")
traceback.install(
    word_wrap=True, show_locals=debug_mode, max_frames=50 if debug_mode else 5
)

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[
        RichHandler(
            level=logging.INFO,
            show_path=debug_mode,
            enable_link_path=debug_mode,
            markup=True,
        )
    ],
)
logger = logging.getLogger("rich")


def print_info(text: str) -> None:
    """Log general information."""
    logger.info(text)


def print_warning(text: str) -> None:
    """Log warnings."""
    logger.warning(text)


def print_error(text: Union[str, Exception]) -> None:
    """Log errors."""
    if debug_mode:
        if isinstance(text, str):
            raise ValueError(text)
        raise ValueError(str(text)) from text
    logger.error(text)
