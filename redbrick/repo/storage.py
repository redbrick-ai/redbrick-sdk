"""Handlers to access APIs for storage methods."""

from typing import Dict, List
from redbrick.common.client import RBClient
from redbrick.common.storage import StorageRepo

from redbrick.repo.shards import STORAGE_METHOD_SHARD


class StorageRepoImpl(StorageRepo):
    """StorageMethodRepo class."""

    def __init__(self, client: RBClient):
        """Construct StorageMethodRepo."""
        self.client = client

    def get_all(self, org_id: str) -> List[Dict]:
        """Get storage methods."""
        query = f"""
            query storageMethodsSDK($orgId: UUID!) {{
                storageMethods(orgId: $orgId) {{
                    {STORAGE_METHOD_SHARD}
                }}
            }}
        """
        variables = {"orgId": org_id}
        response = self.client.execute_query(query, variables)
        return response["storageMethods"]

    def get(self, org_id: str, storage_id: str) -> Dict:
        """Get a storage method."""
        query = f"""
            query storageMethodSDK($orgId: UUID!, $storageId: UUID!) {{
                storageMethod(orgId: $orgId, storageId: $storageId) {{
                    {STORAGE_METHOD_SHARD}
                }}
            }}
        """
        variables = {"orgId": org_id, "storageId": storage_id}
        response = self.client.execute_query(query, variables)
        return response["storageMethod"]

    def create(self, org_id: str, name: str, provider: str, details: Dict) -> Dict:
        """Create a storage method."""
        query = f"""
            mutation createStorageSDK($orgId: UUID!, $name: String!, $provider: PROVIDER!, $details: StorageDetailsInput) {{
                createStorage(orgId: $orgId, name: $name, provider: $provider, details: $details) {{
                    ok
                    storageMethod {{
                        {STORAGE_METHOD_SHARD}
                    }}
                }}
            }}
        """

        variables = {
            "orgId": org_id,
            "name": name,
            "provider": provider,
            "details": details,
        }
        response = self.client.execute_query(query, variables)
        return response["createStorage"]["storageMethod"]

    def update(self, org_id: str, storage_id: str, details: Dict) -> Dict:
        """Update a storage method."""
        query = f"""
            mutation updateStorageSDK($orgId: UUID!, $storageId: UUID!, $details: StorageDetailsInput) {{
                updateStorage(orgId: $orgId, storageId: $storageId, details: $details) {{
                    ok
                    storageMethod {{
                        {STORAGE_METHOD_SHARD}
                    }}
                }}
            }}
        """
        variables = {
            "orgId": org_id,
            "storageId": storage_id,
            "details": details,
        }
        response = self.client.execute_query(query, variables)
        return response["updateStorage"]["storageMethod"]

    def delete(self, org_id: str, storage_id: str) -> bool:
        """Delete a storage method."""
        query = """
            mutation removeStorageSDK($orgId: UUID!, $storageId: UUID!) {
                removeStorage(orgId: $orgId, storageId: $storageId) {
                    ok
                }
            }
        """
        variables = {"orgId": org_id, "storageId": storage_id}
        response = self.client.execute_query(query, variables)
        return response["removeStorage"]["ok"]

    def presign_path(self, org_id: str, storage_id: str, path: str) -> str:
        """Presign storage method path."""
        query = """
            query presignItemSDK($orgId: UUID!, $storageId: UUID!, $item: String!) {
                presignItem(orgId: $orgId, storageId: $storageId, item: $item)
            }
        """
        variables = {"orgId": org_id, "storageId": storage_id, "item": path}
        response = self.client.execute_query(query, variables)
        return response["presignItem"]
