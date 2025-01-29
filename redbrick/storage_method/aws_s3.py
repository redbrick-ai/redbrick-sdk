"""Interdace for getting information about storage methods."""

from dataclasses import dataclass, field
from typing import Dict, Union, Optional
from redbrick.common.storage_method import StorageMethodDetails


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
