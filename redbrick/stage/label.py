"""Label stage."""

from dataclasses import dataclass, field
import json
from typing import Any, Dict, Optional, Union

from redbrick.common.member import ProjectMember
from redbrick.common.stage import Stage
from redbrick.types.taxonomy import Taxonomy


@dataclass
class LabelStage(Stage):
    """Label Stage (Sub class of :obj:`~redbrick.Stage`).

    :ivar str stage_name: Label stage name.
    :ivar Union[bool, str] on_submit: The next stage for the task when submitted in current stage.
        If True (default), the task will go to ground truth.
        If False, the task will be archived.
    :ivar `redbrick.LabelStage.Config` config: Label stage config.
    """

    @dataclass
    class Config(Stage.Config):
        """Label Stage Config.

        Parameters
        --------------
        auto_assignment: Optional[bool]
            Enable task auto assignment. (Default: True)

        auto_assignment_queue_size: Optional[int]
            Task auto-assignment queue size. (Default: 5)

        show_uploaded_annotations: Optional[bool]
            Show uploaded annotations to users. (Default: True)

        read_only_labels_edit_access: Optional[ProjectMember.Role]
            Access level to change the read only labels. (Default: None)

        is_pre_label: Optional[bool]
            Is pre-labeling stage. (Default: False)

        is_consensus_label: Optional[bool]
            Is consensus-labeling stage. (Default: False)
        """

        auto_assignment: Optional[bool] = None
        auto_assignment_queue_size: Optional[int] = None
        show_uploaded_annotations: Optional[bool] = None
        read_only_labels_edit_access: Optional[ProjectMember.Role] = None
        is_pre_label: Optional[bool] = None
        is_consensus_label: Optional[bool] = None

        @classmethod
        def from_entity(
            cls, entity: Optional[Dict] = None, taxonomy: Optional[Taxonomy] = None
        ) -> "LabelStage.Config":
            """Get object from entity."""
            if not entity:
                return cls()
            return cls(
                auto_assignment=entity.get("autoAssign"),
                auto_assignment_queue_size=entity.get("queueSize"),
                show_uploaded_annotations=(
                    None
                    if entity.get("blindedAnnotation") is None
                    else not entity["blindedAnnotation"]
                ),
                read_only_labels_edit_access=(
                    ProjectMember.Role(
                        "MEMBER"
                        if entity["roLabelEditPerm"] == "LABELER"
                        else entity["roLabelEditPerm"]
                    )
                    if entity.get("roLabelEditPerm")
                    else None
                ),
                is_pre_label=(
                    None if entity.get("isPreLabel") is None else entity["isPreLabel"]
                ),
                is_consensus_label=(
                    None
                    if entity.get("isConsensusLabel") is None
                    else entity["isConsensusLabel"]
                ),
            )

        def to_entity(self, taxonomy: Optional[Taxonomy] = None) -> Dict:
            """Get entity from object."""
            entity: Dict[str, Any] = {}
            if self.auto_assignment is not None:
                entity["autoAssign"] = self.auto_assignment
            if self.auto_assignment_queue_size is not None:
                entity["queueSize"] = self.auto_assignment_queue_size
            if self.show_uploaded_annotations is not None:
                entity["blindedAnnotation"] = not self.show_uploaded_annotations
            if self.read_only_labels_edit_access:
                entity["roLabelEditPerm"] = (
                    "LABELER"
                    if self.read_only_labels_edit_access == ProjectMember.Role.MEMBER
                    else self.read_only_labels_edit_access.value
                )
            if self.is_pre_label is not None:
                entity["isPreLabel"] = self.is_pre_label
            if self.is_consensus_label is not None:
                entity["isConsensusLabel"] = self.is_consensus_label
            return entity

    stage_name: str
    on_submit: Union[bool, str] = True
    config: Stage.Config = field(default_factory=Config.from_entity)

    BRICK_NAME = "manual-labeling"

    @classmethod
    def from_entity(
        cls, entity: Dict, taxonomy: Optional[Taxonomy] = None
    ) -> "LabelStage":
        """Get object from entity"""
        config = entity.get("stageConfig")
        if config and isinstance(config, str):
            config = json.loads(config)
        return cls(
            stage_name=entity["stageName"],
            on_submit=cls._get_next_stage_external(entity["routing"]["nextStageName"]),
            config=cls.Config.from_entity(config or {}, taxonomy),
        )

    def to_entity(self, taxonomy: Optional[Taxonomy] = None) -> Dict:
        """Get entity from object."""
        return {
            "brickName": self.BRICK_NAME,
            "stageName": self.stage_name,
            "routing": {
                "nextStageName": self._get_next_stage_internal(self.on_submit),
            },
            "stageConfig": self.config.to_entity(taxonomy),
        }
