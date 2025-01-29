"""AltaDB Storage Method Details."""

from dataclasses import dataclass, field
from typing import Dict, Union, Optional
from redbrick.common.storage_method import StorageMethodDetails


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
