"""Main CLI project."""
import os
from typing import Optional

from halo.halo import Halo  # type: ignore

from redbrick import _populate_context
from redbrick.common.context import RBContext
from redbrick.organization import RBOrganization
from redbrick.project import RBProject
from redbrick.cli.entity import CLICache, CLIConfiguration, CLICredentials
from redbrick.utils.logging import print_info


class CLIProject:
    """CLIProject class."""

    path: str

    creds: CLICredentials
    conf: CLIConfiguration
    cache: CLICache

    _context: Optional[RBContext] = None
    _org: Optional[RBOrganization] = None
    _project: Optional[RBProject] = None

    def __init__(self, path: str = ".", required: bool = True) -> None:
        """Initialize CLIProject."""
        self.path = os.path.realpath(path)
        assert os.path.isdir(self.path), f"Not a valid directory {self.path}"

        self._rb_dir = os.path.join(self.path, ".redbrick")
        self._creds_file = os.path.join(
            os.path.expanduser("~"), ".redbrickai", "credentials"
        )

        self.creds = CLICredentials(
            os.path.join(os.path.expanduser("~"), ".redbrickai", "credentials")
        )
        self.conf = CLIConfiguration(os.path.join(self._rb_dir, "config"))
        self.cache = CLICache(os.path.join(self._rb_dir, "cache"), self.conf)

        if required:
            assert (
                self.creds.exists
            ), "No credentials found, please set it up with `redbrick config`"
            assert self.conf.exists, (
                "No project found in {self.path}\n"
                + "Please create one using `redbrick init` / clone existing using `redbrick clone`"
            )
            assert (
                self.org_id == self.creds.org_id
            ), "Project configuration does not match with current profile"

    @classmethod
    def from_path(
        cls, path: str = ".", required: bool = True
    ) -> Optional["CLIProject"]:
        """Get CLIProject from given directory."""
        path = os.path.realpath(path)

        if os.path.isdir(os.path.join(path, ".redbrick")):
            return cls(path, required)

        parent = os.path.realpath(os.path.join(path, ".."))

        if parent == path:
            if required:
                raise Exception(f"No redbrick project found. Searched upto {path}")
            return None

        return cls.from_path(parent, required)

    @property
    def context(self) -> RBContext:
        """Get RedBrick context."""
        if not self._context:
            self._context = _populate_context(self.creds.context)
        return self._context

    @property
    def org_id(self) -> str:
        """Get org_id of current project."""
        value = self.conf.get_option("org", "id")
        assert value, "Invalid project configuration"
        return value.strip().lower()

    @property
    def project_id(self) -> str:
        """Get project_id of current project."""
        value = self.conf.get_option("project", "id")
        assert value, "Invalid project configuration"
        return value.strip().lower()

    @property
    def org(self) -> RBOrganization:
        """Get org object."""
        if not self._org:
            org = self.cache.get_object("org")
            if (
                isinstance(org, RBOrganization)
                and org.context.client.url == self.context.client.url
                and org.context.client.api_key == self.context.client.api_key
            ):
                self._org = org
            else:
                with Halo(text="Fetching organization", spinner="dots") as spinner:
                    try:
                        self._org = RBOrganization(self.context, self.org_id)
                        self.cache.set_object("org", self._org, True)
                    except Exception as error:
                        spinner.fail()
                        raise error
                spinner.succeed(str(self._org))
        return self._org

    @property
    def project(self) -> RBProject:
        """Get project object."""
        if not self._project:
            project = self.cache.get_object("project")
            if (
                isinstance(project, RBProject)
                and project.context.client.url == self.context.client.url
                and project.context.client.api_key == self.context.client.api_key
            ):
                self._project = project
            else:
                with Halo(text="Fetching project", spinner="dots") as spinner:
                    try:
                        self._project = RBProject(
                            self.context, self.org_id, self.project_id
                        )
                        self.cache.set_object("project", self._project, True)
                    except Exception as error:
                        spinner.fail()
                        raise error
                    spinner.succeed(str(self._project))
        return self._project

    def initialize_project(self, org: RBOrganization, project: RBProject) -> None:
        """Initialize local project."""
        assert not os.path.isdir(
            self._rb_dir
        ), f"Already a RedBrick project {self.path}"

        os.makedirs(self._rb_dir)
        self.conf.save()

        self.conf.set_section("org", {"id": project.org_id})
        self.conf.set_section("project", {"id": project.project_id})

        self.cache.set_object("org", org)
        self.cache.set_object("project", project)

        self.conf.save()

        print_info(
            f"Successfully initialized {project} in {self.path}\nURL: {project.url}"
        )
