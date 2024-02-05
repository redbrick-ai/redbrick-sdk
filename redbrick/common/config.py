"""Container for context config."""

from dataclasses import dataclass


@dataclass
class RBConfig:
    """Basic context config."""

    verify_ssl: bool = True
