"""Handlers to access APIs for storage methods."""

from typing import Dict, List
from redbrick.common.client import RBClient
from redbrick.common.enums import StorageProvider
from redbrick.common.storage_method import StorageMethodRepoInterface
from redbrick.repo.shards import STORAGE_METHOD_SHARD
from redbrick.types.storage_method import StorageMethodDetails


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

    def create_storage_method(
        self,
        org_id: str,
        name: str,
        provider: StorageProvider,
        details: StorageMethodDetails,
    ) -> bool:
        """Create a storage method."""
        query = """
            mutation createStorageSDK($orgId: UUID!, $name: String!, $provider: PROVIDER!, $details: StorageDetailsInput){
                createStorage(orgId: $orgId, name: $name, provider: $provider, details: $details){
                ok
                }
            }
        """
        provider_map = {
            StorageProvider.ALTA_DB: "altaDb",
            StorageProvider.AWS_S3: "s3Bucket",
            StorageProvider.AZURE_BLOB: "azureBucket",
            StorageProvider.GCS: "gcsBucket",
        }
        variables = {
            "orgId": org_id,
            "name": name,
            "provider": provider.value,
            "details": {
                provider_map[provider]: details,
            },
        }
        response = self.client.execute_query(query, variables)
        return response["createStorage"]["ok"]
