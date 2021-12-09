"""CLI configuration handler."""
import os
from configparser import ConfigParser
from typing import Dict, Optional


class CLIConfiguration:
    """CLIConfiguration entity."""

    _conf_file: str
    _conf: ConfigParser

    def __init__(self, conf_file: str) -> None:
        """Initialize CLIConfiguration."""
        self._conf_file = conf_file
        self._conf = ConfigParser()

        if self.exists:
            self._conf.read(self._conf_file)

    @property
    def exists(self) -> bool:
        """Boolean flag to indicate if configuration file exists."""
        if os.path.exists(self._conf_file):
            if os.path.isfile(self._conf_file):
                return True
            raise Exception(f"Not a file {self._conf_file}")
        return False

    def get_section(
        self, section: str, default: Optional[Dict[str, str]] = None
    ) -> Optional[Dict[str, str]]:
        """Get section from configuration."""
        if self.exists and section in self._conf:
            return dict(self._conf[section].items())
        return default

    def set_section(self, section: str, value: Dict[str, str]) -> None:
        """Set section into configuration."""
        self._conf[section] = value

    def get_option(
        self, section: str, option: str, default: Optional[str] = None
    ) -> Optional[str]:
        """Get option from configuration."""
        if self.exists and section in self._conf and option in self._conf[section]:
            return self._conf[section][option]
        return default

    def set_option(self, section: str, option: str, value: str) -> None:
        """Set option into configuration."""
        if section not in self._conf:
            self._conf[section] = {}
        self._conf[section][option] = value

    def save(self) -> None:
        """Save configuration into file."""
        assert os.path.isdir(os.path.dirname(self._conf_file)), "Not a valid project"
        with open(self._conf_file, "w", encoding="utf-8") as conf:
            self._conf.write(conf)
