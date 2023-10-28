"""Tests for `redbrick.utils.rb_tax_utils`."""
import pytest

from redbrick.utils import rb_tax_utils


@pytest.mark.parametrize("is_new", [True, False])
def test_format_taxonomy(is_new):
    common_keys = ["orgId", "name", "createdAt", "archived", "isNew"]
    v2 = ["taxId", "studyClassify", "seriesClassify", "instanceClassify", "objectTypes"]
    v1 = [
        "version",
        "categories",
        "attributes",
        "taskCategories",
        "taskAttributes",
        "colorMap",
    ]
    taxonomy_skeleton = {k: "mock" for k in (common_keys + v2 + v1)}
    taxonomy_skeleton["isNew"] = is_new

    result = rb_tax_utils.format_taxonomy(taxonomy_skeleton)
    if is_new:
        assert set(result) == set(common_keys + v2)
    else:
        assert set(result) == set(common_keys + v1)


def test_validate_attribute():
    attribute = {"name": "Attribute1", "attrType": "TypeA", "attrId": "ID1"}
    message = "Attribute1"
    # No exception should be raised
    rb_tax_utils.validate_attribute(attribute, message)


@pytest.mark.parametrize("missing", ["name", "attrType", "attrId"])
def test_validate_attribute_missing_attr(missing):
    attribute = {"name": "Attribute1", "attrType": "TypeA", "attrId": "ID1"}
    message = "Attribute1"
    attribute.pop(missing, None)
    # Exception with the expected message should be raised
    with pytest.raises(ValueError, match=f"Attribute1 has no `{missing}`"):
        rb_tax_utils.validate_attribute(attribute, message)


def test_validate_taxonomy():
    study_classify = [{"name": "Study1", "attrType": "TypeA", "attrId": "ID1"}]
    series_classify = [{"name": "Series1", "attrType": "TypeB", "attrId": "ID2"}]
    instance_classify = [{"name": "Instance1", "attrType": "TypeC", "attrId": "ID3"}]
    object_types = [
        {
            "category": "CategoryA",
            "classId": "Class1",
            "labelType": "TypeX",
            "attributes": [],
        }
    ]
    # No exception should be raised
    rb_tax_utils.validate_taxonomy(
        study_classify, series_classify, instance_classify, object_types
    )


def test_validate_taxonomy_empty():
    study_classify = []
    series_classify = []
    instance_classify = []
    object_types = []
    # No exception should be raised
    rb_tax_utils.validate_taxonomy(
        study_classify, series_classify, instance_classify, object_types
    )


@pytest.mark.parametrize("missing", ["category", "classId", "labelType"])
def test_validate_taxonomy_missing_object_types_attr(missing):
    study_classify = [{"name": "Study1", "attrType": "TypeA", "attrId": "ID1"}]
    series_classify = [{"name": "Series1", "attrType": "TypeB", "attrId": "ID2"}]
    instance_classify = [{"name": "Instance1", "attrType": "TypeC", "attrId": "ID3"}]
    object_types = [
        {
            "category": "CategoryA",
            "classId": "Class1",
            "labelType": "TypeX",
            "attributes": [],
        }
    ]
    object_types[0].pop(missing, None)
    with pytest.raises(ValueError):
        rb_tax_utils.validate_taxonomy(
            study_classify, series_classify, instance_classify, object_types
        )
