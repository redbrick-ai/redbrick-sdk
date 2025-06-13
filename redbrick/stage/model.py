"""Model stage."""

from dataclasses import dataclass, field
import json
from typing import Any, Dict, List, Literal, Optional, TypedDict, Union

from redbrick.common.stage import Stage
from redbrick.types.taxonomy import Taxonomy


CT_SEGMENTATOR_SUB_TYPE = Literal[  # pylint: disable=invalid-name
    "total",
    "total_mr",
    "lung_vessels",
    "body",
    "cerebral_bleed",
    "hip_implant",
    "coronary_arteries",
    "pleural_pericard_effusion",
    "head_glands_cavities",
    "head_muscles",
    "headneck_bones_vessels",
    "headneck_muscles",
    "liver_vessels",
    "oculomotor_muscles",
]

CT_SEGMENTATOR_CATEGORIES: Dict[CT_SEGMENTATOR_SUB_TYPE, Dict[int, str]] = {
    "total": {
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
        92: "rib_left_1",
        93: "rib_left_2",
        94: "rib_left_3",
        95: "rib_left_4",
        96: "rib_left_5",
        97: "rib_left_6",
        98: "rib_left_7",
        99: "rib_left_8",
        100: "rib_left_9",
        101: "rib_left_10",
        102: "rib_left_11",
        103: "rib_left_12",
        104: "rib_right_1",
        105: "rib_right_2",
        106: "rib_right_3",
        107: "rib_right_4",
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
    },
    "total_mr": {
        1: "spleen",
        2: "kidney_right",
        3: "kidney_left",
        4: "gallbladder",
        5: "liver",
        6: "stomach",
        7: "pancreas",
        8: "adrenal_gland_right",
        9: "adrenal_gland_left",
        10: "lung_left",
        11: "lung_right",
        12: "esophagus",
        13: "small_bowel",
        14: "duodenum",
        15: "colon",
        16: "urinary_bladder",
        17: "prostate",
        18: "sacrum",
        19: "vertebrae",
        20: "intervertebral_discs",
        21: "spinal_cord",
        22: "heart",
        23: "aorta",
        24: "inferior_vena_cava",
        25: "portal_vein_and_splenic_vein",
        26: "iliac_artery_left",
        27: "iliac_artery_right",
        28: "iliac_vena_left",
        29: "iliac_vena_right",
        30: "humerus_left",
        31: "humerus_right",
        32: "fibula",
        33: "tibia",
        34: "femur_left",
        35: "femur_right",
        36: "hip_left",
        37: "hip_right",
        38: "gluteus_maximus_left",
        39: "gluteus_maximus_right",
        40: "gluteus_medius_left",
        41: "gluteus_medius_right",
        42: "gluteus_minimus_left",
        43: "gluteus_minimus_right",
        44: "autochthon_left",
        45: "autochthon_right",
        46: "iliopsoas_left",
        47: "iliopsoas_right",
        48: "quadriceps_femoris_left",
        49: "quadriceps_femoris_right",
        50: "thigh_medial_compartment_left",
        51: "thigh_medial_compartment_right",
        52: "thigh_posterior_compartment_left",
        53: "thigh_posterior_compartment_right",
        54: "sartorius_left",
        55: "sartorius_right",
        56: "brain",
    },
    "lung_vessels": {
        1: "lung_vessels",
        2: "lung_trachea_bronchia",
    },
    "body": {
        1: "body_trunc",
        2: "body_extremities",
    },
    "cerebral_bleed": {
        1: "intracerebral_hemorrhage",
    },
    "hip_implant": {
        1: "hip_implant",
    },
    "coronary_arteries": {
        1: "coronary_arteries",
    },
    "pleural_pericard_effusion": {
        1: "lung_pleural",
        2: "pleural_effusion",
        3: "pericardial_effusion",
    },
    "head_glands_cavities": {
        1: "eye_left",
        2: "eye_right",
        3: "eye_lens_left",
        4: "eye_lens_right",
        5: "optic_nerve_left",
        6: "optic_nerve_right",
        7: "parotid_gland_left",
        8: "parotid_gland_right",
        9: "submandibular_gland_right",
        10: "submandibular_gland_left",
        11: "nasopharynx",
        12: "oropharynx",
        13: "hypopharynx",
        14: "nasal_cavity_right",
        15: "nasal_cavity_left",
        16: "auditory_canal_right",
        17: "auditory_canal_left",
        18: "soft_palate",
        19: "hard_palate",
    },
    "head_muscles": {
        1: "masseter_right",
        2: "masseter_left",
        3: "temporalis_right",
        4: "temporalis_left",
        5: "lateral_pterygoid_right",
        6: "lateral_pterygoid_left",
        7: "medial_pterygoid_right",
        8: "medial_pterygoid_left",
        9: "tongue",
        10: "digastric_right",
        11: "digastric_left",
    },
    "headneck_bones_vessels": {
        1: "larynx_air",
        2: "thyroid_cartilage",
        3: "hyoid",
        4: "cricoid_cartilage",
        5: "zygomatic_arch_right",
        6: "zygomatic_arch_left",
        7: "styloid_process_right",
        8: "styloid_process_left",
        9: "internal_carotid_artery_right",
        10: "internal_carotid_artery_left",
        11: "internal_jugular_vein_right",
        12: "internal_jugular_vein_left",
    },
    "headneck_muscles": {
        1: "sternocleidomastoid_right",
        2: "sternocleidomastoid_left",
        3: "superior_pharyngeal_constrictor",
        4: "middle_pharyngeal_constrictor",
        5: "inferior_pharyngeal_constrictor",
        6: "trapezius_right",
        7: "trapezius_left",
        8: "platysma_right",
        9: "platysma_left",
        10: "levator_scapulae_right",
        11: "levator_scapulae_left",
        12: "anterior_scalene_right",
        13: "anterior_scalene_left",
        14: "middle_scalene_right",
        15: "middle_scalene_left",
        16: "posterior_scalene_right",
        17: "posterior_scalene_left",
        18: "sterno_thyroid_right",
        19: "sterno_thyroid_left",
        20: "thyrohyoid_right",
        21: "thyrohyoid_left",
        22: "prevertebral_right",
        23: "prevertebral_left",
    },
    "liver_vessels": {
        1: "liver_vessels",
        2: "liver_tumor",
    },
    "oculomotor_muscles": {
        1: "skull",
        2: "eyeball_right",
        3: "lateral_rectus_muscle_right",
        4: "superior_oblique_muscle_right",
        5: "levator_palpebrae_superioris_right",
        6: "superior_rectus_muscle_right",
        7: "medial_rectus_muscle_left",
        8: "inferior_oblique_muscle_right",
        9: "inferior_rectus_muscle_right",
        10: "optic_nerve_left",
        11: "eyeball_left",
        12: "lateral_rectus_muscle_left",
        13: "superior_oblique_muscle_left",
        14: "levator_palpebrae_superioris_left",
        15: "superior_rectus_muscle_left",
        16: "medial_rectus_muscle_right",
        17: "inferior_oblique_muscle_left",
        18: "inferior_rectus_muscle_left",
        19: "optic_nerve_right",
    },
}


@dataclass
class ModelStage(Stage):
    """Model Stage (Sub class of :obj:`~redbrick.Stage`).

    :ivar str stage_name: Model stage name.
    :ivar Union[bool, str] on_submit: The next stage for the task when submitted in current stage.
        If True (default), the task will go to ground truth.
        If False, the task will be archived.
    :ivar `redbrick.ModelStage.Config` config: Model stage config.
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
    class MONAIConfig:
        """MONAI config.

        Parameters
        --------------
        batch_count: Optional[int]
            Number of in-progress tasks.

        target_spacing: List[float]
            Target spacing of images.

        roi_size: List[int]
            ROI size.

        max_epochs: int
            Maximum number of epochs.

        early_stop_patience: int
            Early stop patience.

        training_threshold_count: int
            Training threshold count.
        """

        batch_count: Optional[int] = None
        target_spacing: Optional[List[float]] = None
        roi_size: Optional[List[int]] = None
        max_epochs: Optional[int] = None
        early_stop_patience: Optional[int] = None
        training_threshold_count: Optional[int] = None

        def __post_init__(self) -> None:
            """Post init."""
            if self.batch_count is None:
                self.batch_count = 5
            if self.target_spacing is None:
                self.target_spacing = [1.5, 1.5, 1.5]
            if self.roi_size is None:
                self.roi_size = [96, 96, 96]
            if self.max_epochs is None:
                self.max_epochs = 200
            if self.early_stop_patience is None:
                self.early_stop_patience = 0
            if self.training_threshold_count is None:
                self.training_threshold_count = 5

        @classmethod
        def from_entity(cls, config: Optional[Dict] = None) -> "ModelStage.MONAIConfig":
            """Get object from entity."""
            config = config or {}
            monai = config.get("monaiConfig") or {}
            return cls(
                batch_count=monai.get("batchCount"),
                target_spacing=monai.get("targetSpacing"),
                roi_size=monai.get("roiSize"),
                max_epochs=monai.get("maxEpochs"),
                early_stop_patience=monai.get("earlyStopPatience"),
                training_threshold_count=monai.get("trainingThresholdCount"),
            )

        def to_entity(self) -> Dict:
            """Get entity from object."""
            return {
                "batchCount": self.batch_count,
                "monaiConfig": {
                    "targetSpacing": self.target_spacing,
                    "roiSize": self.roi_size,
                    "maxEpochs": self.max_epochs,
                    "earlyStopPatience": self.early_stop_patience,
                    "trainingThresholdCount": self.training_threshold_count,
                },
            }

    @dataclass
    class Config(Stage.Config):
        """Model Stage Config.

        Parameters
        --------------
        name: str
            Model name.

        version: Optional[str]
            Model version.

        app: Optional[str]
            App name.

        url: Optional[str]
            URL for self-hosted model.

        taxonomy_objects: Optional[List[ModelStage.ModelTaxonomyMap]]
            Mapping of model classes to project's taxonomy objects.

        monai: Optional[ModelStage.MONAIConfig] = None
            MONAI config.
        """

        name: str
        version: Optional[str] = None
        app: Optional[str] = None
        url: Optional[str] = None
        taxonomy_objects: Optional[List["ModelStage.ModelTaxonomyMap"]] = None
        monai: Optional["ModelStage.MONAIConfig"] = None

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
                version=entity.get("version") or "v0",
                app=entity.get("subType"),
                url=entity.get("url"),
                taxonomy_objects=ModelStage.Config._get_external_taxonomy_map(
                    entity.get("taxonomyObjects"), taxonomy
                ),
                monai=(
                    ModelStage.MONAIConfig.from_entity(entity)
                    if entity.get("activeLearning")
                    else None
                ),
            )

        def to_entity(self, taxonomy: Optional[Taxonomy] = None) -> Dict:
            """Get entity from object."""
            entity: Dict[str, Any] = {
                "name": self.name,
                "version": self.version or "v0",
            }
            if self.app is not None:
                entity["subType"] = self.app
            if self.url is not None:
                entity["url"] = self.url
            if self.taxonomy_objects is not None:
                entity["taxonomyObjects"] = self._get_internal_taxonomy_map(taxonomy)
            if self.monai is not None:
                entity["activeLearning"] = True
                entity.update(self.monai.to_entity())

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
                app: CT_SEGMENTATOR_SUB_TYPE = (
                    "total" if self.app is None else self.app  # type: ignore
                )
                assert app in CT_SEGMENTATOR_CATEGORIES, (
                    f"'{self.app}' is not a valid CT Segmentator sub type."
                    + f" Please choose from {CT_SEGMENTATOR_SUB_TYPE}"
                )
                ts_cats = set(CT_SEGMENTATOR_CATEGORIES[app].values())
                for obj in self.taxonomy_objects:
                    assert obj["modelCategory"] in ts_cats, (
                        f"'{obj['modelCategory']}' is not a valid "
                        + f"CT Segmentator ('{app}') category"
                    )

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
    config: Stage.Config = field(default_factory=Config.from_entity)

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
