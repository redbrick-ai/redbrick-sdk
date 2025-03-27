"""Handlers to access APIs for getting workspaces."""

import json
from typing import Dict, List, Optional, Tuple

from redbrick.common.client import RBClient
from redbrick.common.workspace import WorkspaceRepo
from redbrick.repo.shards import WORKSPACE_SHARD, datapoint_shard


class WorkspaceRepoImpl(WorkspaceRepo):
    """Class to manage interaction with workspace APIs."""

    def __init__(self, client: RBClient) -> None:
        """Construct WorkspaceRepoImpl."""
        self.client = client

    def get_workspaces(self, org_id: str) -> List[Dict]:
        """Get list of workspaces."""
        query = f"""
            query sdkGetWorkspacesSDK($orgId: UUID!) {{
                workspaces(orgId: $orgId) {{
                    {WORKSPACE_SHARD}
                }}
            }}
        """
        variables = {"orgId": org_id}
        response: Dict[str, List[Dict]] = self.client.execute_query(query, variables)
        return response["workspaces"]

    def get_workspace(self, org_id: str, workspace_id: str) -> Dict:
        """
        Get workspace name and status.

        Raise an exception if workspace does not exist.
        """
        query = f"""
            query sdkGetWorkspaceSDK($orgId: UUID!, $workspaceId: UUID!) {{
                workspace(orgId: $orgId, workspaceId: $workspaceId) {{
                    {WORKSPACE_SHARD}
                }}
            }}
        """
        variables = {"orgId": org_id, "workspaceId": workspace_id}
        response: Dict[str, Dict] = self.client.execute_query(query, variables)
        if response.get("workspace"):
            return response["workspace"]

        raise Exception("Workspace does not exist")

    def create_workspace(
        self, org_id: str, workspace_name: str, exists_okay: bool = False
    ) -> Dict:
        """
        Create a workspace.

        Raise an exception if workspace already exists.
        """
        query = f"""
            mutation sdkCreateWorkspaceSDK($orgId: UUID!, $name: String!) {{
                createWorkspace(orgId: $orgId, name: $name) {{
                    {WORKSPACE_SHARD}
                }}
            }}
        """
        variables = {"orgId": org_id, "name": workspace_name}
        response: Dict[str, Dict] = self.client.execute_query(query, variables)
        if response.get("createWorkspace"):
            return response["createWorkspace"]

        if exists_okay:
            return self.get_workspace(org_id, workspace_name)

        raise Exception("Workspace already exists")

    def update_schema(
        self,
        org_id: str,
        workspace_id: str,
        metadata_schema: Optional[List[Dict]],
        classification_schema: Optional[List[Dict]],
    ) -> None:
        """Update workspace metadata and classification schema."""
        query = """
            mutation updateWorkspaceSchemaSDK(
                $orgId: UUID!
                $workspaceId: UUID!
                $metadataSchema: [MetadataSchemaInput!]
                $classificationSchema: [NewAttributeInput!]
            ) {
                updateWorkspaceSchema(
                    orgId: $orgId
                    workspaceId: $workspaceId
                    metadataSchema: $metadataSchema
                    classificationSchema: $classificationSchema
                ) {
                    ok
                }
            }
        """
        variables = {
            "orgId": org_id,
            "workspaceId": workspace_id,
            "metadataSchema": metadata_schema,
            "classificationSchema": classification_schema,
        }
        self.client.execute_query(query, variables)

    def update_cohorts(
        self, org_id: str, workspace_id: str, cohorts: List[Dict]
    ) -> None:
        """Update workspace cohorts."""
        query = """
            mutation updateWorkspaceCohortsSDK(
                $orgId: UUID!
                $workspaceId: UUID!
                $cohorts: [CohortInput!]!
            ) {
                updateWorkspaceCohorts(
                    orgId: $orgId
                    workspaceId: $workspaceId
                    cohorts: $cohorts
                ) {
                    name
                    color
                    createdBy
                    createdAt
                }
            }
        """
        variables = {
            "orgId": org_id,
            "workspaceId": workspace_id,
            "cohorts": cohorts,
        }
        self.client.execute_query(query, variables)

    def get_datapoints(
        self,
        org_id: str,
        workspace_id: str,
        first: int = 50,
        after: Optional[str] = None,
    ) -> Tuple[List[Dict], Optional[str]]:
        """Get datapoints for a workspace."""
        query_string = f"""
        query workspaceDatapointsSDK(
            $orgId: UUID!
            $workspaceId: UUID!
            $first: Int!
            $after: String
            $counts: Boolean!
            $items: Boolean!
        ) {{
            workspace(orgId: $orgId, workspaceId: $workspaceId) {{
                dataPoints(first: $first, after: $after, counts: $counts, items: $items) {{
                    entries {{
                        {datapoint_shard(True, True)}
                    }}
                    cursor
                }}
            }}
        }}
        """
        # EXECUTE THE QUERY
        query_variables = {
            "orgId": org_id,
            "workspaceId": workspace_id,
            "first": first,
            "after": after,
            "counts": False,
            "items": True,
        }

        result = self.client.execute_query(query_string, query_variables, False)
        dp_paged = (result.get("workspace", {}) or {}).get("dataPoints", {}) or {}
        entries: List[Dict] = dp_paged.get("entries", []) or []  # type: ignore
        return entries, dp_paged.get("cursor")

    def toggle_datapoints_archived_status(
        self, org_id: str, dp_ids: List[str], archived: bool
    ) -> None:
        """Toggle archived status for datapoints."""
        query = """
            mutation toggleDatapointArchivedStatusSDK($orgId: UUID!, $dpIds: [UUID!]!, $archived: Boolean!) {
                toggleDatapointArchivedStatus(orgId: $orgId, dpIds: $dpIds, archived: $archived) {
                    ok
                    message
                }
            }
        """
        variables = {
            "orgId": org_id,
            "dpIds": dp_ids,
            "archived": archived,
        }
        self.client.execute_query(query, variables)

    def toggle_datapoints_cohorts(
        self,
        org_id: str,
        workspace_id: str,
        cohort_name: str,
        dp_ids: List[str],
        include: bool,
    ) -> None:
        """Toggle cohort membership for workspace datapoints."""
        query = """
            mutation toggleCohortDatapointsSDK($orgId: UUID!, $workspaceId: UUID!, $name: String!, $dpIds: [UUID!]!, $include: Boolean!) {
                toggleCohortDatapoints(orgId: $orgId, workspaceId: $workspaceId, name: $name, dpIds: $dpIds, include: $include) {
                    ok
                    message
                }
            }
        """
        variables = {
            "orgId": org_id,
            "workspaceId": workspace_id,
            "name": cohort_name,
            "dpIds": dp_ids,
            "include": include,
        }
        self.client.execute_query(query, variables)

    def update_datapoint_attributes(
        self, org_id: str, dp_id: str, attributes: List[Dict]
    ) -> None:
        """Update datapoint attributes."""
        query = """
        mutation updateDatapointAttributesSDK($orgId: UUID!, $dpId: UUID!, $attributes: JSONString!) {
            updateDatapointAttributes(orgId: $orgId, dpId: $dpId, attributes: $attributes) {
                ok
                message
            }
        }
        """
        variables = {
            "orgId": org_id,
            "dpId": dp_id,
            "attributes": json.dumps(attributes),
        }
        self.client.execute_query(query, variables)

    def add_datapoints_to_projects(
        self,
        org_id: str,
        workspace_id: str,
        project_ids: List[str],
        dp_ids: List[str],
        ground_truth: bool,
    ) -> None:
        """Add datapoints to project."""
        query = """
        mutation importDatapointsFromWorkspaceSDK(
            $orgId: UUID!
            $workspaceId: UUID!
            $projectIds: [UUID!]!
            $dpIds: [UUID!]!
            $isGroundTruth: Boolean
        ) {
            importDatapointsFromWorkspace(
                orgId: $orgId
                workspaceId: $workspaceId
                projectIds: $projectIds
                dpIds: $dpIds
                isGroundTruth: $isGroundTruth
            ) {
                ok
                message
            }
        }
        """
        variables = {
            "orgId": org_id,
            "workspaceId": workspace_id,
            "projectIds": project_ids,
            "dpIds": dp_ids,
            "isGroundTruth": ground_truth,
        }
        self.client.execute_query(query, variables)
