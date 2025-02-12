"""Public interface to settings module."""

from typing import Optional

from redbrick.common.entities import RBProject
from redbrick.common.settings import Settings, LabelValidation, HangingProtocol, Webhook


class SettingsImpl(Settings):
    """Primary interface to project settings."""

    def __init__(self, project: RBProject) -> None:
        """Construct Settings object."""
        self.project = project
        self.context = self.project.context

    @property
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
        return self.context.settings.get_label_validation(
            self.project.org_id, self.project.project_id
        )

    @label_validation.setter
    def label_validation(self, label_validation: LabelValidation) -> None:
        """Label Validation."""
        self.context.settings.set_label_validation(
            self.project.org_id, self.project.project_id, label_validation
        )

    @property
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
        return self.context.settings.get_hanging_protocol(
            self.project.org_id, self.project.project_id
        )

    @hanging_protocol.setter
    def hanging_protocol(self, hanging_protocol: HangingProtocol) -> None:
        """Hanging Protocol."""
        self.context.settings.set_hanging_protocol(
            self.project.org_id, self.project.project_id, hanging_protocol
        )

    @property
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
        return self.context.settings.get_webhook_settings(
            self.project.org_id, self.project.project_id
        )

    @webhook.setter
    def webhook(self, webhook: Webhook) -> None:
        """Project webhook."""
        if webhook["enabled"]:
            assert webhook["url"], "Webhook URL is required."
        else:
            webhook["url"] = None

        self.context.settings.set_webhook_settings(
            self.project.org_id, self.project.project_id, webhook
        )

    def toggle_reference_standard_task(self, task_id: str, enable: bool) -> None:
        """Toggle reference standard task."""
        self.context.settings.toggle_reference_standard_task(
            self.project.org_id, self.project.project_id, task_id, enable
        )

    @property
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
        return self.context.settings.get_sibling_tasks_count(
            self.project.org_id, self.project.project_id
        )

    @task_duplication.setter
    def task_duplication(self, count: Optional[int]) -> None:
        """Hanging Protocol."""
        if not count or count <= 1:
            count = None
        self.context.settings.set_sibling_tasks_count(
            self.project.org_id, self.project.project_id, count
        )
