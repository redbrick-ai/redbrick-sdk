"""Controller for storage methods."""

import asyncio
from typing import List
from redbrick.common.context import RBContext
from redbrick.common.storage_method import (
    StorageMethodDetails,
    InputStorageMethodDetailsType,
    StorageMethodDetailsType,
)
from redbrick.utils.files import is_valid_file_url


class StorageMethodController:
    """Controller for storage methods."""

    def __init__(self, context: RBContext, org_id: str) -> None:
        """Initialize the controller."""
        self.context = context
        self.org_id = org_id

    def get_all(self) -> List[StorageMethodDetailsType]:
        """Get a list of storage methods in the organization."""
        return [
            StorageMethodDetails.from_dict(storage_method)
            for storage_method in self.context.storage_method.get_all(self.org_id)
        ]

    def get(self, storage_id: str) -> StorageMethodDetailsType:
        """Get a storage method by ID."""
        storage_method = self.context.storage_method.get(self.org_id, storage_id)
        return StorageMethodDetails.from_dict(storage_method)

    def verify(self, storage_id: str, path: str) -> bool:
        """Verify a storage method by ID."""
        presigned_url = self.context.storage_method.presign(
            self.org_id, storage_id, path
        )
        return asyncio.run(is_valid_file_url(presigned_url))

    def create(
        self,
        name: str,
        details: InputStorageMethodDetailsType,
    ) -> StorageMethodDetailsType:
        """Create a storage method."""
        res = self.context.storage_method.create(self.org_id, name, details)
        assert isinstance(res["storageMethod"], dict)
        return StorageMethodDetails.from_dict(res["storageMethod"])

    def update(
        self,
        storage_id: str,
        details: InputStorageMethodDetailsType,
    ) -> StorageMethodDetailsType:
        """Update a storage method."""
        storage_method = self.get(storage_id)
        if storage_method.provider_name != details.provider_name:
            raise ValueError("Cannot change storage provider")
        if storage_method.name != details.name:
            raise ValueError("Cannot change storage name")
        res = self.context.storage_method.update(self.org_id, storage_id, details)
        assert isinstance(res["storageMethod"], dict)
        return StorageMethodDetails.from_dict(res["storageMethod"])

    def delete(self, storage_id: str) -> bool:
        """Delete a storage method."""
        return self.context.storage_method.delete(self.org_id, storage_id)
