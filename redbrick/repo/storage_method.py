"""Handlers to access APIs for storage methods."""

from typing import Dict, List, Union
from redbrick.common.client import RBClient
from redbrick.common.storage_method import StorageMethodRepoInterface
from redbrick.repo.shards import STORAGE_METHOD_SHARD
from redbrick.types.storage_method import StorageMethodDetailsType


class StorageMethodRepo(StorageMethodRepoInterface):
    """StorageMethodRepo class."""

    def __init__(self, client: RBClient):
        """Construct StorageMethodRepo."""
        self.client = client

    def get_all(self, org_id: str) -> List[Dict]:
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

    def get(self, org_id: str, storage_method_id: str) -> Dict:
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

    def create(
        self,
        org_id: str,
        name: str,
        details: StorageMethodDetailsType,
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
            "provider": details.provider_name,
            "details": {details.provider_key: details.details},
        }
        response = self.client.execute_query(query, variables)
        return response["createStorage"]

    def update(
        self,
        org_id: str,
        storage_method_id: str,
        details: StorageMethodDetailsType,
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
                details.provider_key: details.details,
            },
        }
        response = self.client.execute_query(query, variables)
        return response["updateStorage"]

    def delete(self, org_id: str, storage_method_id: str) -> bool:
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
