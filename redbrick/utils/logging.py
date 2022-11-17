"""Logging functions."""
import os
from typing import Union
import logging

from rich.logging import RichHandler
from rich import pretty, traceback


debug_mode = bool(os.environ.get("REDBRICK_SDK_DEBUG"))
pretty.install(overflow="fold")
traceback.install(
    word_wrap=True, show_locals=debug_mode, max_frames=10 if debug_mode else 5
)

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[
        RichHandler(
            level=logging.DEBUG if debug_mode else logging.INFO,
            show_path=debug_mode,
            enable_link_path=False,
            markup=True,
        )
    ],
)

logger = logging.getLogger("redbrick")
logger.setLevel(logging.DEBUG if debug_mode else logging.INFO)


def log_error(text: Union[str, Exception]) -> None:
    """Log errors."""
    if debug_mode:
        if isinstance(text, str):
            raise ValueError(text)
        raise ValueError(str(text)) from text
    logger.error(text)
