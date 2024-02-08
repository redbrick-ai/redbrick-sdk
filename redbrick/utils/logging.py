"""Logging functions."""

from typing import Union, Any
import logging

from rich.logging import RichHandler

from redbrick.config import config


__LOG_NAME__ = "redbrick"
logger = logging.getLogger(__LOG_NAME__)
logger.setLevel(logging.DEBUG if config.debug else logging.INFO)
logger.addHandler(
    RichHandler(
        level=logger.level,
        show_path=config.debug,
        enable_link_path=False,
        markup=True,
        rich_tracebacks=True,
        tracebacks_show_locals=config.debug,
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
