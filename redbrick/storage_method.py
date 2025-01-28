"""Controller for storage methods."""

from typing import Dict, List, Union
from redbrick.common.context import RBContext
from redbrick.types.storage_method import StorageMethodDetailsType


class StorageMethodController:
    """Controller for storage methods."""

    def __init__(self, context: RBContext, org_id: str) -> None:
        """Initialize the controller."""
        self.context = context
        self.org_id = org_id

    def get_all(self) -> List[Dict]:
        """Get a list of storage methods in the organization."""
        return self.context.storage_method.get_all(self.org_id)

    def get(self, storage_id: str) -> Dict:
        """Get a storage method by ID."""
        return self.context.storage_method.get(self.org_id, storage_id)

    def create(
        self,
        name: str,
        details: StorageMethodDetailsType,
    ) -> Dict[str, Union[bool, Dict]]:
        """Create a storage method."""
        return self.context.storage_method.create(self.org_id, name, details)

    def update(
        self,
        storage_id: str,
        details: StorageMethodDetailsType,
    ) -> Dict[str, Union[bool, Dict]]:
        """Update a storage method."""
        storage_method = self.get(storage_id)
        if storage_method["provider"] != details.provider_name:
            raise ValueError("Cannot change storage provider")
        return self.context.storage_method.update(self.org_id, storage_id, details)

    def delete(self, storage_id: str) -> bool:
        """Delete a storage method."""
        return self.context.storage_method.delete(self.org_id, storage_id)
