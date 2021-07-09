from typing import Optional, List, Dict, Tuple
from redbrick.common.export import ExportControllerInterface
from redbrick.common.client import RBClient


class ExportRepo(ExportControllerInterface):
    """Handle API requests to get export data."""

    def __init__(self, client: RBClient) -> None:
        """Construct ExportRepo."""
        self.client = client

    def get_datapoints_input(
        self,
        org_id: str,
        project_id: str,
        first: int = 50,
        presign: bool = False,
        cursor: Optional[str] = None,
    ) -> Tuple[List[Dict], Optional[str]]:
        """Get datapoints that were uploaded to the project."""
        raise NotImplementedError()

    def get_datapoints_output(
        self,
        org_id: str,
        project_id: str,
        first: int = 50,
        presign: bool = False,
        cursor: Optional[str] = None,
    ) -> Tuple[List[Dict], Optional[str]]:
        """Get datapoints that have made it to the output of the project."""
        query_string = """
        query ($orgId: UUID!, $name: String!,$first: Int, $cursor: String){
        customGroup(orgId: $orgId, name:$name){
            orgId
            name
            dataType
            taskType
            taxonomy {
            categories {
                name
                children{
                name
                classId
                children {
                    name
                    classId
                    children {
                    name
                    classId
                    }
                }
                }

            }
            }

            datapointsPaged(first:$first, after:$cursor) {
            entries {
                dpId
                name
                itemsPresigned:items (presigned:true)
                items(presigned:false)
                labelData(customGroupName: $name){
                createdByEmail
                labels {
                    category
                    attributes {
                        ... on LabelAttributeInt {
                        name
                        valint: value
                        }
                        ... on LabelAttributeBool {
                        name
                        valbool: value
                        }
                        ... on LabelAttributeFloat {
                        name
                        valfloat: value
                        }
                        ... on LabelAttributeString {
                        name
                        valstr: value
                        }
                    }
                    labelid
                    frameindex
                    trackid
                    keyframe
                    taskclassify
                    frameclassify
                    end
                    bbox2d {
                        xnorm
                        ynorm
                        wnorm
                        hnorm
                    }
                    point {
                        xnorm
                        ynorm
                    }
                    polyline {
                        xnorm
                        ynorm
                    }
                    polygon {
                        xnorm
                        ynorm
                    }
                    pixel {
                        imagesize
                        regions
                        holes
                    }
                    ellipse {
                        xcenternorm
                        ycenternorm
                        xnorm
                        ynorm
                        rot
                    }
                    }
                }


            }
            cursor
            }
        }
        }

        """
        # EXECUTE THE QUERY
        query_variables = {
            "orgId": org_id,
            "name": project_id + "-output",
            "cursor": cursor,
            "first": first,
        }

        result = self.client.execute_query(query_string, query_variables)

        return (
            result["customGroup"]["datapointsPaged"]["entries"],
            result["customGroup"]["datapointsPaged"]["cursor"],
        )

    def get_datapoints_latest(
        self,
        org_id: str,
        project_id: str,
        first: int = 50,
        presign: bool = False,
        cursor: Optional[str] = None,
    ) -> Tuple[List[Dict], Optional[str]]:
        """Get the latest datapoints."""
        raise NotImplementedError()
