"""Logging functions."""
import os
from typing import Union, Any
import logging

from rich.logging import RichHandler


debug_mode = bool(os.environ.get("REDBRICK_SDK_DEBUG"))


logger = logging.getLogger("redbrick")
logger.setLevel(logging.DEBUG if debug_mode else logging.INFO)
logger.addHandler(
    RichHandler(
        level=logger.level,
        show_path=debug_mode,
        enable_link_path=False,
        markup=True,
        rich_tracebacks=True,
        tracebacks_show_locals=debug_mode,
    )
)


def log_error(error: Union[str, Exception], raise_error: bool = False) -> None:
    """Log errors."""
    if isinstance(error, str):
        error = Exception(error)
    logger.error(error, exc_info=error)
    if raise_error:
        raise error


def assert_validation(condition: Any, message: str) -> None:
    """Implement custom validation assertion."""
    if not bool(condition):
        log_error(message, True)
