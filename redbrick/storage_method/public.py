"""Public Storage Method Details."""

from dataclasses import dataclass, field
from typing import Dict, Union, Optional
from redbrick.common.storage_method import StorageMethodDetails


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

    @classmethod
    def from_dict(
        cls, data: Dict  # pylint: disable=unused-argument
    ) -> "PublicStorageMethodDetails":
        """Create the object from the dictionary."""
        return PublicStorageMethodDetails()
