"""Redbrick Storage Method Module."""

import asyncio
from typing import Dict, List, Type
from redbrick.common.context import RBContext
from redbrick.common.storage_method import StorageMethodDetails

from redbrick.storage_method.redbrick import RedbrickStorageMethodDetails
from redbrick.storage_method.public import PublicStorageMethodDetails
from redbrick.storage_method.aws_s3 import AWSS3StorageMethodDetails
from redbrick.storage_method.gcs import GCSStorageMethodDetails
from redbrick.storage_method.azure import AzureBlobStorageMethodDetails
from redbrick.storage_method.altadb import AltaDBStorageMethodDetails
from redbrick.utils.files import is_valid_file_url
from redbrick.common.constants import (
    REDBRICK_STORAGE_PROVIDER,
    PUBLIC_STORAGE_PROVIDER,
    AWS_S3_STORAGE_PROVIDER,
    GCS_STORAGE_PROVIDER,
    AZURE_BLOB_STORAGE_PROVIDER,
    ALTADB_STORAGE_PROVIDER,
)


class StorageMethodController:
    """Storage Method Controller."""

    PROVIDER_CLASS_MAP: Dict[str, Type[StorageMethodDetails]] = {
        REDBRICK_STORAGE_PROVIDER: RedbrickStorageMethodDetails,
        PUBLIC_STORAGE_PROVIDER: PublicStorageMethodDetails,
        AWS_S3_STORAGE_PROVIDER: AWSS3StorageMethodDetails,
        GCS_STORAGE_PROVIDER: GCSStorageMethodDetails,
        AZURE_BLOB_STORAGE_PROVIDER: AzureBlobStorageMethodDetails,
        ALTADB_STORAGE_PROVIDER: AltaDBStorageMethodDetails,
    }

    def __init__(self, context: RBContext, org_id: str):
        """Initialize the controller."""
        self.context = context
        self.org_id = org_id

    def check_provider_creation(self, provider: str) -> bool:
        """Check if a provider can be created."""
        return provider not in [REDBRICK_STORAGE_PROVIDER, PUBLIC_STORAGE_PROVIDER]

    def get_all(self) -> List[StorageMethodDetails]:
        """Get a list of storage methods in the organization."""
        storage_methods = self.context.storage_method.get_all(self.org_id)
        return [
            self.PROVIDER_CLASS_MAP[storage_method["provider"]].from_dict(
                storage_method
            )
            for storage_method in storage_methods
        ]

    def get(self, storage_id: str) -> StorageMethodDetails:
        """Get a storage method by ID."""
        storage_method = self.context.storage_method.get(self.org_id, storage_id)
        return self.PROVIDER_CLASS_MAP[storage_method["provider"]].from_dict(
            storage_method
        )

    def verify(self, storage_id: str, path: str) -> bool:
        """Verify a storage method by ID."""
        presigned_url = self.context.storage_method.presign(
            self.org_id, storage_id, path
        )
        presigned_url = presigned_url.replace("altadb://", "https://")
        return asyncio.run(is_valid_file_url(presigned_url))

    def create(
        self,
        name: str,
        details: StorageMethodDetails,
    ) -> StorageMethodDetails:
        """Create a storage method."""
        if not self.check_provider_creation(details.provider_name):
            raise ValueError(
                f"Cannot create a storage method with provider {details.provider_name}"
            )
        res = self.context.storage_method.create(
            self.org_id,
            name,
            details.provider_key,
            details.provider_name,
            details.details,
        )
        assert isinstance(res["storageMethod"], dict)
        return self.PROVIDER_CLASS_MAP[details.provider_name].from_dict(
            res["storageMethod"]
        )

    def update(
        self,
        storage_id: str,
        details: StorageMethodDetails,
    ) -> StorageMethodDetails:
        """Update a storage method."""
        if not self.check_provider_creation(details.provider_name):
            raise ValueError(
                f"Cannot update a storage method with provider {details.provider_name}"
            )
        storage_method = self.get(storage_id)
        if storage_method.provider_name != details.provider_name:
            raise ValueError("Cannot change storage provider")
        if storage_method.name != details.name:
            raise ValueError(
                f"Cannot change storage name from {storage_method.name} to {details.name}"
            )
        res = self.context.storage_method.update(
            self.org_id, storage_id, storage_method.provider_key, details.details
        )
        assert isinstance(res["storageMethod"], dict)
        return self.PROVIDER_CLASS_MAP[details.provider_name].from_dict(
            res["storageMethod"]
        )

    def delete(self, storage_id: str) -> bool:
        """Delete a storage method."""
        return self.context.storage_method.delete(self.org_id, storage_id)


__all__ = [
    "StorageMethodDetails",
    "RedbrickStorageMethodDetails",
    "PublicStorageMethodDetails",
    "AWSS3StorageMethodDetails",
    "GCSStorageMethodDetails",
    "AzureBlobStorageMethodDetails",
    "AltaDBStorageMethodDetails",
]
