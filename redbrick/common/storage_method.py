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
    def from_dict(
        cls,
        data: Dict,
    ) -> "StorageMethodDetailsType":
        """Create an instance from a dictionary."""
        if data["provider"] == AltaDBStorageMethodDetails.provider_name:
            return AltaDBStorageMethodDetails.from_dict(data)
        if data["provider"] == AWSS3StorageMethodDetails.provider_name:
            return AWSS3StorageMethodDetails.from_dict(data)
        if data["provider"] == GCSStorageMethodDetails.provider_name:
            return GCSStorageMethodDetails.from_dict(data)
        if data["provider"] == AzureBlobStorageMethodDetails.provider_name:
            return AzureBlobStorageMethodDetails.from_dict(data)
        if data["provider"] == PublicStorageMethodDetails.provider_name:
            return PublicStorageMethodDetails()
        if data["provider"] == RedbrickStorageMethodDetails.provider_name:
            return RedbrickStorageMethodDetails()
        raise ValueError(f"Unknown provider: {data['provider']}")


@dataclass
class PublicStorageMethodDetails(StorageMethodDetails):
    """Public Storage Method Type."""

    #: The name of the storage provider
    _provider_name: str = field(default="PUBLIC", init=False, repr=False)

    #: Key required for the API
    _provider_key: str = field(default="public", init=False, repr=False)

    storage_id: str = "11111111-1111-1111-1111-111111111111"
    name: str = "Public"

    @property
    def details(self) -> Dict[str, Optional[Union[str, int, bool]]]:
        """Get the dictionary to be fed to the API.."""
        return {}


@dataclass
class RedbrickStorageMethodDetails(StorageMethodDetails):
    """Redbrick Storage Method Type."""

    #: The name of the storage provider
    _provider_name: str = field(default="REDBRICK", init=False, repr=False)

    #: Key required for the API
    _provider_key: str = field(default="redbrick", init=False, repr=False)

    storage_id: str = "22222222-2222-2222-2222-222222222222"
    name: str = "Redbrick"

    @property
    def details(self) -> Dict[str, Optional[Union[str, int, bool]]]:
        """Get the dictionary to be fed to the API.."""
        return {}


@dataclass
class AWSS3StorageMethodDetails(StorageMethodDetails):
    """AWS S3 Storage Method Type.

    Contains the necessary information to access a user's AWS S3 bucket.
    """

    #: The name of the storage provider
    _provider_name: str = field(default="AWS_S3", init=False, repr=False)

    #: Key required for the API
    _provider_key: str = field(default="s3Bucket", init=False, repr=False)

    #: The details
    #: The name of the bucket
    bucket: str

    #: The region of the bucket
    region: str

    #: The duration of the session
    duration: Optional[int] = None

    #: The access key (AWS_ACCESS_KEY_ID)
    access: Optional[str] = None

    #: The secret key (AWS_SECRET_ACCESS_KEY)
    secret: Optional[str] = None

    # session creds

    #: The role ARN
    role_arn: Optional[str] = None

    #: The role external ID
    role_external_id: Optional[str] = None

    #: The endpoint
    endpoint: Optional[str] = None

    #: Whether to use S3 transfer acceleration
    accelerate: Optional[bool] = None

    @property
    def details(self) -> Dict[str, Optional[Union[str, int, bool]]]:
        """Get the dictionary to be fed to the API.."""
        return {
            k: v
            for k, v in {
                "bucket": self.bucket,
                "region": self.region,
                "duration": self.duration,
                "access": self.access,
                "secret": self.secret if self.secret is not None else "***",
                "roleArn": self.role_arn,
                "roleExternalId": self.role_external_id,
                "endpoint": self.endpoint,
                "accelerate": self.accelerate,
            }.items()
            if v is not None
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "AWSS3StorageMethodDetails":
        """Create an instance from a dictionary."""
        details = data["details"]
        obj = cls(
            bucket=str(details["bucket"]),
            region=str(details["region"]),
        )
        obj.storage_id = data["storageId"]
        obj.name = data["name"]
        non_required_keys = [
            "duration",
            "access",
            "secret",
            "roleArn",
            "roleExternalId",
            "endpoint",
            "accelerate",
        ]
        for key in non_required_keys:
            if key in details and details[key] is not None:
                setattr(obj, key, details[key])
        return obj


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


@dataclass
class AzureBlobStorageMethodDetails(StorageMethodDetails):
    """Azure Blob Storage Method Type."""

    #: The name of the storage provider
    _provider_name: str = field(default="AZURE_BLOB", init=False, repr=False)

    #: Key required for the API
    _provider_key: str = field(default="azureBucket", init=False, repr=False)

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


@dataclass
class AltaDBStorageMethodDetails(StorageMethodDetails):
    """AltaDB Storage Method Type."""

    #: The name of the storage provider
    _provider_name: str = field(default="ALTA_DB", init=False, repr=False)

    #: Key required for the API
    _provider_key: str = field(default="altaDb", init=False, repr=False)

    #: The access key
    access: str

    #: The secret key
    secret: str

    #: The host (backend URL)
    host: Optional[str] = None

    @property
    def details(self) -> Dict[str, Optional[Union[str, int, bool]]]:
        """Get the dictionary to be fed to the API.."""
        details: Dict[str, Optional[Union[str, int, bool]]] = {
            "access": self.access,
            "secret": self.secret,
        }
        if self.host is not None:
            details["host"] = self.host
        return details

    @classmethod
    def from_dict(
        cls,
        data: Dict,
    ) -> "AltaDBStorageMethodDetails":
        """Create an instance from a dictionary."""
        obj = cls(
            access=str(data["details"]["access"]),
            secret=str(data["details"]["secret"]) if "secret" in data else "***",
            host=str(data["details"]["host"]) if "host" in data else None,
        )
        obj.storage_id = data["storageId"]
        obj.name = data["name"]
        return obj


InputStorageMethodDetailsType = Union[
    AWSS3StorageMethodDetails,
    GCSStorageMethodDetails,
    AzureBlobStorageMethodDetails,
    AltaDBStorageMethodDetails,
]

StorageMethodDetailsType = Union[
    AWSS3StorageMethodDetails,
    GCSStorageMethodDetails,
    AzureBlobStorageMethodDetails,
    AltaDBStorageMethodDetails,
    PublicStorageMethodDetails,
    RedbrickStorageMethodDetails,
]


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
        details: InputStorageMethodDetailsType,
    ) -> Dict[str, Union[bool, Dict]]:
        """Create a storage method."""

    @abstractmethod
    def update(
        self,
        org_id: str,
        storage_method_id: str,
        details: InputStorageMethodDetailsType,
    ) -> Dict[str, Union[bool, Dict]]:
        """Update a storage method."""

    @abstractmethod
    def delete(self, org_id: str, storage_method_id: str) -> bool:
        """Delete a storage method."""
