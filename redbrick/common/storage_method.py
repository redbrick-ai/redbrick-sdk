"""Interdace for getting information about storage methods."""

from abc import abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Union, Optional
from redbrick.common.enums import StorageMethod


@dataclass
class StorageMethodDetails:
    """Storage Method Type."""

    _provider_name: str
    _provider_key: str

    storage_id: str = field(default=StorageMethod.PUBLIC, init=False)
    name: str = field(default="Storage Method", init=False)

    @property
    def details(self) -> Dict[str, Optional[Union[str, int, bool]]]:
        """Get the dictionary to be fed to the API.."""
        raise NotImplementedError

    @property
    def provider_name(self) -> str:
        """Get the provider name."""
        return self._provider_name

    @provider_name.setter
    def provider_name(self, value: str) -> None:
        """Set the provider name."""
        raise AssertionError(f"Cannot set provider name to `{value}`")

    @property
    def provider_key(self) -> str:
        """Get the provider key."""
        return self._provider_key

    @provider_key.setter
    def provider_key(self, value: str) -> None:
        """Set the provider key."""
        raise AssertionError(f"Cannot set provider key to `{value}`")

    @classmethod
    @abstractmethod
    def from_dict(
        cls,
        data: Dict,
    ) -> "StorageMethodDetails":
        """Create a StorageMethodDetails object from a dictionary."""
        raise NotImplementedError


__all__ = ["StorageMethodDetails"]
