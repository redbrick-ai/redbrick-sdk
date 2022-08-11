"""Logging functions."""
import os
from typing import Union
import logging

from rich.logging import RichHandler
from rich.traceback import install


debug_mode = bool(os.environ.get("REDBRICK_SDK_DEBUG"))
install(show_locals=debug_mode, max_frames=50 if debug_mode else 5)

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[
        RichHandler(
            level=logging.INFO, show_path=False, enable_link_path=False, markup=True
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
    logger.error(text)
