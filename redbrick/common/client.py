"""Graphql Client responsible for make API requests."""


from typing import Dict, Any
import requests
import aiohttp


class RBClient:
    """Client to communicate with RedBrick AI GraphQL Server."""

    def __init__(self, api_key: str, url: str, retry_count: int = 5,) -> None:
        """Construct RBClient."""
        self.api_key = api_key
        self.url = url.rstrip("/") + "/graphql/"

    def execute_query(self, query: str, variables: Dict[str, Any]) -> Any:
        """Execute a graphql query."""
        headers = {"ApiKey": self.api_key}

        try:
            response = requests.post(
                self.url, headers=headers, json={"query": query, "variables": variables}
            )
            res = {}

            if "errors" in response.json():
                raise ValueError(response.json()["errors"][0]["message"])
            elif "data" in response.json():
                res = response.json()["data"]
            else:
                res = response.json()
            return res
        except ValueError:
            # print(response.content)
            # print(response.status_code)
            raise

    async def execute_query_async(
        self, aio_client: aiohttp.ClientSession, query: str, variables: Dict[str, Any]
    ) -> Any:
        """Execute a graphql query using asyncio."""
        headers = {"ApiKey": self.api_key}

        try:
            async with aio_client.post(
                self.url, headers=headers, json={"query": query, "variables": variables}
            ) as response:

                response_data = await response.json()
                res = {}
                if "errors" in response_data:
                    raise ValueError(response_data["errors"][0]["message"])
                elif "data" in response_data:
                    res = response_data["data"]
                else:
                    res = response_data
                return res
        except ValueError:
            # print(response.content)
            # print(response.status_code)
            raise
