"""Handlers to access APIs for getting datasets."""

from typing import Dict

from redbrick.common.client import RBClient
from redbrick.common.dataset import DatasetRepo


class DatasetRepoImpl(DatasetRepo):
    """Class to manage interaction with workspace APIs."""

    def __init__(self, client: RBClient) -> None:
        """Construct DatasetRepoImpl."""
        self.client = client

    def get_dataset(self, org_id: str, dataset_name: str) -> Dict:
        """Get a dataset."""
        query = """
            query sdkDataStore($orgId: UUID!, $name: String!) {
                dataStore(orgId: $orgId, name: $name) {
                    orgId
                    name
                    displayName
                    createdAt
                    createdBy
                    status
                    updatedAt
                    importStatuses
                }
            }
        """
        variables = {"orgId": org_id, "name": dataset_name}
        response: Dict[str, Dict] = self.client.execute_query(query, variables)
        if response.get("dataStore"):
            return response["dataStore"]

        raise Exception("Dataset does not exist")

    def create_dataset(self, org_id: str, dataset_name: str) -> Dict:
        """Create a dataset."""
        query = """
            mutation sdkCreateDatastore($orgId: UUID!, $dataStore: String!, $displayName: String!) {
                createDatastore(orgId: $orgId, dataStore: $dataStore, displayName: $displayName) {
                    orgId
                    name
                    displayName
                    createdAt
                    createdBy
                    status
                    updatedAt
                    importStatuses
                }
            }
        """
        variables = {
            "orgId": org_id,
            "dataStore": dataset_name,
            "displayName": dataset_name,
        }
        response: Dict[str, Dict] = self.client.execute_query(query, variables)
        return response["createDatastore"]

    def delete_dataset(self, org_id: str, dataset_name: str) -> bool:
        """Delete a dataset."""
        query_string = """
            mutation removeDatastoreSDK($orgId: UUID!, $dataStores: [String!]!) {
                removeDatastore(orgId: $orgId, dataStores: $dataStores) {
                    ok
                    message
                }
            }
        """
        query_variables = {
            "orgId": org_id,
            "dataStores": [dataset_name],
        }
        result = self.client.execute_query(query_string, query_variables)
        return result["removeDatastore"]["ok"]
