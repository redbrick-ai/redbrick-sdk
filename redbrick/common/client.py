"""Graphql Client responsible for make API requests."""


from typing import Dict, Any
import requests
import aiohttp


class RBClient:
    """Client to communicate with RedBrick AI GraphQL Server."""

    def __init__(
        self,
        api_key: str,
        url: str,
    ) -> None:
        """Construct RBClient."""
        assert (
            len(api_key) == 43
        ), "Invalid Api Key length, make sure you've copied it correctly"
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

            if response.status_code == 500:
                raise ValueError(
                    "Internal Server Error: You are probably using an invalid API key"
                )
            if response.status_code == 403:
                raise PermissionError("Problem authenticating with Api Key")
            if "errors" in response.json():
                raise ValueError(response.json()["errors"][0]["message"])
            if "data" in response.json():
                res = response.json()["data"]
            else:
                res = response.json()
            return res
        except ValueError as error:
            raise error

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
                if response.status == 500:
                    raise ValueError(
                        "Internal Server Error: You are probably using an invalid API key"
                    )
                if "errors" in response_data:
                    raise ValueError(response_data["errors"][0]["message"])
                if "data" in response_data:
                    res = response_data["data"]
                else:
                    res = response_data
                return res
        except ValueError as error:
            raise error
