"""Abstract interface to settings."""

from typing import TypedDict, Optional
from abc import ABC, abstractmethod


class LabelValidation(TypedDict):
    """Label Validation."""

    enabled: bool
    enforce: bool
    script: Optional[str]


class HangingProtocol(TypedDict):
    """Hanging Protocol."""

    enabled: bool
    script: Optional[str]


class Webhook(TypedDict):
    """Project webhook."""

    enabled: bool
    url: Optional[str]


class SettingsRepo(ABC):
    """Abstract interface to define methods for Settings."""

    @abstractmethod
    def get_label_validation(self, org_id: str, project_id: str) -> LabelValidation:
        """Get project label validation setting."""

    @abstractmethod
    def set_label_validation(
        self, org_id: str, project_id: str, label_validation: LabelValidation
    ) -> None:
        """Set project label validation setting."""

    @abstractmethod
    def get_hanging_protocol(self, org_id: str, project_id: str) -> HangingProtocol:
        """Get project hanging protocol setting."""

    @abstractmethod
    def set_hanging_protocol(
        self, org_id: str, project_id: str, hanging_protocol: HangingProtocol
    ) -> None:
        """Set project hanging protocol setting."""

    @abstractmethod
    def get_webhook_settings(self, org_id: str, project_id: str) -> Webhook:
        """Get webhook setting."""

    @abstractmethod
    def set_webhook_settings(
        self, org_id: str, project_id: str, webhook: Webhook
    ) -> None:
        """Set webhook setting."""

    @abstractmethod
    def toggle_reference_standard_task(
        self, org_id: str, project_id: str, task_id: str, enable: bool
    ) -> None:
        """Toggle reference standard task."""

    @abstractmethod
    def get_sibling_tasks_count(self, org_id: str, project_id: str) -> Optional[int]:
        """Get sibling tasks count setting."""

    @abstractmethod
    def set_sibling_tasks_count(
        self, org_id: str, project_id: str, count: Optional[int] = None
    ) -> None:
        """Set sibling tasks count setting."""


class Settings(ABC):
    """Abstract interface to Settings module."""

    @property
    @abstractmethod
    def label_validation(self) -> LabelValidation:
        """Label Validation.

        Use custom label validation to prevent annotation errors in real-time. Please visit
        `label validation <https://docs.redbrickai.com/projects/custom-label-validation>`_
        for more info.

        Format: {"enabled": bool, "enforce": bool, "script": str}

        .. tab:: Get

            .. code:: python

                project = redbrick.get_project(org_id, project_id, api_key, url)
                label_validation = project.settings.label_validation


        .. tab:: Set

            .. code:: python

                project = redbrick.get_project(org_id, project_id, api_key, url)
                project.settings.label_validation = label_validation

        """

    @label_validation.setter
    @abstractmethod
    def label_validation(self, label_validation: LabelValidation) -> None:
        """Label Validation."""

    @property
    @abstractmethod
    # pylint: disable=line-too-long
    def hanging_protocol(self) -> HangingProtocol:
        """Hanging Protocol.

        Use hanging protocol to define the visual layout of tool. Please visit
        `hanging protocol <https://docs.redbrickai.com/annotation/layout-and-multiple-volumes/custom-hanging-protocol>`_
        for more info.

        Format: {"enabled": bool, "script": str}

        .. tab:: Get

            .. code:: python

                project = redbrick.get_project(org_id, project_id, api_key, url)
                hanging_protocol = project.settings.hanging_protocol


        .. tab:: Set

            .. code:: python

                project = redbrick.get_project(org_id, project_id, api_key, url)
                project.settings.hanging_protocol = hanging_protocol

        """

    @hanging_protocol.setter
    @abstractmethod
    def hanging_protocol(self, hanging_protocol: HangingProtocol) -> None:
        """Hanging Protocol."""

    @property
    @abstractmethod
    # pylint: disable=line-too-long
    def webhook(self) -> Webhook:
        """Project webhook.

        Use webhooks to receive custom events like tasks entering stages, and many more.

        Format: {"enabled": bool, "url": str}

        .. tab:: Get

            .. code:: python

                project = redbrick.get_project(org_id, project_id, api_key, url)
                webhook = project.settings.webhook


        .. tab:: Set

            .. code:: python

                project = redbrick.get_project(org_id, project_id, api_key, url)
                project.settings.webhook = webhook

        """

    @webhook.setter
    @abstractmethod
    def webhook(self, webhook: Webhook) -> None:
        """Project webhook."""

    @abstractmethod
    def toggle_reference_standard_task(self, task_id: str, enable: bool) -> None:
        """Toggle reference standard task."""

    @property
    @abstractmethod
    # pylint: disable=line-too-long
    def task_duplication(self) -> Optional[int]:
        """Sibling task count.

        Use task duplication to create multiple tasks for a single uploaded datapoint. Please visit
        `task duplication <https://docs.redbrickai.com/projects/multiple-labeling/task-duplication>`_
        for more info.

        Format: Optional[int]

        .. tab:: Get

            .. code:: python

                project = redbrick.get_project(org_id, project_id, api_key, url)
                count = project.settings.task_duplication


        .. tab:: Set

            .. code:: python

                project = redbrick.get_project(org_id, project_id, api_key, url)
                project.settings.task_duplication = count

        """

    @task_duplication.setter
    @abstractmethod
    def task_duplication(self, count: Optional[int]) -> None:
        """Sibling task count."""
