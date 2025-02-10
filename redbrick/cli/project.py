"""Main CLI project."""

import os
from typing import Optional, cast

from rich.console import Console

from redbrick.common.context import RBContext
from redbrick.common.entities import RBOrganization, RBProject
from redbrick.config import config
from redbrick.organization import RBOrganizationImpl
from redbrick.project import RBProjectImpl
from redbrick.cli.entity import CLICache, CLIConfiguration, CLICredentials
from redbrick.utils.logging import assert_validation, logger


class CLIProject:
    """CLIProject class."""

    path: str

    creds: CLICredentials
    conf: CLIConfiguration
    cache: CLICache

    _context: Optional[RBContext] = None
    _org: Optional[RBOrganization] = None
    _project: Optional[RBProject] = None

    def __init__(
        self, path: str = ".", required: bool = True, profile: Optional[str] = None
    ) -> None:
        """Initialize CLIProject."""
        self.path = os.path.realpath(path)
        assert_validation(
            os.path.isdir(self.path), f"Not a valid directory {self.path}"
        )

        self._rb_dir = os.path.join(self.path, ".redbrick")
        self.creds = CLICredentials(profile=profile)
        self.conf = CLIConfiguration(os.path.join(self._rb_dir, "config"))
        self.cache = CLICache(os.path.join(self._rb_dir, "cache"), self.conf)

        if required:
            assert_validation(
                self.creds.exists,
                "No credentials found, please set it up with `redbrick config`",
            )
            assert_validation(
                self.conf.exists,
                f"No project found in `{self.path}`\n"
                + "Please create one using `redbrick init` / clone existing using `redbrick clone`",
            )
            assert_validation(
                self.org_id == self.creds.org_id,
                "Project configuration does not match with current profile",
            )

    @classmethod
    def from_path(
        cls, path: str = ".", required: bool = True, profile: Optional[str] = None
    ) -> Optional["CLIProject"]:
        """Get CLIProject from given directory."""
        path = os.path.realpath(path)

        if os.path.isdir(os.path.join(path, ".redbrick")):
            return cls(path, required, profile)

        parent = os.path.realpath(os.path.join(path, ".."))

        if parent == path:
            if required:
                raise Exception(f"No redbrick project found. Searched upto {path}")
            return None

        return cls.from_path(parent, required, profile)

    @property
    def context(self) -> RBContext:
        """Get RedBrick context."""
        if not self._context:
            self._context = self.creds.context
        return self._context

    @property
    def org_id(self) -> str:
        """Get org_id of current project."""
        value = self.conf.get_option("org", "id")
        assert_validation(value, "Invalid project configuration")
        return cast(str, value).strip().lower()

    @property
    def project_id(self) -> str:
        """Get project_id of current project."""
        value = self.conf.get_option("project", "id")
        assert_validation(value, "Invalid project configuration")
        return cast(str, value).strip().lower()

    @property
    def org(self) -> RBOrganization:
        """Get org object."""
        if not self._org:
            console = Console()
            with console.status("Fetching organization") as status:
                try:
                    self._org = RBOrganizationImpl(self.context, self.org_id)
                except Exception as error:
                    status.stop()
                    raise error
            if config.log_info:
                console.print("[bold green]" + str(self._org))
        return self._org

    @property
    def project(self) -> RBProject:
        """Get project object."""
        if not self._project:
            console = Console()
            with console.status("Fetching project") as status:
                try:
                    self._project = RBProjectImpl(
                        self.context, self.org_id, self.project_id
                    )
                except Exception as error:
                    status.stop()
                    raise error
            if config.log_info:
                console.print("[bold green]" + str(self._project))
        return self._project

    def initialize_project(self, org: RBOrganization, project: RBProject) -> None:
        """Initialize local project."""
        assert_validation(
            not os.path.isdir(self._rb_dir), f"Already a RedBrick project {self.path}"
        )

        os.makedirs(self._rb_dir)
        self.conf.save()

        self.conf.set_section("org", {"id": project.org_id})
        self.conf.set_section("project", {"id": project.project_id})

        self.conf.save()

        self._org = org
        self._project = project

        logger.info(
            f"Successfully initialized {project} in {self.path}\nURL: {project.url}"
        )
