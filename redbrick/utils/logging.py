"""Logging functions."""

from typing import Union
import logging


class Formatter(logging.Formatter):
    """Custom formatter."""

    grey = "\x1b[38;22m"
    blue = "\x1b[34;22m"
    yellow = "\x1b[33;22m"
    red = "\x1b[31;22m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"

    format_color = "%(levelname)s - "
    format_rest = "%(message)s"

    FORMATS = {
        logging.DEBUG: grey + format_color + reset + format_rest,
        logging.INFO: blue + format_color + reset + format_rest,
        logging.WARNING: yellow + format_color + reset + format_rest,
        logging.ERROR: red + format_color + reset + format_rest,
        logging.CRITICAL: bold_red + format_color + reset + format_rest,
    }

    def format(self, record: logging.LogRecord) -> str:
        """Format method."""
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


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
        console.setFormatter(Formatter())

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
