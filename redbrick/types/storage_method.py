"""Storage Method Types"""

import json
from typing import TypedDict, Union
from typing_extensions import NotRequired


class InputAWSS3StorageMethodDetails(TypedDict):
    """AWS S3 Storage Method Type.

    Contains the necessary information to access a user's AWS S3 bucket.
    """

    #: The name of the bucket
    bucket: str

    #: The region of the bucket
    region: str

    #: The duration of the session
    duration: NotRequired[int]

    #: The access key (AWS_ACCESS_KEY_ID)
    access: NotRequired[str]

    #: The secret key (AWS_SECRET_ACCESS_KEY)
    secret: NotRequired[str]

    # session creds

    #: The role ARN
    roleArn: NotRequired[str]

    #: The role external ID
    roleExternalId: NotRequired[str]

    #: The endpoint
    endpoint: NotRequired[str]

    #: Whether to use S3 transfer acceleration
    accelerate: NotRequired[bool]


class InputGCSStorageMethodDetails(TypedDict):
    """Storage information for DataPoints in a user's Google Cloud bucket."""

    #: The name of the bucket
    bucket: str

    #: The service account JSON as a string
    serviceAccount: str


class InputAzureBlobStorageMethodDetails(TypedDict):
    """Azure Blob Storage Method Type."""

    #: The connection string
    connectionString: NotRequired[str]

    #: The SAS URL
    sasUrl: NotRequired[str]


class InputAltaDBStorageMethodDetails(TypedDict):
    """AltaDB Storage Method Type."""

    #: The access key
    access: str

    #: The secret key
    secret: str

    #: The host (backend URL)
    host: NotRequired[str]


StorageMethodDetails = Union[
    InputAWSS3StorageMethodDetails,
    InputGCSStorageMethodDetails,
    InputAzureBlobStorageMethodDetails,
    InputAltaDBStorageMethodDetails,
]
