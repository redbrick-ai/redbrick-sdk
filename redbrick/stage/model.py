"""Model stage."""

from dataclasses import dataclass, field
import json
from typing import Any, Dict, List, Optional, TypedDict, Union

from redbrick.common.stage import Stage
from redbrick.types.taxonomy import Taxonomy


CT_SEGMENTATOR_CATEGORIES = {
    1: "spleen",
    2: "kidney_right",
    3: "kidney_left",
    4: "gallbladder",
    5: "liver",
    6: "stomach",
    7: "pancreas",
    8: "adrenal_gland_right",
    9: "adrenal_gland_left",
    10: "lung_upper_lobe_left",
    11: "lung_lower_lobe_left",
    12: "lung_upper_lobe_right",
    13: "lung_middle_lobe_right",
    14: "lung_lower_lobe_right",
    15: "esophagus",
    16: "trachea",
    17: "thyroid_gland",
    18: "small_bowel",
    19: "duodenum",
    20: "colon",
    21: "urinary_bladder",
    22: "prostate",
    23: "kidney_cyst_left",
    24: "kidney_cyst_right",
    25: "sacrum",
    26: "vertebrae_S1",
    27: "vertebrae_L5",
    28: "vertebrae_L4",
    29: "vertebrae_L3",
    30: "vertebrae_L2",
    31: "vertebrae_L1",
    32: "vertebrae_T12",
    33: "vertebrae_T11",
    34: "vertebrae_T10",
    35: "vertebrae_T9",
    36: "vertebrae_T8",
    37: "vertebrae_T7",
    38: "vertebrae_T6",
    39: "vertebrae_T5",
    40: "vertebrae_T4",
    41: "vertebrae_T3",
    42: "vertebrae_T2",
    43: "vertebrae_T1",
    44: "vertebrae_C7",
    45: "vertebrae_C6",
    46: "vertebrae_C5",
    47: "vertebrae_C4",
    48: "vertebrae_C3",
    49: "vertebrae_C2",
    50: "vertebrae_C1",
    51: "heart",
    52: "aorta",
    53: "pulmonary_vein",
    54: "brachiocephalic_trunk",
    55: "subclavian_artery_right",
    56: "subclavian_artery_left",
    57: "common_carotid_artery_right",
    58: "common_carotid_artery_left",
    59: "brachiocephalic_vein_left",
    60: "brachiocephalic_vein_right",
    61: "atrial_appendage_left",
    62: "superior_vena_cava",
    63: "inferior_vena_cava",
    64: "portal_vein_and_splenic_vein",
    65: "iliac_artery_left",
    66: "iliac_artery_right",
    67: "iliac_vena_left",
    68: "iliac_vena_right",
    69: "humerus_left",
    70: "humerus_right",
    71: "scapula_left",
    72: "scapula_right",
    73: "clavicula_left",
    74: "clavicula_right",
    75: "femur_left",
    76: "femur_right",
    77: "hip_left",
    78: "hip_right",
    79: "spinal_cord",
    80: "gluteus_maximus_left",
    81: "gluteus_maximus_right",
    82: "gluteus_medius_left",
    83: "gluteus_medius_right",
    84: "gluteus_minimus_left",
    85: "gluteus_minimus_right",
    86: "autochthon_left",
    87: "autochthon_right",
    88: "iliopsoas_left",
    89: "iliopsoas_right",
    90: "brain",
    91: "skull",
    92: "rib_right_4",
    93: "rib_right_3",
    94: "rib_left_1",
    95: "rib_left_2",
    96: "rib_left_3",
    97: "rib_left_4",
    98: "rib_left_5",
    99: "rib_left_6",
    100: "rib_left_7",
    101: "rib_left_8",
    102: "rib_left_9",
    103: "rib_left_10",
    104: "rib_left_11",
    105: "rib_left_12",
    106: "rib_right_1",
    107: "rib_right_2",
    108: "rib_right_5",
    109: "rib_right_6",
    110: "rib_right_7",
    111: "rib_right_8",
    112: "rib_right_9",
    113: "rib_right_10",
    114: "rib_right_11",
    115: "rib_right_12",
    116: "sternum",
    117: "costal_cartilages",
}


@dataclass
class ModelStage(Stage):
    """Model Stage.

    Parameters
    --------------
    stage_name: str
        Stage name.

    on_submit: Union[bool, str] = True
        The next stage for the task when submitted in current stage.
        If True, the task will go to ground truth.
        If False, the task will be archived.

    config: Config = Config()
        Stage config.
    """

    class ModelTaxonomyMap(TypedDict):
        """Model taxonomy map.

        Parameters
        --------------
        modelCategory: str
            Model category name.

        rbCategory: str
            Category name as it appears in the RedBrick project's taxonomy.
        """

        modelCategory: str
        rbCategory: str

    @dataclass
    class Config(Stage.Config):
        """Model Stage Config.

        Parameters
        --------------
        name: str
            Model name.

        url: Optional[str]
            URL for self-hosted model.

        taxonomy_objects: Optional[List[ModelStage.ModelTaxonomyMap]]
            Mapping of model classes to project's taxonomy objects.
        """

        name: str
        url: Optional[str] = None
        taxonomy_objects: Optional[List["ModelStage.ModelTaxonomyMap"]] = None

        CT_SEGMENTATOR = "TOTAL_SEGMENTATOR"  # Boost

        @classmethod
        def from_entity(
            cls, entity: Optional[Dict] = None, taxonomy: Optional[Taxonomy] = None
        ) -> "ModelStage.Config":
            """Get object from entity."""
            if not entity:
                raise ValueError("Model name is required")
            return cls(
                name=entity["name"],
                url=entity.get("url"),
                taxonomy_objects=ModelStage.Config._get_external_taxonomy_map(
                    entity.get("taxonomyObjects"), taxonomy
                ),
            )

        def to_entity(self, taxonomy: Optional[Taxonomy] = None) -> Dict:
            """Get entity from object."""
            entity: Dict[str, Any] = {"name": self.name}
            if self.url is not None:
                entity["url"] = self.url
            if self.taxonomy_objects is not None:
                entity["taxonomyObjects"] = self._get_internal_taxonomy_map(taxonomy)
            return entity

        @staticmethod
        def _get_external_taxonomy_map(
            taxonomy_objects: Optional[List[Dict]], taxonomy: Optional[Taxonomy] = None
        ) -> Optional[List["ModelStage.ModelTaxonomyMap"]]:
            """Convert taxonomy map to external format."""
            if (
                taxonomy_objects is None
                or not isinstance(taxonomy_objects, list)
                or any(not isinstance(obj, dict) for obj in taxonomy_objects)
            ):
                return None

            assert taxonomy, "Taxonomy is required"

            category_map = {
                obj["classId"]: obj["category"] for obj in taxonomy["objectTypes"]
            }
            for obj in taxonomy_objects:
                assert isinstance(
                    obj.get("category"), str
                ), f"Invalid category: {obj.get('category')}"
                assert (
                    obj.get("classid") in category_map
                ), f"Class ID: {obj.get('classid')} does not exist in the taxonomy"

            return [
                {
                    "modelCategory": obj["category"],
                    "rbCategory": category_map[obj["classid"]],
                }
                for obj in taxonomy_objects
            ]

        def _get_internal_taxonomy_map(
            self, taxonomy: Optional[Taxonomy] = None
        ) -> Optional[List[Dict]]:
            """Convert taxonomy map to internal format."""
            if self.taxonomy_objects is None:
                return None

            assert taxonomy, "Taxonomy is required"

            if self.name == self.CT_SEGMENTATOR:
                ts_cats = set(CT_SEGMENTATOR_CATEGORIES.values())
                for obj in self.taxonomy_objects:
                    assert (
                        obj["modelCategory"] in ts_cats
                    ), f"{obj['modelCategory']} is not a valid CT Segmentator category"

            category_map = {
                obj["category"]: obj["classId"]
                for obj in taxonomy["objectTypes"]
                if obj["labelType"] == "SEGMENTATION" and not obj.get("archived")
            }
            for obj in self.taxonomy_objects:
                assert (
                    obj["rbCategory"] in category_map
                ), f"SEGMENTATION category {obj['rbCategory']} does not exist or is archived"

            return [
                {
                    "category": obj["modelCategory"],
                    "classid": category_map[obj["rbCategory"]],
                }
                for obj in self.taxonomy_objects
            ]

    stage_name: str
    on_submit: Union[bool, str] = True
    config: Config = field(default_factory=Config.from_entity)

    BRICK_NAME = "model"

    @classmethod
    def from_entity(
        cls, entity: Dict, taxonomy: Optional[Taxonomy] = None
    ) -> "ModelStage":
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
