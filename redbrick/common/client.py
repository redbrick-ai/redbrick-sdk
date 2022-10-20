"""Graphql Client responsible for make API requests."""
import time
from typing import Dict
import requests  # type: ignore

import aiohttp
import tenacity
from tenacity.retry import retry_if_not_exception_type
from tenacity.stop import stop_after_attempt
from tenacity.wait import wait_exponential

from redbrick import __version__ as sdk_version  # pylint: disable=cyclic-import
from redbrick.utils.logging import log_error, logger
from redbrick.common.constants import DEFAULT_URL, MAX_RETRY_ATTEMPTS, PEERLESS_ERRORS


class RBClient:
    """Client to communicate with RedBrick AI GraphQL Server."""

    def __init__(self, api_key: str, url: str) -> None:
        """Construct RBClient."""
        self.url = (url or DEFAULT_URL).rstrip("/") + "/graphql/"
        self.session = requests.Session()

        self.api_key = api_key
        assert (
            len(self.api_key) == 43
        ), "Invalid Api Key length, make sure you've copied it correctly"

    def __del__(self) -> None:
        """Garbage collect and close session."""
        self.session.close()

    @property
    def headers(self) -> Dict:
        """Get request headers."""
        return {"RB-SDK-Version": sdk_version, "ApiKey": self.api_key}

    @tenacity.retry(
        reraise=True,
        stop=stop_after_attempt(MAX_RETRY_ATTEMPTS),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_not_exception_type(PEERLESS_ERRORS),
    )
    def execute_query(
        self, query: str, variables: Dict, raise_for_error: bool = True
    ) -> Dict:
        """Execute a graphql query."""
        start_time = time.time()
        logger.debug("Executing: " + query.strip().split("\n")[0])
        response = self.session.post(
            self.url,
            headers=self.headers,
            json={"query": query, "variables": variables},
        )
        self._check_status_msg(response.status_code, start_time)
        return self._process_json_response(response.json(), raise_for_error)

    @tenacity.retry(
        reraise=True,
        stop=stop_after_attempt(MAX_RETRY_ATTEMPTS),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_not_exception_type(PEERLESS_ERRORS),
    )
    async def execute_query_async(
        self,
        aio_session: aiohttp.ClientSession,
        query: str,
        variables: Dict,
        raise_for_error: bool = True,
    ) -> Dict:
        """Execute a graphql query using asyncio."""
        start_time = time.time()
        logger.debug("Executing async: " + query.strip().split("\n")[0])
        async with aio_session.post(
            self.url,
            headers=self.headers,
            json={"query": query, "variables": variables},
        ) as response:
            self._check_status_msg(response.status, start_time)
            return self._process_json_response(await response.json(), raise_for_error)

    @staticmethod
    def _check_status_msg(response_status: int, start_time: float) -> None:
        total_time = time.time() - start_time
        logger.debug(f"Response status: {response_status} took {total_time} seconds")
        if response_status >= 500:
            if total_time >= 24:
                raise TimeoutError(
                    "Request timed out. Please consider using lower concurrency"
                )
            raise ConnectionError(
                "Internal Server Error: You are probably using an invalid API key"
            )
        if response_status == 403:
            raise PermissionError("Problem authenticating with Api Key")

    @staticmethod
    def _process_json_response(
        response_data: Dict, raise_for_error: bool = True
    ) -> Dict:
        """Process JSON resonse."""
        if "errors" in response_data:
            errors = []
            for error in response_data["errors"]:
                errors.append(error["message"])
                log_error(error["message"])

            if raise_for_error:
                raise ValueError("\n".join(errors))

            del response_data["errors"]

        res = {}
        if "data" in response_data:
            res = response_data["data"]
        else:
            res = response_data
        return res
