"""Abstract interface to Labeling APIs."""

from typing import Optional, List, Dict, Sequence, Tuple
import aiohttp

from redbrick.common.client import RBClient
from redbrick.common.labeling import LabelingRepo
from redbrick.types.task import Comment


class LabelingRepoImpl(LabelingRepo):
    """Implementation of manual labeling apis."""

    def __init__(self, client: RBClient) -> None:
        """Construct ExportRepoImpl."""
        self.client = client

    async def presign_labels_path(
        self,
        session: aiohttp.ClientSession,
        org_id: str,
        project_id: str,
        task_id: str,
        version_id: str,
        data_count: int,
        seg_count: int,
    ) -> Tuple[List[Dict], List[Dict]]:
        """Presign labels path."""
        query = """
        query presignUploadsSDK(
            $orgId: UUID!
            $projectId: UUID!
            $filesData: [String!]!
            $fileTypeData: String!
            $fileEncodingData: String
            $filesSeg: [String!]!
            $fileTypeSeg: String!
            $fileEncodingSeg: String
        ) {
            presignData: presignUploads(
                orgId: $orgId
                projectId: $projectId
                files: $filesData
                fileType: $fileTypeData
                fileEncoding: $fileEncodingData
            ) {
                presignedUrl
                filePath
                fileName
            }
            presignSeg: presignUploads(
                orgId: $orgId
                projectId: $projectId
                files: $filesSeg
                fileType: $fileTypeSeg
                fileEncoding: $fileEncodingSeg
            ) {
                presignedUrl
                filePath
                fileName
            }
        }
        """
        variables = {
            "orgId": org_id,
            "projectId": project_id,
            "filesData": (
                [f"labels/{task_id}/{version_id}/data.json"] if data_count == 1 else []
            ),
            "fileTypeData": "application/json",
            "fileEncodingData": "gzip",
            "filesSeg": [
                f"labels/{task_id}/{version_id}/{num}.nii.gz"
                for num in range(0, seg_count)
            ],
            "fileTypeSeg": "application/octet-stream",
            "fileEncodingSeg": None,
        }
        response = await self.client.execute_query_async(session, query, variables)
        return (response["presignData"], response["presignSeg"])

    async def put_labeling_results(
        self,
        session: aiohttp.ClientSession,
        org_id: str,
        project_id: str,
        stage_name: str,
        task_id: str,
        labels_data: Optional[str] = None,
        labels_data_path: Optional[str] = None,
        labels_map: Optional[Sequence[Optional[Dict]]] = None,
        finished: bool = True,
    ) -> None:
        """Put Labeling results."""
        query = """
        mutation putTaskAndLabelsSDK(
            $orgId: UUID!
            $projectId: UUID!
            $stageName: String!
            $taskId: UUID!
            $elapsedTimeMs: Int!
            $finished: Boolean!
            $labelsData: String
            $labelsDataPath: String
            $labelsMap: [LabelMapInput]
        ) {
            putManualLabelingTaskAndLabels(
                orgId: $orgId
                projectId: $projectId
                stageName: $stageName
                taskId: $taskId
                elapsedTimeMs: $elapsedTimeMs
                finished: $finished
                labelsData: $labelsData
                labelsDataPath: $labelsDataPath
                labelsMap: $labelsMap
            ) {
                ok
            }
        }
        """

        variables = {
            "orgId": org_id,
            "projectId": project_id,
            "stageName": stage_name,
            "taskId": task_id,
            "labelsData": labels_data,
            "labelsDataPath": labels_data_path,
            "labelsMap": labels_map,
            "finished": finished,
            "elapsedTimeMs": 0,
        }
        await self.client.execute_query_async(session, query, variables)

    async def put_labeling_task_result(
        self,
        session: aiohttp.ClientSession,
        org_id: str,
        project_id: str,
        stage_name: str,
        task_id: str,
    ) -> None:
        """Put labeling result for task."""
        query = """
        mutation putLabelingTaskSDK(
            $orgId: UUID!
            $projectId: UUID!
            $stageName: String!
            $taskId: UUID!
        ) {
            putManualLabelingTask(
                orgId: $orgId
                projectId: $projectId
                stageName: $stageName
                taskId: $taskId
            ) {
                ok
            }
        }
        """

        variables = {
            "orgId": org_id,
            "projectId": project_id,
            "stageName": stage_name,
            "taskId": task_id,
        }
        await self.client.execute_query_async(session, query, variables)

    async def put_review_task_result(
        self,
        session: aiohttp.ClientSession,
        org_id: str,
        project_id: str,
        stage_name: str,
        task_id: str,
        review_val: bool,
        review_comment: Optional[Comment] = None,
    ) -> None:
        """Put review result for task."""
        query = """
        mutation putReviewTaskSDK(
            $orgId: UUID!
            $projectId: UUID!
            $stageName: String!
            $reviewVal: Boolean!
            $comment: String
            $commentPin: PinInput
            $taskId: UUID!
            $elapsedTimeMs: Int!
        ) {
            putExpertReviewTask(
                orgId: $orgId
                projectId: $projectId
                stageName: $stageName
                reviewVal: $reviewVal
                comment: $comment
                commentPin: $commentPin
                taskId: $taskId
                elapsedTimeMs: $elapsedTimeMs
            ) {
                ok
            }
        }
        """

        variables = {
            "orgId": org_id,
            "projectId": project_id,
            "stageName": stage_name,
            "taskId": task_id,
            "reviewVal": review_val,
            "comment": (
                review_comment.get("text")
                if isinstance(review_comment, dict)
                else review_comment
            ),
            "commentPin": (
                review_comment.get("pin") if isinstance(review_comment, dict) else None
            ),
            "elapsedTimeMs": 0,
        }

        await self.client.execute_query_async(session, query, variables)

    def assign_tasks(
        self,
        org_id: str,
        project_id: str,
        task_ids: List[str],
        emails: Optional[List[str]] = None,
        current_user: bool = False,
        refresh: bool = True,
    ) -> List[Dict]:
        """Assign tasks to specified email or current API key."""
        query_string = """
        mutation assignTasksMultipleUsersSDK(
            $orgId: UUID!
            $projectId: UUID!
            $taskIds: [UUID!]!
            $emails: [String!]
            $currentUser: Boolean
            $refresh: Boolean
        ) {
            assignTasksMultipleUsers(
                orgId: $orgId
                projectId: $projectId
                taskIds: $taskIds
                emails: $emails
                currentUser: $currentUser
                refresh: $refresh
            ) {
                taskId
                name
                stageName
            }
        }
        """

        # EXECUTE THE QUERY
        query_variables = {
            "orgId": org_id,
            "projectId": project_id,
            "taskIds": task_ids,
            "emails": emails,
            "currentUser": current_user,
            "refresh": refresh,
        }

        response = self.client.execute_query(query_string, query_variables)
        tasks: List[Dict] = response["assignTasksMultipleUsers"]
        return tasks

    async def move_task_to_start(
        self,
        session: aiohttp.ClientSession,
        org_id: str,
        project_id: str,
        task_id: str,
    ) -> None:
        """Move groundtruth task back to start."""
        query = """
        mutation moveTaskToStartSDK(
            $orgId: UUID!
            $projectId: UUID!
            $taskId: UUID!
        ) {
            moveTaskToStart(
                orgId: $orgId
                projectId: $projectId
                taskId: $taskId
            ) {
                ok
            }
        }
        """

        variables = {"orgId": org_id, "projectId": project_id, "taskId": task_id}

        await self.client.execute_query_async(session, query, variables)

    def update_model_tasks_state(
        self, org_id: str, project_id: str, task_ids: List[str], action: str
    ) -> None:
        """Update model tasks state."""
        query = """
        mutation updateModelTasksStateSDK(
            $orgId: UUID!
            $projectId: UUID!
            $taskIds: [UUID!]!
            $action: ActiveLearningTaskAction!
        ) {
            updateModelTasksState(
                orgId: $orgId
                projectId: $projectId
                taskIds: $taskIds
                action: $action
            ) {
                ok
            }
        }
        """

        variables = {
            "orgId": org_id,
            "projectId": project_id,
            "taskIds": task_ids,
            "action": action,
        }

        self.client.execute_query(query, variables)
