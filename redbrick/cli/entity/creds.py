"""CLI credentials handler."""
import os
from typing import Dict, List
from configparser import ConfigParser

from redbrick.common.context import RBContext


class CLICredentials:
    """CLICredentials entity."""

    _creds_file: str
    _creds: ConfigParser

    ENV_VAR: str = "REDBRICK_PROFILE"
    DEFAULT_PROFILE: str = "default"

    def __init__(self, creds_file: str) -> None:
        """Initialize CLICredentials."""
        self._creds_file = creds_file
        self._creds = ConfigParser()

        if self.exists:
            self._creds.read(self._creds_file)

    @property
    def exists(self) -> bool:
        """Boolean flag to indicate if credentials file exists."""
        if os.path.exists(self._creds_file):
            if os.path.isfile(self._creds_file):
                return True
            raise Exception(f"Not a file {self._creds_file}")
        return False

    @property
    def profile_names(self) -> List[str]:
        """List of all profiles."""
        return [
            section
            for section in self._creds.sections()
            if section != self.DEFAULT_PROFILE
        ]

    @property
    def selected_profile(self) -> str:
        """Get name of default selected profile."""
        assert self.exists, "Credentials file does not exist"
        profile = os.environ.get(self.ENV_VAR)
        if not profile:
            assert (
                self.DEFAULT_PROFILE in self._creds
                and "profile" in self._creds[self.DEFAULT_PROFILE]
            ), f"{self.DEFAULT_PROFILE} profile / {self.ENV_VAR} env not present"
            profile = self._creds[self.DEFAULT_PROFILE]["profile"]

        return profile

    @property
    def org_id(self) -> str:
        """Get org_id of default profile."""
        return self.get_profile(self.selected_profile)["org"].strip().lower()

    @property
    def context(self) -> RBContext:
        """Get SDK context."""
        return RBContext(
            api_key=self.get_profile(self.selected_profile)["key"].strip(),
            url=self.get_profile(self.selected_profile)["url"].strip().rstrip("/"),
        )

    def get_profile(self, profile_name: str) -> Dict[str, str]:
        """Get profile object from profile name."""
        assert (
            profile_name in self._creds
            and "key" in self._creds[profile_name]
            and "org" in self._creds[profile_name]
            and "url" in self._creds[profile_name]
        ), f"Profile not present / invalid profile in credentials : {profile_name}"
        return dict(self._creds[profile_name].items())

    def add_profile(
        self, profile_name: str, api_key: str, org_id: str, url: str
    ) -> None:
        """Add profile to credentials."""
        assert profile_name not in self.profile_names, "Profile already exists"
        self._creds[profile_name] = {
            "key": api_key.strip(),
            "org": org_id.strip().lower(),
            "url": url.strip().rstrip("/"),
        }

    def remove_profile(self, profile_name: str) -> None:
        """Remove profile from credentials."""
        assert profile_name in self.profile_names, "Profile does not exist"
        self._creds.pop(profile_name)

    def set_default(self, profile_name: str) -> None:
        """Set default profile in credentials."""
        assert profile_name in self.profile_names, "Profile does not exist"
        self._creds[self.DEFAULT_PROFILE] = {"profile": profile_name}

    def save(self) -> None:
        """Save credentials."""
        creds_dir = os.path.dirname(self._creds_file)
        if os.path.exists(creds_dir):
            if not os.path.isdir(creds_dir):
                raise Exception(f"Not a directory {creds_dir}")
        else:
            os.makedirs(creds_dir)

        profiles = self.profile_names
        if profiles:
            if (
                self.DEFAULT_PROFILE not in self._creds
                or "profile" not in self._creds[self.DEFAULT_PROFILE]
                or self._creds[self.DEFAULT_PROFILE]["profile"] not in profiles
            ):
                self.set_default(profiles[0])
            with open(self._creds_file, "w", encoding="utf-8") as creds:
                self._creds.write(creds)
        else:
            self.remove()

    def remove(self) -> None:
        """Remove credentials."""
        assert self.exists, "Credentials file does not exist"
        os.remove(self._creds_file)
