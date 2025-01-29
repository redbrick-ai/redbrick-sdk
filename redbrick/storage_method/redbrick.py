"""Redbrick Storage Method Details."""

from dataclasses import dataclass, field
from typing import Dict, Union, Optional
from redbrick.common.storage_method import StorageMethodDetails


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

    @classmethod
    def from_dict(
        cls, data: Dict  # pylint: disable=unused-argument
    ) -> "RedbrickStorageMethodDetails":
        """Create the object from the dictionary."""
        return RedbrickStorageMethodDetails()
