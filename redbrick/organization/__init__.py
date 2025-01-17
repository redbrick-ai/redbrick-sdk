"""Organization class."""

from datetime import datetime
from functools import partial
from typing import Any, List, Optional, Dict, Sequence, Union
import platform

from tqdm import tqdm  # type: ignore

from redbrick.config import config
from redbrick.common.context import RBContext
from redbrick.project import RBProject
from redbrick.types.taxonomy import Attribute, ObjectType, Taxonomy
from redbrick.workspace import RBWorkspace
from redbrick.stage import Stage, get_project_stages, get_middle_stages

from redbrick.utils.logging import logger
from redbrick.utils.pagination import PaginationIterator
from redbrick.utils.rb_tax_utils import format_taxonomy, validate_taxonomy


class RBOrganization:
    """
    Representation of RedBrick organization.

    The :attr:`redbrick.organization.RBOrganization` object allows you to programmatically interact with
    your RedBrick organization. This class provides methods for querying your
    organization and doing other high level actions. Retrieve the organization object in the following way:

    .. code:: python

        >>> org = redbrick.get_org(api_key="", org_id="")
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

    def taxonomies(self, only_name: bool = True) -> Union[List[str], List[Taxonomy]]:
        """Get a list of taxonomy names/objects in the organization."""
        taxonomies = self.context.project.get_taxonomies(self._org_id)
        if only_name:
            return [tax["name"] for tax in taxonomies]
        return list(map(format_taxonomy, taxonomies))

    def workspaces_raw(self) -> List[Dict]:
        """Get a list of active workspaces as raw objects in the organization."""
        workspaces = self.context.workspace.get_workspaces(self._org_id)
        workspaces = list(
            filter(lambda x: x["status"] == "CREATION_SUCCESS", workspaces)
        )

        return workspaces

    def projects_raw(self) -> List[Dict]:
        """Get a list of active projects as raw objects in the organization."""
        projects = self.context.project.get_projects(self._org_id)
        projects = list(filter(lambda x: x["status"] == "CREATION_SUCCESS", projects))

        return projects

    def projects(self) -> List[RBProject]:
        """Get a list of active projects in the organization."""
        projects = self.projects_raw()
        return [
            RBProject(self.context, self._org_id, proj["projectId"])
            for proj in tqdm(projects, leave=config.log_info)
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
        redbrick.workspace.RBWorkspace
            A RedBrick Workspace object.
        """
        try:
            workspace_data = self.context.workspace.create_workspace(
                self._org_id, name, exists_okay=exists_okay
            )
        except ValueError as error:
            raise Exception(
                "Workspace with same name exists, try setting exists_okay=True to"
                + " return this workspace instead of creating a new one"
            ) from error

        return RBWorkspace(self.context, self._org_id, workspace_data["workspaceId"])

    def create_project_advanced(
        self,
        name: str,
        taxonomy_name: str,
        stages: Sequence[Stage],
        exists_okay: bool = False,
        workspace_id: Optional[str] = None,
        sibling_tasks: Optional[int] = None,
        consensus_settings: Optional[Dict[str, Any]] = None,
    ) -> RBProject:
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
        redbrick.project.RBProject
            A RedBrick Project object.

        Raises
        --------------
        ValueError:
            If a project with the same name exists but has a different type or taxonomy.

        """
        if exists_okay:
            logger.info("exists_okay=True... checking for project with same name")
            all_projects = self.projects_raw()
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

        try:
            sibling_tasks = (
                None if sibling_tasks is None or sibling_tasks <= 1 else sibling_tasks
            )
            taxonomy = self.context.project.get_taxonomy(
                org_id=self.org_id, tax_id=None, name=taxonomy_name
            )
            project_data = self.context.project.create_project(
                self.org_id,
                name,
                get_project_stages(stages, taxonomy),
                "DICOM_SEGMENTATION",
                taxonomy_name,
                workspace_id,
                sibling_tasks,
                {**consensus_settings, "enabled": True} if consensus_settings else None,
            )
        except ValueError as error:
            raise Exception(
                "Project with same name exists, try setting exists_okay=True to"
                + " return this project instead of creating a new one"
            ) from error

        return RBProject(self.context, self.org_id, project_data["projectId"])

    def create_project(
        self,
        name: str,
        taxonomy_name: str,
        reviews: int = 0,
        exists_okay: bool = False,
        workspace_id: Optional[str] = None,
        sibling_tasks: Optional[int] = None,
        consensus_settings: Optional[Dict[str, Any]] = None,
    ) -> RBProject:
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
        redbrick.project.RBProject
            A RedBrick Project object.

        Raises
        --------------
        ValueError:
            If a project with the same name exists but has a different type or taxonomy.

        """
        return self.create_project_advanced(
            name,
            taxonomy_name,
            get_middle_stages(reviews, consensus_settings),
            exists_okay,
            workspace_id,
            sibling_tasks,
            consensus_settings,
        )

    def get_project(
        self, project_id: Optional[str] = None, name: Optional[str] = None
    ) -> RBProject:
        """Get project by id/name."""
        projects = self.projects_raw()
        if project_id:
            projects = [
                project for project in projects if project["projectId"] == project_id
            ]
        elif name:
            projects = [project for project in projects if project["name"] == name]
        else:
            raise Exception("Either project_id or name is required")

        if not projects:
            raise Exception("No project found")

        return RBProject(self.context, self._org_id, projects[0]["projectId"])

    def delete_project(self, project_id: str) -> bool:
        """Delete a project by ID."""
        return self.context.project.delete_project(self._org_id, project_id)

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
        with tqdm(my_iter, unit=" tasks", leave=config.log_info) as progress:
            tasks = [
                {
                    "orgId": self._org_id,
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
        validate_taxonomy(
            study_classify, series_classify, instance_classify, object_types
        )
        if self.context.project.create_taxonomy(
            self.org_id,
            name,
            study_classify,
            series_classify,
            instance_classify,
            object_types,
        ):
            logger.info(f"Successfully created taxonomy: {name}")

    def get_taxonomy(
        self, name: Optional[str] = None, tax_id: Optional[str] = None
    ) -> Taxonomy:
        """Get a taxonomy created in your organization based on id or name.

        Format reference for categories and attributes objects:
        https://sdk.redbrickai.com/formats/taxonomy.html
        """
        taxonomy = self.context.project.get_taxonomy(self._org_id, tax_id, name)
        return format_taxonomy(taxonomy)

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
        validate_taxonomy(
            study_classify, series_classify, instance_classify, object_types
        )
        if self.context.project.update_taxonomy(
            self._org_id,
            tax_id,
            study_classify,
            series_classify,
            instance_classify,
            object_types,
        ):
            logger.info(f"Successfully updated taxonomy: {tax_id}")

    def delete_taxonomy(
        self, name: Optional[str] = None, tax_id: Optional[str] = None
    ) -> bool:
        """Delete a taxonomy by name or ID."""
        return self.context.project.delete_taxonomy(self._org_id, tax_id, name)

    def self_health_check(self, self_url: str) -> Optional[str]:
        """Send a health check update from the model server."""
        # pylint: disable=too-many-locals, import-outside-toplevel

        import psutil  # type: ignore
        import GPUtil  # type: ignore

        uname = platform.uname()
        cpu_freq = psutil.cpu_freq()
        svmem = psutil.virtual_memory()
        swap = psutil.swap_memory()

        partitions = psutil.disk_partitions()
        total_storage, used_storage, free_storage = 0, 0, 0
        for partition in partitions:
            try:
                partition_usage = psutil.disk_usage(partition.mountpoint)
            except PermissionError:
                continue
            total_storage += partition_usage.total
            used_storage += partition_usage.used
            free_storage += partition_usage.free

        disk_io = psutil.disk_io_counters()
        if_addrs = psutil.net_if_addrs()
        net_io = psutil.net_io_counters()
        gpus = GPUtil.getGPUs()

        self_data = {
            "system": uname.system,
            "node": uname.node,
            "release": uname.release,
            "version": uname.version,
            "machine": uname.machine,
            "processor": uname.processor,
            "boot_time": psutil.boot_time(),
            "physical_cores": psutil.cpu_count(logical=False),
            "total_cores": psutil.cpu_count(logical=True),
            "max_frequency": cpu_freq.max,
            "min_frequency": cpu_freq.min,
            "current_frequency": cpu_freq.current,
            "cores": [
                {"usage": percentage}
                for percentage in psutil.cpu_percent(percpu=True, interval=1)
            ],
            "total_mem": svmem.total,
            "used_mem": svmem.used,
            "free_mem": svmem.free,
            "total_swap": swap.total,
            "used_swap": swap.used,
            "free_swap": swap.free,
            "total_storage": total_storage,
            "used_storage": used_storage,
            "free_storage": free_storage,
            "disk_read": disk_io.read_bytes if disk_io else None,
            "disk_write": disk_io.write_bytes if disk_io else None,
            "network": [
                {
                    "interface": interface_name,
                    "family": str(address.family),
                    "address": address.address,
                    "mask": address.netmask,
                    "broadcast": address.broadcast,
                }
                for interface_name, interface_addresses in if_addrs.items()
                for address in interface_addresses
                if str(address.family)
                in ("AddressFamily.AF_INET", "AddressFamily.AF_PACKET")
            ],
            "network_sent": net_io.bytes_sent,
            "network_recv": net_io.bytes_recv,
            "gpus": [
                {
                    "id": gpu.id,
                    "name": gpu.name,
                    "load": gpu.load,
                    "total_mem": gpu.memoryTotal,
                    "used_mem": gpu.memoryUsed,
                    "free_mem": gpu.memoryFree,
                    "temp": gpu.temperature,
                    "uuid": gpu.uuid,
                }
                for gpu in gpus
            ],
        }
        return self.context.project.self_health_check(self.org_id, self_url, self_data)
