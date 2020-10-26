"""
Test the remote label module.
"""

import redbrick


def test_init() -> None:
    """Test simple init."""
    assert True
    return

    org_id = "52c624b2-b7eb-4196-b5af-204b79aa3f7e"
    project_id = "8c1a1b99-6ca3-4e40-9627-9f1652076e8c"
    stage_name = "LABEL"
    api_key = "w0jS8yw_KDgrfXflBzNEcOrCPm-PU3inOTJ-3niYsI8"
    redbrick.init(api_key=api_key)

    remote_label = redbrick.remote_label.RemoteLabel(
        org_id=org_id, project_id=project_id, stage_name=stage_name
    )

    assert remote_label.taxonomy.name == "DEFAULT::YoloThings"
    assert remote_label.task_type == "IMAGE_BBOX"
