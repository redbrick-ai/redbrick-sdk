"""Public interface to storage module."""

import asyncio
from typing import List

from redbrick.common.entities import RBOrganization
from redbrick.common.storage import (
    Storage,
    StorageMethod,
    StorageProvider,
    STORAGE_PROVIDERS,
)
from redbrick.utils.files import is_valid_file_url


class StorageImpl(Storage):
    """Storage Method Controller."""

    def __init__(self, org: RBOrganization) -> None:
        """Initialize the controller."""
        self.org = org
        self.context = self.org.context

    def get_storage(self, storage_id: str) -> StorageProvider:
        """Get a storage method by ID."""
        storage_method = self.context.storage.get(self.org.org_id, storage_id)
        return STORAGE_PROVIDERS[storage_method["provider"]].from_entity(storage_method)

    def list_storages(self) -> List[StorageProvider]:
        """Get a list of storage methods in the organization."""
        storage_methods = self.context.storage.get_all(self.org.org_id)
        return [
            STORAGE_PROVIDERS[storage_method["provider"]].from_entity(storage_method)
            for storage_method in storage_methods
        ]

    def create_storage(self, storage: StorageProvider) -> StorageProvider:
        """Create a storage method."""
        storage_method = self.context.storage.create(
            self.org.org_id,
            storage.name,
            storage.PROVIDER,
            {storage.details.key: storage.details.to_entity()},
        )
        return STORAGE_PROVIDERS[storage_method["provider"]].from_entity(storage_method)

    def update_storage(
        self, storage_id: str, details: StorageProvider.Details
    ) -> StorageProvider:
        """Update a storage method."""
        storage = self.get_storage(storage_id)
        if details.key != storage.details.key:
            raise ValueError("Cannot change storage provider")

        storage_method = self.context.storage.update(
            self.org.org_id, storage_id, {details.key: details.to_entity()}
        )
        return STORAGE_PROVIDERS[storage_method["provider"]].from_entity(storage_method)

    def delete_storage(self, storage_id: str) -> bool:
        """Delete a storage method."""
        if storage_id in (StorageMethod.REDBRICK, StorageMethod.PUBLIC):
            raise ValueError("Cannot delete REDBRICK or PUBLIC storage methods")

        return self.context.storage.delete(self.org.org_id, storage_id)

    def verify_storage(self, storage_id: str, path: str) -> bool:
        """Verify a storage method by ID."""
        presigned_url = self.context.storage.presign_path(
            self.org.org_id, storage_id, path
        )
        return asyncio.run(is_valid_file_url(presigned_url))
