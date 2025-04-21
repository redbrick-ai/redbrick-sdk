"""Interface for getting basic information about a dataset."""

from typing import Dict
from abc import ABC, abstractmethod


class DatasetRepo(ABC):
    """Abstract interface to Dataset APIs."""

    @abstractmethod
    def get_dataset(self, org_id: str, dataset_name: str) -> Dict:
        """Get a dataset."""

    @abstractmethod
    def create_dataset(self, org_id: str, dataset_name: str) -> Dict:
        """Create a dataset."""

    @abstractmethod
    def delete_dataset(self, org_id: str, dataset_name: str) -> bool:
        """Delete a dataset."""
