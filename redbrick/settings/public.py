"""Public interface to settings module."""
from redbrick.common.context import RBContext
from redbrick.common.settings import LabelValidation, HangingProtocol


class Settings:
    """Primary interface to project settings."""

    def __init__(self, context: RBContext, org_id: str, project_id: str) -> None:
        """Construct Settings object."""
        self.context = context
        self.org_id = org_id
        self.project_id = project_id

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
        return self.context.settings.get_label_validation(self.org_id, self.project_id)

    @label_validation.setter
    def label_validation(self, label_validation: LabelValidation) -> None:
        """Label Validation."""
        self.context.settings.set_label_validation(
            self.org_id, self.project_id, label_validation
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
        return self.context.settings.get_hanging_protocol(self.org_id, self.project_id)

    @hanging_protocol.setter
    def hanging_protocol(self, hanging_protocol: HangingProtocol) -> None:
        """Hanging Protocol."""
        self.context.settings.set_hanging_protocol(
            self.org_id, self.project_id, hanging_protocol
        )

    def toggle_reference_standard_task(self, task_id: str, enable: bool) -> None:
        """Toggle reference standard task."""
        self.context.settings.toggle_reference_standard_task(
            self.org_id, self.project_id, task_id, enable
        )
