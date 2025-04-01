"""Interface for getting information about storage methods."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Type


@dataclass
class StorageProvider:
    """Base storage provider.

    Sub-classes:
    -------------
    - redbrick.StorageMethod.Public (:obj:`~redbrick.StorageMethod.Public`)
    - redbrick.StorageMethod.RedBrick (:obj:`~redbrick.StorageMethod.RedBrick`)
    - redbrick.StorageMethod.AWSS3 (:obj:`~redbrick.StorageMethod.AWSS3`)
    - redbrick.StorageMethod.GoogleCloud (:obj:`~redbrick.StorageMethod.GoogleCloud`)
    - redbrick.StorageMethod.AzureBlob (:obj:`~redbrick.StorageMethod.AzureBlob`)
    - redbrick.StorageMethod.AltaDB (:obj:`~redbrick.StorageMethod.AltaDB`)
    """

    @dataclass
    class Details:
        """Storage details."""

        @property
        @abstractmethod
        def key(self) -> str:
            """Storage proivder details key."""

        @classmethod
        @abstractmethod
        def from_entity(
            cls, entity: Optional[Dict[str, Any]] = None
        ) -> "StorageProvider.Details":
            """Get object from entity"""

        @abstractmethod
        def to_entity(self) -> Dict[str, Any]:
            """Get entity from object."""

        @abstractmethod
        def validate(self, check_secrets: bool = False) -> None:
            """Validate storage provider details."""

    PROVIDER: str = field(default="", init=False)  # pylint: disable=invalid-name

    storage_id: str
    name: str
    details: Details

    @classmethod
    def from_entity(cls, entity: Dict) -> "StorageProvider":
        """Get object from entity"""
        return cls(
            storage_id=entity["storageId"],
            name=entity["name"],
            details=cls.Details.from_entity(entity.get("details")),
        )


class StorageMethod:
    """Storage method integration for organizations.

    - ``PUBLIC`` - Access files from a public cloud storage service using their absolute URLs.
                        (i.e. files available publicly)
    - ``REDBRICK`` - Access files stored on RedBrick AI's servers.
                        (i.e. files uploaded directly to RBAI from a local machine)
    - ``ALTA_DB`` - Access files stored on AltaDB.


    Storage methods:
    ----------------
    - redbrick.StorageMethod.Public (:obj:`~redbrick.StorageMethod.Public`)
    - redbrick.StorageMethod.RedBrick (:obj:`~redbrick.StorageMethod.RedBrick`)
    - redbrick.StorageMethod.AWSS3 (:obj:`~redbrick.StorageMethod.AWSS3`)
    - redbrick.StorageMethod.GoogleCloud (:obj:`~redbrick.StorageMethod.GoogleCloud`)
    - redbrick.StorageMethod.AzureBlob (:obj:`~redbrick.StorageMethod.AzureBlob`)
    - redbrick.StorageMethod.AltaDB (:obj:`~redbrick.StorageMethod.AltaDB`)
    """

    PUBLIC = "11111111-1111-1111-1111-111111111111"
    REDBRICK = "22222222-2222-2222-2222-222222222222"
    ALTA_DB = "33333333-3333-3333-3333-333333333333"

    @dataclass
    class Public(StorageProvider):
        """Public storage provider (Sub class of :obj:`~redbrick.StorageProvider`).

        :cvar str storage_id: ``redbrick.StorageMethod.PUBLIC``
        :cvar str name: ``"Public"``
        :cvar `redbrick.StorageMethod.Public.Details` details: Public storage method details.
        """

        @dataclass
        class Details(StorageProvider.Details):
            """Public storage provider details."""

            @property
            def key(self) -> str:
                """Public storage proivder details key."""
                raise TypeError("You cannot create/update Public storage")

            @classmethod
            def from_entity(
                cls, entity: Optional[Dict[str, Any]] = None
            ) -> "StorageMethod.Public.Details":
                """Get object from entity"""
                return cls()

            @abstractmethod
            def to_entity(self) -> Dict[str, Any]:
                """Get entity from object."""
                raise TypeError("You cannot create/update Public storage")

            def validate(self, check_secrets: bool = False) -> None:
                """Validate Public storage provider details."""

        PROVIDER: str = field(default="PUBLIC", init=False)

        storage_id: str = field(
            default="11111111-1111-1111-1111-111111111111", init=False
        )
        name: str = field(default="Public", init=False)
        details: StorageProvider.Details = field(
            default_factory=Details.from_entity, init=False
        )

        def __setattr__(self, key: str, value: Any) -> None:
            """Set attribute."""
            if key in ("PROVIDER", "storage_id", "name"):
                raise AttributeError(f"Cannot modify {key} for Public storage")

            super().__setattr__(key, value)

        @classmethod
        def from_entity(cls, entity: Dict) -> "StorageMethod.Public":
            """Get object from entity"""
            return cls()

    @dataclass
    class RedBrick(StorageProvider):
        """RedBrick storage provider (Sub class of :obj:`~redbrick.StorageProvider`).

        :cvar str storage_id: ``redbrick.StorageMethod.REDBRICK``
        :cvar str name: ``"Direct Upload"``
        :cvar `redbrick.StorageMethod.RedBrick.Details` details: RedBrick storage method details.
        """

        @dataclass
        class Details(StorageProvider.Details):
            """RedBrick storage provider details."""

            @property
            def key(self) -> str:
                """RedBrick storage proivder details key."""
                raise TypeError("You cannot create/update RedBrick storage")

            @classmethod
            def from_entity(
                cls, entity: Optional[Dict[str, Any]] = None
            ) -> "StorageMethod.RedBrick.Details":
                """Get object from entity"""
                return cls()

            @abstractmethod
            def to_entity(self) -> Dict[str, Any]:
                """Get entity from object."""
                raise TypeError("You cannot create/update RedBrick storage")

            def validate(self, check_secrets: bool = False) -> None:
                """Validate RedBrick storage provider details."""

        PROVIDER: str = field(default="REDBRICK", init=False)

        storage_id: str = field(
            default="22222222-2222-2222-2222-222222222222", init=False
        )
        name: str = field(default="Direct Upload", init=False)
        details: StorageProvider.Details = field(
            default_factory=Details.from_entity, init=False
        )

        def __setattr__(self, key: str, value: Any) -> None:
            """Set attribute."""
            if key in ("PROVIDER", "storage_id", "name"):
                raise AttributeError(f"Cannot modify {key} for RedBrick storage")

            super().__setattr__(key, value)

        @classmethod
        def from_entity(cls, entity: Dict) -> "StorageMethod.RedBrick":
            """Get object from entity"""
            return cls()

    @dataclass
    class AWSS3(StorageProvider):
        """AWS S3 storage provider (Sub class of :obj:`~redbrick.StorageProvider`).

        :ivar str storage_id: AWS S3 storage id.
        :ivar str name: AWS S3 storage name.
        :ivar `redbrick.StorageMethod.AWSS3.Details` details: AWS S3 storage method details.
        """

        @dataclass
        class Details(StorageProvider.Details):
            """AWS S3 storage provider details.

            :ivar str bucket: AWS S3 bucket.
            :ivar str region: AWS S3 region.
            :ivar bool transfer_acceleration: AWS S3 transfer acceleration.
            :ivar str endpoint: Custom endpoint (For S3 compatible storage, e.g. MinIO).
            :ivar str access_key_id: AWS access key id.
            :ivar str secret_access_key: AWS secret access key. (Will be None in output for security reasons)
            :ivar str role_arn: AWS assume_role ARN. (For short-lived credentials instead of access keys)
            :ivar str role_external_id: AWS assume_role external id. (Will be None in output for security reasons)
            :ivar int session_duration: AWS S3 assume_role session duration.
            """

            bucket: str
            region: str
            transfer_acceleration: bool = False
            endpoint: Optional[str] = None

            access_key_id: Optional[str] = None
            secret_access_key: Optional[str] = None

            role_arn: Optional[str] = None
            role_external_id: Optional[str] = None
            session_duration: int = 3600

            @property
            def key(self) -> str:
                """AWS S3 storage proivder details key."""
                return "s3Bucket"

            @classmethod
            def from_entity(
                cls, entity: Optional[Dict[str, Any]] = None
            ) -> "StorageMethod.AWSS3.Details":
                """Get object from entity"""
                if entity is None:
                    raise ValueError("Invalid details for AWS S3 storage")

                details = cls(
                    bucket=entity["bucket"],
                    region=entity["region"],
                    transfer_acceleration=entity.get("accelerate", False),
                    endpoint=entity.get("endpoint"),
                    access_key_id=entity.get("access"),
                    secret_access_key=entity.get("secret"),
                    role_arn=entity.get("roleArn"),
                    role_external_id=entity.get("roleExternalId"),
                    session_duration=entity.get("duration", 3600),
                )
                details.validate()
                return details

            @abstractmethod
            def to_entity(self) -> Dict[str, Any]:
                """Get entity from object."""
                self.validate(True)
                return {
                    "bucket": self.bucket,
                    "region": self.region,
                    "accelerate": self.transfer_acceleration,
                    "endpoint": self.endpoint,
                    "access": self.access_key_id,
                    "secret": self.secret_access_key,
                    "roleArn": self.role_arn,
                    "roleExternalId": self.role_external_id,
                    "duration": self.session_duration,
                }

            def validate(self, check_secrets: bool = False) -> None:
                """Validate AWS S3 storage provider details."""
                if not self.bucket:
                    raise ValueError("bucket is required in AWS S3 storage")

                if not self.region:
                    raise ValueError("region is required in AWS S3 storage")

                if not (bool(self.access_key_id) ^ bool(self.role_arn)):
                    raise ValueError(
                        "Either one of access_key_id or role_arn is required in AWS S3 storage"
                    )

                if check_secrets:
                    if self.access_key_id:
                        if self.role_external_id:
                            raise ValueError(
                                "role_external_id cannot be used with access_key_id in AWS S3 storage"
                            )
                        if not self.secret_access_key:
                            raise ValueError(
                                "secret_access_key is required with access_key_id in AWS S3 storage"
                            )

                    if self.role_arn:
                        if self.secret_access_key:
                            raise ValueError(
                                "secret_access_key cannot be used with role_arn in AWS S3 storage"
                            )
                        if not self.role_external_id:
                            raise ValueError(
                                "role_external_id is required with role_arn in AWS S3 storage"
                            )

            def __post_init__(self) -> None:
                """Post init validation."""
                self.validate()

        PROVIDER: str = field(default="AWS_S3", init=False)

        def __setattr__(self, key: str, value: Any) -> None:
            """Set attribute."""
            if key in ("PROVIDER",):
                raise AttributeError(f"Cannot modify {key} for AWSS3 storage")

            super().__setattr__(key, value)

    @dataclass
    class GoogleCloud(StorageProvider):
        """Google cloud storage provider (Sub class of :obj:`~redbrick.StorageProvider`).

        :ivar str storage_id: Google cloud storage id.
        :ivar str name: Google cloud storage name.
        :ivar `redbrick.StorageMethod.GoogleCloud.Details` details: Google cloud storage method details.
        """

        @dataclass
        class Details(StorageProvider.Details):
            """Google cloud storage provider details.

            :ivar str bucket: GCS bucket.
            :ivar str service_account_json: GCS service account JSON. (Will be None in output for security reasons)
            """

            bucket: str
            service_account_json: Optional[str] = None

            @property
            def key(self) -> str:
                """Google cloud storage proivder details key."""
                return "gcsBucket"

            @classmethod
            def from_entity(
                cls, entity: Optional[Dict[str, Any]] = None
            ) -> "StorageMethod.GoogleCloud.Details":
                """Get object from entity"""
                if entity is None:
                    raise ValueError("Invalid details for Google cloud storage")

                details = cls(
                    bucket=entity["bucket"],
                    service_account_json=entity.get("serviceAccount"),
                )
                details.validate()
                return details

            @abstractmethod
            def to_entity(self) -> Dict[str, Any]:
                """Get entity from object."""
                self.validate(True)
                return {
                    "bucket": self.bucket,
                    "serviceAccount": self.service_account_json,
                }

            def validate(self, check_secrets: bool = False) -> None:
                """Validate Google cloud storage provider details."""
                if not self.bucket:
                    raise ValueError("bucket is required in Google cloud storage")

                if check_secrets:
                    if not self.service_account_json:
                        raise ValueError(
                            "service_account_json is required in Google cloud storage"
                        )

            def __post_init__(self) -> None:
                """Post init validation."""
                self.validate()

        PROVIDER: str = field(default="GCS", init=False)

        def __setattr__(self, key: str, value: Any) -> None:
            """Set attribute."""
            if key in ("PROVIDER",):
                raise AttributeError(f"Cannot modify {key} for GoogleCloud storage")

            super().__setattr__(key, value)

    @dataclass
    class AzureBlob(StorageProvider):
        """Azure blob storage provider (Sub class of :obj:`~redbrick.StorageProvider`).

        :ivar str storage_id: Azure blob storage id.
        :ivar str name: Azure blob storage name.
        :ivar `redbrick.StorageMethod.AzureBlob.Details` details: Azure blob storage method details.
        """

        @dataclass
        class Details(StorageProvider.Details):
            """Azure blob storage provider details.

            :ivar str connection_string: Azure connection string. (Will be None in output for security reasons)
            :ivar str sas_url: Azure Shared Access Signature URL for granular blob access. (Will be None in output for security reasons)
            """

            connection_string: Optional[str] = None
            sas_url: Optional[str] = None

            @property
            def key(self) -> str:
                """Azure blob storage proivder details key."""
                return "azureBucket"

            @classmethod
            def from_entity(
                cls, entity: Optional[Dict[str, Any]] = None
            ) -> "StorageMethod.AzureBlob.Details":
                """Get object from entity"""
                if entity is None:
                    raise ValueError("Invalid details for Azure blob storage")

                details = cls(
                    connection_string=entity.get("connectionString"),
                    sas_url=entity.get("sasUrl"),
                )
                details.validate()
                return details

            @abstractmethod
            def to_entity(self) -> Dict[str, Any]:
                """Get entity from object."""
                self.validate(True)
                return {
                    "connectionString": self.connection_string,
                    "sasUrl": self.sas_url,
                }

            def validate(self, check_secrets: bool = False) -> None:
                """Validate Azure blob storage provider details."""
                if check_secrets:
                    if not (bool(self.connection_string) ^ bool(self.sas_url)):
                        raise ValueError(
                            "Either one of connection_string or sas_url is required in Azure blob storage"
                        )

            def __post_init__(self) -> None:
                """Post init validation."""
                self.validate()

        PROVIDER: str = field(default="AZURE_BLOB", init=False)

        def __setattr__(self, key: str, value: Any) -> None:
            """Set attribute."""
            if key in ("PROVIDER",):
                raise AttributeError(f"Cannot modify {key} for AzureBlob storage")

            super().__setattr__(key, value)

    @dataclass
    class AltaDB(StorageProvider):
        """AltaDB storage provider (Sub class of :obj:`~redbrick.StorageProvider`).

        :cvar str storage_id: ``redbrick.StorageMethod.ALTA_DB``
        :cvar str name: ``"Alta DB"``
        :cvar `redbrick.StorageMethod.AltaDB.Details` details: AltaDB storage method details.
        """

        @dataclass
        class Details(StorageProvider.Details):
            """AltaDB storage provider details."""

            @property
            def key(self) -> str:
                """AltaDB storage proivder details key."""
                raise TypeError("You cannot create/update AltaDB storage")

            @classmethod
            def from_entity(
                cls, entity: Optional[Dict[str, Any]] = None
            ) -> "StorageMethod.AltaDB.Details":
                """Get object from entity"""
                return cls()

            @abstractmethod
            def to_entity(self) -> Dict[str, Any]:
                """Get entity from object."""
                raise TypeError("You cannot create/update AltaDB storage")

            def validate(self, check_secrets: bool = False) -> None:
                """Validate AltaDB storage provider details."""

        PROVIDER: str = field(default="ALTA_DB", init=False)

        storage_id: str = field(
            default="33333333-3333-3333-3333-333333333333", init=False
        )
        name: str = field(default="Alta DB", init=False)
        details: StorageProvider.Details = field(
            default_factory=Details.from_entity, init=False
        )

        def __setattr__(self, key: str, value: Any) -> None:
            """Set attribute."""
            if key in ("PROVIDER", "storage_id", "name"):
                raise AttributeError(f"Cannot modify {key} for AltaDB storage")

            super().__setattr__(key, value)

        @classmethod
        def from_entity(cls, entity: Dict) -> "StorageMethod.AltaDB":
            """Get object from entity"""
            return cls()


STORAGE_PROVIDERS: Dict[str, Type[StorageProvider]] = {
    storage.PROVIDER: storage for storage in StorageProvider.__subclasses__()
}


class StorageRepo(ABC):
    """Abstract interface to Storage Method APIs."""

    @abstractmethod
    def get_all(self, org_id: str) -> List[Dict]:
        """Get storage methods."""

    @abstractmethod
    def get(self, org_id: str, storage_id: str) -> Dict:
        """Get a storage method."""

    @abstractmethod
    def create(self, org_id: str, name: str, provider: str, details: Dict) -> Dict:
        """Create a storage method."""

    @abstractmethod
    def update(self, org_id: str, storage_id: str, details: Dict) -> Dict:
        """Update a storage method."""

    @abstractmethod
    def delete(self, org_id: str, storage_id: str) -> bool:
        """Delete a storage method."""

    @abstractmethod
    def presign_path(self, org_id: str, storage_id: str, path: str) -> str:
        """Presign storage method path."""


class Storage(ABC):
    """Storage Method Controller."""

    @abstractmethod
    def get_storage(self, storage_id: str) -> StorageProvider:
        """Get a storage method by ID."""

    @abstractmethod
    def list_storages(self) -> List[StorageProvider]:
        """Get a list of storage methods in the organization."""

    @abstractmethod
    def create_storage(self, storage: StorageProvider) -> StorageProvider:
        """Create a storage method."""

    @abstractmethod
    def update_storage(
        self, storage_id: str, details: StorageProvider.Details
    ) -> StorageProvider:
        """Update a storage method."""

    @abstractmethod
    def delete_storage(self, storage_id: str) -> bool:
        """Delete a storage method."""

    @abstractmethod
    def verify_storage(self, storage_id: str, path: str) -> bool:
        """Verify a storage method by ID."""
