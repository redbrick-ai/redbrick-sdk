"""Azure Blob Storage Method."""

from dataclasses import dataclass, field
from typing import Dict, Union, Optional
from redbrick.common.constants import (
    AZURE_BLOB_STORAGE_PROVIDER,
    STORAGE_PROVIDER_KEY_MAP,
)
from redbrick.common.storage_method import StorageMethodDetails


@dataclass
class AzureBlobStorageMethodDetails(StorageMethodDetails):
    """Azure Blob Storage Method Type."""

    #: The name of the storage provider
    _provider_name: str = field(
        default=AZURE_BLOB_STORAGE_PROVIDER, init=False, repr=False
    )

    #: Key required for the API
    _provider_key: str = field(
        default=STORAGE_PROVIDER_KEY_MAP[AZURE_BLOB_STORAGE_PROVIDER],
        init=False,
        repr=False,
    )

    #: The connection string
    connection_string: Optional[str] = None

    #: The SAS URL
    sas_url: Optional[str] = None

    @property
    def details(self) -> Dict[str, Optional[Union[str, int, bool]]]:
        """Get the dictionary to be fed to the API.."""
        details: Dict[str, Optional[Union[str, int, bool]]] = {}
        if self.connection_string is not None:
            details["connectionString"] = self.connection_string
        if self.sas_url is not None:
            details["sasUrl"] = self.sas_url
        return details

    @classmethod
    def from_dict(cls, data: Dict) -> "AzureBlobStorageMethodDetails":
        """Create an instance from a dictionary."""
        details = data["details"]
        obj = cls(
            connection_string=(
                str(details["connectionString"])
                if "connectionString" in details
                else None
            ),
            sas_url=str(details["sasUrl"]) if "connectionString" in details else None,
        )
        obj.storage_id = data["storageId"]
        obj.name = data["name"]
        return obj

    def __post_init__(self):
        """Validate the object."""
        if (
            not self.storage_id
            and self.connection_string is None
            and self.sas_url is None
        ):
            raise ValueError(
                "Either connection_string or sas_url must be provided for AzureBlobStorageMethodDetails"
            )
