"""RedBrick SDK global config."""

from typing import Callable, TypedDict
import os


class Config:
    """Basic redbrick config."""

    class ConfigOptions(TypedDict):
        """RedBrick config options."""

        check_version: Callable[[], bool]
        debug: Callable[[], bool]
        verify_ssl: Callable[[], bool]

    class ConfigState(TypedDict, total=False):
        """RedBrick config state."""

        check_version: bool
        debug: bool
        verify_ssl: bool

    def __init__(self) -> None:
        """Define configs."""
        self._options: Config.ConfigOptions = {
            "check_version": lambda: not bool(
                os.environ.get("REDBRICK_DISABLE_VERSION_CHECK")
            ),
            "debug": lambda: bool(os.environ.get("REDBRICK_SDK_DEBUG")),
            "verify_ssl": lambda: not bool(
                os.environ.get("RB_DISABLE_SSL_VERIFICATION")
            ),
        }
        self._state: Config.ConfigState = {}

    def __repr__(self) -> str:
        """Class repr."""
        return str({option: self.__getattribute__(option) for option in self._options})

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
        "Enable debugging."
        if "debug" not in self._state:
            self._state["debug"] = self._options["debug"]()
        return self._state["debug"]

    @debug.setter
    def debug(self, val: bool) -> None:
        "Enable debugging."
        if isinstance(val, bool):
            self._state["debug"] = val

    @debug.deleter
    def debug(self) -> None:
        "Enable debugging."
        if "debug" in self._state:
            del self._state["debug"]

    @property
    def verify_ssl(self) -> bool:
        "Verify SSL when downloading image files."
        if "verify_ssl" not in self._state:
            self._state["verify_ssl"] = self._options["verify_ssl"]()
        return self._state["verify_ssl"]

    @verify_ssl.setter
    def verify_ssl(self, val: bool) -> None:
        "Verify SSL when downloading image files."
        if isinstance(val, bool):
            self._state["verify_ssl"] = val

    @verify_ssl.deleter
    def verify_ssl(self) -> None:
        "Verify SSL when downloading image files."
        if "verify_ssl" in self._state:
            del self._state["verify_ssl"]


config = Config()

__all__ = ["config"]
