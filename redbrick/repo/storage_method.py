"""Handlers to access APIs for storage methods."""

from typing import Dict, List, Union
from redbrick.common.client import RBClient
from redbrick.common.enums import StorageProvider
from redbrick.common.storage_method import StorageMethodRepoInterface
from redbrick.repo.shards import STORAGE_METHOD_SHARD
from redbrick.types.storage_method import StorageMethodDetails


PROVIDER_MAP = {
    StorageProvider.ALTA_DB: "altaDb",
    StorageProvider.AWS_S3: "s3Bucket",
    StorageProvider.AZURE_BLOB: "azureBucket",
    StorageProvider.GCS: "gcsBucket",
}


class StorageMethodRepo(StorageMethodRepoInterface):
    """StorageMethodRepo class."""

    def __init__(self, client: RBClient):
        """Construct StorageMethodRepo."""
        self.client = client

    def get_storage_methods(self, org_id: str) -> List[Dict]:
        """Get storage methods."""
        query = f"""
            query listStorageMethodsSDK($orgId: UUID!) {{
                storageMethods(orgId: $orgId) {{
                    {STORAGE_METHOD_SHARD}
                }}
            }}
        """
        variables = {"orgId": org_id}
        response = self.client.execute_query(query, variables)
        return response["storageMethods"]

    def get_storage_method(self, org_id: str, storage_method_id: str) -> Dict:
        """Get a storage method."""
        query = f"""
            query getStorageSDK($orgId: UUID!, $storageId: UUID!) {{
                storageMethod(orgId: $orgId, storageId: $storageId) {{
                    {STORAGE_METHOD_SHARD}
                }}
            }}
        """
        variables = {"orgId": org_id, "storageId": storage_method_id}
        response = self.client.execute_query(query, variables)
        return response["storageMethod"]

    def create_storage_method(
        self,
        org_id: str,
        name: str,
        provider: StorageProvider,
        details: StorageMethodDetails,
    ) -> Dict[str, Union[bool, Dict]]:
        """Create a storage method."""
        query = f"""
            mutation createStorageSDK($orgId: UUID!, $name: String!, $provider: PROVIDER!, $details: StorageDetailsInput){{
                createStorage(orgId: $orgId, name: $name, provider: $provider, details: $details){{
                    ok
                    storageMethod{{
                        {STORAGE_METHOD_SHARD}
                    }}
                }}
            }}
        """

        variables = {
            "orgId": org_id,
            "name": name,
            "provider": provider.value,
            "details": {
                PROVIDER_MAP[provider]: details,
            },
        }
        response = self.client.execute_query(query, variables)
        return response["createStorage"]

    def update_storage_method(
        self,
        org_id: str,
        storage_method_id: str,
        provider: StorageProvider,
        details: StorageMethodDetails,
    ) -> Dict[str, Union[bool, Dict]]:
        """Update a storage method."""
        query = f"""
            mutation updateStorage($orgId: UUID!, $storageId: UUID!, $details: StorageDetailsInput){{
                updateStorage(orgId: $orgId, storageId: $storageId, details: $details){{
                    ok
                    storageMethod{{
                        {STORAGE_METHOD_SHARD}
                    }}
                }}
            }}
        """
        variables = {
            "orgId": org_id,
            "storageId": storage_method_id,
            "details": {
                PROVIDER_MAP[provider]: details,
            },
        }
        response = self.client.execute_query(query, variables)
        return response["updateStorage"]

    def delete_storage_method(self, org_id: str, storage_method_id: str) -> bool:
        """Delete a storage method."""
        query = """
            mutation removeStorageSDK($orgId: UUID!, $storageId: UUID!){
                removeStorage(orgId: $orgId, storageId: $storageId){
                    ok
                }
            }
        """
        variables = {"orgId": org_id, "storageId": storage_method_id}
        response = self.client.execute_query(query, variables)
        return response["removeStorage"]["ok"]
