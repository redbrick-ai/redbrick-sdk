"""Interdace for getting information about storage methods."""

from abc import ABC, abstractmethod
from typing import Dict, List

from redbrick.common.enums import StorageProvider


class StorageMethodRepoInterface(ABC):
    """Abstract interface to Storage Method APIs."""

    @abstractmethod
    def get_storage_methods(self, org_id: str) -> List[Dict]:
        """Get storage methods."""

    @abstractmethod
    def create_storage_method(
        self, org_id: str, name: str, provider: StorageProvider, details: Dict
    ) -> bool:
        """Create a storage method."""
