"""Redbrick Storage Method Module."""

from redbrick.common.storage_method import StorageMethodDetails

from redbrick.storage_method.redbrick import RedbrickStorageMethodDetails
from redbrick.storage_method.public import PublicStorageMethodDetails
from redbrick.storage_method.aws_s3 import AWSS3StorageMethodDetails
from redbrick.storage_method.gcs import GCSStorageMethodDetails
from redbrick.storage_method.azure import AzureBlobStorageMethodDetails
from redbrick.storage_method.altadb import AltaDBStorageMethodDetails


__all__ = [
    "StorageMethodDetails",
    "RedbrickStorageMethodDetails",
    "PublicStorageMethodDetails",
    "AWSS3StorageMethodDetails",
    "GCSStorageMethodDetails",
    "AzureBlobStorageMethodDetails",
    "AltaDBStorageMethodDetails",
]
