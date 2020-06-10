"""Getting data from redbrick api."""

import redbrick
from dataclasses import dataclass, asdict
from typing import Dict, List, Any
import requests
import numpy as np  # type: ignore

target_url = "https://redbrick-backend.herokuapp.com/graphql/"


@dataclass
class GraphQLQuery:
    """Query to execute on GraphQL."""

    query: str
    variables: Dict


@dataclass
class DataPoint:
    """A Datapoint returned by GraphQL query."""

    image_url: str
    labels: str


def get_datapoint_ids(org_id: str, label_set_name: str) -> List[str]:
    """Get all data points in the label set."""
    query_string = """
        query ($orgId:UUID!, $name:String!) {
            customGroup(orgId: $orgId, name: $name) {
                datapoints(skip:0, first:-1) {
                    dpId
                }
            }
        }
    """

    query_variables = {"orgId": org_id, "name": label_set_name}
    query = GraphQLQuery(query_string, query_variables)

    result = execute_query(query)

    all_dp_ids = [dp["dpId"] for dp in result["customGroup"]["datapoints"]]
    return all_dp_ids


def get_datapoint(org_id: str, label_set_name: str, dp_id: str) -> DataPoint:
    """Get data needed for a specific data point."""
    query_string = """
        query ($orgId: UUID!, $dpId: UUID!, $name:String!) {
            labelData(orgId: $orgId, dpId: $dpId, customGroupName: $name) {
                blob
                dataPoint {
                    items(presigned:true)
                }
            }
        }
    """
    query_variables = {"orgId": org_id, "name": label_set_name, "dpId": dp_id}
    query = GraphQLQuery(query_string, query_variables)
    result = execute_query(query)
    return DataPoint(
        labels=result["labelData"]["blob"],
        image_url=result["labelData"]["dataPoint"]["items"][0],
    )


def execute_query(query: GraphQLQuery) -> Any:
    """Execute a graphql query."""
    client = redbrick.client.RedBrickClient()
    headers = {"ApiKey": client.api_key}
    try:
        response = requests.post(target_url, headers=headers, json=asdict(query),)
        return response.json()["data"]
    except ValueError:
        print(response.content)
        print(response.status_code)
