"""Organization class."""
from datetime import datetime
from functools import partial
from typing import List, Optional, Dict, Union
from tqdm import tqdm  # type: ignore

from redbrick.common.enums import LabelType
from redbrick.common.context import RBContext
from redbrick.project import RBProject
from redbrick.utils.logging import print_info, print_warning, handle_exception
from redbrick.utils.pagination import PaginationIterator
from .basic_project import get_active_learning_project, get_basic_project


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

    @handle_exception
    def taxonomies(self, only_name: bool = True) -> Union[List[str], List[Dict]]:
        """Get a list of taxonomy names/objects in the organization."""
        taxonomies = self.context.project.get_taxonomies(self._org_id)
        if only_name:
            return [tax["name"] for tax in taxonomies]
        return taxonomies

    def _all_projects_raw(self) -> List[Dict]:
        """Get and filter entries from server."""
        projects = self.context.project.get_projects(self._org_id)
        projects = list(filter(lambda x: x["status"] == "CREATION_SUCCESS", projects))

        return projects

    @handle_exception
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

    @handle_exception
    def create_project(
        self,
        name: str,
        label_type: LabelType,
        taxonomy_name: str,
        reviews: int = 0,
        exists_okay: bool = False,
        active_learning: Optional[Dict] = None,
    ) -> RBProject:
        """
        Create a project within the organization.

        This method creates an organization in a similar fashion to the
        quickstart on the RedBrick Ai create project page.

        Parameters
        --------------
        name: str
            A unique name for your project

        label_type: redbrick.LabelType
            Configures the label and data type of your project.

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

        Returns
        --------------
        redbrick.project.RBProject
            A RedBrick Project object.
        """
        if active_learning is not None:
            print_warning("active_learning arg is deprecated and will be ignored")
        stages = get_basic_project(reviews)

        if exists_okay:
            print_info("exists_okay=True... checking for project with same name")
            all_projects = self._all_projects_raw()
            same_name = list(filter(lambda x: x["name"] == name, all_projects))
            if same_name:
                temp = RBProject(self.context, self.org_id, same_name[0]["projectId"])
                if temp.project_type != label_type:
                    raise ValueError(
                        "Project with matching name exists, but it has a different type"
                    )
                if temp.taxonomy_name != taxonomy_name:
                    raise ValueError(
                        "Project with matching name exists, but it has a different taxonomy"
                    )

                print_warning(
                    "exists_okay=True... returning project that already existed"
                )
                return temp

        try:
            project_data = self.context.project.create_project(
                self.org_id, name, stages, label_type.value, taxonomy_name
            )
        except ValueError as error:
            raise Exception(
                "Project with same name exists, try setting exists_okay=True to"
                + " return this project instead of creating a new one"
            ) from error

        return RBProject(self.context, self.org_id, project_data["projectId"])

    @handle_exception
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
                concurrency,
            )
        )
        with tqdm(my_iter, unit=" tasks") as progress:
            tasks = [
                {
                    "projectId": task["project"]["projectId"],
                    "taskId": task["taskId"],
                    "completedBy": task["user"]["email"],
                    "timeSpent": task["timeSpent"],
                    "completedAt": task["date"],
                }
                for task in progress
            ]

        return tasks

    @handle_exception
    def create_taxonomy(
        self,
        name: str,
        categories: List[Dict],
        attributes: Optional[List[Dict]] = None,
        task_categories: Optional[List[Dict]] = None,
        task_attributes: Optional[List[Dict]] = None,
    ) -> None:
        """Create Taxonomy.

        Format reference for categories and attributes objects:
        https://docs.redbrickai.com/python-sdk/sdk-overview/reference#taxonomy-objects
        """
        if self.context.project.create_taxonomy(
            self.org_id,
            name,
            [{"name": "object", "children": categories}],
            attributes,
            [{"name": "object", "children": task_categories}]
            if task_categories
            else task_categories,
            task_attributes,
        ):
            print_info(f"Successfully created taxonomy: {name}")
