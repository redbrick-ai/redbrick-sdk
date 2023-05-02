"""Organization class."""
from datetime import datetime
from functools import partial
from typing import List, Optional, Dict, Union
from tqdm import tqdm  # type: ignore

from redbrick.common.context import RBContext
from redbrick.project import RBProject
from redbrick.workspace import RBWorkspace
from redbrick.utils.logging import logger
from redbrick.utils.pagination import PaginationIterator
from redbrick.utils.rb_tax_utils import format_taxonomy
from .basic_project import get_basic_project


class RBOrganization:
    """
    Representation of RedBrick organization.

    The RBOrganization object allows you to programmatically interact with
    your RedBrick organization. This class provides methods for querying your
    organization and doing other high level actions.
    """

    def __init__(self, context: RBContext, org_id: str) -> None:
        """Construct RBOrganization."""
        self.context = context

        self._org_id = org_id
        self._name: str

        self._get_org()

    def _get_org(self) -> None:
        org = self.context.project.get_org(self._org_id)
        self._name = org["name"]

    def taxonomies(self, only_name: bool = True) -> Union[List[str], List[Dict]]:
        """Get a list of taxonomy names/objects in the organization."""
        taxonomies = self.context.project.get_taxonomies(self._org_id)
        if only_name:
            return [tax["name"] for tax in taxonomies]
        return list(map(format_taxonomy, taxonomies))

    def _all_projects_raw(self) -> List[Dict]:
        """Get and filter entries from server."""
        projects = self.context.project.get_projects(self._org_id)
        projects = list(filter(lambda x: x["status"] == "CREATION_SUCCESS", projects))

        return projects

    def projects(self) -> List[RBProject]:
        """Get a list of active projects in the organization."""
        projects = self._all_projects_raw()
        return [
            RBProject(self.context, self._org_id, proj["projectId"])
            for proj in tqdm(projects)
        ]

    @property
    def org_id(self) -> str:
        """Retrieve the unique org_id of this organization."""
        return self._org_id

    @property
    def name(self) -> str:
        """Retrieve unique name of this organization."""
        return self._name

    def __str__(self) -> str:
        """Get string representation of RBOrganization object."""
        return f"RedBrick AI Organization - {self._name} - ( {self._org_id} )"

    def __repr__(self) -> str:
        """Representation of object."""
        return str(self)

    def create_workspace(self, name: str, exists_okay: bool = False) -> RBWorkspace:
        """
        Create a workspace within the organization.

        This method creates an organization in a similar fashion to the
        quickstart on the RedBrick Ai create project page.

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
        redbrick.workspace.RBWorkspace
            A RedBrick Workspace object.
        """
        try:
            workspace_data = self.context.workspace.create_workspace(
                self._org_id, name, exists_okay=exists_okay
            )
        except ValueError as error:
            raise Exception(
                "Project with same name exists, try setting exists_okay=True to"
                + " return this project instead of creating a new one"
            ) from error

        return RBWorkspace(self.context, self._org_id, workspace_data["workspaceId"])

    def create_project(
        self,
        name: str,
        taxonomy_name: str,
        reviews: int = 0,
        exists_okay: bool = False,
        workspace_id: Optional[str] = None,
    ) -> RBProject:
        """
        Create a project within the organization.

        This method creates an organization in a similar fashion to the
        quickstart on the RedBrick Ai create project page.

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
            The workspace id that you want to add this project to.

        Returns
        --------------
        redbrick.project.RBProject
            A RedBrick Project object.
        """
        stages = get_basic_project(reviews)

        if exists_okay:
            logger.info("exists_okay=True... checking for project with same name")
            all_projects = self._all_projects_raw()
            same_name = list(filter(lambda x: x["name"] == name, all_projects))
            if same_name:
                temp = RBProject(self.context, self.org_id, same_name[0]["projectId"])
                if temp.td_type != "DICOM_SEGMENTATION":
                    raise ValueError(
                        "Project with matching name exists, but it has a different type"
                    )
                if temp.taxonomy_name != taxonomy_name:
                    raise ValueError(
                        "Project with matching name exists, but it has a different taxonomy"
                    )

                logger.warning(
                    "exists_okay=True... returning project that already existed"
                )
                return temp

        taxonomies: Dict[str, Dict] = {
            taxonomy["name"]: taxonomy for taxonomy in self.taxonomies(False)  # type: ignore
        }

        if taxonomy_name not in taxonomies:
            raise ValueError(f"Taxonomy `{taxonomy_name}` does not exist")
        if taxonomies[taxonomy_name].get("archived"):
            raise ValueError(f"Taxonomy `{taxonomy_name}` has been archived")
        if not taxonomies[taxonomy_name].get("isNew"):
            logger.warning(
                f"Deprecated: `{taxonomy_name}` is of type Taxonomy V1."
                + " We suggest creating new projects using Taxonomy V2."
            )

        try:
            project_data = self.context.project.create_project(
                self.org_id,
                name,
                stages,
                "DICOM_SEGMENTATION",
                taxonomy_name,
                workspace_id,
            )
        except ValueError as error:
            raise Exception(
                "Project with same name exists, try setting exists_okay=True to"
                + " return this project instead of creating a new one"
            ) from error

        return RBProject(self.context, self.org_id, project_data["projectId"])

    def labeling_time(
        self, start_date: datetime, end_date: datetime, concurrency: int = 50
    ) -> List[Dict]:
        """Get information of tasks labeled between two dates (both inclusive)."""
        tasks: List[Dict]
        my_iter = PaginationIterator(
            partial(
                self.context.project.get_labeling_information,
                self._org_id,
                start_date,
                end_date,
            ),
            concurrency,
        )
        with tqdm(my_iter, unit=" tasks") as progress:
            tasks = [
                {
                    "projectId": task["project"]["projectId"],
                    "taskId": task["taskId"],
                    "completedBy": task["user"]["email"],
                    "timeSpent": task["timeSpent"],
                    "completedAt": task["date"],
                    "cycle": task["cycle"],
                }
                for task in progress
            ]

        return tasks

    def create_taxonomy_new(
        self,
        name: str,
        study_classify: Optional[List[Dict]] = None,
        series_classify: Optional[List[Dict]] = None,
        instance_classify: Optional[List[Dict]] = None,
        object_types: Optional[List[Dict]] = None,
    ) -> None:
        """
        Create a Taxonomy V2.

        Format reference for categories and attributes objects:
        https://docs.redbrickai.com/python-sdk/sdk-overview/reference#taxonomy-objects
        """
        if self.context.project.create_taxonomy_new(
            self.org_id,
            name,
            study_classify,
            series_classify,
            instance_classify,
            object_types,
        ):
            logger.info(f"Successfully created taxonomy: {name}")

    def get_taxonomy(
        self, tax_id: Optional[str] = None, name: Optional[str] = None
    ) -> Dict:
        """Get a taxonomy created in your organization."""
        taxonomy = self.context.project.get_taxonomy(self._org_id, tax_id, name)
        return format_taxonomy(taxonomy)

    def update_taxonomy(
        self,
        tax_id: str,
        study_classify: Optional[List[Dict]] = None,
        series_classify: Optional[List[Dict]] = None,
        instance_classify: Optional[List[Dict]] = None,
        object_types: Optional[List[Dict]] = None,
    ) -> None:
        """Update the categories/attributes of taxonomy in the organization.

        Format reference for categories and attributes objects:
        https://docs.redbrickai.com/python-sdk/sdk-overview/reference#taxonomy-objects


        Warnings
        ----------
        Only applicable for Taxonomy V2.
        """
        if self.context.project.update_taxonomy(
            self._org_id,
            tax_id,
            study_classify,
            series_classify,
            instance_classify,
            object_types,
        ):
            logger.info(f"Successfully updated taxonomy: {tax_id}")
