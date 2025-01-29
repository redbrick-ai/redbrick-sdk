"""Google Cloud Storage method."""

from dataclasses import dataclass, field
from typing import Dict, Union, Optional
from redbrick.common.storage_method import StorageMethodDetails


@dataclass
class GCSStorageMethodDetails(StorageMethodDetails):
    """Storage information for DataPoints in a user's Google Cloud bucket."""

    #: the name of the storage provider
    _provider_name: str = field(default="GCS", init=False, repr=False)

    #: Key required for the API
    _provider_key: str = field(default="gcsBucket", init=False, repr=False)

    #: The name of the bucket
    bucket: str

    #: The service account JSON as a string
    service_account: str

    @property
    def details(self) -> Dict[str, Optional[Union[str, int, bool]]]:
        """Get the dictionary to be fed to the API.."""
        return {"bucket": self.bucket, "serviceAccount": self.service_account}

    @classmethod
    def from_dict(cls, data: Dict) -> "GCSStorageMethodDetails":
        """Create an instance from a dictionary."""
        details = data["details"]
        obj = cls(
            bucket=str(details["bucket"]),
            service_account=(
                str(details["serviceAccount"]) if "serviceAccount" in details else "***"
            ),
        )
        obj.storage_id = data["storageId"]
        obj.name = data["name"]
        return obj
