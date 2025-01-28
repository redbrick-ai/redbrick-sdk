"""Interdace for getting information about storage methods."""

from abc import ABC, abstractmethod
from typing import Dict, List, Union

from redbrick.types.storage_method import StorageMethodDetailsType


class StorageMethodRepoInterface(ABC):
    """Abstract interface to Storage Method APIs."""

    @abstractmethod
    def get_all(self, org_id: str) -> List[Dict]:
        """Get storage methods."""

    @abstractmethod
    def get(self, org_id: str, storage_method_id: str) -> Dict:
        """Get a storage method."""

    @abstractmethod
    def create(
        self,
        org_id: str,
        name: str,
        details: StorageMethodDetailsType,
    ) -> Dict[str, Union[bool, Dict]]:
        """Create a storage method."""

    @abstractmethod
    def update(
        self,
        org_id: str,
        storage_method_id: str,
        details: StorageMethodDetailsType,
    ) -> Dict[str, Union[bool, Dict]]:
        """Update a storage method."""

    @abstractmethod
    def delete(self, org_id: str, storage_method_id: str) -> bool:
        """Delete a storage method."""
