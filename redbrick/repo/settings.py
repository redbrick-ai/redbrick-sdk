"""Handlers to access APIs for project settings."""
from typing import Dict

from redbrick.common.client import RBClient
from redbrick.common.settings import (
    SettingsControllerInterface,
    LabelValidation,
    HangingProtocol,
)


class SettingsRepo(SettingsControllerInterface):
    """Class to manage interaction with project settings APIs."""

    def __init__(self, client: RBClient) -> None:
        """Construct SettingsRepo."""
        self.client = client

    def get_label_validation(self, org_id: str, project_id: str) -> LabelValidation:
        """Get project label validation setting."""
        query = """
            query getLabelValidationSDK($orgId: UUID!, $projectId: UUID!) {
                project(orgId: $orgId, projectId: $projectId) {
                    labelValidationSettings {
                        enabled
                        enforce
                        script
                    }
                }
            }
        """
        variables = {"orgId": org_id, "projectId": project_id}
        response: Dict[str, Dict] = self.client.execute_query(query, variables)
        if response.get("project"):
            return response["project"]["labelValidationSettings"]

        raise Exception("Project does not exist")

    def set_label_validation(
        self, org_id: str, project_id: str, label_validation: LabelValidation
    ) -> None:
        """Set project label validation setting."""
        query = """
            mutation setLabelValidationSDK(
                $orgId: UUID!
                $projectId: UUID!
                $enabled: Boolean!
                $enforce: Boolean!
                $script: String
            ) {
                updateLabelValidationSettings(
                    orgId: $orgId
                    projectId: $projectId
                    enabled: $enabled
                    enforce: $enforce
                    script: $script
                ) {
                    ok
                }
            }
        """
        variables = {
            "orgId": org_id,
            "projectId": project_id,
            "enabled": label_validation.get("enabled", False) or False,
            "enforce": label_validation.get("enforce", False) or False,
            "script": label_validation.get("script"),
        }
        self.client.execute_query(query, variables)

    def get_hanging_protocol(self, org_id: str, project_id: str) -> HangingProtocol:
        """Get project hanging protocol setting."""
        query = """
            query getHangingProtocolSDK($orgId: UUID!, $projectId: UUID!) {
                project(orgId: $orgId, projectId: $projectId) {
                    hangingProtocol {
                        enabled
                        script
                    }
                }
            }
        """
        variables = {"orgId": org_id, "projectId": project_id}
        response: Dict[str, Dict] = self.client.execute_query(query, variables)
        if response.get("project"):
            return response["project"]["hangingProtocol"]

        raise Exception("Project does not exist")

    def set_hanging_protocol(
        self, org_id: str, project_id: str, hanging_protocol: HangingProtocol
    ) -> None:
        """Set project hanging protocol setting."""
        query = """
            mutation setHangingProtocolSDK(
                $orgId: UUID!
                $projectId: UUID!
                $enabled: Boolean!
                $script: String
            ) {
                updateHangingProtocolScript(
                    orgId: $orgId
                    projectId: $projectId
                    enabled: $enabled
                    script: $script
                ) {
                    ok
                }
            }
        """
        variables = {
            "orgId": org_id,
            "projectId": project_id,
            "enabled": hanging_protocol.get("enabled", False) or False,
            "script": hanging_protocol.get("script"),
        }
        self.client.execute_query(query, variables)

    def toggle_reference_standard_task(
        self, org_id: str, project_id: str, task_id: str, enable: bool
    ) -> None:
        """Toggle reference standard task."""
        query = """
            mutation toggleReferenceStandardTaskSDK(
                $orgId: UUID!
                $projectId: UUID!
                $taskId: UUID!
                $enable: Boolean!
            ) {
                toggleReferenceStandardTask(
                    orgId: $orgId
                    projectId: $projectId
                    taskId: $taskId
                    enable: $enable
                ) {
                    ok
                }
            }
        """
        variables = {
            "orgId": org_id,
            "projectId": project_id,
            "taskId": task_id,
            "enable": enable,
        }
        self.client.execute_query(query, variables)
