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


class SettingsControllerInterface(ABC):
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
