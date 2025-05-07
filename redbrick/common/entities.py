"""Abstract interfaces to entities."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, Iterator, Optional, List, Sequence, Tuple, Union

from redbrick.types.task import InputTask
from redbrick.types.taxonomy import Attribute, ObjectType, Taxonomy
from redbrick.common.context import RBContext
from redbrick.common.stage import Stage
from redbrick.common.upload import Upload, DatasetUpload
from redbrick.common.labeling import Labeling
from redbrick.common.export import Export, DatasetExport
from redbrick.common.settings import Settings
from redbrick.common.member import Team, Workforce
from redbrick.common.storage import Storage


class RBOrganization(ABC):
    """
    Representation of RedBrick organization.

    The :attr:`redbrick.RBOrganization` object allows you to programmatically interact with
    your RedBrick organization. This class provides methods for querying your
    organization and doing other high level actions. Retrieve the organization object in the following way:

    :ivar `redbrick.common.member.Team` team: Organization team management.
    :ivar `redbrick.common.storage.Storage` storage: Organization storage methods integration.

    .. code:: python

        >>> org = redbrick.get_org(org_id="", api_key="")
    """

    context: RBContext

    team: Team
    storage: Storage

    @property
    @abstractmethod
    def org_id(self) -> str:
        """Retrieve the unique org_id of this organization."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Retrieve unique name of this organization."""

    @abstractmethod
    def taxonomies(self, only_name: bool = True) -> Union[List[str], List[Taxonomy]]:
        """Get a list of taxonomy names/objects in the organization."""

    @abstractmethod
    def workspaces_raw(self) -> List[Dict]:
        """Get a list of active workspaces as raw objects in the organization."""

    @abstractmethod
    def projects_raw(self) -> List[Dict]:
        """Get a list of active projects as raw objects in the organization."""

    @abstractmethod
    def projects(self) -> List["RBProject"]:
        """Get a list of active projects in the organization."""

    @abstractmethod
    def create_dataset(self, dataset_name: str) -> Dict:
        """Create a new dataset."""

    @abstractmethod
    def get_dataset(self, dataset_name: str) -> Dict:
        """
        Get dataset name and status.

        Raise an exception if dataset does not exist.
        """

    @abstractmethod
    def delete_dataset(self, dataset_name: str) -> bool:
        """Delete a dataset."""

    @abstractmethod
    def create_workspace(self, name: str, exists_okay: bool = False) -> "RBWorkspace":
        """
        Create a workspace within the organization.

        This method creates a worspace in a similar fashion to the
        quickstart on the RedBrick AI create workspace page.

        Parameters
        --------------
        name: str
            A unique name for your workspace

        exists_okay: bool = False
            Allow workspaces with the same name to be returned instead of trying to create
            a new workspace. Useful for when running the same script repeatedly when you
            do not want to keep creating new workspaces.

        Returns
        --------------
        redbrick.RBWorkspace
            A RedBrick Workspace object.
        """

    @abstractmethod
    def create_project_advanced(
        self,
        name: str,
        taxonomy_name: str,
        stages: Sequence[Stage],
        exists_okay: bool = False,
        workspace_id: Optional[str] = None,
        sibling_tasks: Optional[int] = None,
        consensus_settings: Optional[Dict[str, Any]] = None,
    ) -> "RBProject":
        """
        Create a project within the organization.

        This method creates a project in a similar fashion to the
        quickstart on the RedBrick AI create project page.

        Parameters
        --------------
        name: str
            A unique name for your project

        taxonomy_name: str
            The name of the taxonomy you want to use for this project.
            Taxonomies can be found on the left side bar of the platform.

        stages: List[Stage]
            List of stage configs.

        exists_okay: bool = False
            Allow projects with the same name to be returned instead of trying to create
            a new project. Useful for when running the same script repeatedly when you
            do not want to keep creating new projects.

        workspace_id: Optional[str] = None
            The id of the workspace that you want to add this project to.

        sibling_tasks: Optional[int] = None
            Number of tasks created for each uploaded datapoint.

        consensus_settings: Optional[Dict[str, Any]] = None
            Consensus settings for the project. It has keys:
                - minAnnotations: int
                - autoAcceptThreshold?: float (range [0, 1])

        Returns
        --------------
        redbrick.RBProject
            A RedBrick Project object.

        Raises
        --------------
        ValueError:
            If a project with the same name exists but has a different type or taxonomy.

        """

    @abstractmethod
    def create_project(
        self,
        name: str,
        taxonomy_name: str,
        reviews: int = 0,
        exists_okay: bool = False,
        workspace_id: Optional[str] = None,
        sibling_tasks: Optional[int] = None,
        consensus_settings: Optional[Dict[str, Any]] = None,
    ) -> "RBProject":
        """
        Create a project within the organization.

        This method creates a project in a similar fashion to the
        quickstart on the RedBrick AI create project page.

        Parameters
        --------------
        name: str
            A unique name for your project

        taxonomy_name: str
            The name of the taxonomy you want to use for this project.
            Taxonomies can be found on the left side bar of the platform.

        reviews: int = 0
            The number of review stages that you want to add after the label
            stage.

        exists_okay: bool = False
            Allow projects with the same name to be returned instead of trying to create
            a new project. Useful for when running the same script repeatedly when you
            do not want to keep creating new projects.

        workspace_id: Optional[str] = None
            The id of the workspace that you want to add this project to.

        sibling_tasks: Optional[int] = None
            Number of tasks created for each uploaded datapoint.

        consensus_settings: Optional[Dict[str, Any]] = None
            Consensus settings for the project. It has keys:
                - minAnnotations: int
                - autoAcceptThreshold?: float (range [0, 1])

        Returns
        --------------
        redbrick.RBProject
            A RedBrick Project object.

        Raises
        --------------
        ValueError:
            If a project with the same name exists but has a different type or taxonomy.

        """

    @abstractmethod
    def get_project(
        self, project_id: Optional[str] = None, name: Optional[str] = None
    ) -> "RBProject":
        """Get project by id/name."""

    @abstractmethod
    def archive_project(self, project_id: str) -> bool:
        """Archive a project by ID."""

    @abstractmethod
    def unarchive_project(self, project_id: str) -> bool:
        """Unarchive a project by ID."""

    @abstractmethod
    def delete_project(self, project_id: str) -> bool:
        """Delete a project by ID."""

    @abstractmethod
    def labeling_time(
        self, start_date: datetime, end_date: datetime, concurrency: int = 50
    ) -> List[Dict]:
        """Get information of tasks labeled between two dates (both inclusive)."""

    @abstractmethod
    def create_taxonomy(
        self,
        name: str,
        study_classify: Optional[List[Attribute]] = None,
        series_classify: Optional[List[Attribute]] = None,
        instance_classify: Optional[List[Attribute]] = None,
        object_types: Optional[List[ObjectType]] = None,
    ) -> None:
        """
        Create a Taxonomy V2.

        Parameters
        -------------
        name:
            Unique identifier for the taxonomy.

        study_classify:
            Study level classification applies to the task.

        series_classify:
            Series level classification applies to a single series within a task.

        instance_classify:
            Instance classification applies to a single frame (video) or slice (3D volume).

        object_types:
            Object types are used to annotate features/objects in tasks, for example, segmentation or bounding boxes.

        Raises
        ----------
        ValueError:
            If there are validation errors.
        """

    @abstractmethod
    def get_taxonomy(
        self, name: Optional[str] = None, tax_id: Optional[str] = None
    ) -> Taxonomy:
        """Get a taxonomy created in your organization based on id or name.

        Format reference for categories and attributes objects:
        https://sdk.redbrickai.com/formats/taxonomy.html
        """

    @abstractmethod
    def update_taxonomy(
        self,
        tax_id: str,
        study_classify: Optional[List[Attribute]] = None,
        series_classify: Optional[List[Attribute]] = None,
        instance_classify: Optional[List[Attribute]] = None,
        object_types: Optional[List[ObjectType]] = None,
    ) -> None:
        """Update the categories/attributes of Taxonomy (V2) in the organization.

        Format reference for categories and attributes objects:
        https://sdk.redbrickai.com/formats/taxonomy.html

        Raises
        ----------
        ValueError:
            If there are validation errors.
        """

    @abstractmethod
    def delete_taxonomy(
        self, name: Optional[str] = None, tax_id: Optional[str] = None
    ) -> bool:
        """Delete a taxonomy by name or ID."""


class RBDataset(ABC):
    """Abstract interface to RBDataset.

    :ivar `redbrick.common.upload.DatasetUpload` upload: Upload data to dataset.
    :ivar `redbrick.common.export.DatasetExport` export: Dataset data export.

    .. code:: python

        >>> dataset = redbrick.get_dataset(org_id="", dataset_name="", api_key="")
    """

    context: RBContext

    upload: DatasetUpload
    export: DatasetExport

    @property
    @abstractmethod
    def org_id(self) -> str:
        """
        Read only property.

        Retrieves the unique Organization UUID that this dataset belongs to
        """

    @property
    @abstractmethod
    def dataset_name(self) -> str:
        """
        Read only name property.

        Retrieves the dataset name.
        """


class RBWorkspace(ABC):
    """Interface for interacting with your RedBrick AI Workspaces."""

    @property
    @abstractmethod
    def org_id(self) -> str:
        """
        Read only property.

        Retrieves the unique Organization UUID that this workspace belongs to
        """

    @property
    @abstractmethod
    def workspace_id(self) -> str:
        """
        Read only property.

        Retrieves the unique Workspace ID UUID.
        """

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Read only name property.

        Retrieves the workspace name.
        """

    @property
    @abstractmethod
    def metadata_schema(self) -> List[Dict]:
        """Retrieves the workspace metadata schema."""

    @property
    @abstractmethod
    def classification_schema(self) -> List[Dict]:
        """Retrieves the workspace classification schema."""

    @property
    @abstractmethod
    def cohorts(self) -> List[Dict]:
        """Retrieves the workspace cohorts."""

    @abstractmethod
    def update_schema(
        self,
        metadata_schema: Optional[List[Dict]] = None,
        classification_schema: Optional[List[Dict]] = None,
    ) -> None:
        """Update workspace metadata and classification schema."""

    @abstractmethod
    def update_cohorts(self, cohorts: List[Dict]) -> None:
        """Update workspace cohorts."""

    @abstractmethod
    def get_datapoints(
        self,
        *,
        concurrency: int = 10,
    ) -> Iterator[Dict]:
        """Get datapoints in a workspace."""

    @abstractmethod
    def archive_datapoints(self, dp_ids: List[str]) -> None:
        """Archive datapoints."""

    @abstractmethod
    def unarchive_datapoints(self, dp_ids: List[str]) -> None:
        """Unarchive datapoints."""

    @abstractmethod
    def add_datapoints_to_cohort(self, cohort_name: str, dp_ids: List[str]) -> None:
        """Add datapoints to a cohort."""

    @abstractmethod
    def remove_datapoints_from_cohort(
        self, cohort_name: str, dp_ids: List[str]
    ) -> None:
        """Remove datapoints from a cohort."""

    @abstractmethod
    def update_datapoint_attributes(self, dp_id: str, attributes: Dict) -> None:
        """Update datapoint attributes."""

    @abstractmethod
    def add_datapoints_to_projects(
        self, project_ids: List[str], dp_ids: List[str], is_ground_truth: bool = False
    ) -> None:
        """Add datapoints to project.

        Parameters
        --------------
        project_ids: List[str]
            The projects in which you'd like to add the given datapoints.

        dp_ids: List[str]
            List of datapoints that need to be added to projects.

        is_ground_truth: bool = False
            Whether to create tasks directly in ground truth stage.
        """

    @abstractmethod
    def create_datapoints(
        self,
        storage_id: str,
        points: List[InputTask],
        *,
        concurrency: int = 50,
    ) -> List[Dict]:
        """
        Create datapoints in workspace.

        Upload data to your workspace (without annotations). Please visit
        `our documentation <https://sdk.redbrickai.com/formats/index.html#import>`_
        to understand the format for ``points``.

        .. code:: python

            workspace = redbrick.get_workspace(org_id, workspace_id, api_key, url)
            points = [
                {
                    "name": "...",
                    "series": [
                        {
                            "items": "...",
                        }
                    ]
                }
            ]
            workspace.create_datapoints(storage_id, points)


        Parameters
        --------------
        storage_id: str
            Your RedBrick AI external storage_id. This can be found under the Storage Tab
            on the RedBrick AI platform. To directly upload images to rbai,
            use redbrick.StorageMethod.REDBRICK.

        points: List[:obj:`~redbrick.types.task.InputTask`]
            Please see the RedBrick AI reference documentation for overview of the format.
            https://sdk.redbrickai.com/formats/index.html#import.
            Fields with `annotation` information are not supported in workspace.

        concurrency: int = 50

        Returns
        -------------
        List[Dict]
            List of datapoint objects with key `response` if successful, else `error`

        Note
        ----------
            1. If doing direct upload, please use ``redbrick.StorageMethod.REDBRICK``
            as the storage id. Your items path must be a valid path to a locally stored image.

            2. When doing direct upload i.e. ``redbrick.StorageMethod.REDBRICK``,
            if you didn't specify a "name" field in your datapoints object,
            we will assign the "items" path to it.
        """

    @abstractmethod
    def update_datapoints_metadata(self, storage_id: str, points: List[Dict]) -> None:
        """Update datapoints metadata.

        Update metadata for datapoints in workspace.

        .. code:: python

            workspace = redbrick.get_workspace(org_id, workspace_id, api_key, url)
            points = [
                {
                    "dpId": "...",
                    "metaData": {
                        "property": "value",
                    }
                }
            ]
            workspace.update_datapoints_metadata(storage_id, points)


        Parameters
        --------------
        storage_id: str
            Storage method where the datapoints are stored.

        points: List[:obj:`~redbrick.types.task.InputTask`]
            List of datapoints with dpId and metaData values.
        """

    @abstractmethod
    def delete_datapoints(self, dp_ids: List[str], concurrency: int = 50) -> bool:
        """Delete workspace datapoints based on ids.

        >>> workspace = redbrick.get_workspace(org_id, workspace_id, api_key, url)
        >>> workspace.delete_datapoints([...])

        Parameters
        --------------
        dp_ids: List[str]
            List of datapoint ids to delete.

        concurrency: int = 50
            The number of datapoints to delete at a time.
            We recommend keeping this less than or equal to 50.

        Returns
        -------------
        bool
            True if successful, else False.
        """

    @abstractmethod
    def import_from_dataset(
        self,
        dataset_name: str,
        *,
        import_id: Optional[str] = None,
        series_ids: Optional[List[str]] = None,
        group_by_study: bool = False,
    ) -> None:
        """Import tasks from a dataset for a given import_id or list of series_ids.

        Parameters
        --------------
        dataset_name: str
            The name of the dataset to import from.

        import_id: Optional[str] = None
            The import id of the dataset to import from.

        series_ids: Optional[List[str]] = None
            The series ids to import from the dataset.

        group_by_study: bool = False
            Whether to group the tasks by study.
        """


class RBProject(ABC):
    """Abstract interface to RBProject.

    :ivar `redbrick.common.upload.Upload` upload: Upload data to project.
    :ivar `redbrick.common.labeling.Labeling` labeling: Labeling activities.
    :ivar `redbrick.common.labeling.Labeling` review: Review activities.
    :ivar `redbrick.common.export.Export` export: Project data export.
    :ivar `redbrick.common.settings.Settings` settings: Project settings management.
    :ivar `redbrick.common.member.Workforce` workforce: Project workforce management.

    .. code:: python

        >>> project = redbrick.get_project(org_id="", project_id="", api_key="")
    """

    context: RBContext

    upload: Upload
    labeling: Labeling
    review: Labeling
    export: Export
    settings: Settings
    workforce: Workforce

    output_stage_name: str
    is_consensus_enabled: bool

    @property
    @abstractmethod
    def org_id(self) -> str:
        """
        Read only property.

        Retrieves the unique Organization UUID that this project belongs to
        """

    @property
    @abstractmethod
    def project_id(self) -> str:
        """
        Read only property.

        Retrieves the unique Project ID UUID.
        """

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Read only name property.

        Retrieves the project name.
        """

    @property
    @abstractmethod
    def url(self) -> str:
        """
        Read only property.

        Retrieves the project URL.
        """

    @property
    @abstractmethod
    def taxonomy_name(self) -> str:
        """
        Read only taxonomy_name property.

        Retrieves the taxonomy name.
        """

    @property
    @abstractmethod
    def taxonomy(self) -> Taxonomy:
        """Retrieves the project taxonomy."""

    @property
    @abstractmethod
    def workspace_id(self) -> Optional[str]:
        """
        Read only workspace_id property.

        Retrieves the workspace id.
        """

    @property
    @abstractmethod
    def label_storage(self) -> Tuple[str, str]:
        """
        Read only label_storage property.

        Retrieves the label storage id and path.
        """

    @property
    @abstractmethod
    def archived(self) -> bool:
        """Get if project is archived."""

    @property
    @abstractmethod
    def stages(self) -> List[Stage]:
        """Get list of stages."""

    @abstractmethod
    def set_label_storage(self, storage_id: str, path: str) -> Tuple[str, str]:
        """
        Set label storage method for a project.

        By default, all annotations get stored in RedBrick AI's storage
        i.e. ``redbrick.StorageMethod.REDBRICK``.
        Set a custom external storage, within which RedBrick AI will write all annotations.

        >>> project = redbrick.get_project(org_id, project_id, api_key)
        >>> project.set_label_storage(storage_id)

        Parameters
        ------------
        storage_id: str
            The unique ID of your RedBrick AI storage method integration.
            Found on the storage method tab on the left sidebar.

        path: str
            A prefix path within which the annotations will be written.

        Returns
        --------------
        Tuple[str, str]
            Returns [storage_id, path]

        Important
        ------------
        You only need to run this command once per project.

        Raises
        ----------
        ValueError:
            If there are validation errors.
        """

    @abstractmethod
    def update_stage(self, stage: Stage) -> None:
        """Update stage."""
