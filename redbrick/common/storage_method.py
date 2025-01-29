"""Interdace for getting information about storage methods."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Union, Optional
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


class StorageMethodRepoInterface(ABC):
    """Abstract interface to Storage Method APIs."""

    @abstractmethod
    def get_all(self, org_id: str) -> List[Dict]:
        """Get storage methods."""

    @abstractmethod
    def get(self, org_id: str, storage_method_id: str) -> Dict:
        """Get a storage method."""

    @abstractmethod
    def presign(self, org_id: str, storage_method_id: str, path: str) -> str:
        """Verify a storage method."""

    @abstractmethod
    def create(
        self,
        org_id: str,
        name: str,
        provider_key: str,
        provider_name: str,
        details: Dict,
    ) -> Dict[str, Union[bool, Dict]]:
        """Create a storage method."""

    @abstractmethod
    def update(
        self,
        org_id: str,
        storage_method_id: str,
        provider_key: str,
        details: Dict,
    ) -> Dict[str, Union[bool, Dict]]:
        """Update a storage method."""

    @abstractmethod
    def delete(self, org_id: str, storage_method_id: str) -> bool:
        """Delete a storage method."""


__all__ = ["StorageMethodDetails"]
