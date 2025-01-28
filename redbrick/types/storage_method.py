"""Storage Method Types"""

from dataclasses import dataclass, field
from typing import Dict, Optional, Union


@dataclass
class _StorageMethodDetails:
    """Storage Method Type."""

    _provider_name: str
    _provider_key: str

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


@dataclass
class InputAWSS3StorageMethodDetails(_StorageMethodDetails):
    """AWS S3 Storage Method Type.

    Contains the necessary information to access a user's AWS S3 bucket.
    """

    #: The name of the storage provider
    _provider_name: str = field(default="AWS_S3", init=False)

    #: Key required for the API
    _provider_key: str = field(default="s3Bucket", init=False)

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
                "secret": self.secret,
                "roleArn": self.role_arn,
                "roleExternalId": self.role_external_id,
                "endpoint": self.endpoint,
                "accelerate": self.accelerate,
            }.items()
            if v is not None
        }


@dataclass
class InputGCSStorageMethodDetails(_StorageMethodDetails):
    """Storage information for DataPoints in a user's Google Cloud bucket."""

    #: the name of the storage provider
    _provider_name: str = field(default="GCS", init=False)

    #: Key required for the API
    _provider_key: str = field(default="gcsBucket", init=False)

    #: The name of the bucket
    bucket: str

    #: The service account JSON as a string
    service_account: str

    @property
    def details(self) -> Dict[str, Optional[Union[str, int, bool]]]:
        """Get the dictionary to be fed to the API.."""
        return {"bucket": self.bucket, "serviceAccount": self.service_account}


@dataclass
class InputAzureBlobStorageMethodDetails(_StorageMethodDetails):
    """Azure Blob Storage Method Type."""

    #: The name of the storage provider
    _provider_name: str = field(default="AZURE_BLOB", init=False)

    #: Key required for the API
    _provider_key: str = field(default="azureBucket", init=False)

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


@dataclass
class InputAltaDBStorageMethodDetails(_StorageMethodDetails):
    """AltaDB Storage Method Type."""

    #: The name of the storage provider
    _provider_name: str = field(default="ALTA_DB", init=False)

    #: Key required for the API
    _provider_key: str = field(default="altaDb", init=False)

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


StorageMethodDetailsType = Union[
    InputAWSS3StorageMethodDetails,
    InputGCSStorageMethodDetails,
    InputAzureBlobStorageMethodDetails,
    InputAltaDBStorageMethodDetails,
]
