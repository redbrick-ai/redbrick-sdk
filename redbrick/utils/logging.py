"""Logging functions."""

from typing import Union
import logging


class Logger:
    """Custom logger."""

    def __init__(self) -> None:
        """Construct logging object."""
        # Create a custom logger
        logger_ = logging.getLogger(__name__)
        logger_.setLevel(logging.INFO)

        # Create handlers
        console = logging.StreamHandler()

        # Create formatters and add it to handlers
        console.setFormatter(logging.Formatter("%(levelname)s - %(message)s"))

        # Add handlers to the logger
        logger_.addHandler(console)

        self.logger = logger_


logger = Logger().logger


def print_info(text: str) -> None:
    """Log general information."""
    logger.info(text)


def print_warning(text: str) -> None:
    """Log warnings."""
    logger.warning(text)


def print_error(text: Union[str, Exception]) -> None:
    """Log errors."""
    logger.error(text)
