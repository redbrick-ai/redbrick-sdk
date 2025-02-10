"""RedBrick SDK global config."""

import logging
from typing import Callable, TypedDict
import os
from typing_extensions import Required  # type: ignore


class RBConfig:
    """Basic redbrick config."""

    class ConfigOptions(TypedDict):
        """RedBrick config options."""

        check_version: Callable[[], bool]
        debug: Callable[[], bool]
        verify_ssl: Callable[[], bool]
        log_level: Callable[[], int]

    class ConfigState(TypedDict, total=False):
        """RedBrick config state."""

        logger: Required[logging.Logger]
        check_version: bool
        debug: bool
        verify_ssl: bool
        log_level: int

    def __init__(self) -> None:
        """Define configs."""
        self._options: RBConfig.ConfigOptions = {
            "check_version": lambda: not bool(
                os.environ.get("REDBRICK_DISABLE_VERSION_CHECK")
            ),
            "debug": lambda: bool(os.environ.get("REDBRICK_SDK_DEBUG")),
            "verify_ssl": lambda: not bool(
                os.environ.get("RB_DISABLE_SSL_VERIFICATION")
            ),
            "log_level": lambda: int(
                os.environ.get("REDBRICK_SDK_LOG_LEVEL", logging.INFO)
            ),
        }
        logger = logging.getLogger("redbrick")
        logger.setLevel(
            logging.DEBUG if self._options["debug"]() else self._options["log_level"]()
        )
        self._state: RBConfig.ConfigState = {"logger": logger}

    def __repr__(self) -> str:
        """Class repr."""
        return str({option: self.__getattribute__(option) for option in self._options})

    @property
    def version(self) -> str:
        """Get redbrick sdk version."""
        # pylint: disable=import-outside-toplevel, cyclic-import
        from redbrick import __version__ as sdk_version

        return sdk_version

    @property
    def check_version(self) -> bool:
        """Check for redbrick version updates."""
        if "check_version" not in self._state:
            self._state["check_version"] = self._options["check_version"]()
        return self._state["check_version"]

    @check_version.setter
    def check_version(self, val: bool) -> None:
        """Check for redbrick version updates."""
        if isinstance(val, bool):
            self._state["check_version"] = val

    @check_version.deleter
    def check_version(self) -> None:
        """Check for redbrick version updates."""
        if "check_version" in self._state:
            del self._state["check_version"]

    @property
    def debug(self) -> bool:
        """Enable debugging."""
        if "debug" not in self._state:
            self._state["debug"] = self._options["debug"]()
        return self._state["debug"]

    @debug.setter
    def debug(self, val: bool) -> None:
        """Enable debugging."""
        if isinstance(val, bool):
            self._state["debug"] = val

    @debug.deleter
    def debug(self) -> None:
        """Enable debugging."""
        if "debug" in self._state:
            del self._state["debug"]

    @property
    def verify_ssl(self) -> bool:
        """Verify SSL when downloading image files."""
        if "verify_ssl" not in self._state:
            self._state["verify_ssl"] = self._options["verify_ssl"]()
        return self._state["verify_ssl"]

    @verify_ssl.setter
    def verify_ssl(self, val: bool) -> None:
        """Verify SSL when downloading image files."""
        if isinstance(val, bool):
            self._state["verify_ssl"] = val

    @verify_ssl.deleter
    def verify_ssl(self) -> None:
        """Verify SSL when downloading image files."""
        if "verify_ssl" in self._state:
            del self._state["verify_ssl"]

    @property
    def logger(self) -> logging.Logger:
        """Get default application logger."""
        return self._state["logger"]

    @property
    def log_level(self) -> int:
        """Get default application logging severity."""
        if "log_level" not in self._state:
            self._state["log_level"] = self._options["log_level"]()
        return self._state["log_level"]

    @log_level.setter
    def log_level(self, val: int) -> None:
        """Set default application logging severity."""
        if isinstance(val, int):
            self._state["log_level"] = val
        self.logger.setLevel(logging.DEBUG if self.debug else self.log_level)

    @log_level.deleter
    def log_level(self) -> None:
        """Reset default application logging severity."""
        if "log_level" in self._state:
            del self._state["log_level"]
        self.logger.setLevel(logging.DEBUG if self.debug else self.log_level)

    @property
    def log_info(self) -> bool:
        """Show info logs."""
        return self.log_level <= logging.INFO


config = RBConfig()

__all__ = ["config"]
